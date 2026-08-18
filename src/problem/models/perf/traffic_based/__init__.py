"""基于流量模式的性能模型——广义无阻塞潜能。

OptimalValiantModel — 核心：R 个排列 → 包络 L（最优路由，f 为决策变量）。
ObliviousValiantModel — 静态 oblivious Valiant 路由下的 L 包络（V5 §7.3，f 固定均匀分流）。
traffic/      — 流量模式选择器（排列代表元）。
"""

from problem.models.perf.traffic_based._envelope import (
    OptimalValiantModel, SelectedOptimalValiantModel,
)
from problem.models.perf.traffic_based._oblivious import (
    ObliviousValiantModel, SelectedObliviousValiantModel,
)
from problem.models.perf.traffic_based.traffic import (
    Pattern, Selector,
    PermutationPattern,
    TrafficMatrixPattern,
    ConjugacySelector,
    DerangementSelector,
    ManualSelector,
    select_representatives,
)

__all__ = [
    "OptimalValiantModel", "SelectedOptimalValiantModel",
    "ObliviousValiantModel", "SelectedObliviousValiantModel",
    "Pattern", "Selector",
    "PermutationPattern",
    "TrafficMatrixPattern",
    "ConjugacySelector",
    "DerangementSelector",
    "ManualSelector",
    "select_representatives",
]
