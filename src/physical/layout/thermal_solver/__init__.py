"""求解器子包 — 工厂驱动的多态架构。

对外只暴露:
  - ThermalSolver (ABC)
  - create_solver (工厂)

所有具体实现类为私有。
"""

from ._base import ThermalSolver
from ._simple import _SimpleSolver
from ._mfit import _MfitSolver, _MfitSimConfig
from ._hierarchical import _HierarchicalSolver, _WaferConfig


def create_solver(
    kind: str = "auto",
    sim_config: _MfitSimConfig | None = None,
    wafer_config: _WaferConfig | None = None,
) -> ThermalSolver:
    """创建热求解器。

    kind:
        "simple"        — 面积×功率密度，零依赖
        "mfit"         — MFIT 3D RC 网络，需要 C 库
        "hierarchical" — 分层模型 (MFIT 标定 + 2D 晶圆网络)
        "auto"         — 自动选择最佳可用求解器
    """
    if kind == "simple":
        return _SimpleSolver()

    if kind == "mfit":
        return _MfitSolver(sim_config=sim_config)

    if kind == "hierarchical":
        return _HierarchicalSolver(
            calibrator=_MfitSolver(sim_config=sim_config),
            wafer_config=wafer_config,
        )

    if kind == "auto":
        mfit = _MfitSolver(sim_config=sim_config)
        if mfit.available:
            return _HierarchicalSolver(
                calibrator=mfit, wafer_config=wafer_config,
            )
        return _SimpleSolver()

    raise ValueError(
        f"Unknown solver kind: {kind!r}. "
        f"Choose from: simple, mfit, hierarchical, auto"
    )
