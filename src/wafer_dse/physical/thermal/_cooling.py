"""
热边界条件 — 冷却方案定义。

cooling 是热分析的**输入**，不是判据。
真正的约束是温度上限 (85°C 翘曲 / 125°C 可靠性 / T_junction 器件规范)。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoolingSolution:
    """一种冷却方案的热边界条件。

    散热密度 q_max 映射到 MFIT 的对流换热系数 (HTC)，
    作为 3D RC 热网络的顶部边界条件。
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
