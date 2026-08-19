"""
性能约束族 —— 纯路由问题，与端口带宽 B 无关。

PerfModel —— 抽象基类：
  traffic_based/  ObliviousValiantModel（静态 oblivious Valiant 包络，V5 §7.3，f 固定）
"""

from problem.ctx import Model


class PerfModel(Model):
    """性能约束族 —— 流量模式 → 链路负载 L。

    build(ctx, B) 接受 B 但忽略：路由是纯拓扑问题，
    流量分配与端口带宽无关。
    """


# 子模块
from problem.models.perf.traffic_based import (  # noqa: E402
    ObliviousValiantModel,
)

__all__ = ["PerfModel", "ObliviousValiantModel"]
