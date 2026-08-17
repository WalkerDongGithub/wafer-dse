"""
性能约束族 —— 纯路由问题，与端口带宽 B 无关。

PerfModel —— 抽象基类：
  traffic_based/  EnvelopeModel（多需求模式包络）
"""

from lp.ctx import Model


class PerfModel(Model):
    """性能约束族 —— 流量模式 → 链路负载 L。

    build(ctx, B) 接受 B 但忽略：路由是纯拓扑问题，
    流量分配与端口带宽无关。
    """


# backward compat
PerformanceModel = PerfModel

# 子模块
from lp.models.perf.traffic_based import EnvelopeModel, SelectedEnvelopeModel  # noqa: E402

__all__ = ["PerfModel", "PerformanceModel", "EnvelopeModel",
           "SelectedEnvelopeModel"]
