"""
求解器——把 Ctx 编译为数学规划问题并求解。

Solver（ABC）—— 抽象求解接口。当前实现：CvxSolver（cvxpy）。
Result —— 一次求解的原始结果，不做语义解释。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from problem.ctx import Ctx, LinExpr


@dataclass
class Result:
    """一次求解的原始结果——通用字段，不绑定特定求解器。"""

    status: str
    solve_time_s: float = 0.0
    objective: float | None = None
    variables: dict[str, list[float]] | None = None
    duals: dict[str, float] | None = None


class Solver(ABC):
    """求解器抽象接口。

    solve(ctx, objective=None) → Result。
    当前唯一实现：CvxSolver（cvxpy）。
    """

    @abstractmethod
    def solve(self, ctx: Ctx,
              objective: LinExpr | None = None,
              maximize: bool = False,
              ) -> Result:
        ...


from problem.engine.solution._cvx import CvxSolver  # noqa: E402

__all__ = ["Result", "Solver", "CvxSolver"]
