"""DieAreaModel —— die 面积上界（MATH_MODEL_V5_JOINT_SENSITIVITY §2 (2f)）。

存在意义：
  A_die(B) = d(B)² ≤ A_max 是一级约束（V5 v5.21 作者定案）——α_d > 0 时
  面积约束直接给出 B 的上界（"B 只有上限没有下限"的模型侧形态）。
  约束不含 L 变量：纯 B 门槛，常数约束（0 ≤ A_max − d(B)²）。

怎么用：
  model = DieAreaModel(d0_mm=10.0, alpha_d=0.1, a_max_mm2=2500.0)
  model.build(ctx, B=400.0)   # 写 0 ≤ A_max − d(B)² 常数约束

读者指南：
  - 约束形式与 V5 §2(2f) 逐式对应；A_max 由 builder 按布局算出
    （粗上界 ≈ interposer 面积 ÷ 芯粒数）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from problem.models.phys import PhysModel

if TYPE_CHECKING:
    from problem.ctx import Ctx


class DieAreaModel(PhysModel):
    """die 面积上界——V5 §2(2f)。

    约束 0 ≤ A_max − d(B)²（常数，无 L 项）。rhs < 0 时 LP 不可行，
    BmaxQuery 判定该 B 不可行——面积约束作为纯 B 门槛生效。
    """

    def __init__(self, d0_mm: float, alpha_d: float, a_max_mm2: float) -> None:
        self._d0 = d0_mm
        self._alpha = alpha_d
        self._a_max = a_max_mm2

    def build(self, ctx: Ctx, B: float) -> None:
        d = self._d0 + self._alpha * B
        ctx.constrain(
            "area_die", [], "<=", float(self._a_max - d * d),
            meaning="die 面积达到上界 A_max",
        )

    def cache_key(self) -> tuple:
        return ("area_v1", self._d0, self._alpha, self._a_max)
