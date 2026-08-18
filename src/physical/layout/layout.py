"""Layout 实体 — 布局结果, lp builder 的输入契约.

解决什么问题: 把拓扑分片 + die 摆放结果封装成一个值对象,
作为 build_scenario 的输入. layout 是建立物理模型的唯一依据.
怎么用: from physical.layout.layout import Layout
读者: Layout 是纯数据契约; DiePlacement 的定义在同包 thermal_network 子包;
      placement 算法在 physical/placement/.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from physical.layout.thermal_network._mfit_system import DiePlacement


@dataclass(frozen=True)
class Layout:
    """布局结果 —— lp builder 的输入契约.

    placements:  每个 die 的位置（DiePlacement 列表，序号 = die id）
    node_to_die: 拓扑节点 → die 的分片映射
    """

    placements: tuple[DiePlacement, ...]
    node_to_die: dict[int, int]

    @property
    def n_dies(self) -> int:
        return len(self.placements)


__all__ = ["Layout"]
