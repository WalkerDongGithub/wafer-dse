"""对抗 LP — 拓扑绝对理论上限。

对每条链路求 max load over 双随机矩阵 (排列的凸组合):
  max sum_{pairs traversing link} D[i][j]
  s.t. D doubly stochastic

等价于 Hungarian 的 LP 形式——但对大 N 可用 LP 求解器替代 Hungarian。
"""

from __future__ import annotations

from ._config import PotentialConfig
from ._strategy import _LoadStrategy, _Enumeration, Demands


class _AdversarialLp(_LoadStrategy):
    """对抗 LP: 对每条链路分别求最大负载 (LP 形式)。

    每链路: max sum D[i][j] for pairs traversing this link
            s.t. D doubly stochastic (行和=列和=1, 非负, 对角线=0)

    Birkhoff-von Neumann: 双随机矩阵的极点 = 排列矩阵
    → LP 最优解在极点上 = 最坏排列在该链路上的负载
    """

    def compute(self, topo, route_fn,
                demands: Demands, terminals: list[int],
                cfg: PotentialConfig) -> float:
        try:
            import cvxpy as cvx
        except ImportError:
            return _Enumeration().compute(topo, route_fn, demands, terminals, cfg)

        n = len(terminals)
        idx = {t: i for i, t in enumerate(terminals)}

        # 预计算每条链路上有哪些 (src,dst) 对经过 (det 路由, 单路径)
        link_pairs: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for src in terminals:
            for dst in terminals:
                if src == dst:
                    continue
                paths = topo.det(src, dst)
                if not paths:
                    continue
                path = paths[0]
                si, di = idx[src], idx[dst]
                for k in range(len(path) - 1):
                    link = (path[k], path[k + 1])
                    link_pairs.setdefault(link, []).append((si, di))

        if not link_pairs:
            return 0.0

        # 通用约束: D 双随机 + 对角线=0
        base_constraints = []
        D_param = cvx.Variable((n, n), nonneg=True)
        for i in range(n):
            base_constraints.append(cvx.sum(D_param[i, :]) == 1)
            base_constraints.append(cvx.sum(D_param[:, i]) == 1)
        for i in range(n):
            base_constraints.append(D_param[i, i] == 0)

        worst = 0.0
        for link, pairs in link_pairs.items():
            if not pairs:
                continue
            # 目标: max sum D[i][j] for pairs traversing this link
            row_idx = [p[0] for p in pairs]
            col_idx = [p[1] for p in pairs]
            objective = cvx.Maximize(cvx.sum(D_param[row_idx, col_idx]))
            prob = cvx.Problem(objective, base_constraints)
            prob.solve(verbose=False, solver=cvx.CLARABEL)

            if prob.status in ("optimal", "optimal_inaccurate"):
                val = float(prob.value)
                if val > worst:
                    worst = val

        return cfg.lambda_scale * worst


class _AdversarialValiantLp(_LoadStrategy):
    """对抗 + 最优路由联合 LP (valiant 候选路径)。

    同时优化 D (对抗流量) 和每条路径的流量分配:
    min t
    s.t. D doubly stochastic
         每条 (i,j) 的 valiant 路径流量和 = D[i][j]
         每条链路总负载 ≤ t

    N 较小时精确 (N ≤ 16)，变量数 O(N³)。
    """

    def compute(self, topo, route_fn,
                demands: Demands, terminals: list[int],
                cfg: PotentialConfig) -> float:
        try:
            import cvxpy as cvx
        except ImportError:
            return _Enumeration().compute(topo, route_fn, demands, terminals, cfg)

        n = len(terminals)
        idx = {t: i for i, t in enumerate(terminals)}

        # 收集所有 (src,dst) 的 valiant 候选路径
        by_pair: dict[tuple[int, int], list[list[int]]] = {}
        for src in terminals:
            for dst in terminals:
                if src == dst:
                    continue
                paths = topo.valiant(src, dst)
                if paths:
                    by_pair[(src, dst)] = paths

        if not by_pair:
            return 0.0

        # D 矩阵 + 路径流量变量
        D = cvx.Variable((n, n), nonneg=True)
        t = cvx.Variable(nonneg=True)
        constraints = []

        # 双随机
        for i in range(n):
            constraints.append(cvx.sum(D[i, :]) == 1)
            constraints.append(cvx.sum(D[:, i]) == 1)
        for i in range(n):
            constraints.append(D[i, i] == 0)

        # 路径流量 + 链路约束
        link_vars: dict[tuple[int, int], list] = {}
        for (src, dst), paths in by_pair.items():
            si, di = idx[src], idx[dst]
            L = cvx.Variable(len(paths), nonneg=True)
            constraints.append(cvx.sum(L) == D[si, di])
            for pi, path in enumerate(paths):
                for k in range(len(path) - 1):
                    link = (path[k], path[k + 1])
                    link_vars.setdefault(link, []).append(L[pi])

        if not link_vars:
            return 0.0

        for vars_list in link_vars.values():
            constraints.append(cvx.sum(cvx.hstack(vars_list)) <= t)

        prob = cvx.Problem(cvx.Minimize(t), constraints)
        prob.solve(verbose=False, solver=cvx.CLARABEL)

        if prob.status in ("optimal", "optimal_inaccurate"):
            return float(prob.value)
        return _Enumeration().compute(topo, route_fn, demands, terminals, cfg)
