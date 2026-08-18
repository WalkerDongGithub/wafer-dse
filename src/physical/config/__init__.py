"""物理参数校验层 — YAML → dict → 完整性校验 + 工艺规格预设.

解决什么问题: 把 interconnect / bump / thermal 三类工艺规格集中成 frozen
dataclass 预设, 并提供 YAML dict 结构校验, 缺字段报错不静默兜底.
怎么用:
    from physical.config import (
        BumpSpec, UBUMP_45UM, C4_130UM,
        InterconnectSpec, UCIE_32G_ADVANCED, SERDES_112G_VSR,
        CoolingSolution, ThermalConfig,
        validate_params_dict,
    )
读者: 这是物理参数的入口层; layout 几何/热网络在 physical/layout/.
"""

from physical.config.spec_interconnect import (
    InterconnectSpec,
    UCIE_16G_ADVANCED, UCIE_24G_ADVANCED, UCIE_32G_ADVANCED,
    SERDES_112G_VSR,
)
from physical.config.spec_bump import (
    BumpSpec,
    UBUMP_25UM, UBUMP_45UM, C4_130UM,
    HYBRID_9UM, HYBRID_5UM, HYBRID_1UM,
    DieBumpBudget, C4Budget,
)
from physical.config.spec_thermal import (
    T_AMBIENT_K, T_JUNCTION_MAX_K,
    CoolingSolution,
    AIR_COOLING, LIQUID_COOLING, IMMERSION, MICROFLUIDIC,
    ThermalConfig, ThermalResult,
)
from physical.config.validator import validate_params_dict

__all__ = [
    # interconnect
    "InterconnectSpec",
    "UCIE_16G_ADVANCED", "UCIE_24G_ADVANCED", "UCIE_32G_ADVANCED",
    "SERDES_112G_VSR",
    # bump
    "BumpSpec",
    "UBUMP_25UM", "UBUMP_45UM", "C4_130UM",
    "HYBRID_9UM", "HYBRID_5UM", "HYBRID_1UM",
    "DieBumpBudget", "C4Budget",
    # thermal
    "T_AMBIENT_K", "T_JUNCTION_MAX_K",
    "CoolingSolution",
    "AIR_COOLING", "LIQUID_COOLING", "IMMERSION", "MICROFLUIDIC",
    "ThermalConfig", "ThermalResult",
    # validator
    "validate_params_dict",
]
