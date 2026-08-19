"""k-ary n-cube 拓扑族。

经典的 k-ary n-cube 是 MeshTopology 和 TorusTopology 的 n 维推广：
    - k：每维节点数（radix）
    - n：维度数
    - wrap=True  → n 维 TorusTopology（每维有环绕链路）
    - wrap=False → n 维 MeshTopology（无边环绕）

特例：
    - KaryNCubeTopology(k=4, n=2, wrap=False) 等价于 MeshTopology(4)
    - KaryNCubeTopology(k=4, n=2, wrap=True)  等价于 TorusTopology(4)（但路由顺序不同）
    - KaryNCubeTopology(k=2, n=3, wrap=True)  即 2-ary 3-cube（经典 3D TorusTopology/超立方）

路由：统一维序路由，从最高维到最低维（dim n-1 → dim 0）。
      这与 MeshTopology 的先 y 后 x 一致，与 TorusTopology 的先 x 后 y 不同。
"""

from __future__ import annotations

from topology import Topology


class KaryNCubeTopology(Topology):
    """k-ary n-cube：n 维网格，每维 k 个节点。

    所有节点都是 terminal。全互联规模 = k^n。

    Attributes:
        k: 每维节点数（radix）。
        n: 维度数。
        wrap: True 表示 TorusTopology（环绕链路），False 表示 MeshTopology（无边环绕）。

    Example:
        >>> # 4x4 mesh（等价于 MeshTopology(4) 但路由顺序统一）
        >>> topo = KaryNCubeTopology(k=4, n=2, wrap=False)
        >>> topo.terminal_num()
        16

        >>> # 4x4 torus
        >>> topo = KaryNCubeTopology(k=4, n=2, wrap=True)
        >>> topo.terminal_num()
        16

        >>> # 3D torus: 4×4×4 = 64 nodes
        >>> topo = KaryNCubeTopology(k=4, n=3, wrap=True)
        >>> topo.terminal_num()
        64

        >>> # 4D mesh: 3×3×3×3 = 81 nodes (hypersquare)
        >>> topo = KaryNCubeTopology(k=3, n=4, wrap=False)
        >>> topo.terminal_num()
        81
    """

    def __init__(self, k: int, n: int, wrap: bool = True) -> None:
        if k < 2:
            raise ValueError(f"k (radix) 必须 ≥ 2，got {k}")
        if n < 1:
            raise ValueError(f"n (维度数) 必须 ≥ 1，got {n}")
        self.k = k
        self.n = n
        self.wrap = wrap
        self.total_nodes = k ** n

    # ------------------------------------------------------------------
    # 坐标转换
    # ------------------------------------------------------------------

    def to_loc(self, node_id: int) -> list[int]:
        """节点编号 → n 维坐标 [d_0, d_1, ..., d_{n-1}]。

        d_0 为最低位（fastest-varying），row-major 排列。
        """
        loc = []
        rem = node_id
        for _ in range(self.n):
            rem, d = divmod(rem, self.k)
            loc.append(d)
        return loc  # [d_0, d_1, ..., d_{n-1}]

    def to_node(self, loc: list[int]) -> int:
        """n 维坐标 → 节点编号。"""
        node_id = 0
        multiplier = 1
        for d in loc:
            node_id += (d % self.k if self.wrap else d) * multiplier
            multiplier *= self.k
        return node_id

    # ------------------------------------------------------------------
    # terminal / 节点数
    # ------------------------------------------------------------------

    def is_terminal(self, node_id: int) -> bool:
        return True  # 所有节点都是 terminal

    def terminal_num(self) -> int:
        return self.total_nodes

    def node_num(self) -> int:
        return self.total_nodes

    # ------------------------------------------------------------------
    # 维序路由（dim n-1 → dim 0）
    # ------------------------------------------------------------------

    def next(self, now: int, dst: int) -> int:
        """维序单步路由：从最高维到最低维依次对齐。

        - wrap=True:  每维选最短环绕方向（mod k）。
        - wrap=False: 每维直接走 ±1，不穿越边界。
        """
        if now == dst:
            return now

        src_loc = self.to_loc(now)
        dst_loc = self.to_loc(dst)

        # 从高维到低维找第一个未对齐的维度
        for dim in range(self.n - 1, -1, -1):
            s, d = src_loc[dim], dst_loc[dim]
            if s == d:
                continue
            step = self._step(s, d, dim)
            new_loc = list(src_loc)
            new_loc[dim] = s + step
            return self.to_node(new_loc)

        return now  # unreachable unless now==dst

    def _step(self, src: int, dst: int, dim: int) -> int:
        """计算在 dim 维上从 src 到 dst 的单步方向。"""
        if self.wrap:
            # 最短环绕方向
            diff = (dst - src) % self.k
            return 1 if diff <= self.k // 2 else -1
        else:
            return 1 if dst > src else -1
