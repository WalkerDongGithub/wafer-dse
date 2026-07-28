"""
晶圆级热模型 — 工厂驱动的多态架构。

公共 API (9 个符号):
  - 冷却方案: CoolingSolution, AIR_COOLING, LIQUID_COOLING, IMMERSION, MICROFLUIDIC
  - 配置/结果: ThermalConfig, ThermalResult
  - 求解器:   ThermalSolver (ABC), create_solver (工厂)

用法
----
>>> from wafer_dse.physical.thermal import (
...     ThermalConfig, LIQUID_COOLING, create_solver,
... )
>>> solver = create_solver("auto")
>>> config = ThermalConfig(die_count=4, die_power_w=25, cooling=LIQUID_COOLING)
>>> result = solver.solve(config)
"""

from ._cooling import (
    CoolingSolution,
    AIR_COOLING,
    LIQUID_COOLING,
    IMMERSION,
    MICROFLUIDIC,
)
from ._config import ThermalConfig, ThermalResult
from ._solver import ThermalSolver, create_solver

__all__ = [
    "CoolingSolution", "AIR_COOLING", "LIQUID_COOLING", "IMMERSION", "MICROFLUIDIC",
    "ThermalConfig", "ThermalResult",
    "ThermalSolver", "create_solver",
]
