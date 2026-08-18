"""Interposer 物理实体 — reticle 级硅中介层的几何与容量.

解决什么问题: 定义一个 interposer 容纳多颗 die 的几何实体,
回答 "能放几颗 die" 的面积约束问题.
怎么用:
    interposer = Interposer(label="i0", dies=[...], area_mm2=858)
    print(interposer.max_dies, interposer.can_fit(6))
读者: 纯几何实体, 不含布线算法 (route_intra 已移除, V5 模型用 LP 处理布线).
"""

from __future__ import annotations

from dataclasses import dataclass

from physical.config.spec_bump import DieBumpBudget


@dataclass
class Interposer:
    """一个 reticle 大小的硅中介层.

    布线/路由逻辑已移除——V5 模型通过 LP 约束 (WiringModel) 处理 interposer 内布线,
    不在此实体上做 route().
    """

    label: str
    dies: list[DieBumpBudget]
    area_mm2: float = 858.0             # reticle 面积 (~26×33mm)

    @property
    def die_count(self) -> int:
        return len(self.dies)

    @property
    def max_dies(self) -> int:
        """面积约束：最多能放多少颗 die。"""
        if not self.dies:
            return 999
        die_area = self.dies[0].width_mm * self.dies[0].height_mm
        return int(self.area_mm2 * 0.7 / die_area)

    def can_fit(self, n_dies: int) -> bool:
        return n_dies <= self.max_dies

    def summary(self) -> str:
        return (
            f"{self.label}: {self.die_count} dies, {self.area_mm2:.0f}mm², "
            f"max_dies={self.max_dies}"
        )


__all__ = ["Interposer"]
