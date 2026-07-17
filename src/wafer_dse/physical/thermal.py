"""
晶圆级系统热约束。

散热能力是硬约束 — 散不掉就是散不掉。与 bump 约束形成闭环:
  功耗 ↑ → 性能 ↑, 但 bump ↓, 热风险 ↑

模型
====
给定 interposer 面积 A 和冷却方案的散热密度 q_max:
  P_max = A × q_max

常见 q_max:
  风冷 (air):         0.5 W/mm²
  液冷 (liquid):      2.0 W/mm²
  浸没 (immersion):   5.0 W/mm²
  微流体 (microfluidic): 10.0 W/mm² (实验级)
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================================
# 冷却方案预设
# ============================================================================


@dataclass(frozen=True)
class CoolingSolution:
    """一种冷却方案的能力上限。"""

    name: str
    max_power_density_w_per_mm2: float     # 散热密度上限 [W/mm²]

    def max_power(self, area_mm2: float) -> float:
        """给定面积下的总散热能力 [W]."""
        return area_mm2 * self.max_power_density_w_per_mm2


AIR_COOLING     = CoolingSolution("Air",        0.5)
LIQUID_COOLING  = CoolingSolution("Liquid",     2.0)
IMMERSION       = CoolingSolution("Immersion",  5.0)
MICROFLUIDIC    = CoolingSolution("Microfluidic", 10.0)


# ============================================================================
# 热检查结果
# ============================================================================


@dataclass(frozen=True)
class ThermalCheck:
    """单次热检查结果。"""

    feasible: bool
    total_power_w: float
    area_mm2: float
    cooling: CoolingSolution
    headroom_w: float              # 剩余散热余量 [W]
    power_density_w_per_mm2: float

    @property
    def margin_pct(self) -> float:
        """散热余量百分比。"""
        max_p = self.cooling.max_power(self.area_mm2)
        return (self.headroom_w / max_p * 100) if max_p > 0 else 0.0


def check_thermal(
    total_power_w: float,
    area_mm2: float,
    cooling: CoolingSolution,
) -> ThermalCheck:
    """检查给定功耗和面积的散热可行性。"""
    max_p = cooling.max_power(area_mm2)
    headroom = max_p - total_power_w
    return ThermalCheck(
        feasible=(headroom >= 0),
        total_power_w=total_power_w,
        area_mm2=area_mm2,
        cooling=cooling,
        headroom_w=headroom,
        power_density_w_per_mm2=total_power_w / area_mm2 if area_mm2 > 0 else float('inf'),
    )
