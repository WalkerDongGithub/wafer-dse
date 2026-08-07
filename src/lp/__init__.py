"""
lp2 —— 晶圆级交换机 DSE 的线性规划引擎。

架构：
  ctx/      — 变量声明与约束收集器
  models/   — 约束模型（perf/phys/therm + traffic）
  engine/   — Solver + Runner + ResultStore
  queries/  — 查询模式（feasibility, bmax, ...）
"""

# 数据契约
from lp.ctx import Ctx, LinearC, Model, Sense, Term, VarSpec

# 约束模型 + 流量选择器
from lp.models import (
    TopoStructure, analyze_topo,
    PerformanceModel, EnvelopeModel,
    PermutationRep, SConjugacyReps, AllDerangements, ManualSelector,
    BumpModel,
    ThermalModel, ThermalNetwork, NetworkModel, build_thermal_network,
    PowerDensityModel,
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
    "Ctx", "VarSpec", "Term", "LinearC", "Sense",
    "TopoStructure", "analyze_topo",
    "PerformanceModel", "EnvelopeModel",
    "PermutationRep", "SConjugacyReps", "AllDerangements", "ManualSelector",
    "BumpModel",
    "ThermalModel", "ThermalNetwork", "NetworkModel", "build_thermal_network",
    "PowerDensityModel",
    "Result", "Solver", "CvxSolver", "Runner", "ResultStore",
    "Query", "FeasibilityQuery", "FeasibilityResult",
    "BmaxQuery", "BmaxResult", "partition_bmax",
]
