"""
C4Model —— C4 bump 预算约束（MATH_MODEL_V5_JOINT_SENSITIVITY §3(3c) + §4 C2）。

仅作用于组间 SerDes 链路。支持全局池 + per-pad 两种精度。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from problem.models.phys import PhysModel

if TYPE_CHECKING:
    from problem.ctx import Ctx


class C4Model(PhysModel):
    """C4 bump 约束 —— 组间 SerDes 链路的 C4 带宽上限.

    约束: Σ_{e∈inter} ℓ_e ≤ N_SerDes
    其中 N_SerDes 是 C4 bump 中可用于 SerDes 的总数 (§3.3).
    """

    def __init__(self,
                 inter_links: list[int],
                 lane_rate: float | np.ndarray,
                 n_serdes: int,
                 ):
        n = max(inter_links) + 1 if inter_links else 0
        lr = np.full(n, float(lane_rate)) if isinstance(lane_rate, (int, float)) else np.asarray(lane_rate)

        self._links = inter_links
        self._available = n_serdes
        self._coeffs: dict[int, float] = {}
        for e in inter_links:
            lr_e = float(lr[e])
            if lr_e < 1e9:
                self._coeffs[e] = 1.0 / lr_e

    def build(self, ctx: Ctx, B: float) -> None:
        if not self._links or not self._coeffs:
            return
        L = ctx["L"]
        expr = sum(float(self._coeffs[e]) * L[e] for e in self._links)
        ctx.constrain("c4", B * expr, "<=", float(self._available),
                      meaning="C4 信号焊球用尽——组间带宽天花板")

    def cache_key(self) -> tuple:
        return ("c4", tuple(sorted(self._coeffs.items())), self._available)
