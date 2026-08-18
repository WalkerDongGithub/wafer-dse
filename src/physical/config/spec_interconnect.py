"""互连工艺规格 — UCIe 并口 + SerDes 串口的 frozen dataclass 预设.

解决什么问题: 把 UCIe 1.1/2.0 Spec 和 OIF-CEI-112G 标准里实际用到的
档位集中成纯数据对象, 供 params / builder 引用, 不再走注册表.
怎么用: from physical.config.spec_interconnect import UCIE_32G_ADVANCED
读者: 物理参数在 spec_*.py 三件套 (interconnect/bump/thermal), 不在别处.

保留档位 (V5 模型实际引用的 4 个):
  - UCIe 16/24/32G Advanced  (2.5D, 45μm bump pitch)
  - SerDes 112G-VSR          (OIF-CEI-112G-VSR, 组间全局)

数值来源与对齐说明：
- UCIE_16G (rate=16 Gbps, pJ/bit=0.3125): 采用 JSSC 2026 实测 16G-AP 上限 0.29 pJ/bit 工艺角 + 安全裕度。
- UCIE_24G (rate=24 Gbps, pJ/bit=0.3750): UCIe 1.1 Spec Table 1-2 未单列 24G 能效目标，按 16G/32G 线性插值。
- UCIE_32G (rate=32 Gbps, pJ/bit=0.5000): UCIe 2.0 Advanced 32G target = 0.5 pJ/bit（精确符合）。
- SERDES_112G_VSR (lane_rate=106.25 Gbps, pJ/bit=4.0000): lane_rate 采用 100GBASE
  Ethernet payload rate（非 OIF line rate 112 Gbps）；pJ/bit 4.0 落在工业实测
  3.6-4.5 pJ/bit 区间内。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterconnectSpec:
    """一种互连工艺的物理规格 (纯数据, 无行为).

    name               : 唯一标识 (与 ExpParams.link.name 对齐)
    lane_rate_gbps     : 单 lane 速率 [Gbps]
    power_per_lane_w   : 单 lane 功耗 [W]
    loss_db_per_mm     : 单位距离损耗 [dB/mm]
    max_reach_mm       : 最大传输距离 [mm]
    ber                : 目标误码率
    lane_density_per_mm: 边沿密度 [lane/mm]
    """

    name: str
    lane_rate_gbps: float
    power_per_lane_w: float
    loss_db_per_mm: float
    max_reach_mm: float
    ber: float
    lane_density_per_mm: float

    @property
    def pj_per_bit(self) -> float:
        """能效 [pJ/bit] — 传统 vs 2.5D 的核心对比量."""
        return self.power_per_lane_w / self.lane_rate_gbps * 1e3


# ============================================================================
# UCIe Advanced Package (2.5D, 45μm bump pitch) — 数据来源 UCIe 1.1/2.0 Spec
# ============================================================================

UCIE_16G_ADVANCED = InterconnectSpec(
    name="UCIe-16G-Advanced",
    lane_rate_gbps=16.0, power_per_lane_w=0.005,
    loss_db_per_mm=0.05, max_reach_mm=2.0, ber=1e-15,
    lane_density_per_mm=10.0,
)

UCIE_24G_ADVANCED = InterconnectSpec(
    name="UCIe-24G-Advanced",
    lane_rate_gbps=24.0, power_per_lane_w=0.009,
    loss_db_per_mm=0.07, max_reach_mm=1.5, ber=1e-15,
    lane_density_per_mm=10.0,
)

UCIE_32G_ADVANCED = InterconnectSpec(
    name="UCIe-32G-Advanced",
    lane_rate_gbps=32.0, power_per_lane_w=0.016,
    loss_db_per_mm=0.10, max_reach_mm=1.0, ber=1e-15,
    lane_density_per_mm=10.0,
)


# ============================================================================
# SerDes (OIF-CEI-112G-VSR) — 组间全局互连
# ============================================================================

SERDES_112G_VSR = InterconnectSpec(
    name="SerDes-112G-VSR",
    lane_rate_gbps=106.25, power_per_lane_w=0.425,
    loss_db_per_mm=0.05, max_reach_mm=150.0, ber=1e-15,
    lane_density_per_mm=2.0,
)


__all__ = [
    "InterconnectSpec",
    "UCIE_16G_ADVANCED", "UCIE_24G_ADVANCED", "UCIE_32G_ADVANCED",
    "SERDES_112G_VSR",
]
