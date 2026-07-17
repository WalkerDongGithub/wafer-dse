"""
晶圆分区网格模型

将 300mm 晶圆离散化为 N×N 功能分区网格。每个分区有:
  - 类型 (交换/电源/路由/冗余)
  - 固定物理位置 → Manhattan 距离精确可算
  - 资源容量 (lane 数, 层数)

这是 Phase 2 (互连标准自适应布线) 的空间约束基础。

数学
====
分区网格 G = (N, zone_size_mm) 其中 zone_size_mm = usable_diameter / N。

对于 300mm 晶圆, 排除 6mm 边缘 → usable_diameter = 288mm:
  N=8  → zone_size = 36mm  (64 分区,  粗略)
  N=12 → zone_size = 24mm  (144 分区, 中等)
  N=16 → zone_size = 18mm  (256 分区, 细粒度)

分区间 Manhattan 距离:
  d(z₁, z₂) = (|x₁ - x₂| + |y₁ - y₂|) × zone_size_mm

这是走线长度的精确值，无需做连续 placement。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ===========================================================================
# 分区类型
# ===========================================================================


class PartitionType(Enum):
    """分区功能类型。"""

    SWITCH = auto()       # 交换 die — 放置 switch chiplet
    POWER = auto()        # 电源 — 固定位置, 满足 PDN 完整性
    ROUTING = auto()      # 路由 — 纯走线, 无有源器件 (passive routing)
    SPARE = auto()        # 预留/冗余 — 良率替换
    UNUSABLE = auto()     # 不可用 — wafer 边缘或缺陷


# ===========================================================================
# 分区网格
# ===========================================================================


@dataclass(frozen=True)
class Zone:
    """单个晶圆分区。"""

    x: int                # 网格列坐标 [0, N)
    y: int                # 网格行坐标 [0, N)
    zone_type: PartitionType
    label: str = ""       # 人类可读标签, 如 "S(2,3)", "PWR", "SPARE"

    # 资源容量 — 布线搜索的约束
    max_lanes: int = 64   # 该分区能承载的最大穿越 lane 数
    max_layers: int = 4   # 该分区能支持的最大布线层数


@dataclass(frozen=True)
class WaferGrid:
    """N×N 晶圆分区网格。

    这是整个 Phase 2 的空间约束输入。所有距离和容量检查都基于此结构。

    使用方式:
        grid = WaferGrid.rect(n=12, die_zones=[(2,3), (3,3), ...])
        d = grid.distance((2, 3), (9, 9))  # Manhattan 距离 in mm
    """

    n: int                          # 网格维度 (n × n)
    zone_size_mm: float             # 每个分区的物理尺寸 [mm]
    zones: dict[tuple[int, int], Zone]  # (x, y) → Zone

    def distance(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """两个分区中心的 Manhattan 走线距离 [mm]。

        这是实际物理走线长度的第一近似。
        """
        return (abs(a[0] - b[0]) + abs(a[1] - b[1])) * self.zone_size_mm

    def is_valid(self, pos: tuple[int, int]) -> bool:
        """该分区是否在可用范围内。"""
        return pos in self.zones and self.zones[pos].zone_type != PartitionType.UNUSABLE

    def zone_type(self, pos: tuple[int, int]) -> PartitionType:
        """获取分区类型。不存在返回 UNUSABLE。"""
        z = self.zones.get(pos)
        return z.zone_type if z else PartitionType.UNUSABLE

    def switch_zones(self) -> list[tuple[int, int]]:
        """所有交换 die 分区的坐标列表。"""
        return [pos for pos, z in self.zones.items()
                if z.zone_type == PartitionType.SWITCH]

    @staticmethod
    def rect(
        n: int = 12,
        wafer_diameter_mm: float = 300.0,
        edge_exclusion_mm: float = 6.0,
        die_zones: Optional[list[tuple[int, int]]] = None,
        power_zones: Optional[list[tuple[int, int]]] = None,
    ) -> WaferGrid:
        """创建一个矩形网格分区。

        Args:
            n: 网格维度。
            wafer_diameter_mm: 晶圆直径。
            edge_exclusion_mm: 边缘排除区宽度。
            die_zones: 交换 die 分区坐标列表。None = 自动填充 (全为 SWITCH)。
            power_zones: 电源分区坐标列表。默认为四角。
        """
        usable = wafer_diameter_mm - 2 * edge_exclusion_mm
        zone_size = usable / n

        die_set = set(die_zones or [])
        power_set = set(power_zones or _default_power_zones(n))

        zones: dict[tuple[int, int], Zone] = {}
        for x in range(n):
            for y in range(n):
                # 判断是否在晶圆可用范围内 (圆形)
                cx = (x - (n - 1) / 2) * zone_size
                cy = (y - (n - 1) / 2) * zone_size
                r = (cx ** 2 + cy ** 2) ** 0.5

                if r > usable / 2:
                    # 圆形晶圆边界外
                    zones[(x, y)] = Zone(x, y, PartitionType.UNUSABLE, f"OUT({x},{y})")
                elif (x, y) in power_set:
                    zones[(x, y)] = Zone(x, y, PartitionType.POWER, f"PWR({x},{y})")
                elif (x, y) in die_set:
                    zones[(x, y)] = Zone(x, y, PartitionType.SWITCH, f"S({x},{y})")
                elif die_set:
                    # die_zones 明确指定 → 其余是路由分区
                    zones[(x, y)] = Zone(x, y, PartitionType.ROUTING, f"R({x},{y})")
                else:
                    # die_zones 未指定 → 默认全为 SWITCH
                    zones[(x, y)] = Zone(x, y, PartitionType.SWITCH, f"S({x},{y})")

        return WaferGrid(n=n, zone_size_mm=zone_size, zones=zones)

    def summary(self) -> str:
        """返回网格的 ASCII 可视化。"""
        type_chars = {
            PartitionType.SWITCH: "S",
            PartitionType.POWER: "P",
            PartitionType.ROUTING: ".",
            PartitionType.SPARE: "_",
            PartitionType.UNUSABLE: " ",
        }
        lines = [f"WaferGrid {self.n}×{self.n}, zone={self.zone_size_mm:.0f}mm"]
        for y in range(self.n - 1, -1, -1):  # 从顶行到底行
            row = ""
            for x in range(self.n):
                z = self.zones.get((x, y))
                row += type_chars.get(z.zone_type if z else PartitionType.UNUSABLE, "?")
            lines.append(row)
        return "\n".join(lines)


def _default_power_zones(n: int) -> list[tuple[int, int]]:
    """默认电源分区: 四角 + 每边中点。"""
    return [
        (0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1),
        (0, n // 2), (n - 1, n // 2), (n // 2, 0), (n // 2, n - 1),
    ]
