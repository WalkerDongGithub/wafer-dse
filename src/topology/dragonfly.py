"""Dragonfly 拓扑族。

DragonflyTopology 是面向高性能互连的分层拓扑：
    - 组（group）内全互联（a 个 router，每 router p 个 terminal）
    - 组间通过全局链路连接（每 router h 个全局端口）
    - 总 group 数 = a × h + 1

经典变体（当前实现的是标准 DragonflyTopology）：
    - DragonflyTopology     —— Cray Cascade 风格，单层全局链路
    - DragonflyPlusTopology —— 增加 trunk link（组间直连），减少全局跳数
    - MegaFly       —— 两层层次化 DragonflyTopology（group of groups）
"""

from __future__ import annotations

from topology import Topology, _unique_paths


class DragonflyTopology(Topology):
    """标准 DragonflyTopology 拓扑。

    参数：
        a: 每组 router 数
        p: 每 router 的 terminal 数
        h: 每 router 的全局端口数

    结构：
        - 共 g = a×h + 1 个 group
        - 每 group：a 个 router，每 router 1 个内部节点 + p 个 terminal
        - 全局链路：group i 的第 j 个 router 连接 group (i+j+1) % g
        - 总节点数 = g × a × (p + 1)
        - 总 terminal 数 = g × a × p

    Valiant 路由覆写：
        优化为只经中间 group 的全局 router 中转（而非所有 terminal），
        减少冗余路径以加速求解。
    """

    def __init__(self, a: int, p: int, h: int) -> None:
        self.a = a
        self.p = p
        self.h = h
        self.g = a * h + 1
        self.total_terminal_num = self.g * a * p
        self.total_node_num = self.g * a * (p + 1)

    # —— 全局端口映射 ——

    def global_port(self, src_group: int, dst_group: int) -> int:
        """返回 src_group 中负责连接 dst_group 的 router 编号。"""
        return (dst_group - src_group - 1 + self.g) % self.g // self.h

    # —— 坐标转换 ——

    def to_node(self, loc: list[int]) -> int:
        group, router, terminal = loc
        return (
            terminal
            + router * (self.p + 1)
            + group * (self.p + 1) * self.a
        )

    def to_loc(self, node_id: int) -> list[int]:
        per_group = self.a * (self.p + 1)
        group = node_id // per_group
        router = (node_id % per_group) // (self.p + 1)
        terminal = (node_id % per_group) % (self.p + 1)
        return [group, router, terminal]

    # —— terminal / 节点数 ——

    def is_terminal(self, node_id: int) -> bool:
        return self.to_loc(node_id)[2] != 0

    def terminal_num(self) -> int:
        return self.total_terminal_num

    def node_num(self) -> int:
        return self.total_node_num

    # —— 单步路由 ——

    def next(self, now: int, dst: int) -> int:
        sg, sr, st = self.to_loc(now)
        dg, dr, dt = self.to_loc(dst)

        # 已到达
        if [sg, sr, st] == [dg, dr, dt]:
            return now

        # terminal → 本地 router
        if st != 0:
            return self.to_node([sg, sr, 0])

        # 同 group：走本地 router → 目标
        if sg == dg:
            if sr == dr:
                return self.to_node([dg, dr, dt])
            return self.to_node([dg, dr, 0])

        # 跨 group：走全局链路
        src_global = self.global_port(sg, dg)
        if sr == src_global:
            dst_global = self.global_port(dg, sg)
            return self.to_node([dg, dst_global, 0])
        return self.to_node([sg, src_global, 0])

    # —— Valiant（覆写：经 group-level 全局 router 中转） ——

    def valiant(self, src: int, dst: int) -> list[list[int]]:
        """Dragonfly Valiant：只枚举中间 group 的全局 router。

        与基类实现的区别：
            - 基类枚举所有 terminal（数量 = g×a×p，可能数千）
            - 本实现只枚举中间 group 的对应全局 router（数量 = g-2）
            - 大幅减少候选路径数，对求解性能至关重要
        """
        paths = self.det(src, dst)
        sg, _, _ = self.to_loc(src)
        dg, _, _ = self.to_loc(dst)
        for mid_group in range(self.g):
            if mid_group in {sg, dg}:
                continue
            mid = self.to_node(
                [mid_group, self.global_port(sg, mid_group), 0]
            )
            paths.append(
                self.det(src, mid)[0] + self.det(mid, dst)[0][1:]
            )
        return _unique_paths(paths)


# ---------------------------------------------------------------------------
# DragonflyPlusTopology（骨架占位，未接入——论文 DSE 只用标准 DragonflyTopology）
# ---------------------------------------------------------------------------


class DragonflyPlusTopology(Topology):
    """Dragonfly+ 拓扑（骨架占位，未接入）。

    DragonflyTopology+ 在标准 DragonflyTopology 基础上增加了 trunk link：
        - 每 router 除全局端口外，还有 trunk 端口连接相邻 group。
        - 好处：减少 Valiant 中转跳数，降低延迟。

    骨架占位，未接入：核心方法全部 NotImplementedError，
    不参与论文 §2.7 的组间 DSE（论文只用标准 DragonflyTopology）。
    """

    def __init__(self, a: int, p: int, h: int, t: int = 1) -> None:
        """
        Args:
            a: 每组 router 数
            p: 每 router 的 terminal 数
            h: 每 router 的全局端口数
            t: 每 router 的 trunk 端口数（默认 1）
        """
        self.a = a
        self.p = p
        self.h = h
        self.t = t
        self.g = a * h + 1
        self.total_terminal_num = self.g * a * p
        # trunk links 增加了额外的中间节点
        self.total_node_num = self.g * a * (p + 1 + t)

    def to_loc(self, node_id: int) -> list[int]:
        raise NotImplementedError("DragonflyPlus 为骨架，待完整实现")

    def to_node(self, loc: list[int]) -> int:
        raise NotImplementedError("DragonflyPlus 为骨架，待完整实现")

    def is_terminal(self, node_id: int) -> bool:
        raise NotImplementedError("DragonflyPlus 为骨架，待完整实现")

    def terminal_num(self) -> int:
        return self.total_terminal_num

    def node_num(self) -> int:
        return self.total_node_num

    def next(self, now: int, dst: int) -> int:
        raise NotImplementedError("DragonflyPlus 为骨架，待完整实现")
