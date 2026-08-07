"""
SerDes 高速串行互连 — 多个独立标准实例

数据来源: OIF-CEI-112G/224G, IEEE 802.3ck/802.3dj

每个 (速率, 距离等级) 组合 = 独立的 InterconnectProfile 实例。

物理实现方案
============
SerDes: 端点A (SerDes PHY macro) → 差分走线 → 端点B (SerDes PHY macro)
  - VSR (≤150mm): 无需中继
  - MR (≤500mm): 背板走线, 可能需中继
  - LR (≤1000mm): 长距, 需中继器
"""

from __future__ import annotations
import math

from physical.interconnect.base import (
    Footprint,
    InterconnectProfile,
    ZoneType,
    ZoneUsage,
    register,
)


class _SerDesBase(InterconnectProfile):
    """SerDes 家族共享的物理模型。"""

    def __init__(self, name: str, params: dict, zone_size_mm: float = 12.0):
        self._name = name
        self._p = params
        self._zone_size_mm = zone_size_mm
        self._needs_retimer = params.get("_needs_retimer", False)

    @property
    def name(self) -> str:      return self._name

    @property
    def _params(self) -> dict:  return self._p

    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        hop_zones = max(1, int(math.ceil(length_mm / self._zone_size_mm)))
        trace_layer = 2  # 差分对 + 阻抗控制

        zones = [
            ZoneUsage(-1, -1, ZoneType.SERDES_PHY, layer_count=1, lane_count=0),
        ]
        for i in range(hop_zones):
            zones.append(
                ZoneUsage(-1, -1, ZoneType.COPPER_TRACE,
                          layer_count=trace_layer, lane_count=lanes)
            )
            if self._needs_retimer and i == hop_zones // 2:
                zones.append(
                    ZoneUsage(-1, -1, ZoneType.SERDES_PHY,
                              layer_count=1, lane_count=0)
                )
        zones.append(
            ZoneUsage(-1, -1, ZoneType.SERDES_PHY, layer_count=1, lane_count=0),
        )
        return Footprint(
            path=tuple((i, 0) for i in range(-1, hop_zones + 1)),
            zones=tuple(zones),
            total_layers=trace_layer,
            total_power_w=lanes * self.power_per_lane_w,
        )

    def _distance_power(self, length_mm: float, lanes: int) -> float:
        """长距离驱动增强: 每 100mm 附加 ~0.05-0.10W/lane。"""
        if "VSR" in self.name:
            return 0.0
        elif "MR" in self.name:
            return lanes * 0.05 * (length_mm / 100.0)
        elif "LR" in self.name:
            return lanes * 0.10 * (length_mm / 100.0)
        return 0.0


for _name, _params in [
    ("SerDes-112G-VSR", dict(
        lane_rate_gbps=106.25, power_per_lane_w=0.425,
        loss_db_per_mm=0.05, max_reach_mm=150.0, ber=1e-15,
        lane_density_per_mm=2.0,
    )),
    ("SerDes-112G-MR", dict(
        lane_rate_gbps=106.25, power_per_lane_w=0.637,
        loss_db_per_mm=0.03, max_reach_mm=500.0, ber=1e-15,
        lane_density_per_mm=1.5,
    )),
    ("SerDes-112G-LR", dict(
        lane_rate_gbps=106.25, power_per_lane_w=1.062,
        loss_db_per_mm=0.02, max_reach_mm=1000.0, ber=1e-15,
        lane_density_per_mm=1.0, _needs_retimer=True,
    )),
    ("SerDes-224G-VSR", dict(
        lane_rate_gbps=212.5, power_per_lane_w=1.062,
        loss_db_per_mm=0.08, max_reach_mm=100.0, ber=1e-15,
        lane_density_per_mm=2.0,
    )),
]:
    register(_SerDesBase(_name, _params))
