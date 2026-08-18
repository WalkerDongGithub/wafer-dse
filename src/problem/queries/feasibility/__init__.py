"""
feasibility query —— 在给定 B 下，系统是否存在可行配置？

这是所有 query 的基础——其他 query（bmax、sweep）内部调用它。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from problem.queries import Query

if TYPE_CHECKING:
    from problem.ctx import Ctx
    from problem.engine import Result


@dataclass
class FeasibilityResult:
    """一问一答：B 可行吗？"""

    B: float
    feasible: bool
    solve_time_s: float = 0.0

    envelope_L: dict[int, float] = field(default_factory=dict)
    binding_constraints: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def worst_load(self) -> float:
        return max(self.envelope_L.values()) if self.envelope_L else float("inf")


class FeasibilityQuery(Query):
    """固定 B 的可行性判定。

    目标函数：无（feasibility）。
    结果：FeasibilityResult（可行 + 包络负载）。
    """

    query_id = "feasibility"

    def interpret(self, sol: Result, ctx: Ctx, B: float) -> FeasibilityResult:
        feasible = sol.status in ("optimal", "optimal_inaccurate")
        L = {}
        if sol.variables and "L" in sol.variables:
            L = {i: v for i, v in enumerate(sol.variables["L"])}
        return FeasibilityResult(
            B=B, feasible=feasible, solve_time_s=sol.solve_time_s,
            envelope_L=L,
            binding_constraints=list(sol.duals.keys()) if sol.duals else [],
        )
