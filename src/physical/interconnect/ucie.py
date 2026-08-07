"""
UCIe 并口互连 — 多个独立标准实例

数据来源: UCIe 1.1/2.0 Specification
  - Table 1-1: Standard Package (2D), 110μm bump pitch
  - Table 1-2: Advanced Package (2.5D), 45μm bump pitch

每个 (封装类型, 速率) 组合 = 一个独立的 InterconnectProfile 实例。
它们共享 UCIe 的物理形态建模 (铜走线 + PHY 端点)，
但参数不同、注册名不同、在搜索中平等竞争。

物理实现方案
============
UCIe 并口: 端点A (UCIe PHY) → 铜走线 → 端点B (UCIe PHY)
分区占用:
  - 两端: 各 1 个 ENDPOINT 分区
  - 中间: COPPER_TRACE 分区 × ceil(length / zone_size)
  - 层数: Advanced (interposer) 1 层, Standard (substrate) 2 层
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


class _UCIeBase(InterconnectProfile):
    """UCIe 家族共享的物理模型。不同实例只在 _params 上不同。"""

    def __init__(self, name: str, params: dict, zone_size_mm: float = 12.0):
        self._name = name
        self._p = params
        self._zone_size_mm = zone_size_mm

    @property
    def name(self) -> str:
        return self._name

    @property
    def _params(self) -> dict:
        return self._p

    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        is_advanced = "Advanced" in self.name
        trace_layer = 1 if is_advanced else 2
        hop_zones = max(1, int(math.ceil(length_mm / self._zone_size_mm)))

        zones = [
            ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0),
        ]
        for _ in range(hop_zones):
            zones.append(
                ZoneUsage(-1, -1, ZoneType.COPPER_TRACE,
                          layer_count=trace_layer, lane_count=lanes)
            )
        zones.append(
            ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0),
        )
        return Footprint(
            path=tuple((i, 0) for i in range(-1, hop_zones + 1)),
            zones=tuple(zones),
            total_layers=trace_layer,
            total_power_w=lanes * self.power_per_lane_w,
        )


# ---- 注册所有 UCIe 标准实例 ----

for _name, _params in [
    # === Advanced Package (2.5D): 45μm bump pitch ===
    ("UCIe-12G-Advanced", dict(
        lane_rate_gbps=12.0, power_per_lane_w=0.00375,
        loss_db_per_mm=0.05, max_reach_mm=2.0, ber=1e-27,
        lane_density_per_mm=10.0,
    )),
    ("UCIe-16G-Advanced", dict(
        lane_rate_gbps=16.0, power_per_lane_w=0.005,
        loss_db_per_mm=0.05, max_reach_mm=2.0, ber=1e-27,
        lane_density_per_mm=10.0,
    )),
    ("UCIe-24G-Advanced", dict(
        lane_rate_gbps=24.0, power_per_lane_w=0.009,
        loss_db_per_mm=0.07, max_reach_mm=1.5, ber=1e-27,
        lane_density_per_mm=10.0,
    )),
    ("UCIe-32G-Advanced", dict(
        lane_rate_gbps=32.0, power_per_lane_w=0.016,
        loss_db_per_mm=0.10, max_reach_mm=1.0, ber=1e-27,
        lane_density_per_mm=10.0,
    )),
    # === Standard Package (2D): 110μm bump pitch ===
    ("UCIe-8G-Standard", dict(
        lane_rate_gbps=8.0, power_per_lane_w=0.008,
        loss_db_per_mm=0.30, max_reach_mm=25.0, ber=1e-27,
        lane_density_per_mm=4.0,
    )),
    ("UCIe-16G-Standard", dict(
        lane_rate_gbps=16.0, power_per_lane_w=0.016,
        loss_db_per_mm=0.40, max_reach_mm=25.0, ber=1e-27,
        lane_density_per_mm=4.0,
    )),
]:
    register(_UCIeBase(_name, _params))
