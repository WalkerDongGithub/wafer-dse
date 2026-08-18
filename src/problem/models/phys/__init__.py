"""
物理约束族 (LP 约束模板层) —— 链路负载 L → 物理资源上限.

PhysModel —— 抽象基类，所有物理约束的公共入口：
  bumps/  — bump 预算 (μbump + C4)
  therm/  — 热约束 (温度上限 + 翘曲极限)
  wiring/ — 布线容量

本包只导出 LP 约束模板，不导出物理/几何实体——DiePlacement /
MfitStackConfig / ThermalNetwork / ThermalNetworkBuilder /
AnalyticNetworkBuilder / plot_temperature 在 physical/layout/thermal_network/,
由 problem/builder 直接 import.
"""

from problem.ctx import Model


class PhysModel(Model):
    """物理约束族 —— L → ℓ → 物理资源上限。

    build(ctx, B) 接收 B：B 越大，lane 数越多，物理约束越紧。
    """

    def build(self, ctx, B: float):
        raise NotImplementedError


from problem.models.phys.bumps import BumpModel, C4Model
from problem.models.phys.therm import (
    ThermalModel, SteadyStateModel, GlobalPowerModel,
)

__all__ = [
    "PhysModel",
    "BumpModel", "C4Model",
    "ThermalModel", "SteadyStateModel", "GlobalPowerModel",
]

