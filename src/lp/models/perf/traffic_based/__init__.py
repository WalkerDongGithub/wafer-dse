"""基于流量模式的性能模型——广义无阻塞潜能。

EnvelopeModel — 核心：R 个排列 → 包络 L。
traffic/      — 流量模式选择器（排列代表元）。
"""

from lp.models.perf.traffic_based._envelope import (
    EnvelopeModel, SelectedEnvelopeModel,
)
from lp.models.perf.traffic_based.traffic import (
    Pattern, Selector,
    PermutationRep, PermutationPattern,
    TrafficMatrixPattern, TrafficMatrix,
    ConjugacySelector, SConjugacyReps,
    DerangementSelector, AllDerangements,
    ManualSelector,
    select_representatives,
)

__all__ = [
    "EnvelopeModel", "SelectedEnvelopeModel",
    "Pattern", "Selector",
    "PermutationRep", "PermutationPattern",
    "TrafficMatrixPattern", "TrafficMatrix",
    "ConjugacySelector", "SConjugacyReps",
    "DerangementSelector", "AllDerangements",
    "ManualSelector",
    "select_representatives",
]
