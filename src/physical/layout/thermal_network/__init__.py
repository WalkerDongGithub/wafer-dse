"""热网络子包 — 布局 → 预计算热网络（纯构建，无 LP 模型）.

物理/几何层：消费 DiePlacement (几何位置) + MfitStackConfig (热参数),
产出 ThermalNetwork (预计算的 G⁻¹/rhs/link_coeff 矩阵).

不包含 LP 约束模板——LP 约束留在 problem/models/phys/therm/ (Stage 4 改名).

模块组织:
  _mfit_system.py   DiePlacement / MfitStackConfig (几何 + 热参数)
  _net.py           ThermalNetwork (预计算结果容器, init=False)
  _heatmap.py       per-die 温度可视化 (matplotlib, 几何渲染)
  builder/          构建器多态：ABC 在 __init__，每个子类一个文件
                      _analytic.py — AnalyticNetworkBuilder

消费方:
  - problem/models/phys/therm/_steady_state.py (LP 约束模板, Stage 4 改名后)
  - 测试 / 报告生成器
"""

from physical.layout.thermal_network._mfit_system import (
    DiePlacement, MfitStackConfig,
)
from physical.layout.thermal_network._net import ThermalNetwork
from physical.layout.thermal_network.builder import (
    ThermalNetworkBuilder, AnalyticNetworkBuilder,
)

__all__ = [
    "DiePlacement", "MfitStackConfig",
    "ThermalNetwork",
    "ThermalNetworkBuilder", "AnalyticNetworkBuilder",
]
