"""L0 热约束：总功耗 ≤ 散热能力。一条不等式，O(1)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from problem.models.phys.therm import ThermalModel
from problem.ctx import Ctx

if TYPE_CHECKING:
    from physical.config.spec_thermal import CoolingSolution


class GlobalPowerModel(ThermalModel):
    """L0 精度——全局功率密度约束.

    总功耗 ≤ 散热面积 × 冷却能力.
    不计算温度 T——只判断功耗是否超出散热能力的理论上限.
    适合大规模初筛.

    约束: Σ_v P_v ≤ A_total · q_max
         = Σ_v (P₀_v + ppl·(B/λ)·Σ_{e∈δ(v)} L_e) ≤ A_total · q_max
    """

    def __init__(
        self,
        P0_total: float,
        total_area_mm2: float,
        cooling: CoolingSolution,
        total_incident_links: int,
        power_per_lane: float = 0.005,
        lane_rate: float = 32.0,
    ):
        self._P0 = P0_total
        self._max_power = total_area_mm2 * cooling.max_power_density_w_per_mm2
        self._coeff_per_L = power_per_lane / lane_rate * total_incident_links

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        coeff = self._coeff_per_L * B
        ctx.constrain("therm_l0", coeff * sum(L), "<=",
                      self._max_power - self._P0,
                      meaning="总功耗达到散热能力上限")

    def cache_key(self) -> tuple:
        return ("therm_l0", self._P0, self._max_power, self._coeff_per_L)
