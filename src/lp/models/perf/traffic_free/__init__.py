"""流量无关的性能模型——RNB 等（留白）。

与 traffic_based 的区别：不依赖排列模式枚举。
直接用结构条件（如 Clos m≥n）判定无阻塞。
"""

from lp.models.perf import PerformanceModel


class TrafficFreeModel(PerformanceModel):
    """流量无关的性能模型基类（占位）。"""

    def build(self, ctx, B: float) -> None:
        raise NotImplementedError("流量无关模型待实现")
