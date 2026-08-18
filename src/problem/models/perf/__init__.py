"""
性能约束族 —— 纯路由问题，与端口带宽 B 无关。

PerfModel —— 抽象基类：
  traffic_based/  OptimalValiantModel（最优路由包络，f 为决策变量）
                   ObliviousValiantModel（静态 oblivious Valiant 包络，V5 §7.3）
"""

from problem.ctx import Model


class PerfModel(Model):
    """性能约束族 —— 流量模式 → 链路负载 L。

    build(ctx, B) 接受 B 但忽略：路由是纯拓扑问题，
    流量分配与端口带宽无关。
    """


# 子模块
from problem.models.perf.traffic_based import (  # noqa: E402
    OptimalValiantModel, SelectedOptimalValiantModel,
    ObliviousValiantModel, SelectedObliviousValiantModel,
)

__all__ = ["PerfModel",
           "OptimalValiantModel", "SelectedOptimalValiantModel",
           "ObliviousValiantModel", "SelectedObliviousValiantModel"]
