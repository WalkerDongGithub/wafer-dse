"""拓扑潜能求解器 — Strategy 模式。

流程:
  pattern → _generate_demands → [(src,dst,demand)]
  (route, pattern, N) → _select_strategy → strategy.compute(demands)

策略选择:
             uniform              worst_case
  det/val    _Enumeration         _HungarianWorstCase (N≤64)
             枚举 O(N²)           / _Enumeration (N>64, 回退)
  opt        _LpFlow              _LpFlow
             CVXPY LP             CVXPY LP

N>64 时 worst_case 回退 uniform——精确最坏情况计算代价过高，
用 opt LP 上界作为拓扑潜能参考即可。
"""

from __future__ import annotations

from wafer_dse.architecture_model.solver.interface import (
    Solver,
    SolverResult,
)
from wafer_dse.architecture_model.topology import Topology

from ._config import PotentialConfig
from ._strategy import (
    _LoadStrategy, _Enumeration, _generate_demands,
)
from ._hungarian import _HungarianWorstCase
from ._optimal import _LpFlow
from ._adversarial import _AdversarialLp


# ============================================================================
# Strategy 选择
# ============================================================================


def _select_strategy(
    route: str, pattern: str, n_terminals: int, cfg: PotentialConfig,
) -> _LoadStrategy:
    # 对抗 LP: 最优路由 + 最坏流量, 拓扑绝对上限
    if pattern == "adversarial":
        if n_terminals > cfg.max_terminals_opt:
            return _Enumeration()
        return _AdversarialLp()

    if route == "opt":
        if n_terminals > cfg.max_terminals_opt:
            return _Enumeration()
        return _LpFlow()

    if pattern == "uniform":
        return _Enumeration()

    if pattern == "worst_case":
        if n_terminals <= cfg.max_terminals_hungarian:
            return _HungarianWorstCase()
        # N 太大，Hungarian 不可行——回退枚举 (uniform 作为近似)
        return _Enumeration()

    raise ValueError(f"unsupported pattern: {pattern!r}")


# ============================================================================
# 求解器
# ============================================================================


class _PotentialSolver(Solver):
    """拓扑潜能求解器。

    实现 Solver 接口。内部: pattern → demand → strategy → relative load。
    """

    def __init__(self, config: PotentialConfig | None = None):
        self.config = config or PotentialConfig()

    @property
    def supported_routes(self) -> frozenset[str]:
        return frozenset({"opt"})

    def solve(
        self, topo: Topology, route: str,
        link_capacity_gbps: float,
    ) -> SolverResult:
        if route not in ("det", "val", "opt"):
            raise ValueError(f"unsupported route: {route!r}")

        cfg = self.config
        terminals = topo.terminals()
        route_fn = topo.valiant if route == "val" else topo.det

        # 1. 生成 demand 列表 (adversarial 不需要——LP 自己找最坏流量)
        if cfg.pattern == "adversarial":
            demands = []
        else:
            demands = _generate_demands(cfg.pattern, terminals, cfg)

        # 2. 选择计算策略
        strategy = _select_strategy(route, cfg.pattern, len(terminals), cfg)

        # 3. 计算相对负载
        rel_load = strategy.compute(topo, route_fn, demands, terminals, cfg)
        nonblocking = link_capacity_gbps / rel_load if rel_load > 0 else float("inf")

        return SolverResult(
            worst_load=rel_load,
            worst_link=None,
            nonblocking_gbps_per_port=nonblocking,
            witness=[],
        )
