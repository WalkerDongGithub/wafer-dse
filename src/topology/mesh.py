"""二维 MeshTopology 拓扑。

所有节点都是 terminal，维序路由先走 y 再走 x。
"""

from __future__ import annotations

from topology import Topology


class MeshTopology(Topology):
    """二维 mesh：N = size × size，全 terminal。

    路由：维序，先 y 后 x（dim 1 → dim 0）。
    """

    def __init__(self, size: int) -> None:
        self.size = size
        self.x = size
        self.n = size * size

    # —— 坐标转换 ——

    def to_loc(self, node_id: int) -> list[int]:
        return [node_id % self.size, node_id // self.size]  # [x, y]

    def to_node(self, loc: list[int]) -> int:
        return loc[0] + loc[1] * self.size

    # —— terminal / 节点数 ——

    def is_terminal(self, node_id: int) -> bool:
        return True

    def terminal_num(self) -> int:
        return self.n

    def node_num(self) -> int:
        return self.n

    # —— 单步路由（先 y 后 x） ——

    def next(self, now: int, dst: int) -> int:
        sx, sy = self.to_loc(now)
        dx, dy = self.to_loc(dst)
        if sy != dy:
            sy += 1 if sy < dy else -1
        elif sx != dx:
            sx += 1 if sx < dx else -1
        return self.to_node([sx, sy])
