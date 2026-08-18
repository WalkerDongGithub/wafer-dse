"""Substrate 物理实体 — 有机基板的几何与 C4 预算.

解决什么问题: 定义多个 interposer 贴在有机基板上的几何实体,
回答 "最远走线距离" 和 "C4 信号池" 的容量问题.
怎么用:
    sub = Substrate(interposers=[...], grid_rows=4, grid_cols=4)
    print(sub.max_distance_mm, sub.c4_budget.available)
读者: 纯几何实体, 不含布线算法 (route_global 已移除, V5 模型用 LP 处理).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from physical.config.spec_bump import BumpSpec, C4Budget, C4_130UM
from physical.layout.interposer import Interposer


@dataclass
class Substrate:
    """有机基板: 承载多个 interposer, 提供 interposer 间全互联的几何载体.

    布线逻辑已移除——V5 模型通过 LP 约束处理 interposer 间互连,
    不在此实体上做 route_global().
    """

    interposers: list[Interposer]
    grid_rows: int = 4
    grid_cols: int = 4
    c4_spec: BumpSpec = field(default=C4_130UM)

    # ── 几何 ──
    interposer_spacing_mm: float = 31.0   # ~26 + 5mm gap
    interposer_height_mm: float = 38.0    # ~33 + 5mm gap

    @property
    def max_distance_mm(self) -> float:
        """4×4 网格中对角 interposer 间的最远走线距离 (含绕线因子)。"""
        dx = (self.grid_cols - 1) * self.interposer_spacing_mm
        dy = (self.grid_rows - 1) * self.interposer_height_mm
        return math.sqrt(dx ** 2 + dy ** 2) * 1.3

    @property
    def c4_budget(self) -> C4Budget:
        """所有 interposer 的总 C4 信号池。"""
        total_area = sum(i.area_mm2 for i in self.interposers)
        total_power = sum(sum(d.power_w for d in i.dies) for i in self.interposers)
        return C4Budget(
            spec=self.c4_spec,
            area_mm2=total_area,
            total_power_w=total_power,
        )

    def summary(self) -> str:
        c4 = self.c4_budget
        return (
            f"Substrate: {len(self.interposers)} interposers "
            f"({self.grid_rows}×{self.grid_cols}), "
            f"max_distance={self.max_distance_mm:.0f}mm, "
            f"C4 pool={c4.available} signals"
        )


__all__ = ["Substrate"]
