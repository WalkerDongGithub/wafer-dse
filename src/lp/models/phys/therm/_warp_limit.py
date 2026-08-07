"""翘曲极限约束——相邻节点温差 ≤ ΔT_max（留白，待实现）。

利用 G⁻¹ ≥ 0：W·T ≤ ΔT_max 等价于 W·G⁻¹(P+b) ≤ ΔT_max。
与温度上限独立——两个约束可各自开启/关闭。
"""

from lp.models.phys.therm import ThermalModel


class WarpModel(ThermalModel):
    """翘曲约束（占位）。"""

    def build(self, ctx, B: float) -> None:
        raise NotImplementedError("翘曲约束待实现")
