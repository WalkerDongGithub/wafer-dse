"""
TSMC 晶圆级专用互连 Profile

数据来源: TSMC 3DFabric 技术文档, IEEE OJSSCS 2024 (Li et al.)
  - InFO-SoW: Integrated Fan-Out System-on-Wafer (RDL, molding compound)
  - SoW-X:    System-on-Wafer eXtended (两级互连: LSI + SerDes)

这些是 TSMC 专有工艺，不是标准组织发布的。但它们和 UCIe/SerDes
一样可以用 InterconnectProfile 的接口建模——输入距离和带宽，返回账单。

物理实现方案
============
InFO-SoW:
  Die → μbump → RDL 铜线 (fan-out) → μbump → Die
  没有硅中介层，RDL 直接在 molding compound 上
  单级互连，所有链路统一走 RDL

SoW-X:
  Die → μbump → LSI (极短距高密度) 或 SerDes (中距串行化) → μbump → Die
  两级互连，距离决定使用哪种
"""

from __future__ import annotations

from physical.interconnect.base import (
    Footprint,
    InterconnectProfile,
    ZoneType,
    ZoneUsage,
    register,
)


class _InFoSowProfile(InterconnectProfile):
    """InFO-SoW RDL 互连。

    参数来源: TSMC InFO-SoW documentation, Li et al. 2024 Table 1.
    RDL 线宽 ~2μm, 单层走线, 所有边统一处理。
    """

    def __init__(self, zone_size_mm: float = 12.0):
        self._name = "InFO-SoW"
        self._p = {
            "lane_rate_gbps": 200.0,
            "power_per_lane_w": 0.030,     # 200G × 0.15 pJ/bit
            "loss_db_per_mm": 0.05,
            "max_reach_mm": 50.0,
            "ber": 1e-15,
            "lane_density_per_mm": 8.0,
        }
        self._zone_size_mm = zone_size_mm

    @property
    def name(self) -> str:           return self._name

    @property
    def _params(self) -> dict:       return self._p

    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        hop_zones = max(1, int(__import__('math').ceil(length_mm / self._zone_size_mm)))
        zones = [
            ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0),
        ]
        for _ in range(hop_zones):
            zones.append(ZoneUsage(-1, -1, ZoneType.COPPER_TRACE, layer_count=1, lane_count=lanes))
        zones.append(ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0))
        return Footprint(
            path=tuple((i, 0) for i in range(-1, hop_zones + 1)),
            zones=tuple(zones), total_layers=1,
            total_power_w=lanes * self.power_per_lane_w,
        )


class _SoWXLsiProfile(InterconnectProfile):
    """SoW-X LSI 短距互连。

    极短距高密度并口, 用于邻接 die 间的超大带宽连接。
    """

    def __init__(self, zone_size_mm: float = 12.0):
        self._name = "SoW-X-LSI"
        self._p = {
            "lane_rate_gbps": 400.0,
            "power_per_lane_w": 0.040,     # 400G × 0.10 pJ/bit (原 TopoPack 系数 0.10W/GBps)
            "loss_db_per_mm": 0.03,
            "max_reach_mm": 6.5,            # ≤6.5mm
            "ber": 1e-15,
            "lane_density_per_mm": 15.0,    # 极短距 → 更高密度
        }
        self._zone_size_mm = zone_size_mm

    @property
    def name(self) -> str:  return self._name

    @property
    def _params(self) -> dict:       return self._p

    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        hop_zones = max(1, int(__import__('math').ceil(length_mm / self._zone_size_mm)))
        zones = [
            ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0),
        ]
        for _ in range(hop_zones):
            zones.append(ZoneUsage(-1, -1, ZoneType.COPPER_TRACE, layer_count=1, lane_count=lanes))
        zones.append(ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0))
        return Footprint(
            path=tuple((i, 0) for i in range(-1, hop_zones + 1)),
            zones=tuple(zones), total_layers=1,
            total_power_w=lanes * self.power_per_lane_w,
        )


class _SoWXSerdesProfile(InterconnectProfile):
    """SoW-X SerDes 中距互连。

    中距串行化链路, 用于超越邻接范围的 die 间连接。
    """

    def __init__(self, zone_size_mm: float = 12.0):
        self._name = "SoW-X-SerDes"
        self._p = {
            "lane_rate_gbps": 100.0,
            "power_per_lane_w": 0.025,     # 100G × 0.25 pJ/bit (原 TopoPack 系数 0.25W/GBps)
            "loss_db_per_mm": 0.05,
            "max_reach_mm": 50.0,           # ≤50mm
            "ber": 1e-15,
            "lane_density_per_mm": 12.0,
        }
        self._zone_size_mm = zone_size_mm

    @property
    def name(self) -> str:  return self._name

    @property
    def _params(self) -> dict:       return self._p

    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        hop_zones = max(1, int(__import__('math').ceil(length_mm / self._zone_size_mm)))
        zones = [
            ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0),
        ]
        for _ in range(hop_zones):
            zones.append(ZoneUsage(-1, -1, ZoneType.COPPER_TRACE, layer_count=2, lane_count=lanes))
        zones.append(ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=1, lane_count=0))
        return Footprint(
            path=tuple((i, 0) for i in range(-1, hop_zones + 1)),
            zones=tuple(zones), total_layers=2,
            total_power_w=lanes * self.power_per_lane_w,
        )


# 注册
register(_InFoSowProfile())
register(_SoWXLsiProfile())
register(_SoWXSerdesProfile())
