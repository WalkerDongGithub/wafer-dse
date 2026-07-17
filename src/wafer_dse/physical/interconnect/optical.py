"""
硅光互连 — 多个独立标准实例

数据来源:
  - JLT 2025: 1.6 Tbps FOWLP Silicon Photonic Engine
  - COL 2024: MDM-WDM SiPh Transmitter Chiplet
  - Optica 2025: Polymer Waveguides + SiPh for CPO

物理实现方案
============
光互连: EIC → CPO TX (MRM) → 波导 → CPO RX (GeSi PD) → EIC
  - 两个 CPO 模块固定开销 (面积 ~6mm²/个, 功耗 ~0.4W/个)
  - 波导段损耗极低 (0.03 dB/mm), 距离不限
  - 两端各有一小段铜跳线 (CPO ↔ die)
"""

from __future__ import annotations
import math

from wafer_dse.physical.interconnect.base import (
    Footprint,
    InterconnectProfile,
    ZoneType,
    ZoneUsage,
    register,
)


# 光互连固定开销 — 与速率/距离无关
_CPO_AREA_MM2 = 6.0
_CPO_POWER_W = 0.4       # 激光器 + thermal tuning
_COPPER_SHORT_MM = 2.0   # CPO ↔ die 短铜跳线
_COPPER_POWER_W_PER_MM = 0.001


class _OpticalBase(InterconnectProfile):
    """光互连家族共享的物理模型。"""

    def __init__(self, name: str, params: dict, zone_size_mm: float = 12.0):
        self._name = name
        self._p = params
        self._zone_size_mm = zone_size_mm

    @property
    def name(self) -> str:      return self._name

    @property
    def _params(self) -> dict:  return self._p

    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        """光互连: CPO → Cu → WG → Cu → CPO.

        固定 = 4 分区 (2×CPO + 2×Cu), 波导段按 length 扩展.
        """
        fixed = 4
        wg_zones = max(0, int(math.ceil(length_mm / self._zone_size_mm)) - fixed)

        zones = [
            ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0),
            ZoneUsage(-1, -1, ZoneType.WAVEGUIDE, layer_count=2, lane_count=0),  # CPO TX
            ZoneUsage(-1, -1, ZoneType.COPPER_TRACE, layer_count=1,
                      lane_count=lanes),
        ]
        for _ in range(wg_zones):
            zones.append(
                ZoneUsage(-1, -1, ZoneType.WAVEGUIDE, layer_count=1, lane_count=1)
            )
        zones += [
            ZoneUsage(-1, -1, ZoneType.COPPER_TRACE, layer_count=1,
                      lane_count=lanes),
            ZoneUsage(-1, -1, ZoneType.WAVEGUIDE, layer_count=2, lane_count=0),  # CPO RX
            ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0),
        ]
        return Footprint(
            path=tuple((i, 0) for i in range(-1, len(zones))),
            zones=tuple(zones),
            total_layers=2,
            total_power_w=lanes * self.power_per_lane_w + 2 * _CPO_POWER_W
                          + 2 * _COPPER_SHORT_MM * _COPPER_POWER_W_PER_MM,
        )


for _name, _params in [
    ("Optical-1.6T-8λ", dict(
        lane_rate_gbps=200.0, power_per_lane_w=0.6,
        loss_db_per_mm=0.03, max_reach_mm=500.0, ber=1e-15,
        lane_density_per_mm=0.0,
    )),
    ("Optical-3.2T-16λ", dict(
        lane_rate_gbps=200.0, power_per_lane_w=0.5,
        loss_db_per_mm=0.03, max_reach_mm=500.0, ber=1e-15,
        lane_density_per_mm=0.0,
    )),
]:
    register(_OpticalBase(_name, _params))
