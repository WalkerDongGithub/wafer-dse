"""求解器接口定义。

该模块定义求解器的抽象契约，与任何具体算法或拓扑无关。
所有求解器必须实现 Solver 接口，返回 SolverResult。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wafer_dse.architecture_model.topology import Topology


# ---------------------------------------------------------------------------
# 求解结果 —— 求解器与调用方之间的数据契约
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SolverResult:
    """单次求解的完整输出。

    Attributes:
        worst_load:
            全网最坏链路的归一化负载（≥0）。
            含义：在 worst-case traffic 下，某条链路承载的归一化流量倍数。
            值越大说明该链路越是瓶颈。
        worst_link:
            瓶颈链路的 (src_node, dst_node) 标识。
            无链路时为 None（例如单节点拓扑）。
        nonblocking_gbps_per_port:
            在此 worst-case 下，每个端口能保证的无阻塞注入带宽 (Gbps)。
            计算公式：link_capacity_gbps / worst_load。
        witness:
            造成 worst_load 的具体 traffic pattern ——
            [(src_0, dst_0), (src_1, dst_1), ...] 的排列/derangement。
            空列表表示未计算 witness。
    """

    worst_load: float
    worst_link: tuple[int, int] | None
    nonblocking_gbps_per_port: float
    witness: list[tuple[int, int]]


# ---------------------------------------------------------------------------
# 求解器抽象基类
# ---------------------------------------------------------------------------


class Solver(ABC):
    """网络潜能求解器抽象基类。

    每一种求解器代表一种计算 nonblocking bandwidth 的独立策略：

    - FixedRouteSolver  —— 固定路由 + Hungarian exact worst-case
    - (未来) AdaptiveLPSolver   —— 自适应路由 + cvxpy LP
    - (未来) MonteCarloSolver   —— 采样近似，面向大规模拓扑
    - (未来) CuttingPlaneSolver —— 切割平面法证书

    使用方式：

        solver = create_solver("det")
        result = solver.solve(topo, route="det", link_capacity_gbps=800.0)
        print(f"{result.nonblocking_gbps_per_port:.1f} Gbps/port")
    """

    @abstractmethod
    def solve(
        self,
        topo: Topology,
        route: str,
        link_capacity_gbps: float,
    ) -> SolverResult:
        """计算拓扑在给定路由和链路容量下的无阻塞潜能。

        Args:
            topo: 待评估的拓扑实例（实现 Topology 接口）。
            route: 路由策略标识，如 "det" / "val" / "opt"。
            link_capacity_gbps: 单条物理链路的基础容量 (Gbps)。

        Returns:
            SolverResult：包含 worst_load、nonblocking 带宽和 witness。

        Raises:
            ValueError: 该求解器不支持给定的 route。
        """
        ...

    @property
    @abstractmethod
    def supported_routes(self) -> frozenset[str]:
        """该求解器支持的路由策略集合。

        用于 solver factory 做自动匹配，也供调用方做能力查询。
        """
        ...
