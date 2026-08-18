"""L1 稳态温度约束 —— SteadyStateModel.

model 层：只认 ThermalNetwork（预计算网络），不关心 G/b 怎么来。
网络构建见 network/ 子包（ThermalNetworkBuilder）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from problem.models.phys.therm import ThermalModel

if TYPE_CHECKING:
    from problem.ctx import Ctx
    from physical.layout.thermal_network._net import ThermalNetwork


class SteadyStateModel(ThermalModel):
    """L1 精度——稳态热网络 per-die 温度约束.

    P → G·T = P + b → T ≤ T_max.
    每条 die 一条不等式，考虑 die 间热耦合 (G⁻¹ ≥ 0).

    注意：link_coeff 已在 ThermalNetworkBuilder.precompute 中归一化为 K/Gbps
    （ppl/lane_rate 折进 M），所以约束是 B·link_coeff·L ≤ rhs(B)，
    scale 恒为 B——没有 lane_rate 参数（曾因重复除以 lane_rate 让
    热约束失效 32×）。

    §2.8 die 缩放：P_peak(B)=P0+β_P·B 进入 rhs，
    rhs(B) = rhs_ambient − β_P·B·(G⁻¹·1)。
    """

    def __init__(self, network: ThermalNetwork,
                 beta_p: float | np.ndarray = 0.0):
        self._net = network
        n = network.G_inv.shape[0]
        self._beta_p = np.full(n, float(beta_p)) \
            if isinstance(beta_p, (int, float)) else np.asarray(beta_p, dtype=float)
        # rhs_ambient 是 β_P=0 基线：T_max − G⁻¹(P0+b)
        self._rhs0 = network.rhs_ambient.copy()
        # G⁻¹·1：峰值功耗每升 1W 对每 die 温度的贡献
        self._peak_coeff = network.G_inv @ np.ones(n)

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        lc = self._net.link_coeff
        n_links = lc.shape[1]
        rhs = self._rhs0 - self._beta_p * B * self._peak_coeff
        for i in range(self._net.G_inv.shape[0]):
            coeffs = lc[i] * B
            expr = sum(float(coeffs[e]) * L[e] for e in range(n_links)
                       if abs(coeffs[e]) > 1e-15)
            if expr._terms:
                ctx.constrain(
                    f"therm_d{i}", expr, "<=",
                    float(rhs[i]),
                    meaning=f"die {i} 温度达到 T_max")

    def cache_key(self) -> tuple:
        return ("therm_l1",
                self._net.link_coeff.tobytes(),
                self._net.rhs_ambient.tobytes(),
                self._peak_coeff.tobytes(),
                self._beta_p.tobytes())
