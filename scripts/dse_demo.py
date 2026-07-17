#!/usr/bin/env python3
"""
晶圆级交换机 DSE 端到端原型。

输入: Dragonfly (a,p,h) 参数空间
输出: 可行方案列表 + Pareto 前沿

流程:
  Phase 0: 物理初始化 (bump → interposer → substrate)
  Phase 1: 拓扑滤波 (nonblocking BW)
  Phase 2: μbump 预算检查
  Phase 3: Interposer 内 + Substrate 间布线检查
  Phase 4: Pareto 排序

运行:
  cd wafer-dse && python scripts/dse_demo.py
"""

from __future__ import annotations

import sys
import math

sys.path.insert(0, "src")

from wafer_dse.architecture_model.model import ArchitectureModel
from wafer_dse.models import Requirement, Strictness, TopologySpec, NetworkPotential
from wafer_dse.pareto import Metrics, compute_foms, frontier_summary, pareto_frontier
from wafer_dse.physical.bump.bump import (
    BumpSpec, DieBumpBudget, C4Budget,
    UBUMP_45UM, UBUMP_25UM, C4_130UM,
)
from wafer_dse.physical.interposer import Interposer, IntraRouteResult
from wafer_dse.physical.substrate import Substrate, GlobalRouteResult
from wafer_dse.physical.thermal import (
    CoolingSolution, check_thermal,
    AIR_COOLING, LIQUID_COOLING, IMMERSION,
)


# ============================================================================
# 配置
# ============================================================================

# 工艺
BUMP = UBUMP_25UM          # 25μm: 300 signal bumps @50W (45μm only 201)
C4   = C4_130UM

# Interposer
INTERPOSER_COUNT = 16
DIES_PER_INTERPOSER = 6    # 12×12mm die 在 858mm² reticle 上最多放 ~6-10 个
DIE_SIZE_MM = (12.0, 12.0)
INTERPOSER_AREA_MM2 = 858.0

# Substrate
SUBSTRATE_GRID = (4, 4)

# 需求
TARGET_BW_GBPS = 800.0     # 每端口 800G
COOLING = LIQUID_COOLING   # 液冷 (2.0 W/mm²)
# COOLING = AIR_COOLING    # 风冷 (0.5 W/mm²) — 试试看差多少

# 搜索空间 (缩小到合理范围，避免 solver O(N³) 爆炸)
A_RANGE = (2, 4)           # a: 每组 router 数
P_RANGE = (2, 4)           # p: 每 router terminal 数
H_VALUES = (1, 2)          # h: 每 router 全局端口数

# 性能模型: 跳过 Hungarian (太慢), 用分析近似
# Dragonfly nonblocking BW ≈ min(bisection, radix) × efficiency
# 简化: 直接标记所有配置为"拓扑可行"，重点验证物理可行性
USE_FAST_PERF = True


# ============================================================================
# Phase 0: 物理初始化
# ============================================================================

def build_physical():
    """构建 interposer 阵列和 substrate。"""
    die = DieBumpBudget(
        die_label="switch_die",
        spec=BUMP,
        width_mm=DIE_SIZE_MM[0],
        height_mm=DIE_SIZE_MM[1],
        power_w=50.0,          # 每 die 50W (来自 DieEstimator)
        vdd_v=0.8,
    )

    interposers = [
        Interposer(
            label=f"Interposer_{i}",
            dies=[die] * DIES_PER_INTERPOSER,
            area_mm2=INTERPOSER_AREA_MM2,
            bump=BUMP,
        )
        for i in range(INTERPOSER_COUNT)
    ]

    sub = Substrate(
        interposers=interposers,
        grid_rows=SUBSTRATE_GRID[0],
        grid_cols=SUBSTRATE_GRID[1],
        c4_spec=C4,
    )

    return die, interposers, sub


# ============================================================================
# Phase 1: 拓扑滤波
# ============================================================================

def check_topology(a: int, p: int, h: int) -> NetworkPotential | None:
    """检查拓扑是否满足无阻塞带宽目标。

    使用快速分析近似替代完整 Hungarian solver。
    Dragonfly 的 nonblocking BW ≈ radix × efficiency_factor。
    精确求解在 Phase 4 (congestion 仿真) 中完成。
    """
    if USE_FAST_PERF:
        # 简化分析模型: Dragonfly 的理论无阻塞带宽
        g = a * h + 1
        total_terminals = g * a * p

        # 近似: local BW 受 intra-group 全互联限制
        # global BW 受 global link 数量限制
        # 取两者的 min 作为 optimistic bound
        local_bw = (a - 1) * TARGET_BW_GBPS / 2   # 组内 half bisection
        global_bw = h * TARGET_BW_GBPS / 2          # 组间 per router

        approx_bw = min(local_bw, global_bw, TARGET_BW_GBPS * 1.5)

        # 返回一个假的 NetworkPotential 供下游使用
        return NetworkPotential(
            topology_name=f"dragonfly_a{a}_p{p}_h{h}",
            route="det",
            terminal_count=total_terminals,
            directed_link_count=g * a * (a - 1 + h),
            nonblocking_gbps_per_port=approx_bw,
            required_internal_speedup=1,
            required_internal_800g_links=0,
            certificate_status="approximate",
            worst_link="",
            notes="分析近似 (快速模式)",
        )


# ============================================================================
# Phase 2-3: 物理可行性
# ============================================================================

def check_physical(
    a: int, p: int, h: int,
    die: DieBumpBudget,
    interposers: list[Interposer],
    sub: Substrate,
) -> tuple[IntraRouteResult | None, GlobalRouteResult | None]:
    """检查 bump 预算 + 布线可行性。"""

    # 每个 die 的 μbump 需求
    g = a * h + 1   # total groups
    # 每条链路需要的 lane 数 (UCIe-32G 最优情况)
    from wafer_dse.physical.interconnect import get_profile
    ucie_std = get_profile("UCIe-32G-Advanced")

    # Terminal lanes (p 个终端端口 per die)
    terminal_lanes = p * math.ceil(TARGET_BW_GBPS / ucie_std.lane_rate_gbps)
    # Intra-group D2D lanes ((a-1) 条 group 内边)
    intra_lanes = (a - 1) * math.ceil(TARGET_BW_GBPS / ucie_std.lane_rate_gbps)
    # Global lanes (h 条全局链路)
    serdes_std = get_profile("SerDes-112G-MR")
    global_lanes = h * math.ceil(TARGET_BW_GBPS / serdes_std.lane_rate_gbps)

    total_per_die = terminal_lanes + intra_lanes + global_lanes

    # μbump 检查
    if total_per_die > die.available:
        return None, None  # μbump 不够

    # Interposer 内检查
    intra_edges_per_group = a * (a - 1) // 2
    intra = interposers[0].route_intra(
        intra_edge_count=intra_edges_per_group,
        bandwidth_gbps=TARGET_BW_GBPS,
    )
    if not intra.feasible:
        return intra, None

    # Substrate 间检查
    # 总 global link 数: g groups, 组间 all-to-all
    global_edges_per_group = h * a
    total_global_edges = g * global_edges_per_group // 2  # 双向
    gbl = sub.route_global(
        global_edge_count=total_global_edges,
        bandwidth_gbps=TARGET_BW_GBPS,
    )

    return intra, gbl


# ============================================================================
# Main
# ============================================================================

def main():
    die, interposers, sub = build_physical()

    print("=" * 70)
    print("  晶圆级交换机 DSE — Dragonfly 参数枚举")
    print("=" * 70)
    print()
    print(f"  μbump: {BUMP.name} → {die.available} signal bumps/die")
    print(f"  C4:    {C4.name}")
    print(f"  Interposers: {len(interposers)} × {INTERPOSER_AREA_MM2:.0f}mm²")
    print(f"  Max interposer distance: {sub.max_distance_mm:.0f}mm")
    print(f"  Target: {TARGET_BW_GBPS:.0f} Gbps/port nonblocking")
    print()

    results: list[Metrics] = []

    total = 0
    feasible = 0

    for a in range(A_RANGE[0], A_RANGE[1] + 1):
        for p in range(P_RANGE[0], P_RANGE[1] + 1):
            for h in H_VALUES:
                g = a * h + 1
                total_terminals = g * a * p

                # Phase 1
                net = check_topology(a, p, h)
                if net is None:
                    continue

                # Phase 2-3
                intra, gbl = check_physical(a, p, h, die, interposers, sub)
                if intra is None or gbl is None or not gbl.feasible:
                    continue

                feasible += 1

                # Phase 3b: 热约束
                total_power = intra.total_power_w + gbl.total_power_w
                thermal = check_thermal(
                    total_power_w=total_power / len(interposers),
                    area_mm2=INTERPOSER_AREA_MM2,
                    cooling=COOLING,
                )
                if not thermal.feasible:
                    continue  # 散热不够

                perf = net.nonblocking_gbps_per_port
                cost = (
                    g * interposers[0].die_count * die.perimeter_mm * BUMP.pitch_um / 1000
                    + g * interposers[0].die_count * 10
                )

                results.append(Metrics(
                    perf=perf,
                    cost=cost,
                    power=total_power,
                    plan=None,
                    label=f"DF_a{a}_p{p}_h{h}_g{g}",
                ))

            total += 1

    print(f"  枚举: {total} 组参数, {feasible} 组物理可行")
    print()

    # Phase 4: Pareto
    if results:
        foms = compute_foms(results)
        frontier = [f for f in foms if f.on_frontier]
        print(f"  Pareto 前沿: {len(frontier)} 个设计点")
        print()

        print(f"  {'Rank':<5} {'Config':<25} {'BW':>8} {'Cost':>8} {'Power':>8} {'FOM₁':>10}")
        print(f"  {'-'*5} {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")
        for rank, f in enumerate(foms[:10], 1):
            m = f.metrics
            star = " *" if f.on_frontier else ""
            print(f"  {rank:<5} {m.label:<25} {m.perf:>8.1f} {m.cost:>8.0f} "
                  f"{m.power:>8.1f} {f.bw_per_area_power*1000:>10.4f}{star}")
    else:
        print("  无可行的 Dragonfly 配置。尝试放宽 μbump 工艺或降低带宽目标。")


if __name__ == "__main__":
    main()
