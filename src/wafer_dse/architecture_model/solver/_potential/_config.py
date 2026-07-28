"""拓扑潜能求解器配置。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PotentialConfig:
    """拓扑潜能求解器配置。

    target:
        "relative_load" — 相对负载 (max link utilization)
        "power"         — 总动态功耗
    pattern:
        "uniform"     — 均匀随机流量 (精确)
        "worst_case"  — 最坏情况 permutation
    """

    target: str = "relative_load"
    pattern: str = "uniform"
    lambda_scale: float = 1.0
    max_terminals_hungarian: int = 64
    max_terminals_opt: int = 64
    greedy_restarts: int = 20
    greedy_2opt_iter: int = 200
