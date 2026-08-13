"""
BumpModel —— bump 预算分配（MATH_MODEL_COMPLETE_V2 §3.2）。

支持 per-link 异构互联标准（UCIe / SerDes 不同 lane_rate 和 power_per_lane）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from lp.models.phys import PhysModel

if TYPE_CHECKING:
    from lp.ctx import Ctx
    from physical.bump.bump import DieBumpBudget


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
        self._rhs: list[float] = []
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
            # available = total - power_bumps(P0), 已扣除静态电源 bump.
            # 动态部分通过 coeff 中的 ppl/(V·I) 项线性加入.
            # 注意: 不再加回 pwr_P0 —— 那会 double-count 静态电源 bump.
            rhs_val = float(budget.available)

            coeffs = {}
            for e in links:
                lr_e = float(lr[e])
                if lr_e >= 1e9:   # 无限容量 = 零代价 (on-die)
                    continue
                coeffs[e] = (1.0 / lr_e) * (1.0 + float(ppl[e]) / (budget.vdd_v * mA))

            if coeffs:
                self._incid.append(list(coeffs.keys()))
                self._coeffs.append(coeffs)
                self._rhs.append(rhs_val)
                self._names.append(budget.die_label)

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        for idx in range(len(self._incid)):
            expr = sum(float(self._coeffs[idx][e]) * L[e]
                       for e in self._incid[idx])
            ctx.constrain(
                f"bump_{self._names[idx]}", B * expr, "<=", self._rhs[idx],
                meaning=f"die {self._names[idx]} 的信号+功率 bump 用尽预算",
            )

    def cache_key(self) -> tuple:
        return ("bump_v2",
                tuple(tuple(sorted(c.items())) for c in self._coeffs),
                tuple(self._rhs))
