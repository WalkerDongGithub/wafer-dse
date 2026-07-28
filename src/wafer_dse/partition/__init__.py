"""晶圆分区建模与布线搜索问题定义。

使用方式:
    from wafer_dse.partition import WaferGrid, RoutingProblem, GreedyRouter
    from wafer_dse.partition import GridPlacer, RoutingFeasibility

    # placement
    placer = GridPlacer(grid_size=8)
    result = placer.place(die_ids=[0,1,2,3], edges=[(0,1,1.0)])

    # routing feasibility
    grid = WaferGrid.rect(n=8, die_zones=[(2,3), (4,5)])
    checker = RoutingFeasibility(grid)
    ok = checker.check(result.positions, demands=[(0,1,12.5)])
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
from wafer_dse.partition.placement import (
    GridPlacer,
    PlacementResult,
)
from wafer_dse.partition.routing_lp import (
    RoutingFeasibility,
    RoutingFeasibilityResult,
)

__all__ = [
    # grid
    "PartitionType",
    "WaferGrid",
    "Zone",
    # placement
    "GridPlacer",
    "PlacementResult",
    # routing LP
    "RoutingFeasibility",
    "RoutingFeasibilityResult",
    # assignment
    "GreedyRouter",
    "LogicalEdge",
    "LogicalTopology",
    "RoutedEdge",
    "RoutingPlan",
    "RoutingProblem",
    "SearchStrategy",
]
