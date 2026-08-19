"""FullMesh 拓扑 — 组内全互连。

a 个 die 完全互连，每个 die 有 p 个终端端口。
用于 DragonflyTopology 的组内无阻塞带宽判定。

节点布局:
  0 .. a-1           → die (router) 节点
  a .. a + a*p - 1   → 终端节点 (die d 的终端 t = a + d*p + t)

路由: 终端 → 本地 die → (目标 die, 直连, 1 hop) → 目标终端.
     同 die 内终端互访不经外部链路.
"""

from __future__ import annotations

from topology import Topology, _unique_paths


class FullMeshTopology(Topology):
    """a 个 die 全互连，每个 die 挂 p 个终端."""

    def __init__(self, a: int, p: int = 1):
        self.a = a
        self.p = p
        self._n_dies = a
        self._n_terminals = a * p
        self._n_nodes = a + a * p  # a router nodes + a*p terminals

    # -- 坐标转换 -----------------------------------------------------------

    def to_loc(self, node_id: int) -> list[int]:
        if node_id < self.a:
            return [node_id, -1]       # router node: [die, -1]
        else:
            t = node_id - self.a
            die = t // self.p
            port = t % self.p
            return [die, port]          # terminal: [die, port]

    def to_node(self, loc: list[int]) -> int:
        die, port = loc
        if port == -1:
            return die
        return self.a + die * self.p + port

    def is_terminal(self, node_id: int) -> bool:
        return node_id >= self.a

    def terminal_num(self) -> int:
        return self._n_terminals

    def node_num(self) -> int:
        return self._n_nodes

    # -- 单步路由 -----------------------------------------------------------

    def next(self, now: int, dst: int) -> int:
        if now == dst:
            return now

        sd, sp = self.to_loc(now)
        dd, dp = self.to_loc(dst)

        # 终端 → 本地 die
        if sp != -1:
            return self.to_node([sd, -1])

        # 已到目标 die → 目标终端
        if sd == dd:
            if dp == -1:
                return now  # 同为 router
            return self.to_node([dd, dp])

        # 不同 die: 直连（全互连，1 hop）
        # 先到目标 die 的 router node
        return self.to_node([dd, -1])

    # -- Valiant ------------------------------------------------------------

    def valiant(self, src: int, dst: int) -> list[list[int]]:
        """FullMesh Valiant: det + 经中间 die 中转.

        中转只枚举中间 die，不枚举所有终端——减少候选路径数。
        """
        paths = self.det(src, dst)
        sd, _ = self.to_loc(src)
        dd, _ = self.to_loc(dst)
        for md in range(self.a):
            if md in {sd, dd}:
                continue
            mid_node = self.to_node([md, -1])
            paths.append(
                self.det(src, mid_node)[0] + self.det(mid_node, dst)[0][1:]
            )
        return _unique_paths(paths)


# -- node_to_die 映射 -------------------------------------------------------

def fullmesh_node_to_die(topo: FullMeshTopology) -> dict[int, int]:
    """所有节点（router + terminal）映射到 die index."""
    m = {}
    for n in range(topo.node_num()):
        die, port = topo.to_loc(n)
        m[n] = die
    return m
