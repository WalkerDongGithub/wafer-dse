"""
约束模型——不同物理层面的约束族。

  topo/  拓扑结构分析（perf/phys/therm 的共同数据源）
  perf/  性能约束族
  phys/  物理约束族
"""

from lp.models.topo import TopoStructure, analyze as analyze_topo
from lp.models.perf import PerformanceModel, EnvelopeModel
from lp.models.perf.traffic_based import (
    PermutationRep, SConjugacyReps, AllDerangements, ManualSelector,
)
from lp.models.phys import (
    BumpModel,
    ThermalModel, ThermalNetwork, NetworkModel, build_thermal_network,
)
from lp.models.phys.therm._temp_limit import PowerDensityModel

__all__ = [
    "TopoStructure", "analyze_topo",
    "PerformanceModel", "EnvelopeModel",
    "PermutationRep", "SConjugacyReps", "AllDerangements", "ManualSelector",
    "BumpModel",
    "ThermalModel", "ThermalNetwork", "NetworkModel", "build_thermal_network",
    "PowerDensityModel",
]
