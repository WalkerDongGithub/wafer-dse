"""
ObliviousValiantModel —— 静态 oblivious Valiant 路由下的 L 包络（V5 §7.3）。

存在意义：
  对每条链路 e，在 Birkhoff 多面体上最大化 L_e(D)，得到"最严苛性能包络" L*。
  f 固定为均匀分流（每条候选路径分 D_{ij}/K_{ij}），不是决策变量。
  L* 与 B 无关（纯拓扑量），在 __init__ 一次性预解，build() 只注入 L ≥ L*。

怎么用：
  model = ObliviousValiantModel(topo)
  L_star = model.solve_envelope()   # 长度 n_links
  model.build(ctx, B=1.0)           # 把 L ≥ L* 写入 ctx

读者指南：
  - 想理解 oblivious 路由系数怎么算 → 读 _precompute
  - 想理解每条链路的子 LP → 读 _solve_envelope
  - build() 只是注入 L* 下界，没有别的
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from problem.models.perf import PerfModel

if TYPE_CHECKING:
    from problem.ctx import Ctx
    from topology import Topology


class ObliviousValiantModel(PerfModel):
    """静态 oblivious Valiant 路由下的 L 包络——V5 §7.3。

    f 固定为均匀分流（对每条候选路径分 D_{ij}/K_{ij}），
    D 是决策变量（Birkhoff 多面体），对每条链路 e 求 max L_e(D)。

    这是"最严苛性能约束"——网络必须在 oblivious 路由下承受最坏流量模式：
    f 固定为均匀分流、只优化 D（最大化 L_e），故 L* 更悲观。
    """

    def __init__(self, topo: Topology) -> None:
        self._topo = topo
        # precompute oblivious routing coefficients c_{ij}^e
        self._paths, self._coeffs = self._precompute()
        # pre-solve: for each link e, max_D L_e(D) over Birkhoff polytope
        self._L_star: list[float] = self._solve_envelope()

    # ------------------------------------------------------------------
    # 预计算
    # ------------------------------------------------------------------

    def _precompute(self) -> tuple[
        dict[tuple[int, int], list[list[int]]],
        list[np.ndarray],
    ]:
        """预计算所有 OD 对的候选路径 + 每条链路 e 的系数 c_{ij}^e。

        Returns:
            paths: {(i, j): [link_idx_seq, ...]} 每个 OD 对（terminal 索引）的
                候选路径。自环 (i, i) 不参与。
            coeffs: 长度 n_links 的列表，每个是 N×N 系数矩阵。
                coeffs[e][i, j] = (通过 e 的候选路径数) / K_{ij}。
                自环 (i, i) 系数为 0（不贡献流量），但 Birkhoff 约束仍含 D_{ii}。
        """
        topo = self._topo
        terminals = topo.terminals
        N = len(terminals)
        li = topo.link_index

        # 1. enumerate OD pairs (i, j), i ≠ j → valiant candidate paths (link idx seqs)
        paths: dict[tuple[int, int], list[list[int]]] = {}
        for i in range(N):
            for j in range(N):
                if i == j:
                    continue
                src = terminals[i]
                dst = terminals[j]
                raw = topo.valiant(src, dst)
                ppl: list[list[int]] = [
                    [li[(path[k], path[k + 1])] for k in range(len(path) - 1)]
                    for path in raw
                ]
                paths[(i, j)] = ppl

        # 2. for each link e, c_{ij}^e = |{k : e ∈ path_k(i,j)}| / K_{ij}
        #    uniform oblivious split: f_k(i,j) = D_{ij}/K_{ij}
        #    → L_e(D) = Σ_{(i,j)} c_{ij}^e · D_{ij}
        coeffs: list[np.ndarray] = [
            np.zeros((N, N), dtype=float) for _ in range(topo.n_links)
        ]
        for (i, j), ppl in paths.items():
            K = len(ppl)
            if K == 0:
                continue
            for path_links in ppl:
                for e in path_links:
                    coeffs[e][i, j] += 1.0
            # normalize by K → each path carries D_{ij}/K_{ij}
            for e in range(topo.n_links):
                if coeffs[e][i, j] > 0:
                    coeffs[e][i, j] /= K

        return paths, coeffs

    # ------------------------------------------------------------------
    # 包络求解（V5 §7.3 子 LP）
    # ------------------------------------------------------------------

    def _solve_envelope(self) -> list[float]:
        """对每条链路 e 解子 LP：max_D Σ c_{ij}^e D_{ij}，D ∈ Birkhoff。

        Birkhoff 多面体 = {D ∈ R^{N×N} : D ≥ 0, D·1 = 1, D^T·1 = 1}。
        线性目标在顶点取到最优（Birkhoff-von Neumann 定理），即某个置换矩阵 σ*。
        自环 D_{ii} 系数为 0，不贡献流量，但仍受行/列和约束。

        Returns: L* 向量，长度 n_links，L*[e] = max_D L_e(D)。
        """
        import cvxpy as cp

        topo = self._topo
        N = len(topo.terminals)

        L_star: list[float] = []
        for e in range(topo.n_links):
            # fresh D per link — avoid cvxpy variable reuse side effects
            D = cp.Variable((N, N), nonneg=True)
            cons = [cp.sum(D, axis=1) == 1, cp.sum(D, axis=0) == 1]
            c = self._coeffs[e]
            obj = cp.Maximize(cp.sum(cp.multiply(c, D)))
            prob = cp.Problem(obj, cons)
            prob.solve()
            val = float(prob.value) if prob.value is not None else 0.0
            L_star.append(val)
        return L_star

    def solve_envelope(self) -> list[float]:
        """返回预解的 L* 向量（长度 n_links）。"""
        return list(self._L_star)

    # ------------------------------------------------------------------
    # build（三段式：只做 B 缩放 + 写约束）
    # ------------------------------------------------------------------

    def build(self, ctx: Ctx, B: float = 1.0) -> None:
        """把 L ≥ L* 写入 ctx——L* 在 __init__ 预解完毕。

        B 不参与：性能包络与端口带宽无关（V5 §7.2）。
        """
        L = ctx.vector("L", self._topo.n_links)
        for e, lstar in enumerate(self._L_star):
            ctx.constrain(
                f"oblivious_env_e{e}", L[e], ">=", float(lstar),
                meaning=f"链路 {e} 在 oblivious Valiant 下的最坏负载",
            )

    # ------------------------------------------------------------------
    # cache_key
    # ------------------------------------------------------------------

    def cache_key(self) -> tuple:
        # L* fully determines the constraints — encode it in the key
        lstar = tuple(round(x, 9) for x in self._L_star)
        return ("oblivious_valiant",
                self._topo.__class__.__name__,
                self._topo.n_links, lstar)

