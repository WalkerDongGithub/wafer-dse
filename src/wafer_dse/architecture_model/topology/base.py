"""拓扑抽象基类。

定义所有拓扑必须实现的统一接口。
所有拓扑子类只需实现坐标转换、terminal 判定和单步路由逻辑，
基类提供 det / valiant 路径生成的通用实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Topology(ABC):
    """拓扑抽象基类。

    子类必须实现：
        to_loc       —— 节点编号 → 坐标
        to_node      —— 坐标 → 节点编号
        is_terminal  —— 是否为 terminal
        terminal_num —— terminal 总数
        node_num     —— 节点总数（含中间 router）
        next         —— 单步 deterministic 路由
    """

    # ------------------------------------------------------------------
    # 子类必须实现
    # ------------------------------------------------------------------

    @abstractmethod
    def to_loc(self, node_id: int) -> list[int]:
        """节点编号 → 坐标列表。"""
        ...

    @abstractmethod
    def to_node(self, loc: list[int]) -> int:
        """坐标列表 → 节点编号。"""
        ...

    @abstractmethod
    def is_terminal(self, node_id: int) -> bool:
        """该节点是否为 terminal（可注入/接收流量）。"""
        ...

    @abstractmethod
    def terminal_num(self) -> int:
        """terminal 总数。"""
        ...

    @abstractmethod
    def node_num(self) -> int:
        """节点总数（含中间 router/switch）。"""
        ...

    @abstractmethod
    def next(self, now: int, dst: int) -> int:
        """从 now 到 dst 的 deterministic 单步路由：返回下一跳节点编号。

        Args:
            now: 当前节点编号。
            dst: 目标节点编号。

        Returns:
            下一跳节点编号；若 now == dst 则返回 now。
        """
        ...

    # ------------------------------------------------------------------
    # 基类提供的通用实现
    # ------------------------------------------------------------------

    def terminals(self) -> list[int]:
        """所有 terminal 节点编号列表。"""
        return [n for n in range(self.node_num()) if self.is_terminal(n)]

    def det(self, src: int, dst: int) -> list[list[int]]:
        """deterministic 路由：从 src 到 dst 的唯一路径。

        返回格式：[[node0, node1, ..., nodeN]]。
        外层为 list 以与 valiant 统一（det 只有一条路径）。
        """
        now, path = src, [src]
        limit = max(1, self.node_num() * 4)
        for _ in range(limit):
            if now == dst:
                return [path]
            now = self.next(now, dst)
            path.append(now)
        raise RuntimeError(
            f"路由未收敛: {src}->{dst}, last_path={path}"
        )

    def valiant(self, src: int, dst: int) -> list[list[int]]:
        """Valiant 路由：det 直连 + 经所有中间 terminal 的中转路径。

        子类可覆写以优化中转节点选择（如 Dragonfly 只选 global router）。
        """
        paths = self.det(src, dst)
        for mid in self.terminals():
            if mid in {src, dst}:
                continue
            paths.append(
                self.det(src, mid)[0] + self.det(mid, dst)[0][1:]
            )
        return _unique_paths(paths)


# ---------------------------------------------------------------------------
# 共享工具
# ---------------------------------------------------------------------------


def _unique_paths(paths: list[list[int]]) -> list[list[int]]:
    """路径去重，保持首次出现顺序。"""
    seen: set[tuple[int, ...]] = set()
    unique: list[list[int]] = []
    for path in paths:
        key = tuple(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique
