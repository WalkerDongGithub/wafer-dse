"""晶圆分区建模与布线搜索问题定义。

使用方式:
    from wafer_dse.partition import WaferGrid, RoutingProblem, GreedyRouter

    grid = WaferGrid.rect(n=12)
    problem = RoutingProblem(topology=..., grid=grid, ...)
    router = GreedyRouter(problem)
    plan = router.solve()
    print(plan.summary())
"""

from wafer_dse.partition.grid import (
    PartitionType,
    WaferGrid,
    Zone,
)
from wafer_dse.partition.assignment import (
    GreedyRouter,
    LogicalEdge,
    LogicalTopology,
    RoutedEdge,
    RoutingPlan,
    RoutingProblem,
    SearchStrategy,
)

__all__ = [
    # grid
    "PartitionType",
    "WaferGrid",
    "Zone",
    # assignment
    "GreedyRouter",
    "LogicalEdge",
    "LogicalTopology",
    "RoutedEdge",
    "RoutingPlan",
    "RoutingProblem",
    "SearchStrategy",
]
