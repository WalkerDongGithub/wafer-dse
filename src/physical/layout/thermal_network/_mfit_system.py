"""
MFIT 式热网络构建器 — placement → 稳态热导矩阵 G.

参考文献:
  Zhang, R. et al. "MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D
  Chiplet Systems." ACM TACO, 2025.

方法论借鉴:
  - 矩形节点离散化（非均匀网格）
  - 面邻接判定 + 半单元串联热导公式
  - nodal analysis 组装: G = diag(rowsum) - off_diag, 自动满足 M-矩阵

与 MFIT 的关键差异:
  - 粒度: die 级（非 sub-die 热节点）
  - 稳态: 只需求解 G·T = P + b（不关心瞬态 dT/dt）
  - 垂直简化: 等效集总 R_vert 代替逐层离散化（TIM/ubump/C4/substrate/lid）

不依赖 MFIT 代码。纯 numpy + 几何计算。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ============================================================================
# 数据结构
# ============================================================================


@dataclass(frozen=True)
class DiePlacement:
    """单个 die 在 interposer 上的物理位置.

    (x, y) 是左下角坐标 (mm)，w/h 是 die 尺寸 (mm).
    """

    id: str
    x: float
    y: float
    w: float
    h: float


@dataclass(frozen=True)
class MfitStackConfig:
    """等效垂直 stack 的热参数.

    参考 MFIT 的九层模型，压缩为三个集总参数:
      k_interposer : interposer 面内热导率——主导 die 间横向热耦合
      t_interposer : interposer 厚度
      R_vert       : 单 die 的等效 die→ambient 垂直热阻 (K/W)
                     = R_die_z + R_ubump + R_interposer_z
                       + R_C4 + R_substrate + R_convection

    典型值 (12×12mm die, liquid cooling, Si interposer):
      k_interposer ≈ 150 W/(m·K)
      t_interposer ≈ 0.1 mm
      R_vert       ≈ 1.5–3.0 K/W
    """

    k_interposer: float = 150.0
    t_interposer: float = 0.1
    R_vert: float = 2.0
    T_ambient: float = 300.0
