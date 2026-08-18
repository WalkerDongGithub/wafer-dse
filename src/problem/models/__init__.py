"""
约束模型——不同物理层面的约束族 (LP 约束模板层).

  perf/  性能约束族
  phys/  物理约束族 (LP 模板; 物理/几何实体在 physical/)

拓扑结构数据由 topology.Topology 的属性直接提供，不再需要独立的分析层。

物理/几何符号 (DiePlacement / MfitStackConfig / ThermalNetwork /
ThermalNetworkBuilder / AnalyticNetworkBuilder / plot_temperature)
不在此导出——由 problem/builder 直接 import physical.layout.thermal_network.
"""

from problem.models.perf import PerfModel, EnvelopeModel, SelectedEnvelopeModel
from problem.models.perf.traffic_based import (
    Pattern, Selector,
    PermutationPattern,
    TrafficMatrixPattern,
    ConjugacySelector,
    DerangementSelector,
    ManualSelector,
    select_representatives,
)
from problem.models.phys import (
    PhysModel,
    BumpModel, C4Model,
    ThermalModel, SteadyStateModel, GlobalPowerModel,
)
# 注意：WarpModel 有意不导出——已移出论文约束集（见 archive/MATH_MODEL_COMPLETE_V3.md §3.5 状态注（V4 无此约束））
from problem.models.phys.wiring import (
    WiringModel,
    WiringGrid,
    build_wiring_grid, build_routing_grid, populate_paths,
    make_wiring_model, make_routing_model,
)

__all__ = [
    "PerfModel", "EnvelopeModel", "SelectedEnvelopeModel",
    "PhysModel",
    "Pattern", "Selector",
    "PermutationPattern",
    "TrafficMatrixPattern",
    "ConjugacySelector",
    "DerangementSelector",
    "ManualSelector", "select_representatives",
    "BumpModel", "C4Model",
    "ThermalModel", "SteadyStateModel", "GlobalPowerModel",
    "WiringModel",
    "WiringGrid",
    "build_wiring_grid", "build_routing_grid", "populate_paths",
    "make_wiring_model", "make_routing_model",
]

