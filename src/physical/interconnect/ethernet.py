"""
外部以太网辅助互连 — 多个独立标准实例

数据来源: IEEE 802.3df-2024 (800GBASE), IEEE 802.3dj (1.6TBASE)

物理实现方案
============
以太网外部交换: dieA SerDes → PCB出线 → 外部交换机 → PCB入线 → dieB SerDes
  - 晶圆内几乎不占布线资源 (0 层, 0 分区)
  - 代价: 高延迟、低带宽、依赖外部设备
"""

from __future__ import annotations

from physical.interconnect.base import (
    Footprint,
    InterconnectProfile,
    ZoneType,
    ZoneUsage,
    register,
)


# 外部交换固有代价
_EXTERNAL_SWITCH_LATENCY_NS = 200.0
_EXTERNAL_SWITCH_POWER_W = 500.0    # 交换芯片总功耗 (分摊到所有使用者)
_PCB_ESCAPE_MM = 100.0              # PCB escape routing 长度


class _EthernetBase(InterconnectProfile):
    """以太网外部交换家族共享的物理模型。"""

    def __init__(self, name: str, params: dict):
        self._name = name
        self._p = params

    @property
    def name(self) -> str:      return self._name

    @property
    def _params(self) -> dict:  return self._p

    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        """外部交换: 只占两个 SerDes PHY, 不在晶圆上布线。"""
        return Footprint(
            path=((0, 0), (1, 0)),
            zones=(
                ZoneUsage(-1, -1, ZoneType.SERDES_PHY, layer_count=0, lane_count=0),
                ZoneUsage(-1, -1, ZoneType.SERDES_PHY, layer_count=0, lane_count=0),
            ),
            total_layers=0,
            total_power_w=0.0,  # 功耗在 _distance_power 里
        )

    def _distance_power(self, length_mm: float, lanes: int) -> float:
        """PCB 走线 + 交换机分摊。"""
        pcb = lanes * 0.01 * (_PCB_ESCAPE_MM / 100.0)
        switch_share = _EXTERNAL_SWITCH_POWER_W / 64.0  # 假设 64 链路共享
        return pcb + switch_share


for _name, _params in [
    ("Ethernet-800G", dict(
        lane_rate_gbps=106.25, power_per_lane_w=0.425,
        loss_db_per_mm=0.02, max_reach_mm=2000.0, ber=1e-15,
        lane_density_per_mm=2.0,
    )),
    ("Ethernet-1.6T", dict(
        lane_rate_gbps=212.5, power_per_lane_w=1.062,
        loss_db_per_mm=0.02, max_reach_mm=2000.0, ber=1e-15,
        lane_density_per_mm=2.0,
    )),
]:
    register(_EthernetBase(_name, _params))
