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

# 求解器延迟导入 — MFIT 需要 numpy/scipy/c 库，不是所有环境都有
_ThermalSolver = None
_create_solver = None


def __getattr__(name):
    global _ThermalSolver, _create_solver
    if name == "ThermalSolver":
        if _ThermalSolver is None:
            from ._solver import ThermalSolver as TS
            _ThermalSolver = TS
        return _ThermalSolver
    if name == "create_solver":
        if _create_solver is None:
            from ._solver import create_solver as cs
            _create_solver = cs
        return _create_solver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CoolingSolution", "AIR_COOLING", "LIQUID_COOLING", "IMMERSION", "MICROFLUIDIC",
    "ThermalConfig", "ThermalResult",
    "ThermalSolver", "create_solver",
]
