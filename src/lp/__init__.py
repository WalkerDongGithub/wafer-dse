"""
lp2 —— 晶圆级交换机 DSE 的线性规划引擎。

架构：
  ctx/      — 变量声明与约束收集器
  models/   — 约束模型（perf/phys/therm + traffic）
  engine/   — Solver + Runner + ResultStore
  queries/  — 查询模式（feasibility, bmax, ...）
"""

# 数据契约
from lp.ctx import Ctx, LinearC, Model, Term, VarSpec

# 约束模型 + 流量选择器
from lp.models import (
    PerfModel, PerformanceModel, EnvelopeModel, SelectedEnvelopeModel,
    PhysModel,
    Pattern, Selector,
    PermutationRep, PermutationPattern,
    TrafficMatrixPattern, TrafficMatrix,
    ConjugacySelector, SConjugacyReps,
    DerangementSelector, AllDerangements,
    ManualSelector, select_representatives,
    BumpModel, C4Model,
    ThermalModel, ThermalNetwork, SteadyStateModel,
    ThermalNetworkBuilder, AnalyticNetworkBuilder,
    DiePlacement, MfitStackConfig,
    GlobalPowerModel,
    WiringModel, RoutingModel,
    WiringGrid, RoutingGrid,
    build_wiring_grid, build_routing_grid, populate_paths,
    make_wiring_model, make_routing_model,
)

# 引擎
from lp.engine import Result, Solver, CvxSolver, Runner, ResultStore

# 查询
from lp.queries import (
    Query, FeasibilityQuery, FeasibilityResult,
    BmaxQuery, BmaxResult, partition_bmax,
)

__all__ = [
    "Model",
    "Ctx", "VarSpec", "Term", "LinearC",
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
    "Result", "Solver", "CvxSolver", "Runner", "ResultStore",
    "Query", "FeasibilityQuery", "FeasibilityResult",
    "BmaxQuery", "BmaxResult", "partition_bmax",
]
