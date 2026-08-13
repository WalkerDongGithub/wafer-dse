"""
布局求解器.

接口:
  PlacementSolver (ABC) —— solve(problem) -> PlacementSolution
实现:
  GridFillSolver —— 逐行填充 (feasible only, 不使用 topology)
未来:
  拓扑感知求解器 —— 链路多的 die 对放相邻位置 (problem.edges 预留)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from physical.placement._problem import (
    DieSpec, PlacementProblem, DiePosition, PlacementSolution,
)


class PlacementSolver(ABC):
    """布局求解器抽象接口."""

    name: str = "abstract"

    @abstractmethod
    def solve(self, problem: PlacementProblem) -> PlacementSolution:
        ...


class GridFillSolver(PlacementSolver):
    """逐行填充.

    n = floor(L/d), 从 [0,0] 开始逐行放 die.
    problem.edges 预留给未来拓扑感知求解器.
    """

    name = "grid_fill"

    def solve(self, problem: PlacementProblem) -> PlacementSolution:
        d = problem.die_side_mm
        L = problem.interposer_side_mm
        n = int(L / d)
        if n < 1:
            raise ValueError(f"interposer {L}mm < die {d}mm")

        k = problem.die_count
        if k > n * n:
            raise ValueError(f"{k} dies > {n}×{n} = {n*n} grid capacity")

        positions = []
        for i in range(k):
            row = i // n
            col = i % n
            spec = DieSpec(label=f"d{i}", side_mm=d,
                           group_id=i // 2, router_id=i % 2)
            positions.append(DiePosition(spec=spec, row=row, col=col))

        return PlacementSolution(
            positions=positions,
            grid_n=n, die_side_mm=d, interposer_side_mm=L,
        )


def solve_grid_placement(problem: PlacementProblem) -> PlacementSolution:
    """函数接口（backward compat）—— GridFillSolver 的薄封装."""
    return GridFillSolver().solve(problem)
