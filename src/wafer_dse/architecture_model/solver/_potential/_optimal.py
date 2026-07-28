"""LP 求解器 — 线性规划求最优分流比。"""

from __future__ import annotations

from ._config import PotentialConfig
from ._strategy import _LoadStrategy, _Enumeration, Demands


class _LpFlow(_LoadStrategy):
    """CVXPY LP: 在 valiant 候选路径集上优化分流比，求最小相对负载。"""

    def compute(self, topo, route_fn,
                demands: Demands, terminals: list[int],
                cfg: PotentialConfig) -> float:
        try:
            import cvxpy as cvx
        except ImportError:
            return _Enumeration().compute(topo, route_fn, demands, terminals, cfg)

        # 收集所有 (src,dst) 的候选路径
        by_pair: dict[tuple[int, int], list[list[int]]] = {}
        for src, dst, _ in demands:
            if (src, dst) not in by_pair:
                paths = topo.valiant(src, dst)
                if paths:
                    by_pair[(src, dst)] = paths

        if not by_pair:
            return 0.0

        constraints = []
        link_vars: dict[tuple[int, int], list] = {}

        for src, dst, demand in demands:
            paths = by_pair.get((src, dst))
            if not paths:
                continue
            L = cvx.Variable(len(paths), nonneg=True)
            constraints.append(cvx.sum(L) == demand)
            for pi, path in enumerate(paths):
                for i in range(len(path) - 1):
                    link = (path[i], path[i + 1])
                    link_vars.setdefault(link, []).append(L[pi])

        if not link_vars:
            return 0.0

        t = cvx.Variable(nonneg=True)
        for vars_list in link_vars.values():
            constraints.append(cvx.sum(cvx.hstack(vars_list)) <= t)

        prob = cvx.Problem(cvx.Minimize(t), constraints)
        prob.solve(verbose=False, solver=cvx.CLARABEL)

        if prob.status in ("optimal", "optimal_inaccurate"):
            return float(prob.value)
        return _Enumeration().compute(topo, route_fn, demands, terminals, cfg)
