"""热约束构建 — 功率密度上限。

简单模型 (v1):
    Σ_e  p_e · L_e  ≤  A_total · q_max

其中:
    p_e = 链路 e 的每单位负载功耗 (W/unit_load)
    A_total = 总面积 (mm²)
    q_max = 冷却方案的最大功率密度 (W/mm²)

v2: 分层热网络 G · T = P + b,  T_max ≤ T_junc
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# 直接从 _cooling 模块导入，避免触发 thermal/__init__.py → _solver → numpy 的导入链
from wafer_dse.physical.thermal._cooling import (
    CoolingSolution,
    AIR_COOLING,
    LIQUID_COOLING,
    IMMERSION,
    MICROFLUIDIC,
)

# 重导出方便使用
__all__ = [
    "AIR_COOLING", "IMMERSION", "LIQUID_COOLING", "MICROFLUIDIC",
    "CoolingSolution", "ThermalConfig", "ThermalConstraint",
    "build_thermal_constraints", "thermal_check",
]


# ============================================================================
# 数据结构
# ============================================================================


@dataclass(frozen=True)
class ThermalConfig:
    """热约束的输入配置。"""

    total_area_mm2: float = 858.0       # 单个 interposer 面积
    interposer_count: int = 1            # interposer 数量
    power_per_lane_w: float = 0.005      # 每 lane 功耗 (W/lane)
    cooling: CoolingSolution = LIQUID_COOLING
    target_gbps: float = 800.0           # 端口目标带宽
    lane_rate_gbps: float = 32.0         # lane 速率


@dataclass(frozen=True)
class ThermalConstraint:
    """一个热约束。"""

    name: str                       # "thermal_power_density"
    coefficients: dict[int, float]  # link_idx → power_coefficient (W per unit L)
    rhs: float                      # 最大允许功耗 (W)


# ============================================================================
# 约束构建
# ============================================================================


def build_thermal_constraints(
    cfg: ThermalConfig,
    n_links: int,
) -> list[ThermalConstraint]:
    """构建功率密度约束。

    约束形式:
        Σ_e  (power_per_lane_w * target_gbps / lane_rate_gbps) · L[e]
        ≤  total_area * interposer_count * q_max

    其中 q_max 来自冷却方案。

    Args:
        cfg: 热配置
        n_links: 总链路数 (用于系数索引)

    Returns:
        单个功率密度约束的列表
    """
    # 每单位 L 的功耗: p_e = P_lane_per_w * (B / R_e) lanes/unit * 1 W/lane
    # 即: p_e = power_per_lane_w * target_gbps / lane_rate_gbps
    coeff_per_unit = cfg.power_per_lane_w * cfg.target_gbps / cfg.lane_rate_gbps

    # 最大功耗
    total_area = cfg.total_area_mm2 * cfg.interposer_count
    q_max = cfg.cooling.max_power_density_w_per_mm2
    max_power_w = total_area * q_max

    # 所有链路系数相同 (简化假设)
    coeffs = {i: coeff_per_unit for i in range(n_links)}

    return [ThermalConstraint(
        name="thermal_power_density",
        coefficients=coeffs,
        rhs=max_power_w,
    )]


# ============================================================================
# 便捷检查
# ============================================================================


def thermal_check(
    per_link_load: dict[tuple[int, int], float],
    links: list[tuple[int, int]],
    cfg: ThermalConfig,
) -> tuple[bool, float, float]:
    """对给定的 per-link 负载做热约束检查。

    Returns:
        (ok, total_power_w, max_power_w)
    """
    coeff_per_unit = cfg.power_per_lane_w * cfg.target_gbps / cfg.lane_rate_gbps
    total_power = sum(
        per_link_load.get(link, 0.0) * coeff_per_unit
        for link in links
    )
    total_area = cfg.total_area_mm2 * cfg.interposer_count
    max_power = total_area * cfg.cooling.max_power_density_w_per_mm2
    return total_power <= max_power, total_power, max_power
