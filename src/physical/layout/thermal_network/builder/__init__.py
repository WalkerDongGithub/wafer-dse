"""热网络构建器 —— "布局 → ThermalNetwork" 的多态入口.

本包惯例（与 physical/layout/thermal_solver 一致）：ABC 写在 __init__，
每个子类一个文件。

  ThermalNetworkBuilder(ABC).build()
    ├─ 子类算法: placements → (G, b)      ← 多态点（解析式 / MFIT 仿真 / 标定）
    └─ 共享步骤: (G, b) → ThermalNetwork   ← precompute（静态，所有子类通用）

ThermalNetwork 禁止私自构造——本类是唯一生产家族
（_make_network 是全代码库唯一生产点）。

将来换 MFIT 仿真标定、hierarchical 标定网络，只是加一个子类文件。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

from physical.layout.thermal_network._net import ThermalNetwork

if TYPE_CHECKING:
    from physical.layout.thermal_network._mfit_system import MfitStackConfig


class ThermalNetworkBuilder(ABC):
    """热网络构建器接口 —— 布局 + 链路参数 → ThermalNetwork."""

    name: str = "abstract"

    @abstractmethod
    def build(self, placements, die_to_links: dict[int, list[int]],
              n_links: int, lane_rate, ppl,
              P0_vec: np.ndarray) -> ThermalNetwork:
        """placements → (G, b)（子类算法）→ 预计算网络（共享步骤）."""
        ...

    # -- 共享步骤 ----------------------------------------------------------

    @staticmethod
    def precompute(G: np.ndarray, b: np.ndarray, T_max: float,
                   die_to_links: dict[int, list[int]], n_links: int,
                   lane_rate: float | np.ndarray = 32.0,
                   power_per_lane: float | np.ndarray = 0.005,
                   P0_vec: np.ndarray | None = None) -> ThermalNetwork:
        """(G, b) → ThermalNetwork —— 所有子类通用，不随物理模型变.

        link_coeff = G⁻¹·M·diag(ppl/lr)  [K/Gbps]，
        rhs_ambient = T_max − G⁻¹·(P0+b)。
        """
        n_nodes = G.shape[0]
        G_inv = np.linalg.inv(G)

        ppl = np.full(n_links, float(power_per_lane)) \
            if isinstance(power_per_lane, (int, float)) \
            else np.asarray(power_per_lane)
        lr = np.full(n_links, float(lane_rate)) \
            if isinstance(lane_rate, (int, float)) \
            else np.asarray(lane_rate)

        rhs_offset = b.copy() if P0_vec is None else b + P0_vec
        rhs = T_max - G_inv @ rhs_offset

        M = np.zeros((n_nodes, n_links))
        for i, links in die_to_links.items():
            for e in links:
                lr_e = float(lr[e])
                if lr_e >= 1e9:
                    continue
                M[i, e] = float(ppl[e]) / lr_e

        return ThermalNetworkBuilder._make_network(G_inv, rhs, G_inv @ M)

    @staticmethod
    def _make_network(G_inv: np.ndarray, rhs_ambient: np.ndarray,
                      link_coeff: np.ndarray) -> ThermalNetwork:
        """ThermalNetwork 的唯一生产点 —— 校验 M-矩阵不变量后构造.

        ThermalNetwork 是 init=False 的纯数据容器且类上无工厂，
        本方法是全代码库唯一能造出它的地方。
        """
        n = G_inv.shape[0]
        if G_inv.shape != (n, n):
            raise ValueError(f"G_inv 必须是方阵, 收到 {G_inv.shape}")
        if rhs_ambient.shape != (n,):
            raise ValueError(f"rhs_ambient 长度必须 = {n}, 收到 {rhs_ambient.shape}")
        if link_coeff.shape[0] != n:
            raise ValueError(f"link_coeff 行数必须 = {n}, 收到 {link_coeff.shape}")
        if (G_inv < 0).any():
            raise ValueError("G_inv 必须非负——G 是对角占优 M-矩阵")

        obj = ThermalNetwork.__new__(ThermalNetwork)
        object.__setattr__(obj, "G_inv", G_inv)
        object.__setattr__(obj, "rhs_ambient", rhs_ambient)
        object.__setattr__(obj, "link_coeff", link_coeff)
        return obj


from physical.layout.thermal_network.builder._analytic import (  # noqa: E402
    AnalyticNetworkBuilder,
)

__all__ = [
    "ThermalNetworkBuilder",
    "AnalyticNetworkBuilder",
]
