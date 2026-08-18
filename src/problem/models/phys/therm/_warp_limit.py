"""翘曲约束 — 相邻 die 温差 ≤ ΔT_max.

物理背景:
  材料热膨胀系数 (CTE) 失配 — Si die (~3 ppm/°C) vs substrate (~15 ppm/°C).
  温度梯度越大, bump 处剪切应力越大. 当前用 die 间温差作为代理:
  |T_i − T_j| ≤ ΔT_max  ∀ 邻接 die 对.

和温度约束完全同构:
  T = G⁻¹(P + b) = G⁻¹(P0 + b) + B · K · L
  W · T ≤ ΔT_max ⟺ B · (W·K) · L ≤ ΔT_max − W·G⁻¹(P0+b)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from problem.models.phys.therm import ThermalModel

if TYPE_CHECKING:
    from problem.ctx import Ctx


def _are_adjacent(a, b, gap_max_mm=5.0) -> bool:
    ox = max(0.0, min(a.x + a.w, b.x + b.w) - max(a.x, b.x))
    oy = max(0.0, min(a.y + a.h, b.y + b.h) - max(a.y, b.y))
    if oy > 1e-6:
        return min(abs(b.x - (a.x + a.w)), abs(a.x - (b.x + b.w))) <= gap_max_mm
    if ox > 1e-6:
        return min(abs(b.y - (a.y + a.h)), abs(a.y - (b.y + b.h))) <= gap_max_mm
    return False


class WarpModel(ThermalModel):
    """翘曲约束 — 邻接 die 温差 ≤ ΔT_max.

    __init__ 预计算: 从 G 和 placement 构建 W 矩阵, 然后算 warp_coeff 和 warp_rhs.
    build() 只做 B 缩放和写不等式.
    """

    def __init__(self, G: np.ndarray, b: np.ndarray,
                 P0_vec: np.ndarray, placements: list,
                 net_link_coeff: np.ndarray,
                 delta_T_max: float = 10.0):
        n = G.shape[0]
        G_inv = np.linalg.inv(G)

        # 构建 W: 每对邻接 die (i,j) → 两行 [+1,-1] 和 [-1,+1]
        rows = []
        for i in range(n):
            for j in range(i + 1, n):
                if _are_adjacent(placements[i], placements[j]):
                    r1 = np.zeros(n); r1[i] = 1.0; r1[j] = -1.0
                    rows.append(r1)
                    r2 = np.zeros(n); r2[i] = -1.0; r2[j] = 1.0
                    rows.append(r2)

        if not rows:
            self._W = np.zeros((1, n))
        else:
            self._W = np.array(rows)

        self._link_coeff = self._W @ net_link_coeff
        self._rhs = delta_T_max - self._W @ (G_inv @ (P0_vec + b))

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        lc = self._link_coeff
        for i in range(lc.shape[0]):
            coeffs = lc[i] * B
            expr = sum(float(coeffs[e]) * L[e]
                       for e in range(lc.shape[1])
                       if abs(coeffs[e]) > 1e-15)
            if expr._terms:
                ctx.constrain(
                    f"warp_{i}", expr, "<=", float(self._rhs[i]),
                    meaning=f"邻接 die 对 #{i} 温差达到 ΔT_max——翘曲风险边界")

    def cache_key(self) -> tuple:
        return ("warp_v2",
                self._link_coeff.tobytes(),
                self._rhs.tobytes())
