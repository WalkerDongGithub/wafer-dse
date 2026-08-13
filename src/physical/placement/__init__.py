"""
Interposer 布局层 —— 芯粒物理摆放在 interposer 上的位置计算.

问题定义与求解分离:
  - 数据结构:    DieSpec, PlacementProblem, DiePosition, PlacementSolution
  - 求解器:      PlacementSolver (ABC) → GridFillSolver (逐行填充)
  - 函数入口:    solve_grid_placement (GridFillSolver 的薄封装, backward compat)
  - 可视化:      plot_placement (调试用)
"""

from physical.placement._problem import (
    DieSpec, PlacementProblem, DiePosition, PlacementSolution,
)
from physical.placement._solver import (
    PlacementSolver, GridFillSolver, solve_grid_placement,
)
from physical.placement._viz import plot_placement

__all__ = [
    "DieSpec", "PlacementProblem", "DiePosition", "PlacementSolution",
    "PlacementSolver", "GridFillSolver",
    "solve_grid_placement",
    "plot_placement",
]
