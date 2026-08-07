"""基于流量模式的性能模型——广义无阻塞潜能。

EnvelopeModel — 核心：R 个排列 → 包络 L。
traffic/      — 流量模式选择器（排列代表元）。
"""

from lp.models.perf.traffic_based._envelope import EnvelopeModel
from lp.models.perf.traffic_based.traffic import (
    PermutationRep,
    SConjugacyReps, AllDerangements, ManualSelector,
)

__all__ = [
    "EnvelopeModel",
    "PermutationRep",
    "SConjugacyReps", "AllDerangements", "ManualSelector",
]
