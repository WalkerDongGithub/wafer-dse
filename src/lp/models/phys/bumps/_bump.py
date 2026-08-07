"""
BumpModel —— bump 预算分配（MATH_MODEL_COMPLETE_V2 §3）。

物理问题：每条链路需要 ℓ_e 条物理 lane，每条 lane 占一个信号 bump。
         ℓ_e 同时拉高动态功耗 → 拉高电源 bump 需求。
         信号 bump + 电源 bump ≤ 总 bump 数（零和）。

消去中间变量后，每条 die 一条不等式直接写在 L 上：
  (B/λ) · (1 + ppl/(V·I)) · Σ_{e∈δ(die)} L_e ≤ N_total − P₀/(V·I)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lp.ctx import Model

if TYPE_CHECKING:
    from lp.ctx import Ctx
    from lp.models.topo import TopoStructure
    from physical.bump.bump import DieBumpBudget


class BumpModel(Model):
    """per-die bump 不等式。__init__ 预计算常数，build() 只乘 B。"""

    def __init__(self, cs: TopoStructure,
                 die_budgets: list[DieBumpBudget],
                 lane_rate: float = 32.0,
                 power_per_lane: float = 0.005,
                 ):
        self._rate = lane_rate
        self._rhs: list[float] = []       # per-die RHS
        self._incid: list[list[int]] = []  # per-die 链路索引
        self._factor: list[float] = []     # 1 + ppl/(V·I)

        for v, budget in enumerate(die_budgets):
            links = cs.die_to_links.get(v, [])
            if not links:
                continue
            mA = budget.spec.current_per_bump_ma * 1e-3
            pwr_P0 = budget.power_w / (budget.vdd_v * mA)
            self._rhs.append(float(budget.available) + pwr_P0)
            self._incid.append(links)
            pwr_per_lane = power_per_lane / (budget.vdd_v * mA)
            self._factor.append(1.0 + pwr_per_lane)

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        coeff = B / self._rate
        for idx in range(len(self._incid)):
            c = coeff * self._factor[idx]
            (c * L[self._incid[idx]]) <= self._rhs[idx]

    def cache_key(self) -> tuple:
        return ("bump", self._rate,
                tuple(zip(self._rhs, self._factor)),
                tuple(tuple(li) for li in self._incid))
