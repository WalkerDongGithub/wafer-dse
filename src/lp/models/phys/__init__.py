"""
物理约束族。

  bumps/  — bump 预算
  therm/  — 热约束（温度上限 + 翘曲极限）
"""

from lp.models.phys.bumps import BumpModel
from lp.models.phys.therm import (
    ThermalModel, ThermalNetwork, NetworkModel, build_thermal_network,
)

__all__ = [
    "BumpModel",
    "ThermalModel", "ThermalNetwork", "NetworkModel", "build_thermal_network",
]
