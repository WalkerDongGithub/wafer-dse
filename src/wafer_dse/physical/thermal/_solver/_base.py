"""热求解器 ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .._config import ThermalConfig, ThermalResult


class ThermalSolver(ABC):
    """热求解器统一接口。

    所有求解器接受 ThermalConfig 输入，返回 ThermalResult 输出。
    具体实现类为私有 (_前缀)，外部通过 create_solver() 工厂获取。

    标定接口 (calibrate / is_calibrated / r_eff) 有默认实现：
    - 简单求解器 (如 _SimpleSolver) 直接可用，is_calibrated=True
    - 分层求解器 (如 _HierarchicalSolver) 需先 calibrate() 标定 R_eff
    """

    @abstractmethod
    def solve(self, config: ThermalConfig) -> ThermalResult:
        """求解并返回热分析结果。"""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """求解器名称 (用于 DSE 报告)。"""
        ...

    @property
    def available(self) -> bool:
        """求解器是否可用。默认 True，子类可覆盖。"""
        return True

    # ── 标定接口 (子类按需覆写) ──

    def calibrate(self, config: ThermalConfig, force: bool = False) -> float:
        """标定求解器参数。默认 no-op（简单模型不需要标定）。"""
        return 0.0

    @property
    def is_calibrated(self) -> bool:
        """求解器是否已就绪。无需标定的求解器始终返回 True。"""
        return True

    @property
    def r_eff(self) -> float | None:
        """有效热阻 [K/W]。简单模型返回 None。"""
        return None
