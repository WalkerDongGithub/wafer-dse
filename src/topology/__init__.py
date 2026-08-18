"""拓扑定义子包。

Topology(ABC) 定义拓扑抽象接口：图结构 + 路由原语。
子类只需实现坐标转换、terminal 判定和单步路由。

结构数据的派生关系：

    terminals ─── (node_num + is_terminal)
    links ─────── (terminals + det)
    link_index ── (links)

pairs / paths_for_pair / link_incidence 不属于拓扑——它们是
(topology, pattern) 的派生产物，由 OptimalValiantModel 在使用点按需计算。
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topology.types import NodeId, Pair


# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════

def _unique_paths(paths: list[list[int]]) -> list[list[int]]:
    """路径去重 + 过滤非简单路径——保持首次出现顺序。

    Valiant 拼接 `det(src,mid) + det(mid,dst)[1:]` 时可能产生非简单路径
    （中间节点重复），物理上无意义（包绕一圈再回），必须丢弃。
    """
    seen: set[tuple[int, ...]] = set()
    result: list[list[int]] = []
    for p in paths:
        # 简单性检查：节点不重复
        if len(set(p)) != len(p):
            continue
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result


# ═══════════════════════════════════════════════════════════════════════════
# Topology ABC
# ═══════════════════════════════════════════════════════════════════════════

class Topology(ABC):
    """拓扑抽象基类。

    子类必须实现:
        to_loc, to_node, is_terminal, terminal_num, node_num, next

    结构属性（@property，函数式按需构造）:
        terminals, n_terminals
        links, n_links, link_index

    路由:
        det, valiant
    """

    # ------------------------------------------------------------------
    # 子类必须实现
    # ------------------------------------------------------------------

    @abstractmethod
    def to_loc(self, node: int) -> list[int]: ...

    @abstractmethod
    def to_node(self, loc: list[int]) -> int: ...

    @abstractmethod
    def is_terminal(self, node: int) -> bool: ...

    @abstractmethod
    def terminal_num(self) -> int: ...

    @abstractmethod
    def node_num(self) -> int: ...

    @abstractmethod
    def next(self, now: int, dst: int) -> int: ...

    # ------------------------------------------------------------------
    # terminal 枚举
    # ------------------------------------------------------------------

    def _terminal_nodes(self) -> list[int]:
        """所有 terminal 节点 ID，按 node_id 升序。

        子类可覆写（如 Dragonfly 优化 valiant 中间节点枚举）。
        """
        return [n for n in range(self.node_num()) if self.is_terminal(n)]

    @property
    def terminals(self) -> list[int]:
        """所有 terminal 节点 ID 列表。"""
        return self._terminal_nodes()

    @property
    def n_terminals(self) -> int:
        """terminal 总数。"""
        return len(self.terminals)

    # ------------------------------------------------------------------
    # 路由
    # ------------------------------------------------------------------

    def det(self, src: int, dst: int) -> list[list[int]]:
        """确定性路由——从 src 到 dst 的唯一路径。"""
        now, path = src, [src]
        limit = max(1, self.node_num() * 4)
        for _ in range(limit):
            if now == dst:
                return [path]
            now = self.next(now, dst)
            path.append(now)
        raise RuntimeError(f"路由未收敛: {src}->{dst}, last_path={path}")

    def valiant(self, src: int, dst: int) -> list[list[int]]:
        """Valiant 路由——det + 经所有中间 terminal 中转。"""
        paths = self.det(src, dst)
        for mid in self._terminal_nodes():
            if mid in {src, dst}:
                continue
            paths.append(
                self.det(src, mid)[0] + self.det(mid, dst)[0][1:]
            )
        return _unique_paths(paths)

    # ------------------------------------------------------------------
    # 链路
    # ------------------------------------------------------------------

    @property
    def links(self) -> list[tuple[int, int]]:
        """所有有向链路 (src, dst)，按首次发现顺序排列。

        遍历所有 terminal pair 的 det() 路径收集首次出现的 link。
        """
        seen: dict[tuple[int, int], int] = {}
        result: list[tuple[int, int]] = []
        for src, dst in itertools.permutations(self.terminals, 2):
            paths = self.det(src, dst)
            if not paths:
                continue
            for k in range(len(paths[0]) - 1):
                link = (paths[0][k], paths[0][k + 1])
                if link not in seen:
                    seen[link] = len(result)
                    result.append(link)
        return result

    @property
    def n_links(self) -> int:
        """链路总数。"""
        return len(self.links)

    @property
    def link_index(self) -> dict[tuple[int, int], int]:
        """链路 → 索引 的映射表。"""
        return {link: i for i, link in enumerate(self.links)}


# ═══════════════════════════════════════════════════════════════════════════
# 子类 import（必须在 Topology 定义之后——子类依赖 Topology）
# ═══════════════════════════════════════════════════════════════════════════

from topology.dragonfly import Dragonfly, DragonflyPlus
from topology.fullmesh import FullMesh
from topology.kary_ncube import KaryNCube
from topology.mesh import Mesh
from topology.torus import Torus

__all__ = [
    "Topology",
    "Mesh",
    "Torus",
    "KaryNCube",
    "Dragonfly",
    "DragonflyPlus",
    "FullMesh",
]
