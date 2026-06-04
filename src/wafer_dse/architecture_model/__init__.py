"""体系结构级初筛模块。

公开 API：
    ArchitectureModel —— 编排器，评估拓扑的无阻塞带宽潜能
    Solver / SolverResult —— 求解器抽象接口
    FixedRouteSolver + create_solver —— 求解器实现与工厂
    Topology / Mesh / Torus / Dragonfly —— 拓扑定义

模块结构：
    topology.py       拓扑定义（纯数据结构）
    solver/           求解器子包
        interface.py   Solver ABC + SolverResult（契约）
        algorithm/     纯数学工具（Hungarian, derangement）
        fixed_route.py 固定路由求解器实现
        __init__.py    导出 + create_solver 工厂
    model.py          编排层（薄 facade）
"""

from wafer_dse.architecture_model.model import ArchitectureModel
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
    "ArchitectureModel",
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
