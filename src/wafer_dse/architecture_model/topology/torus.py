"""二维 Torus 拓扑。

所有节点都是 terminal，环绕维序路由（先 x 后 y，每维选最短方向）。
"""

from __future__ import annotations

from wafer_dse.architecture_model.topology.base import Topology


class Torus(Topology):
    """二维 torus：N = size × size，全 terminal。

    路由：维序，先 x 后 y（dim 0 → dim 1），每维选最短环绕方向。
    """

    def __init__(self, size: int) -> None:
        self.size = size
        self.x = size  # 兼容旧属性
        self.n = size * size

    # —— 坐标转换 ——

    def to_loc(self, node_id: int) -> list[int]:
        return [node_id % self.size, node_id // self.size]  # [x, y]

    def to_node(self, loc: list[int]) -> int:
        return loc[0] % self.size + (loc[1] % self.size) * self.size

    # —— terminal / 节点数 ——

    def is_terminal(self, node_id: int) -> bool:
        return True

    def terminal_num(self) -> int:
        return self.n

    def node_num(self) -> int:
        return self.n

    # —— 单步路由（先 x 后 y，最短环绕） ——

    def next(self, now: int, dst: int) -> int:
        sx, sy = self.to_loc(now)
        dx, dy = self.to_loc(dst)
        if sx != dx:
            step = 1 if (dx - sx) % self.size <= (sx - dx) % self.size else -1
            return self.to_node([sx + step, sy])
        if sy != dy:
            step = 1 if (dy - sy) % self.size <= (sy - dy) % self.size else -1
            return self.to_node([sx, sy + step])
        return now
