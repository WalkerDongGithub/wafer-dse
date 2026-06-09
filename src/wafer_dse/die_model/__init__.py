"""Die 物理模型 —— 单 die 面积/功耗/预算估计。

核心公式：crossbar 面积 ∝ N²（交叉开关矩阵）+ O(N)（buffer SRAM）。
"""

from wafer_dse.die_model.estimator import DieEstimator

__all__ = ["DieEstimator"]
