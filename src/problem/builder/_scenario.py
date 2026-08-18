"""场景组装 —— 拓扑 + 参数 + Layout → LP 模型列表.

build_scenario 是 problem.builder 的主入口:
  perf              — 只有性能包络（B 不约束）
  perf+bump         — + μbump 预算
  perf+bump+therm   — + 几何热网络（L1 稳态 per-die 温度极限）

物理/几何实体从 physical 直接 import:
  - Layout (physical.layout) — 几何实体, builder 的输入契约
  - DiePlacement / MfitStackConfig / AnalyticNetworkBuilder
    (physical.layout.thermal_network) — 热网络构建
  - DieBumpBudget (physical.config.spec_bump) — bump 预算
LP 约束模板从 problem.models import:
  - BumpModel / SteadyStateModel / SelectedOptimalValiantModel
"""

from __future__ import annotations

import numpy as np

from problem import (
    SelectedOptimalValiantModel,
    BumpModel, SteadyStateModel,
)
from physical.config.spec_bump import DieBumpBudget
from physical.layout import Layout
from physical.layout.thermal_network import (
    AnalyticNetworkBuilder, MfitStackConfig,
)
from physical.params import ExpParams


def die_to_links(topo, node_to_die: dict[int, int]) -> dict[int, list[int]]:
    """从拓扑链路 + 分片映射派生 die→链路索引表."""
    d2l: dict[int, list[int]] = {}
    for li, (u, v) in enumerate(topo.links):
        du, dv = node_to_die[u], node_to_die[v]
        d2l.setdefault(du, []).append(li)
        if dv != du:
            d2l.setdefault(dv, []).append(li)
    return {k: sorted(v) for k, v in d2l.items()}


def build_scenario(topo, scenario: str, P: ExpParams, layout: Layout):
    """按场景组装 (models, 元信息)。P 是参数组合，layout 由更高层传入。

    perf              — 只有性能包络（B 不约束）
    perf+bump         — + μbump 预算
    perf+bump+therm   — + 几何热网络（L1 稳态 per-die 温度极限）
    """
    n2d = layout.node_to_die
    d2l = die_to_links(topo, n2d)
    n_dies = layout.n_dies

    perf = SelectedOptimalValiantModel(topo)  # 默认共轭类选择器

    if scenario == "perf":
        return [perf], {"n_dies": n_dies}

    lane_rate = np.full(topo.n_links, P.link.lane_rate_gbps)
    ppl = np.full(topo.n_links, P.link.power_per_lane_w)
    # on-die 链路（router↔terminal 同 die）不走 interposer：零 bump/热代价
    for li, (u, v) in enumerate(topo.links):
        if n2d[u] == n2d[v]:
            lane_rate[li] = float("inf")
            ppl[li] = 0.0
    budgets = [DieBumpBudget(f"d{i}", P.bump.spec(),
                             P.die.width_mm, P.die.height_mm,
                             P.die.static_power_w, P.die.vdd_v,
                             P.bump.utilization,
                             P.die.d0_mm, P.die.alpha_d, P.die.beta_p)
               for i in range(n_dies)]
    bump = BumpModel(budgets, d2l, topo.n_links, lane_rate, ppl)

    if scenario == "perf+bump":
        return [perf, bump], {"n_dies": n_dies}

    stack = MfitStackConfig(k_interposer=P.thermal.k_interposer,
                            t_interposer=P.thermal.t_interposer_mm,
                            R_vert=P.thermal.r_vert_k_per_w,
                            T_ambient=P.thermal.t_ambient_k)
    P0 = np.full(n_dies, P.die.static_power_w)
    net = AnalyticNetworkBuilder(stack=stack, T_max=P.thermal.t_max_k).build(
        layout.placements, d2l, topo.n_links, lane_rate, ppl, P0)
    therm = SteadyStateModel(net, beta_p=P.die.beta_p)
    return [perf, bump, therm], {"n_dies": n_dies}
