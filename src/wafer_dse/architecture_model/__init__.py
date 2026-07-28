"""体系结构模块。

公开 API：
    Solver / SolverResult —— 求解器抽象接口
    FixedRouteSolver + create_solver —— 求解器实现与工厂
    Topology / Mesh / Torus / Dragonfly —— 拓扑定义

模块结构：
    topology/          拓扑定义
    solver/            求解器子包
        interface.py   Solver ABC + SolverResult（契约）
        algorithm/     纯数学工具（Hungarian, derangement）
        fixed_route.py 固定路由求解器实现
        rust_backend.py Rust 加速后端
        __init__.py    导出 + create_solver 工厂
"""

from wafer_dse.architecture_model.solver import (
    FixedRouteSolver,
    Solver,
    SolverResult,
    create_solver,
)
from wafer_dse.architecture_model.topology import (
    Dragonfly,
    DragonflyPlus,
    KaryNCube,
    Mesh,
    Topology,
    Torus,
)

__all__ = [
    "Dragonfly",
    "DragonflyPlus",
    "FixedRouteSolver",
    "KaryNCube",
    "Mesh",
    "Solver",
    "SolverResult",
    "Topology",
    "Torus",
    "create_solver",
]
