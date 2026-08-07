"""
性能约束族。

PerformanceModel —— 抽象基类（两种实现路径）：
  traffic_based/  基于流量模式的模型（广义无阻塞潜能）
  traffic_free/   流量无关的模型（RNB 等，留白）
"""

from lp.ctx import Model


class PerformanceModel(Model):
    """性能约束族。子类实现 traffic_based 或 traffic_free。"""


# 子模块
from lp.models.perf.traffic_based import EnvelopeModel  # noqa: E402

__all__ = ["PerformanceModel", "EnvelopeModel"]
