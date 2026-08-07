"""L0 热约束：总功耗 ≤ 散热能力。一条不等式，O(1)。"""

from lp.models.phys.therm import ThermalModel
from lp.ctx import Ctx
from physical.thermal._cooling import CoolingSolution


class PowerDensityModel(ThermalModel):
    """L0 精度——全局功率密度约束。

    总功耗 ≤ 散热面积 × 冷却能力。
    忽略热的空间分布，适合大规模初筛。

    约束：Σ_v (P₀_v + ppl·(B/λ)·Σ_{e∈δ(v)} L_e) ≤ A_total · q_max。
    预计算 P₀_total，build() 时用 B 缩放动态部分。
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
        """
        Args:
          P0_total:           所有 die 的静态功耗之和 (W)
          total_area_mm2:     总散热面积 (mm²)
          cooling:            冷却方案
          total_incident_links: Σ_v |δ(v)|（所有 die 的 incident 链路数之和）
          power_per_lane:     每 lane 动态功耗 (W)
          lane_rate:          每 lane 带宽 (Gbps)
        """
        self._P0 = P0_total
        self._max_power = total_area_mm2 * cooling.max_power_density_w_per_mm2
        self._coeff_per_L = power_per_lane / lane_rate * total_incident_links

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        coeff = self._coeff_per_L * B
        (coeff * sum(L)) <= (self._max_power - self._P0)
