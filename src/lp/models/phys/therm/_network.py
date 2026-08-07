"""
L1 热网络约束（MATH_MODEL_COMPLETE_V2 §4）。

思路：P 和 T 都不进 LP。利用 G⁻¹ ≥ 0（M-矩阵），温度约束直接写在 L 上。

  T = G⁻¹(P + b) ≤ T_max
  P = P₀ + ppl · (B/λ) · M · L

  ⇒ (B/λ) · Σ_e link_coeff[i,e] · L_e ≤ rhs_ambient[i]

G⁻¹ 和 link_coeff 在构造时预计算一次，build() 只做 B 相关缩放。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from lp.models.phys.therm import ThermalModel

if TYPE_CHECKING:
    from lp.ctx import Ctx


@dataclass(frozen=True)
class ThermalNetwork:
    """预计算的热网络——G⁻¹ + 与 B 无关的系数。"""

    G_inv: np.ndarray           # (n_nodes, n_nodes)
    rhs_ambient: np.ndarray      # T_max − G⁻¹·b, (n_nodes,)
    link_coeff: np.ndarray       # G⁻¹·(ppl·M), (n_nodes, n_links)


def build_thermal_network(
    G: np.ndarray, b: np.ndarray, T_max: float,
    node_links: dict[int, list[int]], n_links: int,
    power_per_lane: float = 0.005,
) -> ThermalNetwork:
    """预计算 G⁻¹ 和 link_coeff 矩阵。"""

    n_nodes = G.shape[0]
    G_inv = np.linalg.inv(G)
    rhs = T_max - G_inv @ b

    M = np.zeros((n_nodes, n_links))
    for j, links in node_links.items():
        for e in links:
            M[j, e] = 1.0

    return ThermalNetwork(
        G_inv=G_inv, rhs_ambient=rhs,
        link_coeff=G_inv @ (power_per_lane * M),
    )


class NetworkModel(ThermalModel):
    """L1 温度约束。每个热节点一条不等式。"""

    def __init__(self, network: ThermalNetwork, lane_rate: float = 32.0):
        self._net = network
        self._rate = lane_rate

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        scale = B / self._rate
        lc = self._net.link_coeff
        n_links = lc.shape[1]
        for i in range(self._net.G_inv.shape[0]):
            coeffs = lc[i] * scale
            expr = sum(float(coeffs[e]) * L[e] for e in range(n_links)
                       if abs(coeffs[e]) > 1e-15)
            if expr._terms:
                expr <= float(self._net.rhs_ambient[i])

    def cache_key(self) -> tuple:
        return ("therm_l1", self._rate,
                self._net.link_coeff.tobytes(),
                self._net.rhs_ambient.tobytes())
