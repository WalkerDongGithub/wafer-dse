"""求解器子包。

提供：
    - Solver / SolverResult   —— 求解器抽象接口与结果契约
    - FixedRouteSolver        —— 固定路由精确求解器
    - create_solver           —— 根据路由策略自动选择求解器的工厂函数

分层关系：
    solver/
      interface.py        ← 契约层：Solver ABC, SolverResult
      algorithm/          ← 工具层：Hungarian, derangement（纯数学，不感知网络）
      fixed_route.py      ← 实现层：组合算法 + 拓扑路由遍历
      __init__.py         ← 聚合层：导出 + 求解器工厂

扩展方式：
    新增求解器时：
    1. 在 solver/ 下新建 your_solver.py，实现 Solver 接口
    2. 在 create_solver() 的注册表中添加该求解器类
"""

from __future__ import annotations

from wafer_dse.architecture_model.solver.algorithm import (
    hungarian_min_cost,
    max_weight_derangement,
)
from wafer_dse.architecture_model.solver.fixed_route import FixedRouteSolver
from wafer_dse.architecture_model.solver.interface import (
    Solver,
    SolverResult,
)

# ---------------------------------------------------------------------------
# 求解器注册表 —— 新增求解器在此登记
# ---------------------------------------------------------------------------

# 按优先级排列的求解器类列表。create_solver 按顺序尝试匹配。
_SOLVER_CLASSES: list[type[Solver]] = [
    FixedRouteSolver,
    # 未来扩展：
    # AdaptiveLPSolver,
    # MonteCarloSolver,
    # CuttingPlaneSolver,
]


def create_solver(route: str) -> Solver:
    """根据路由策略自动创建匹配的求解器。

    遍历注册的求解器类，返回第一个声明支持该 route 的实例。
    当多个求解器支持同一 route 时，注册表中靠前的优先。

    Args:
        route: 路由策略标识（"det", "val", "opt", ...）。

    Returns:
        匹配的 Solver 实例。

    Raises:
        ValueError: 没有任何注册的求解器支持给定的 route。

    Example:
        >>> solver = create_solver("det")
        >>> isinstance(solver, FixedRouteSolver)
        True
        >>> solver.supported_routes
        frozenset({'det', 'val'})
    """
    for solver_cls in _SOLVER_CLASSES:
        # 创建临时实例以查询 supported_routes
        # （规模很小，构造开销可忽略）
        instance = solver_cls()
        if route in instance.supported_routes:
            return instance

    supported = set()
    for cls in _SOLVER_CLASSES:
        supported |= set(cls().supported_routes)
    raise ValueError(
        f"无求解器支持 route={route!r}。"
        f"当前已注册的 route：{supported}"
    )


__all__ = [
    "FixedRouteSolver",
    "Solver",
    "SolverResult",
    "create_solver",
    "hungarian_min_cost",
    "max_weight_derangement",
]
