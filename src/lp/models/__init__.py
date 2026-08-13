"""
约束模型——不同物理层面的约束族。

  perf/  性能约束族
  phys/  物理约束族

拓扑结构数据由 topology.Topology 的属性直接提供，不再需要独立的分析层。
"""

from lp.models.perf import PerfModel, PerformanceModel, EnvelopeModel, SelectedEnvelopeModel
from lp.models.perf.traffic_based import (
    Pattern, Selector,
    PermutationRep, PermutationPattern,
    TrafficMatrixPattern, TrafficMatrix,
    ConjugacySelector, SConjugacyReps,
    DerangementSelector, AllDerangements,
    ManualSelector,
    select_representatives,
)
from lp.models.phys import (
    PhysModel,
    BumpModel, C4Model,
    ThermalModel, ThermalNetwork, SteadyStateModel,
    ThermalNetworkBuilder, AnalyticNetworkBuilder,
    DiePlacement, MfitStackConfig,
)
from lp.models.phys.therm._temp_limit import GlobalPowerModel
# 注意：WarpModel 有意不导出——已移出论文约束集（见 archive/MATH_MODEL_COMPLETE_V3.md §3.5 状态注（V4 无此约束））
from lp.models.phys.wiring import (
    WiringModel, RoutingModel,
    WiringGrid, RoutingGrid,
    build_wiring_grid, build_routing_grid, populate_paths,
    make_wiring_model, make_routing_model,
)

__all__ = [
    "PerfModel", "PerformanceModel", "EnvelopeModel", "SelectedEnvelopeModel",
    "PhysModel",
    "Pattern", "Selector",
    "PermutationRep", "PermutationPattern",
    "TrafficMatrixPattern", "TrafficMatrix",
    "ConjugacySelector", "SConjugacyReps",
    "DerangementSelector", "AllDerangements",
    "ManualSelector", "select_representatives",
    "BumpModel", "C4Model",
    "ThermalModel", "ThermalNetwork", "SteadyStateModel",
    "ThermalNetworkBuilder", "AnalyticNetworkBuilder",
    "DiePlacement", "MfitStackConfig",
    "GlobalPowerModel",
    "WiringModel", "RoutingModel",
    "WiringGrid", "RoutingGrid",
    "build_wiring_grid", "build_routing_grid", "populate_paths",
    "make_wiring_model", "make_routing_model",
]
