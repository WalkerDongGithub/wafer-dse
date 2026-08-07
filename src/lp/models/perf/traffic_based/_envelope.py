"""
EnvelopeModel —— 多排列包络性能约束。

问题：R 个排列代表元打过来，每条链路能不能扛住最大负载？
答案：对每个排列分别分流，L 取所有模式的包络。

逻辑（MATH_MODEL_COMPLETE_V2 §1, §5.2）：
  1. 对每个排列 r ∈ R，D^(r) 是固定的 0-1 矩阵
  2. 分流变量 f^(r) 在 Valiant 候选路径间分配流量
  3. L^(r)_e = 经过链路 e 的所有分流之和
  4. 包络 L_e ≥ L^(r)_e  ∀r —— 每条边按最坏模式配置
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lp.models.perf import PerformanceModel

if TYPE_CHECKING:
    from lp.ctx import Ctx, LinExpr
    from lp.models.perf.traffic_based.traffic import PermutationRep
    from lp.models.topo import TopoStructure


class EnvelopeModel(PerformanceModel):
    """多排列包络——L_e = max_r L^(r)_e。"""

    def __init__(self, cs: TopoStructure, reps: list[PermutationRep]):
        if len(reps) == 0:
            raise ValueError("排列列表为空")
        if cs.n_terminals != reps[0].n:
            raise ValueError(f"终端数 {cs.n_terminals} ≠ 排列维数 {reps[0].n}")
        self._cs = cs
        self._reps = reps

    # ==================================================================
    # build: 往 ctx 加 L + 分流变量 + 包络约束
    # ==================================================================

    def build(self, ctx: Ctx, B: float) -> None:
        from lp.ctx import Sense as S
        cs = self._cs
        node_to_idx = {n: i for i, n in enumerate(cs.terminals)}
        L = ctx.vector("L", cs.n_links)

        for rep_idx, rep in enumerate(self._reps):
            D = rep.as_flow_matrix()
            pre = f"rep{rep_idx}"
            f_map: dict[tuple[int, int], LinExpr] = {}

            # --- 分流变量 + 流量守恒 ---
            for pi in range(cs.n_pairs):
                src, dst = cs.pairs[pi]
                demand = float(D[node_to_idx[src]][node_to_idx[dst]])
                n_paths = len(cs.paths_for_pair[pi])
                if n_paths == 0:
                    if demand > 0:
                        L[0] <= -1.0           # 无路径 → 人工不可行
                    continue

                f_pi = [ctx.scalar(f"f_{pre}_p{pi}_k{ki}")
                        for ki in range(n_paths)]
                for ki, fe in enumerate(f_pi):
                    f_map[(pi, ki)] = fe
                ctx.constrain(f"{pre}_flow_p{pi}", sum(f_pi), S.EQ, demand)

            # --- 链路负载 L^(r)_e = Σ 经过 e 的分流 ---
            Lr = ctx.vector(f"Lr_{pre}", cs.n_links)
            for li in range(cs.n_links):
                incident = sum(f_map[(pi, ki)]
                               for pi, ki in cs.link_incidence[li])
                ctx.constrain(f"{pre}_load_l{li}",
                              Lr[li] - incident, S.EQ, 0.0)

            # --- 包络 L_e ≥ L^(r)_e ---
            for li in range(cs.n_links):
                (L[li] - Lr[li]) >= 0.0

    def cache_key(self) -> tuple:
        return ("perf", tuple(r.label for r in self._reps), self._cs.n_links)
