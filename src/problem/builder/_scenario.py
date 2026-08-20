"""场景组装 —— 拓扑 + 参数 + Layout → LP 模型列表.

build_scenario 是 problem.builder 的主入口，场景用 '+' 分隔的 token 表达
（V5 v5.21 布线/面积一级化 + v5.22 双旋钮，E3 阶梯逐级加严方向一致）：

  perf                    — 只有性能包络（B 不约束）
  perf+bump               — + μbump 预算
  perf+bump+therm         — + 几何热网络（L1 稳态 per-die 温度极限）
  perf+bump+therm+wiring  — + interposer 布线（V5 §2(2d)：edge/vert/pad 三维容量）
  perf+bump+therm+area    — + die 面积上界（V5 §2(2f)：A_die(B) ≤ A_max）
  perf+bump+therm+wiring+area — E3 完整阶梯

双旋钮 token（V5 §0.1 v5.22，正交可组合）：
  egress_peak — 要求旋钮 R_peak：单对流量包络 L_e* = max c_ij^e（§7.3b），
                替代默认 R_qos 的 Birkhoff 子 LP 包络；
  rated       — 约束旋钮 C_rated：峰值项 β_P B 置 0（§2.8），
                替代默认 C_peak 的峰值工况。

物理/几何实体从 physical 直接 import:
  - Layout (physical.layout) — 几何实体, builder 的输入契约
  - DiePlacement / MfitStackConfig / AnalyticNetworkBuilder
    (physical.layout.thermal_network) — 热网络构建
  - DieBumpBudget (physical.config.spec_bump) — bump 预算
LP 约束模板从 problem.models import:
  - BumpModel / SteadyStateModel / ObliviousValiantModel / WiringModel / DieAreaModel
"""

from __future__ import annotations

import numpy as np

from problem import (
    ObliviousValiantModel,
    BumpModel, SteadyStateModel,
    WiringModel, DieAreaModel,
)
from problem.models.phys.wiring import build_wiring_grid, populate_paths
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


def _lane_rates(topo, P: ExpParams, n2d: dict[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """per-link lane 速率与功耗——on-die 链路零物理代价（V5 §1 链路族定义）."""
    lane_rate = np.full(topo.n_links, P.link.lane_rate_gbps)
    ppl = np.full(topo.n_links, P.link.power_per_lane_w)
    for li, (u, v) in enumerate(topo.links):
        if n2d[u] == n2d[v]:
            lane_rate[li] = float("inf")
            ppl[li] = 0.0
    return lane_rate, ppl


def _bump_model(topo, P: ExpParams, layout: Layout, d2l, lane_rate, ppl,
                beta_p: float | None = None) -> BumpModel:
    """μbump 预算模型——V5 §2(2c) + §4 C1。

    beta_p 覆盖（C_rated 档 β_P:=0，V5 §2.8 v5.22）：
    None → 用 P.die.beta_p（C_peak 档）；0.0 → 额定工况。
    """
    if beta_p is None:
        beta_p = P.die.beta_p
    budgets = [DieBumpBudget(f"d{i}", P.bump.spec(),
                             P.die.width_mm, P.die.height_mm,
                             P.die.static_power_w, P.die.vdd_v,
                             P.bump.utilization,
                             P.die.d0_mm, P.die.alpha_d, beta_p)
               for i in range(layout.n_dies)]
    return BumpModel(budgets, d2l, topo.n_links, lane_rate, ppl)


def _therm_model(topo, P: ExpParams, layout: Layout, d2l, lane_rate, ppl,
                 beta_p: float | None = None) -> SteadyStateModel:
    """几何热网络（L1 稳态）——V5 §2(2e)。

    beta_p 覆盖（C_rated 档 β_P:=0）：None → P.die.beta_p；0.0 → 额定工况。
    """
    if beta_p is None:
        beta_p = P.die.beta_p
    stack = MfitStackConfig(k_interposer=P.thermal.k_interposer,
                            t_interposer=P.thermal.t_interposer_mm,
                            R_vert=P.thermal.r_vert_k_per_w,
                            T_ambient=P.thermal.t_ambient_k)
    P0 = np.full(layout.n_dies, P.die.static_power_w)
    net = AnalyticNetworkBuilder(stack=stack, T_max=P.thermal.t_max_k).build(
        layout.placements, d2l, topo.n_links, lane_rate, ppl, P0)
    return SteadyStateModel(net, beta_p=beta_p)


def _wiring_model(topo, P: ExpParams, layout: Layout, lane_rate) -> WiringModel:
    """interposer 布线模型——V5 §2(2d) 多商品流（edge/vert/pad 三维容量）。

    D2D 链路（die→die）在网格上生成 L 形候选路径；on-die 链路（from==to）
    在 populate_paths 中 src==dst → 空路径 → build 跳过。
    不设 c4_pad（C4 属 I2I 段，范围外）→ 无 route_c4pad 约束。
    power 走线项（V5 §2(2d) v5.25）：c_pwr 从 P.pkg 读（0=关闭），
    P0/β_P 从 P.die 读，s_dyn 用 ppl（每 lane 动态功耗）。
    """
    n2d = layout.node_to_die
    link_specs = [{"from_die": n2d[u], "to_die": n2d[v]}
                  for (u, v) in topo.links]
    grid = build_wiring_grid(layout.placements,
                             P.pkg.interposer_w_mm, P.pkg.interposer_h_mm,
                             P.pkg.metal_layers, P.pkg.lanes_per_mm,
                             P.pkg.c4_pitch_mm)
    grid = populate_paths(grid, link_specs)
    return WiringModel(grid, link_specs, list(range(topo.n_links)), lane_rate,
                       c_pwr_lane_per_w=P.pkg.c_pwr_lane_per_w,
                       p0_w=P.die.static_power_w,
                       beta_p=P.die.beta_p,
                       s_dyn=_lane_rates(topo, P, n2d)[1])


def build_wiring_fixed(topo, P: ExpParams, layout: Layout) -> WiringModel:
    """固定候选路径布线模型——E3B v2 分离基线布线因素（V5 §2(2d)）。

    与联合模型（build_scenario 的 wiring，x_D2D 分流）相对：每条链路
    lane 数全部走首条候选路径，无 x 变量、容量直接 Σ (B/lr)·L ≤ cap。
    分离基线用固定选路，不能利用路径多样性 → 布线饱和时 B* 更紧
    （分歧机制，实测 Mesh(3)/KaryNCube(2,3) rel_diff>0.15，lanes=100）。
    power 走线项与联合模型同口径（c_pwr/P0/β_P/s_dyn 同源，防不公平基线）。
    """
    n2d = layout.node_to_die
    link_specs = [{"from_die": n2d[u], "to_die": n2d[v]}
                  for (u, v) in topo.links]
    lane_rate, ppl = _lane_rates(topo, P, n2d)
    grid = build_wiring_grid(layout.placements,
                             P.pkg.interposer_w_mm, P.pkg.interposer_h_mm,
                             P.pkg.metal_layers, P.pkg.lanes_per_mm,
                             P.pkg.c4_pitch_mm)
    grid = populate_paths(grid, link_specs)
    return WiringModel(grid, link_specs, list(range(topo.n_links)),
                       lane_rate, fixed_paths=True,
                       c_pwr_lane_per_w=P.pkg.c_pwr_lane_per_w,
                       p0_w=P.die.static_power_w,
                       beta_p=P.die.beta_p,
                       s_dyn=ppl)


def _area_model(P: ExpParams, layout: Layout) -> DieAreaModel:
    """die 面积上界——V5 §2(2f)：A_max ≈ interposer 面积 ÷ 芯粒数（粗上界）。"""
    a_max = (P.pkg.interposer_w_mm * P.pkg.interposer_h_mm) / layout.n_dies
    return DieAreaModel(d0_mm=P.die.base_side_mm,
                        alpha_d=P.die.alpha_d,
                        a_max_mm2=a_max)


def build_scenario(topo, scenario: str, P: ExpParams, layout: Layout):
    """按场景组装 (models, 元信息)。P 是参数组合，layout 由更高层传入。

    场景 = '+' 分隔的 token：perf 必有；bump / therm / wiring / area 可选。
    token 顺序即约束加严顺序（E3 消融阶梯）。
    """
    n2d = layout.node_to_die
    d2l = die_to_links(topo, n2d)
    n_dies = layout.n_dies

    tokens = set(scenario.split("+"))
    _KNOWN = {"perf", "bump", "therm", "wiring", "area",
              "egress_peak", "rated"}
    unknown = tokens - _KNOWN
    if unknown:
        raise ValueError(
            f"场景 '{scenario}' 含未知 token {sorted(unknown)}，"
            f"可选: {sorted(_KNOWN)}")

    # 双旋钮（V5 §0.1 v5.22）：R 只作用于性能包络（egress_peak → 单对包络），
    # C 只作用于物理 rhs（rated → β_P:=0）
    requirement = "peak" if "egress_peak" in tokens else "qos"
    rated = "rated" in tokens

    perf = ObliviousValiantModel(topo, requirement=requirement)

    models = [perf]
    if "bump" in tokens:
        lane_rate, ppl = _lane_rates(topo, P, n2d)
        models.append(_bump_model(topo, P, layout, d2l, lane_rate, ppl,
                                  beta_p=0.0 if rated else None))
    if "therm" in tokens:
        lane_rate, ppl = _lane_rates(topo, P, n2d)
        models.append(_therm_model(topo, P, layout, d2l, lane_rate, ppl,
                                   beta_p=0.0 if rated else None))
    if "wiring" in tokens:
        lane_rate, _ = _lane_rates(topo, P, n2d)
        models.append(_wiring_model(topo, P, layout, lane_rate))
    if "area" in tokens:
        models.append(_area_model(P, layout))

    return models, {"n_dies": n_dies}
