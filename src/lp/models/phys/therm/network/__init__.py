"""热网络子包 —— 布局 → 预计算热网络（纯构建，无 LP 模型）.

  _mfit_system.py   DiePlacement / MfitStackConfig
  _net.py           ThermalNetwork
  builder/          构建器多态：ABC 在 __init__，每个子类一个文件
                      _analytic.py — AnalyticNetworkBuilder

消费方是 SteadyStateModel（therm/_steady_state.py，model 层）。
"""

from lp.models.phys.therm.network._mfit_system import (
    DiePlacement, MfitStackConfig,
)
from lp.models.phys.therm.network._net import ThermalNetwork
from lp.models.phys.therm.network.builder import (
    ThermalNetworkBuilder, AnalyticNetworkBuilder,
)

__all__ = [
    "DiePlacement", "MfitStackConfig",
    "ThermalNetwork",
    "ThermalNetworkBuilder", "AnalyticNetworkBuilder",
]
