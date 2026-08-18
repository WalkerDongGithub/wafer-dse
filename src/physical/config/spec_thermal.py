"""热边界条件 + 热求解配置 — CoolingSolution / ThermalConfig / ThermalResult.

解决什么问题: 把冷却方案 (W/mm² 上限) 和热求解输入/输出统一成 frozen
dataclass, 供 layout 热网络与 thermal_solver 引用.
怎么用: from physical.config.spec_thermal import CoolingSolution, ThermalConfig
读者: 这里只有数据契约; 热网络构建 (G/b) 在 physical/layout/thermal_network/.

数值来源：
- T_AMBIENT_K=300K (27°C): 工业标准 ambient。
- T_JUNCTION_MAX_K=358.15K (85°C): 消费级温度上限（低于工业级 105/125°C，本项目采用保守值）。
- Air cooling 0.5 W/mm²: 工业典型 0.1-1 W/mm²。
- Liquid cooling 2.0 W/mm²: 工业典型 1-5 W/mm²。
- Immersion 5.0 W/mm²: 工业典型 0.5-5 W/mm²。
- Microfluidic 10.0 W/mm²: 工业上限 100-1000+ W/cm²。
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================================
# 共享常量
# ============================================================================

T_AMBIENT_K = 300.0                   # 环境温度 27°C
T_JUNCTION_MAX_K = 273.15 + 85.0      # 温度上限 T_max（SteadyStateModel 用作 per-die 温度阈值）


# ============================================================================
# 冷却方案 — 热边界条件
# ============================================================================


@dataclass(frozen=True)
class CoolingSolution:
    """一种冷却方案的热边界条件.

    散热密度 q_max 映射到 MFIT 的对流换热系数 (HTC),
    作为 3D RC 热网络的顶部边界条件.
    """

    name: str
    max_power_density_w_per_mm2: float     # 散热密度 [W/mm²]

    def max_power(self, area_mm2: float) -> float:
        """给定面积下的散热能力上限 [W]."""
        return area_mm2 * self.max_power_density_w_per_mm2


AIR_COOLING     = CoolingSolution("Air",        0.5)
LIQUID_COOLING  = CoolingSolution("Liquid",     2.0)
IMMERSION       = CoolingSolution("Immersion",  5.0)
MICROFLUIDIC    = CoolingSolution("Microfluidic", 10.0)


# ============================================================================
# 热求解输入
# ============================================================================


@dataclass(frozen=True)
class ThermalConfig:
    """一次热求解的完整输入.

    所有字段均有默认值, DSE 循环中只覆盖关心的部分.
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
# 热求解输出
# ============================================================================


@dataclass(frozen=True)
class ThermalResult:
    """统一的热分析结果 — 所有求解器共用.

    不同求解器填充的字段子集不同.
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


__all__ = [
    "T_AMBIENT_K", "T_JUNCTION_MAX_K",
    "CoolingSolution",
    "AIR_COOLING", "LIQUID_COOLING", "IMMERSION", "MICROFLUIDIC",
    "ThermalConfig", "ThermalResult",
]
