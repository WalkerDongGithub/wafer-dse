"""几何约束构建 — bump 预算。

每 die v 的信号 bump 预算约束:
    Σ_{e ∈ δ(v)}  L_e · B / R_e  ≤  N_signal(v)

其中:
    N_signal(v) = η · A_die / pitch²  -  ceil(P_die(v) / (V_dd · I_bump))
    L_e = 链路 e 的归一化负载 (变量)
    B   = 端口目标带宽 (Gbps)
    R_e = 链路 e 的 lane 速率 (Gbps/lane)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from wafer_dse.architecture_model.topology import Topology
from wafer_dse.physical.bump.bump import BumpSpec, DieBumpBudget


# ============================================================================
# 数据结构
# ============================================================================


@dataclass(frozen=True)
class DieConfig:
    """单个 die 的物理配置 — 约束构建的输入。"""

    label: str                  # "die_0"
    width_mm: float = 12.0
    height_mm: float = 12.0
    power_w: float = 50.0       # die 总功耗 (含 router + SerDes 等)
    vdd_v: float = 0.8
    utilization: float = 0.7    # bump 面积利用率


@dataclass(frozen=True)
class GeometryConstraint:
    """一个几何约束: 一组链路的总负载有上限。"""

    name: str                   # "bump_die_0"
    coefficients: dict[int, float]  # link_idx → coefficient (B/R_e or equivalent)
    rhs: float                  # N_signal (可用信号 bump 数)


# ============================================================================
# 约束构建
# ============================================================================


def build_die_to_links(
    topo: Topology,
    group_to_die: dict[int, int] | None = None,
    links: list[tuple[int, int]] | None = None,
) -> dict[int, list[int]]:
    """将链路按 die 分组。

    默认策略: 每个 Dragonfly group 映射到一个 die。
    对于非 Dragonfly 拓扑，所有链路归到一个 die。

    Args:
        topo: 拓扑实例
        group_to_die: 显式的 group→die 映射 (None=自动)
        links: 有向链路列表 (None=自动枚举)

    Returns:
        {die_idx: [link_idx, ...]}
    """
    from wafer_dse.lp.performance import enumerate_links

    if links is None:
        links = enumerate_links(topo)

    # 确定每个节点属于哪个 die (通过 group)
    node_to_die: dict[int, int] = {}

    if hasattr(topo, "g") and hasattr(topo, "a"):
        # Dragonfly 拓扑: 按 group 映射
        for node_id in range(topo.node_num()):
            loc = topo.to_loc(node_id)
            group = loc[0]
            if group_to_die:
                die = group_to_die.get(group, group)
            else:
                die = group  # 默认: group i → die i
            node_to_die[node_id] = die
    else:
        # 非 Dragonfly: 所有节点在一个 die 上
        for node_id in range(topo.node_num()):
            node_to_die[node_id] = 0

    # 分配链路到 die:
    #   同 die 内的链路 → 算在该 die 头上
    #   跨 die 的链路 → 两端各算一次
    die_to_links: dict[int, list[int]] = {}

    for li, (u, v) in enumerate(links):
        die_u = node_to_die.get(u)
        die_v = node_to_die.get(v)
        if die_u is not None:
            die_to_links.setdefault(die_u, []).append(li)
        if die_v is not None and die_v != die_u:
            die_to_links.setdefault(die_v, []).append(li)

    return die_to_links


def build_geometry_constraints(
    die_configs: list[DieConfig],
    die_to_links: dict[int, list[int]],
    bump_spec: BumpSpec,
    target_gbps: float = 800.0,
    lane_rate_gbps: float = 32.0,
) -> list[GeometryConstraint]:
    """为每个 die 构建 bump 预算约束。

    约束形式:
        Σ_{link_idx ∈ δ(die)} coeff · L[link_idx]  ≤  N_signal

    其中 coeff = target_gbps / lane_rate_gbps (lane 数 per unit load)
    假设所有链路使用相同的 lane 速率。

    Args:
        die_configs: 每个 die 的物理配置
        die_to_links: build_die_to_links() 的输出
        bump_spec: bump 工艺
        target_gbps: 端口目标带宽 B
        lane_rate_gbps: lane 速率 R_e (所有链路统一)

    Returns:
        约束列表，每个 die 一个
    """
    coeff = target_gbps / lane_rate_gbps  # lanes per unit L
    constraints: list[GeometryConstraint] = []

    for die_idx, cfg in enumerate(die_configs):
        # 计算 N_signal
        die = DieBumpBudget(
            die_label=cfg.label,
            spec=bump_spec,
            width_mm=cfg.width_mm,
            height_mm=cfg.height_mm,
            power_w=cfg.power_w,
            vdd_v=cfg.vdd_v,
            utilization=cfg.utilization,
        )
        n_signal = die.available

        # 构建系数
        incident = die_to_links.get(die_idx, [])
        if not incident:
            continue

        coeffs = {li: coeff for li in incident}

        constraints.append(GeometryConstraint(
            name=f"bump_{cfg.label}",
            coefficients=coeffs,
            rhs=float(n_signal),
        ))

    return constraints


# ============================================================================
# 便捷函数
# ============================================================================


def geometry_check(
    per_link_load: dict[tuple[int, int], float],
    die_configs: list[DieConfig],
    die_to_links: dict[int, list[int]],
    links: list[tuple[int, int]],
    bump_spec: BumpSpec,
    target_gbps: float = 800.0,
    lane_rate_gbps: float = 32.0,
) -> tuple[bool, dict[str, float], dict[str, float]]:
    """对给定的 per-link 负载做几何约束检查 (det 路径的非 LP 版本)。

    Returns:
        (all_ok, violations, margins)
        violations: {die_name: violation_amount} (正=超标)
        margins: {die_name: remaining_signal_bumps}
    """
    constraints = build_geometry_constraints(
        die_configs, die_to_links, bump_spec, target_gbps, lane_rate_gbps,
    )

    link_idx_map = {link: i for i, link in enumerate(links)}
    all_ok = True
    violations: dict[str, float] = {}
    margins: dict[str, float] = {}

    for gc in constraints:
        total = sum(
            per_link_load.get(links[li], 0.0) * coeff
            for li, coeff in gc.coefficients.items()
        )
        margin = gc.rhs - total
        margins[gc.name] = margin
        if margin < 0:
            all_ok = False
            violations[gc.name] = -margin

    return all_ok, violations, margins
