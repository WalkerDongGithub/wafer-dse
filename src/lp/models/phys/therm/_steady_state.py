"""L1 稳态温度约束 —— SteadyStateModel.

model 层：只认 ThermalNetwork（预计算网络），不关心 G/b 怎么来。
网络构建见 network/ 子包（ThermalNetworkBuilder）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lp.models.phys.therm import ThermalModel

if TYPE_CHECKING:
    from lp.ctx import Ctx
    from lp.models.phys.therm.network._net import ThermalNetwork


class SteadyStateModel(ThermalModel):
    """L1 精度——稳态热网络 per-die 温度约束.

    P → G·T = P + b → T ≤ T_max.
    每条 die 一条不等式，考虑 die 间热耦合 (G⁻¹ ≥ 0).

    注意：link_coeff 已在 ThermalNetworkBuilder.precompute 中归一化为 K/Gbps
    （ppl/lane_rate 折进 M），所以约束是 B·link_coeff·L ≤ rhs_ambient，
    scale 恒为 B——没有 lane_rate 参数（曾因重复除以 lane_rate 让
    热约束失效 32×）。
    """

    def __init__(self, network: ThermalNetwork):
        self._net = network

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        lc = self._net.link_coeff
        n_links = lc.shape[1]
        for i in range(self._net.G_inv.shape[0]):
            coeffs = lc[i] * B
            expr = sum(float(coeffs[e]) * L[e] for e in range(n_links)
                       if abs(coeffs[e]) > 1e-15)
            if expr._terms:
                ctx.constrain(
                    f"therm_d{i}", expr, "<=",
                    float(self._net.rhs_ambient[i]),
                    meaning=f"die {i} 温度达到 T_max")

    def cache_key(self) -> tuple:
        return ("therm_l1",
                self._net.link_coeff.tobytes(),
                self._net.rhs_ambient.tobytes())
