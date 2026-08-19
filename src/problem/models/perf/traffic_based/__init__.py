"""基于流量模式的性能模型——广义无阻塞潜能。

ObliviousValiantModel — 静态 oblivious Valiant 路由下的 L 包络（V5 §7.3，f 固定均匀分流）。
"""

from problem.models.perf.traffic_based._oblivious import (
    ObliviousValiantModel,
)

__all__ = [
    "ObliviousValiantModel",
]
