"""物理 layout 层 — 几何实体 + 热网络 + 热求解器.

解决什么问题: 一个 layout 对象是建立物理模型的唯一依据, 能回答
"可不可行" 和 "G/b 是什么". 把 Layout/Interposer/Substrate 几何实体
集中到 physical/layout/, 与 config (参数) 和 problem (数学) 分离.

子包:
  - thermal_network/  布局 → 预计算热网络 (G⁻¹/rhs/link_coeff)
  - thermal_solver/    工厂驱动的热求解器多态 (simple/mfit/hierarchical)

怎么用:
    from physical.layout import Layout, Interposer, Substrate
    from physical.layout.thermal_network import ThermalNetworkBuilder
    from physical.layout.thermal_solver import create_solver

读者: 几何/热网络/热求解器都在这里; 物理参数在 physical/config/;
      LP 约束在 problem/ (Stage 4 改名后).
"""

from physical.layout.layout import Layout
from physical.layout.interposer import Interposer
from physical.layout.substrate import Substrate

__all__ = [
    "Layout",
    "Interposer",
    "Substrate",
]

