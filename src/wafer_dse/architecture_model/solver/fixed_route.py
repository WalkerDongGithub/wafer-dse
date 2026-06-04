"""固定路由精确求解器。

组合 algorithm/ 中的纯数学工具与拓扑路由遍历逻辑，
实现 FixedRouteSolver —— 固定路由 (det/val) 下的 exact worst-case 求解。

职责边界：
    - 知道 Topology 接口（遍历路由、枚举 terminal）
    - 知道 algorithm/ 提供的 Hungarian / derangement 工具
    - 不关心用户需求（Requirement）、封装（Packaging）等上层概念
"""

from __future__ import annotations

import itertools

from wafer_dse.architecture_model.solver.algorithm import (
    max_weight_derangement,
)
from wafer_dse.architecture_model.solver.interface import (
    Solver,
    SolverResult,
)
from wafer_dse.architecture_model.topology import Topology


class FixedRouteSolver(Solver):
    """固定路由下的 exact worst-case 无阻塞带宽求解器。

    算法流程：
        1. 枚举所有 src→dst 排列。
        2. 对每个 demand，按路由策略（det/val）将流量均分到候选路径。
        3. 对每条有向链路 e，累计 weight_e[src][dst] = demand 经过 e 的比例。
        4. 对每条链路求解 max-weight derangement → worst_load_e。
        5. worst_load = max_e worst_load_e。
        6. nonblocking_gbps_per_port = link_capacity / worst_load。

    复杂度：O(|L| × N³)，|L| 是有向链路数，N 是 terminal 数。
           对 N ≤ 64 的中等规模拓扑可在秒级完成。

    支持的路由策略：
        - "det": deterministic（维序路由，唯一路径）
        - "val": Valiant（det + 所有中间 terminal 中转）
    """

    # ------------------------------------------------------------------
    # Solver 接口实现
    # ------------------------------------------------------------------

    @property
    def supported_routes(self) -> frozenset[str]:
        return frozenset({"det", "val"})

    def solve(
        self,
        topo: Topology,
        route: str,
        link_capacity_gbps: float,
    ) -> SolverResult:
        self._validate_route(route)

        terminals = topo.terminals()
        index: dict[int, int] = {node: i for i, node in enumerate(terminals)}

        # —— 阶段 1：构建每条链路的 src→dst 权重矩阵 ——
        link_weights = self._build_link_weights(topo, route, terminals, index)

        # —— 阶段 2：对每条链路求 worst-case derangement ——
        worst_load, worst_link, worst_assignment = self._find_worst_link(
            link_weights
        )

        # —— 阶段 3：组装结果 ——
        nonblocking = (
            float("inf")
            if worst_load <= 0
            else link_capacity_gbps / worst_load
        )
        witness = (
            [(terminals[i], terminals[worst_assignment[i]]) for i in range(len(terminals))]
            if worst_assignment
            else []
        )

        return SolverResult(
            worst_load=worst_load,
            worst_link=worst_link,
            nonblocking_gbps_per_port=nonblocking,
            witness=witness,
        )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _validate_route(self, route: str) -> None:
        if route not in self.supported_routes:
            raise ValueError(
                f"FixedRouteSolver 不支持 route={route!r}，"
                f"仅支持 {set(self.supported_routes)}"
            )

    @staticmethod
    def _build_link_weights(
        topo: Topology,
        route: str,
        terminals: list[int],
        index: dict[int, int],
    ) -> dict[tuple[int, int], list[list[float]]]:
        """遍历所有 src→dst demand，计算每条链路的总负载系数矩阵。

        对每个 (src, dst) demand：
            - 获取候选路径（det=1条, val=1+terminals条）
            - 将 demand 均分到每条候选路径
            - 沿路径累加分摊系数到对应链路的 weight[src][dst] 上
        """
        n = len(terminals)
        link_weights: dict[tuple[int, int], list[list[float]]] = {}

        for src, dst in itertools.permutations(terminals, 2):
            paths = (
                topo.det(src, dst) if route == "det"
                else topo.valiant(src, dst)
            )
            share = 1.0 / len(paths)
            si, di = index[src], index[dst]

            for path in paths:
                for k in range(len(path) - 1):
                    link = (path[k], path[k + 1])
                    if link not in link_weights:
                        link_weights[link] = [
                            [0.0 for _ in range(n)] for _ in range(n)
                        ]
                    link_weights[link][si][di] += share

        return link_weights

    @staticmethod
    def _find_worst_link(
        link_weights: dict[tuple[int, int], list[list[float]]],
    ) -> tuple[float, tuple[int, int] | None, list[int]]:
        """对所有链路并行求解 max-weight derangement，返回全局最坏值。"""
        worst_load: float = -1.0
        worst_link: tuple[int, int] | None = None
        worst_assignment: list[int] = []

        for link, weight in link_weights.items():
            load, assignment = max_weight_derangement(weight)
            if load > worst_load:
                worst_load = load
                worst_link = link
                worst_assignment = assignment

        return worst_load, worst_link, worst_assignment
