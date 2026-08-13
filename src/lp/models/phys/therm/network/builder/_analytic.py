"""解析式热网络构建器 —— MFIT 式面邻接 + 集总垂直路径.

参考 Zhang et al., "MFIT: Multi-Fidelity Thermal Modeling for 2.5D
and 3D Chiplet Systems," ACM TACO 2025 的节点离散化与串联热导公式，
简化为 die 级粒度 + 集总 R_vert（不依赖 MFIT 代码）。
"""

from __future__ import annotations

import numpy as np

from lp.models.phys.therm.network.builder import ThermalNetworkBuilder
from lp.models.phys.therm.network._mfit_system import (
    DiePlacement, MfitStackConfig,
)
from lp.models.phys.therm.network._net import ThermalNetwork


class AnalyticNetworkBuilder(ThermalNetworkBuilder):
    """MFIT 式解析热系统：面邻接 + 集总垂直路径 → G, b → 预计算网络."""

    name = "analytic"

    def __init__(self, stack: MfitStackConfig | None = None,
                 T_max: float = 358.15):
        self._stack = stack if stack is not None else MfitStackConfig()
        self._T_max = T_max

    # -- 子类算法：placements → (G, b) -------------------------------------

    @staticmethod
    def system_of(placements, stack: MfitStackConfig):
        """解析式稳态热系统 (G, b).

        G 是对角占优 M-矩阵（G⁻¹ ≥ 0：任意位置加热，温度只升不降）；
        b[i] = G_vert·T_ambient 是环境温度贡献向量。
        """
        n = len(placements)
        G = np.zeros((n, n))

        g_vert = 1.0 / stack.R_vert
        for i in range(n):
            G[i, i] = g_vert

        for i in range(n):
            for j in range(i + 1, n):
                g = AnalyticNetworkBuilder._lateral_conductance(
                    placements[i], placements[j], stack)
                if g > 0:
                    G[i, i] += g
                    G[j, j] += g
                    G[i, j] = -g
                    G[j, i] = -g

        b = np.full(n, g_vert * stack.T_ambient)
        return G, b

    @staticmethod
    def _lateral_conductance(a: DiePlacement, b: DiePlacement,
                             stack: MfitStackConfig) -> float:
        """MFIT 式面邻接热导：半单元串联公式.

        G_lateral = k · overlap · t / (d_a/2 + d_b/2 + gap)
        """
        k, t = stack.k_interposer, stack.t_interposer
        tol = 1e-4

        ov_x = AnalyticNetworkBuilder._overlap(
            a.x, a.x + a.w, b.x, b.x + b.w)
        if ov_x > tol:
            gap = b.y - (a.y + a.h)
            if gap >= -tol:
                return k * ov_x * t / (a.h / 2 + b.h / 2 + max(gap, 0.0))
            gap = a.y - (b.y + b.h)
            if gap >= -tol:
                return k * ov_x * t / (a.h / 2 + b.h / 2 + max(gap, 0.0))

        ov_y = AnalyticNetworkBuilder._overlap(
            a.y, a.y + a.h, b.y, b.y + b.h)
        if ov_y > tol:
            gap = b.x - (a.x + a.w)
            if gap >= -tol:
                return k * ov_y * t / (a.w / 2 + b.w / 2 + max(gap, 0.0))
            gap = a.x - (b.x + b.w)
            if gap >= -tol:
                return k * ov_y * t / (a.w / 2 + b.w / 2 + max(gap, 0.0))

        return 0.0

    @staticmethod
    def _overlap(lo1: float, hi1: float, lo2: float, hi2: float) -> float:
        """两个区间 [lo1,hi1] 和 [lo2,hi2] 的重叠长度."""
        return max(0.0, min(hi1, hi2) - max(lo1, lo2))

    # -- 组装 --------------------------------------------------------------

    def build(self, placements, die_to_links: dict[int, list[int]],
              n_links: int, lane_rate, ppl,
              P0_vec: np.ndarray) -> ThermalNetwork:
        G, b_vec = self.system_of(placements, self._stack)
        return self.precompute(G, b_vec, self._T_max, die_to_links,
                               n_links, lane_rate, ppl, P0_vec)
