"""
BumpModel —— μbump 预算分配（MATH_MODEL_V5_JOINT_SENSITIVITY §2 + §4 C1）。

支持 per-link 异构互联标准（UCIe / SerDes 不同 lane_rate 和 power_per_lane）。
rhs = N_total(B) - N_pwr(B)，其中 N_total(B)=η·A_die(B)/p²、
N_pwr(B)=ceil(P_peak(B)/(V_dd·I_bump))，随 B 在 build() 里计算。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from problem.models.phys import PhysModel

if TYPE_CHECKING:
    from problem.ctx import Ctx
    from physical.config.spec_bump import DieBumpBudget


class BumpModel(PhysModel):
    """per-die μbump 不等式.

    __init__ 预计算 per-link 系数，build() 只乘 B.
    支持 per-link 异构 lane_rate 和 power_per_lane.
    可选 link_mask 限制只对部分链路施加约束.
    """

    def __init__(self,
                 die_budgets: list[DieBumpBudget | None],
                 die_to_links: dict[int, list[int]],
                 n_links: int,
                 lane_rate: float | np.ndarray = 32.0,
                 power_per_lane: float | np.ndarray = 0.005,
                 link_mask: list[int] | None = None,
                 ):
        lr = np.full(n_links, float(lane_rate)) if isinstance(lane_rate, (int, float)) else np.asarray(lane_rate)
        ppl = np.full(n_links, float(power_per_lane)) if isinstance(power_per_lane, (int, float)) else np.asarray(power_per_lane)

        self._incid: list[list[int]] = []
        self._coeffs: list[dict[int, float]] = []   # per-die, {link_idx: linear_coeff}
        self._budgets: list[DieBumpBudget] = []     # per-die, 供 build 按 B 计算 rhs
        self._names: list[str] = []                 # per-约束的 die 标签（约束名用）

        for v, budget in enumerate(die_budgets):
            if budget is None:
                continue
            links = die_to_links.get(v, [])
            if link_mask is not None:
                links = [e for e in links if e in link_mask]
            if not links:
                continue

            mA = budget.spec.current_per_bump_ma * 1e-3
            # 动态功耗经 coeff 的 ppl/(V·I) 项折进 lhs；
            # 静态峰值功耗 P_peak(B)=P0+β_P·B 与总面积 A_die(B) 留在 rhs，
            # 由 build() 按 B 调 budget.available_at(B) 计算。
            coeffs = {}
            for e in links:
                lr_e = float(lr[e])
                if lr_e >= 1e9:   # 无限容量 = 零代价 (on-die)
                    continue
                coeffs[e] = (1.0 / lr_e) * (1.0 + float(ppl[e]) / (budget.vdd_v * mA))

            if coeffs:
                self._incid.append(list(coeffs.keys()))
                self._coeffs.append(coeffs)
                self._budgets.append(budget)
                self._names.append(budget.die_label)

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        for idx in range(len(self._incid)):
            expr = sum(float(self._coeffs[idx][e]) * L[e]
                       for e in self._incid[idx])
            ctx.constrain(
                f"bump_{self._names[idx]}", B * expr, "<=",
                float(self._budgets[idx].available_at(B)),
                meaning=f"die {self._names[idx]} 的信号+功率 bump 用尽预算",
            )

    def cache_key(self) -> tuple:
        # rhs 是 B 的函数，结构由缩放参数决定；具体 B 值不在 cache_key 里
        # （B 已在 Runner 的缓存 key 中单独存在）。
        budget_keys = tuple(
            (b.base_side_mm, b.alpha_d, b.beta_p, b.power_w,
             b.vdd_v, b.utilization,
             b.spec.pitch_um, b.spec.current_per_bump_ma)
            for b in self._budgets)
        return ("bump_v2",
                tuple(tuple(sorted(c.items())) for c in self._coeffs),
                budget_keys)
