"""
热模型统一配置与结果。

所有求解器共享 ThermalConfig (输入) 和 ThermalResult (输出)。
求解器专属配置定义在各自的模块中。
"""

from __future__ import annotations

from dataclasses import dataclass

from ._cooling import CoolingSolution


# ============================================================================
# 共享常量
# ============================================================================

T_AMBIENT_K = 300.0                   # 环境温度 27°C
T_JUNCTION_MAX_K = 273.15 + 85.0      # 结温上限 85°C (翘曲约束)


# ============================================================================
# 输入
# ============================================================================


@dataclass(frozen=True)
class ThermalConfig:
    """一次热求解的完整输入。

    所有字段均有默认值，DSE 循环中只覆盖关心的部分。
    """

    die_width_mm: float = 12.0
    die_height_mm: float = 12.0
    die_count: int = 6
    die_power_w: float = 50.0
    interposer_area_mm2: float = 858.0
    interposer_count: int = 16
    cooling: CoolingSolution | None = None
    powers: list[float] | None = None       # None → 均匀分配
    t_junction_max_k: float = T_JUNCTION_MAX_K

    @property
    def total_power_w(self) -> float:
        return self.die_count * self.die_power_w * self.interposer_count

    @property
    def per_interposer_power_w(self) -> float:
        return self.die_count * self.die_power_w


# ============================================================================
# 输出
# ============================================================================


@dataclass(frozen=True)
class ThermalResult:
    """统一的热分析结果 — 所有求解器共用。

    不同求解器填充的字段子集不同。
    """

    feasible: bool
    solver_name: str
    max_temperature_k: float
    max_temperature_c: float
    avg_temperature_k: float
    margin_k: float                    # 距结温上限的余量 (正=有余量)
    temperatures: list[float] | None = None
    r_eff: float | None = None
    node_count: int = 0
    simulation_time_s: float = 0.0
    fallback: bool = False
