"""
problem —— 晶圆级交换机 DSE 的线性规划引擎 (纯数学层).

架构：
  ctx/      — 变量声明与约束收集器
  models/   — 约束模型 (perf/phys, LP 模板, 不 import physical)
  engine/   — Solver + Runner + ResultStore
  queries/  — 查询模式（feasibility, bmax, ...）
  builder/  — 编排层: 拓扑 + 参数 + Layout → 模型列表 (Stage 4 拆分)

物理/几何符号 (DiePlacement / MfitStackConfig / ThermalNetwork /
ThermalNetworkBuilder / AnalyticNetworkBuilder / plot_temperature)
在 physical/layout/thermal_network/, 不在此导出——
builder 直接 import physical.layout.thermal_network.
"""

# 数据契约
from problem.ctx import Ctx, LinearC, Model, Term, VarSpec

# 约束模型
from problem.models import (
    PerfModel,
    ObliviousValiantModel,

    PhysModel,
    BumpModel, C4Model,
    ThermalModel, SteadyStateModel, GlobalPowerModel,
    DieAreaModel,
    WiringModel,
    WiringGrid,
    build_wiring_grid, build_routing_grid, populate_paths,
    make_wiring_model, make_routing_model,
)

# 引擎
from problem.engine import Result, Solver, CvxSolver, Runner, ResultStore

# 查询
from problem.queries import (
    Query, FeasibilityQuery, FeasibilityResult,
    BmaxQuery, BmaxResult, partition_bmax,
)

__all__ = [
    "Model",
    "Ctx", "VarSpec", "Term", "LinearC",
    "PerfModel",
    "ObliviousValiantModel",

    "PhysModel",
    "BumpModel", "C4Model",
    "ThermalModel", "SteadyStateModel", "GlobalPowerModel",
    "DieAreaModel",
    "WiringModel",
    "WiringGrid",
    "build_wiring_grid", "build_routing_grid", "populate_paths",
    "make_wiring_model", "make_routing_model",
    "Result", "Solver", "CvxSolver", "Runner", "ResultStore",
    "Query", "FeasibilityQuery", "FeasibilityResult",
    "BmaxQuery", "BmaxResult", "partition_bmax",
]

