"""
物理约束族 —— 链路负载 L → 物理资源，需要端口带宽 B 做缩放。

PhysModel —— 抽象基类，所有物理约束的公共入口：
  bumps/  — bump 预算 (μbump + C4)
  therm/  — 热约束 (温度上限 + 翘曲极限)
  wiring/ — 布线容量
"""

from lp.ctx import Model


class PhysModel(Model):
    """物理约束族 —— L → ℓ → 物理资源上限。

    build(ctx, B) 接收 B：B 越大，lane 数越多，物理约束越紧。
    """

    def build(self, ctx, B: float):
        raise NotImplementedError


from lp.models.phys.bumps import BumpModel, C4Model
from lp.models.phys.therm import (
    ThermalModel, ThermalNetwork, SteadyStateModel,
    ThermalNetworkBuilder, AnalyticNetworkBuilder,
    DiePlacement, MfitStackConfig,
)

__all__ = [
    "PhysModel",
    "BumpModel", "C4Model",
    "ThermalModel", "ThermalNetwork", "SteadyStateModel",
    "ThermalNetworkBuilder", "AnalyticNetworkBuilder",
    "DiePlacement", "MfitStackConfig",
]
