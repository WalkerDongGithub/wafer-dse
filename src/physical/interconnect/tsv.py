"""
TSV 3D 垂直互连 — 多个独立标准实例

数据来源:
  - UCIe 2.0 Spec §2.3 (UCIe-3D), Table 1-3
  - Intel Nature Electronics 2024: "High-Performance, Power-Efficient 3D SiP with UCIe"
  - IMEC IRDS 2024 Packaging Roadmap: hybrid bonding pitch roadmap

物理实现方案 (与其他标准根本不同)
=====================================
TSV 互连是垂直方向的——不在分区网格上水平走线:

    上层 die (面朝下, face-to-face)
    ── Cu-Cu hybrid bond ──   ← bump pitch 1-9μm
    下层 die (面朝上)

与平面互连的关键区别:
  - 水平距离 = 0 (两个 die 在同一 (x,y) 分区, 只是 z 不同)
  - 传输距离 = die 厚度 (~50-100μm) + bonding interface
  - 不需要穿越任何中间分区
  - lane 密度极高 (1/5μm → 200 lane/mm 对 9μm pitch)
  - 功耗极低 (0.01-0.05 pJ/bit vs. UCIe 的 0.25 pJ/bit)

这些数字意味着 3D 堆叠在各维度都碾压平面互连——
前提是 die 可以堆叠 (热密度、成本、设计复杂度是代价)。

Footprint 模型
==============
TSV 不穿越任何水平分区:
  - 两个 ENDPOINT 共用同一 (x,y) 坐标
  - 层数 = 0 (垂直层, 不计入水平布线层上限)
  - 真正的成本不在 routing, 而在 stacking 本身的面积/热/良率代价
"""

from __future__ import annotations

from physical.interconnect.base import (
    Footprint,
    InterconnectProfile,
    ZoneType,
    ZoneUsage,
    register,
)


class _TSVBase(InterconnectProfile):
    """TSV 3D 互连家族 — 垂直方向, 无水平走线。"""

    def __init__(self, name: str, params: dict):
        self._name = name
        self._p = params

    @property
    def name(self) -> str:      return self._name

    @property
    def _params(self) -> dict:  return self._p

    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        """TSV 的物理占位: 两个 die 在同一 (x,y), 垂直对穿。

        不占用水平布线层, 不穿越中间分区。
        length_mm 参数在这里 = die 厚度 (~0.05-0.1mm), 对 footprint 无影响。
        """
        return Footprint(
            path=((0, 0),),      # 同分区, 无水平移动
            zones=(
                ZoneUsage(-1, -1, ZoneType.ENDPOINT, layer_count=0, lane_count=0),
            ),
            total_layers=0,       # 不计入水平布线层
            total_power_w=lanes * self.power_per_lane_w,
        )


for _name, _params in [
    # UCIe-3D 标准档位, 来自 Intel Nature Electronics 2024 Table 1
    ("TSV-3D-9μm", dict(
        lane_rate_gbps=4.0,          # UCIe-3D @ SoC logic frequency (典型 ~4GHz)
        power_per_lane_w=0.00016,    # 4G × 0.04 pJ/bit + margin
        loss_db_per_mm=0.001,        # 垂直 TSV 损耗极低
        max_reach_mm=0.1,            # die 厚度 ~100μm
        ber=1e-27,
        lane_density_per_mm=100.0,   # 1/9μm × 0.9 利用率 → ~100 lane/mm
    )),
    ("TSV-3D-5μm", dict(
        lane_rate_gbps=4.0,
        power_per_lane_w=0.0001,     # 更小间距 → 更低电容 → 更低功耗
        loss_db_per_mm=0.001,
        max_reach_mm=0.1,
        ber=1e-27,
        lane_density_per_mm=180.0,   # 1/5μm × 0.9
    )),
    ("TSV-3D-1μm", dict(
        lane_rate_gbps=4.0,
        power_per_lane_w=0.00004,    # 1μm hybrid bond → ~0.01 pJ/bit
        loss_db_per_mm=0.001,
        max_reach_mm=0.1,
        ber=1e-27,
        lane_density_per_mm=900.0,   # 1/1μm × 0.9
    )),
]:
    register(_TSVBase(_name, _params))
