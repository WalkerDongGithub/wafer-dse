"""灵敏度分析模块 — 约束松弛对 t* 的影响。

核心问题:
    "松弛约束 i，t* 降多少？"

LP 是 min t, s.t. 性能约束 + M·L ≤ b + C·L ≤ d。
对偶变量 λ_i = ∂t*/∂b_i 给出精确答案。

使用方式:
    from wafer_dse.lp.sensitivity import analyze_sensitivity, sweep_constraint

    report = analyze_sensitivity(result)
    print(f"Binding: {report.binding_constraints}")
    print(f"Dual values: {report.dual_values}")
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from wafer_dse.lp import UnifiedLp
from wafer_dse.lp.engine import _has_cvxpy
from wafer_dse.lp.report import LpResult
from wafer_dse.lp.geometry import DieConfig
from wafer_dse.lp.thermal import ThermalConfig


@dataclass
class SensitivityReport:
    """单点灵敏度分析报告。

    对一个 LpResult，回答:
    - 哪些约束是绑定的？
    - 绑定了多少（影子价格）？
    - 每个约束还有多少松弛？
    """

    label: str = ""
    feasible: bool = False
    t_star: float = float("inf")

    # 约束状态
    binding_constraints: list[str] = field(default_factory=list)
    slack_per_constraint: dict[str, float] = field(default_factory=dict)
    dual_values: dict[str, float] = field(default_factory=dict)
    # 改进潜力: 如果把这个约束完全移除，t* 最多降多少
    improvement_potential: dict[str, float] = field(default_factory=dict)

    # 诊断
    bottleneck_severity: str = "unknown"
    # "performance" — 基础性能瓶颈，拓扑/路由本身的限制
    # "physical"  — 物理瓶颈 (bump/热/布线)，可通过工艺或冷却方案放宽
    # "feasible"  — 所有约束满足

    # 元信息
    notes: list[str] = field(default_factory=list)


def analyze_sensitivity(result: LpResult) -> SensitivityReport:
    """从 LpResult 提取灵敏度信息。

    当前版本: 基于 LpResult 中已有的 constraint status。
    完整版本 (需要 cvxpy): 额外提取对偶变量。

    Args:
        result: UnifiedLp.solve() 的输出

    Returns:
        SensitivityReport 包含绑定约束、松弛量、瓶颈诊断
    """
    report = SensitivityReport(
        label=result.bottleneck_link or "",
        feasible=result.feasible,
        t_star=result.worst_load,
    )

    # 收集约束状态
    for cs in result.constraints:
        report.slack_per_constraint[cs.name] = cs.max_slack
        report.dual_values[cs.name] = cs.dual_values.get("sum", 0.0) if cs.dual_values else 0.0

        if cs.binding_constraints:
            report.binding_constraints.extend(cs.binding_constraints)

    # 瓶颈诊断
    if result.feasible:
        report.bottleneck_severity = "feasible"
    elif result.worst_load > 1.0:
        # t* > 1: 性能约束本身就不满足
        # 检查物理约束是否也绑定了
        has_physical_binding = any(
            cs.binding_constraints
            for cs in result.constraints
            if cs.name != "performance"
        )
        if has_physical_binding:
            report.bottleneck_severity = "mixed"
            report.notes.append(
                f"性能+物理双重瓶颈: t*={result.worst_load:.3f}>1, "
                f"物理约束同时绑定"
            )
        else:
            report.bottleneck_severity = "performance"
            report.notes.append(
                f"纯性能瓶颈: t*={result.worst_load:.3f}>1, "
                f"物理约束有松弛"
            )
    else:
        # t* ≤ 1 但不可行 → 纯物理瓶颈
        report.bottleneck_severity = "physical"
        physical_bindings = [
            cs.name for cs in result.constraints
            if not cs.satisfied and cs.name != "performance"
        ]
        report.notes.append(
            f"纯物理瓶颈: {', '.join(physical_bindings)}, "
            f"t*={result.worst_load:.3f}≤1 (性能可达)"
        )

    return report


def sweep_constraint_rhs(
    base_lp: UnifiedLp,
    constraint_name: str,
    rhs_multipliers: list[float],
    output_dir: str = "outputs/paper_experiments",
    csv_name: str = "sensitivity_sweep",
    progress: bool = True,
) -> list[dict]:
    """扫描某个约束的 RHS 乘数，观察 t* 变化。

    对每个乘数 m:
        b' = m * b  (原始约束 RHS)
        重新求解 LP
        记录 t*

    这给出"松弛-收益"曲线: 横轴=约束放宽倍数, 纵轴=t*。

    Args:
        base_lp: 已配置好的 UnifiedLp（含 die_configs, thermal_cfg）
        constraint_name: "geometry" | "thermal" | "performance"
        rhs_multipliers: RHS 乘数列表，如 [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
        output_dir: CSV 输出目录
        csv_name: CSV 文件名
        progress: 是否打印进度

    Returns:
        每行的 dict 列表
    """
    if not _has_cvxpy():
        raise ImportError("灵敏度扫描需要 cvxpy。 pip install \".[lp]\"")
    import csv
    import os
    import time

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f"{csv_name}.csv")

    rows: list[dict] = []
    n = len(rhs_multipliers)

    for i, mult in enumerate(rhs_multipliers):
        t0 = time.time()

        # 克隆 LP 并修改 RHS
        lp = _clone_with_multiplier(base_lp, constraint_name, mult)
        result = lp.solve()
        elapsed = time.time() - t0

        row = {
            "constraint": constraint_name,
            "rhs_multiplier": mult,
            "feasible": result.feasible,
            "t_star": result.worst_load,
            "nonblocking_gbps": result.nonblocking_gbps,
            "solve_time_s": round(elapsed, 4),
        }

        # 每个约束组的 violation/slack
        for cs in result.constraints:
            row[f"{cs.name}_violation"] = round(cs.max_violation, 6)
            row[f"{cs.name}_slack"] = round(cs.max_slack, 6)
            row[f"{cs.name}_satisfied"] = cs.satisfied

        rows.append(row)

        if progress:
            status = "✓" if result.feasible else "✗"
            print(f"  [{i+1:3d}/{n}] {status} mult={mult:.2f}  "
                  f"t*={result.worst_load:.4f}  {elapsed:.2f}s")

    # 写 CSV
    fieldnames = list(rows[0].keys()) if rows else []
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  → {len(rows)} rows → {csv_path}")
    return rows


def _clone_with_multiplier(
    base_lp: UnifiedLp,
    constraint_name: str,
    multiplier: float,
) -> UnifiedLp:
    """克隆 UnifiedLp 并按乘数调整某个约束组的 RHS。

    当前实现: 创建新的 UnifiedLp，参数不变，通过调整
    die_configs 或 thermal_cfg 中的参数来缩放 RHS。

    Args:
        base_lp: 原始 LP 配置
        constraint_name: "geometry" (缩放 bump budget) | "thermal" (缩放散热能力)
        multiplier: RHS 乘数 (>1 = 放宽, <1 = 收紧)

    Returns:
        新的 UnifiedLp 实例
    """
    new_lp = UnifiedLp(
        topo=base_lp.topo,
        route=base_lp.route,
        target_gbps=base_lp.target_gbps,
    )

    # 几何约束: 缩放 die 面积（等价于缩放 bump budget）
    if constraint_name == "geometry" and base_lp._die_configs:
        scaled_configs = []
        for cfg in base_lp._die_configs:
            # 面积缩放 → bump 数量等比缩放
            scaled = DieConfig(
                label=cfg.label,
                width_mm=cfg.width_mm * (multiplier ** 0.5),
                height_mm=cfg.height_mm * (multiplier ** 0.5),
                power_w=cfg.power_w,
                vdd_v=cfg.vdd_v,
                utilization=cfg.utilization,
            )
            scaled_configs.append(scaled)
        new_lp.add_geometry(scaled_configs, base_lp._bump_spec)

    elif constraint_name == "thermal" and base_lp._thermal_cfg:
        # 热约束: 缩放 q_max（等价于缩放散热能力）
        from wafer_dse.physical.thermal._cooling import CoolingSolution
        orig = base_lp._thermal_cfg
        scaled_cooling = CoolingSolution(
            name=f"{orig.cooling.name}-{multiplier:.1f}x",
            max_power_density_w_per_mm2=(
                orig.cooling.max_power_density_w_per_mm2 * multiplier
            ),
        )
        scaled_thermal = ThermalConfig(
            total_area_mm2=orig.total_area_mm2,
            interposer_count=orig.interposer_count,
            power_per_lane_w=orig.power_per_lane_w,
            cooling=scaled_cooling,
            target_gbps=orig.target_gbps,
            lane_rate_gbps=orig.lane_rate_gbps,
        )
        new_lp.add_thermal(scaled_thermal)

    elif constraint_name == "performance":
        # 性能约束: 改变 target_gbps（等价于改变需求）
        new_lp = UnifiedLp(
            topo=base_lp.topo,
            route=base_lp.route,
            target_gbps=base_lp.target_gbps * multiplier,
        )
        # 保留物理约束
        if base_lp._die_configs and base_lp._bump_spec:
            new_lp.add_geometry(base_lp._die_configs, base_lp._bump_spec)
        if base_lp._thermal_cfg:
            new_lp.add_thermal(base_lp._thermal_cfg)
    else:
        # 未知约束名或无可缩放参数 → 原样复制
        if base_lp._die_configs and base_lp._bump_spec:
            new_lp.add_geometry(base_lp._die_configs, base_lp._bump_spec)
        if base_lp._thermal_cfg:
            new_lp.add_thermal(base_lp._thermal_cfg)

    return new_lp


def bottleneck_ranking(
    results: list[LpResult],
) -> dict[str, int]:
    """统计所有不可行结果中，每个约束作为"杀手"出现的次数。

    Args:
        results: 多个设计点的 LpResult 列表

    Returns:
        {constraint_name: count} — 该约束导致不可行的次数
    """
    ranking: dict[str, int] = {}
    for r in results:
        if r.feasible:
            continue
        for cs in r.constraints:
            if not cs.satisfied:
                ranking[cs.name] = ranking.get(cs.name, 0) + 1
    return dict(sorted(ranking.items(), key=lambda x: x[1], reverse=True))
