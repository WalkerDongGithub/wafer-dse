"""
Pareto 前沿计算模块

三维权衡空间 — 性能 · 成本 · 功耗 — 的非支配过滤与品质因数。

数学框架
========
将设计点参数化为 θ = (topology, a, p, h, K, packaging)，
三个目标函数:

    maximize  f_perf(θ) = nonblocking bandwidth per port  [Gbps]
    minimize  f_cost(θ) = total system cost                [mm² 或 USD]
    minimize  f_power(θ) = total system power              [W]

Pareto 前沿 P ⊆ Θ 定义为不被任何其他可行解支配的点集:

    P = {θ ∈ Θ : ∄ θ' ∈ Θ 使得 f_i(θ') 在所有维度上都不差于 f_i(θ)，
         且至少一个维度上严格更优}

品质因数 (Figure of Merit) 将三维标量化:

    FOM_1(θ) = f_perf / (f_cost · f_power)      [Gbps / (mm²·W)]
    FOM_2(θ) = f_perf / f_cost                  [Gbps / mm²]   (忽略功耗)
    FOM_3(θ) = f_perf / f_power                 [Gbps / W]     (忽略成本)

其中成本可以选用 total_area_mm2（物理面积）或引入良率模型后的
等效 die_cost_usd（经济成本）。当前用面积作为成本的第一近似。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from wafer_dse.models import WaferPlan


# ===========================================================================
# 度量值提取
# ===========================================================================


@dataclass(frozen=True)
class Metrics:
    """一个设计点在三维空间中的度量值。

    三个字段都是标量 —— 除了这三个数，Pareto 模块不感知任何内部细节。
    """

    perf: float      # nonblocking bandwidth per port [Gbps], 越大越好
    cost: float      # total area [mm²] 或 cost [USD], 越小越好
    power: float     # total power [W], 越小越好

    plan: WaferPlan   # 原始数据引用（只读，用于回溯和报告）

    # 可选：记录标签以便结果展示
    label: str = ""


def metrics_from_plan(plan: WaferPlan) -> Metrics:
    """从 WaferPlan 提取三维度量值。

    性能取第一个 group 的 nonblocking bandwidth（所有 group 同构）。
    成本用 total_area_mm2（后续可替换为良率加权 die_cost_usd）。
    """
    perf = plan.groups[0].network.nonblocking_gbps_per_port
    label = plan.group_config + f"_g{plan.group_count}_K{plan.groups[0].best_partition.die_count if plan.groups[0].best_partition else '?'}"
    return Metrics(
        perf=perf,
        cost=plan.total_area_mm2,
        power=plan.total_power_w,
        plan=plan,
        label=label,
    )


# ===========================================================================
# Pareto 核心运算
# ===========================================================================


class Direction:
    """度量优化方向。"""
    MAXIMIZE = 1
    MINIMIZE = -1


# 三个维度的优化方向
_DIRECTIONS = (
    Direction.MAXIMIZE,   # perf: 越大越好
    Direction.MINIMIZE,   # cost: 越小越好
    Direction.MINIMIZE,   # power: 越小越好
)


def dominates(a: Metrics, b: Metrics,
              directions: tuple[int, int, int] = _DIRECTIONS) -> bool:
    """判断 a 是否 Pareto-支配 b。

    a 支配 b 当且仅当:
      (1) a 在每个维度上都不差于 b:
            d_i · f_i(a) ≥ d_i · f_i(b)   for all i ∈ {perf, cost, power}
      (2) a 在至少一个维度上严格更优:
            ∃ i : d_i · f_i(a) > d_i · f_i(b)

    其中 d_i = +1 (MAXIMIZE) 或 -1 (MINIMIZE)。
    """
    d_perf, d_cost, d_power = directions

    # 条件 (1): 所有维度不差于
    if not (d_perf * a.perf >= d_perf * b.perf):
        return False
    if not (d_cost * a.cost >= d_cost * b.cost):
        return False
    if not (d_power * a.power >= d_power * b.power):
        return False

    # 条件 (2): 至少一个维度严格更优
    if d_perf * a.perf > d_perf * b.perf:
        return True
    if d_cost * a.cost > d_cost * b.cost:
        return True
    if d_power * a.power > d_power * b.power:
        return True

    return False  # 三个维度完全相同 → 互不支配


def pareto_frontier(
    points: list[Metrics],
    directions: tuple[int, int, int] = _DIRECTIONS,
) -> list[Metrics]:
    """返回 Pareto 前沿 —— 所有不被任何其他点支配的点。

    结果保持输入顺序中的相对关系（稳定排序对于报告一致性很重要）。
    算法: O(N²) 朴素比较。对于 N ≤ 10⁴ 足够快；若 N 更大可用
    O(N log^{k-1} N) 的扫描线方法。

    只对三维实现了朴素方法。对 2D 问题可直接按第一维排序后扫描。
    """
    frontier: list[Metrics] = []
    for i, a in enumerate(points):
        dominated = False
        for j, b in enumerate(points):
            if i == j:
                continue
            if dominates(b, a, directions):
                dominated = True
                break
        if not dominated:
            frontier.append(a)
    return frontier


def pareto_layers(
    points: list[Metrics],
    directions: tuple[int, int, int] = _DIRECTIONS,
) -> list[list[Metrics]]:
    """Pareto 分层: 递归剥去前沿，返回 [Layer 1, Layer 2, ...]。

    Layer 1 = Pareto 前沿
    Layer 2 = 去除 Layer 1 后的 Pareto 前沿
    ...
    最后一层 = 被所有其他层支配的残余点。
    """
    remaining = list(points)
    layers: list[list[Metrics]] = []
    while remaining:
        layer = pareto_frontier(remaining, directions)
        layers.append(layer)
        # 从 remaining 中移除本层
        layer_set = set(id(p) for p in layer)
        remaining = [p for p in remaining if id(p) not in layer_set]
    return layers


# ===========================================================================
# 品质因数 (Figure of Merit)
# ===========================================================================


@dataclass(frozen=True)
class FOM:
    """一个设计点的品质因数分解。"""
    metrics: Metrics
    bw_per_area_power: float    # FOM_1 = perf / (cost × power)  [Gbps / (mm²·W)]
    bw_per_area: float          # FOM_2 = perf / cost             [Gbps / mm²]
    bw_per_power: float         # FOM_3 = perf / power            [Gbps / W]
    on_frontier: bool           # 该点是否在 Pareto 前沿上
    layer: int                  # Pareto 层数 (1 = 前沿)


def compute_foms(
    points: list[Metrics],
    directions: tuple[int, int, int] = _DIRECTIONS,
) -> list[FOM]:
    """计算所有设计点的品质因数并标记 Pareto 前沿。

    返回按 FOM_1 降序排列的列表。
    """
    layers = pareto_layers(points, directions)
    # 标记每个点属于哪一层
    point_layer: dict[int, int] = {}
    for layer_idx, layer in enumerate(layers, start=1):
        for p in layer:
            point_layer[id(p)] = layer_idx

    results: list[FOM] = []
    for p in points:
        fom = FOM(
            metrics=p,
            bw_per_area_power=(p.perf / (p.cost * p.power))
            if p.cost > 0 and p.power > 0
            else 0.0,
            bw_per_area=(p.perf / p.cost) if p.cost > 0 else 0.0,
            bw_per_power=(p.perf / p.power) if p.power > 0 else 0.0,
            on_frontier=(point_layer.get(id(p), -1) == 1),
            layer=point_layer.get(id(p), -1),
        )
        results.append(fom)

    results.sort(key=lambda f: f.bw_per_area_power, reverse=True)
    return results


# ===========================================================================
# 敏感性分析
# ===========================================================================


def sweep_scaling(
    plans: list[WaferPlan],
    param_fn: Callable[[WaferPlan], float],
    param_name: str,
    bins: int = 10,
) -> dict[str, list[float]]:
    """对某个参数做分箱扫描，观察 FOM 的变化趋势。

    将设计点按参数值分 bins 个等宽区间，对每个区间取平均 FOM_1，
    返回 {param_name, bin_centers, avg_fom1} 供绘图。

    这是量化研究中的标准敏感性分析步骤 — 识别主导参数。
    """
    points = [metrics_from_plan(p) for p in plans if p.feasible]
    if not points:
        return {"param_name": [], "bin_centers": [], "avg_fom1": []}

    foms = compute_foms(points)
    params = [param_fn(f.metrics.plan) for f in foms]
    fom1s = [f.bw_per_area_power for f in foms]

    if max(params) == min(params):
        return {"param_name": [], "bin_centers": [], "avg_fom1": []}

    bin_width = (max(params) - min(params)) / bins
    bin_centers: list[float] = []
    avg_fom1: list[float] = []

    for b in range(bins):
        lo = min(params) + b * bin_width
        hi = lo + bin_width
        bin_foms = [f for f, p in zip(fom1s, params) if lo <= p < hi]
        if bin_foms:
            bin_centers.append((lo + hi) / 2)
            avg_fom1.append(sum(bin_foms) / len(bin_foms))

    return {
        "param_name": [param_name] * len(bin_centers),
        "bin_centers": bin_centers,
        "avg_fom1": avg_fom1,
    }


# ===========================================================================
# 报告输出
# ===========================================================================


def frontier_summary(
    plans: list[WaferPlan],
    top_n: int = 10,
) -> str:
    """返回 Pareto 前沿的 Markdown 表格摘要。

    只展示 feasible 设计点。按 FOM_1 (bw_per_area_power) 排序。
    """
    points = [metrics_from_plan(p) for p in plans if p.feasible]
    if not points:
        return "无可行设计点。"

    foms = compute_foms(points)
    frontier = [f for f in foms if f.on_frontier]

    lines = [
        f"## Pareto 前沿 ({len(frontier)} / {len(foms)} 个设计点)",
        "",
        "| 排名 | 配置 | perf [Gbps] | area [mm²] | power [W] | FOM₁ | FOM₂ | FOM₃ | 层 |",
        "|------|------|-------------|------------|-----------|------|------|------|----|",
    ]

    for rank, f in enumerate(foms[:top_n], start=1):
        m = f.metrics
        frontier_mark = "⭐" if f.on_frontier else ""
        lines.append(
            f"| {rank} | {m.label} {frontier_mark} | "
            f"{m.perf:.1f} | {m.cost:.0f} | {m.power:.1f} | "
            f"{f.bw_per_area_power:.4f} | {f.bw_per_area:.4f} | "
            f"{f.bw_per_power:.4f} | L{f.layer} |"
        )

    return "\n".join(lines)


def pareto_json(plans: list[WaferPlan]) -> list[dict]:
    """导出 Pareto 前沿为 JSON-serializable dict 列表。"""
    points = [metrics_from_plan(p) for p in plans if p.feasible]
    foms = compute_foms(points)
    return [
        {
            "label": f.metrics.label,
            "perf_gbps": f.metrics.perf,
            "area_mm2": f.metrics.cost,
            "power_w": f.metrics.power,
            "fom1": f.bw_per_area_power,
            "fom2": f.bw_per_area,
            "fom3": f.bw_per_power,
            "on_frontier": f.on_frontier,
            "layer": f.layer,
            "group_config": f.metrics.plan.group_config,
            "group_count": f.metrics.plan.group_count,
            "total_dies": f.metrics.plan.total_dies,
        }
        for f in foms
    ]
