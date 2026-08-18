"""面积×功率密度求解器 — 零依赖粗筛。

不做热仿真，只用 P ≤ A×q 比较功率密度。
有热模型时应使用 MfitSolver 或 HierarchicalSolver。
"""

from __future__ import annotations

from dataclasses import dataclass

from physical.config.spec_thermal import (
    CoolingSolution, ThermalConfig, ThermalResult, T_AMBIENT_K,
)
from ._base import ThermalSolver


# ============================================================================
# 内部：简单功率密度比较
# ============================================================================


@dataclass(frozen=True)
class _PowerDensityResult:
    feasible: bool
    total_power_w: float
    area_mm2: float
    cooling: CoolingSolution
    headroom_w: float
    power_density_w_per_mm2: float


def _check_power_density(
    total_power_w: float, area_mm2: float, cooling: CoolingSolution,
) -> _PowerDensityResult:
    """P ≤ A×q 粗筛。"""
    max_p = cooling.max_power(area_mm2)
    headroom = max_p - total_power_w
    return _PowerDensityResult(
        feasible=(headroom >= 0),
        total_power_w=total_power_w, area_mm2=area_mm2,
        cooling=cooling, headroom_w=headroom,
        power_density_w_per_mm2=total_power_w / area_mm2 if area_mm2 > 0 else float('inf'),
    )


# ============================================================================
# 求解器
# ============================================================================


class _SimpleSolver(ThermalSolver):
    """面积×功率密度模型。

    cooling 是输入（边界条件），config.t_junction_max_k 是真正的约束。
    """

    name = "simple"

    def solve(self, config: ThermalConfig) -> ThermalResult:
        if config.cooling is None:
            raise ValueError("ThermalConfig.cooling is required")

        per = config.per_interposer_power_w
        area = config.interposer_area_mm2
        result = _check_power_density(per, area, config.cooling)

        # 用功率密度比估算温度: T ≈ T_amb + (P/A)/q_max × (T_junc - T_amb)
        power_density = per * config.interposer_count / (area * config.interposer_count)
        q_max = config.cooling.max_power_density_w_per_mm2
        ratio = min(power_density / q_max, 2.0) if q_max > 0 else 1.0
        est_max_k = T_AMBIENT_K + ratio * (config.t_junction_max_k - T_AMBIENT_K)

        return ThermalResult(
            feasible=result.feasible,
            solver_name=self.name,
            max_temperature_k=est_max_k,
            max_temperature_c=est_max_k - 273.15,
            avg_temperature_k=est_max_k,
            margin_k=config.t_junction_max_k - est_max_k,
            fallback=True,
        )
