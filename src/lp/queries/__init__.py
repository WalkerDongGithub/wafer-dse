"""
查询模式——每个 Query = 一个待回答的问题。

不同 query 有独立的 query_id、结果类型、store 条目。
内部可能共享 engine 和下层 query（如 bmax 调用 feasibility）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lp.ctx import Ctx, LinExpr
    from lp.engine import Result


class Query(ABC):
    """查询基类。

    query_id   — 唯一标识（store key 前缀）
    objective  — 目标表达式，None = feasibility
    interpret  — Result → 语义结果
    """

    query_id: str

    def objective(self, ctx: Ctx) -> LinExpr | None:
        return None

    @abstractmethod
    def interpret(self, sol: Result, ctx: Ctx, B: float):
        ...


# 子查询
from lp.queries.feasibility import FeasibilityQuery, FeasibilityResult  # noqa: E402
from lp.queries.bmax import BmaxQuery, BmaxResult, partition_bmax  # noqa: E402

__all__ = [
    "Query",
    "FeasibilityQuery", "FeasibilityResult",
    "BmaxQuery", "BmaxResult", "partition_bmax",
]
