"""预计算热网络 —— G⁻¹ + 与 B 无关的系数（MATH_MODEL_COMPLETE_V2 §4）.

思路：P 和 T 都不进 LP。利用 G⁻¹ ≥ 0（M-矩阵），温度约束直接写在 L 上。

  T = G⁻¹(P + b) ≤ T_max
  P = P₀ + ppl · (B/λ) · M · L

  ⇒ (B/λ) · Σ_e link_coeff[i,e] · L_e ≤ rhs_ambient[i]

ThermalNetwork 禁止私自构造（init=False）：唯一生产者是
ThermalNetworkBuilder（其 _make_network 做构造 + M-矩阵不变量校验）。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, init=False)
class ThermalNetwork:
    """预计算的热网络——只能由 ThermalNetworkBuilder 生产.

    没有构造方法（init=False），类上也无任何工厂——Builder 是唯一入口。

    G_inv  (n_nodes, n_nodes): 温度格林函数，M-矩阵之逆（≥ 0）
    rhs_ambient (n_nodes,):    T_max − G⁻¹·(P0+b)，每 die 的动态温升预算
    link_coeff (n_nodes, n_links): G⁻¹·(ppl/lr·M)，每 Gbps 的温升贡献 [K/Gbps]
    """

    G_inv: np.ndarray
    rhs_ambient: np.ndarray
    link_coeff: np.ndarray
