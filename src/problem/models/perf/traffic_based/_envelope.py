"""
EnvelopeModel —— 多需求模式包络性能约束。

对 R 个需求模式分别做 Valiant 分流，L 取各模式的最坏情况包络。

数学（MATH_MODEL_COMPLETE_V2 §5.2）：对每个 r ∈ R，

  (1)  Σ_k  f^{k,(r)}_{ij} = D^{(r)}_{ij}     ∀ OD 对 (i,j)
  (2)  L^{(r)}_e = Σ_{(i,j,k): e∈path} f^{k,(r)}_{ij}   ∀ 链路 e
  (3)  L_e ≥ L^{(r)}_e                         ∀ 链路 e

求解时用 min ΣL 把 L 压至真实包络下界。

paths_for_pair 和 link_incidence 不是拓扑的预计算属性——
它们是 (topology, pattern) 的派生产物，在 build() 内按非零 demand 的 OD 对动态计算。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from problem.models.perf import PerfModel

if TYPE_CHECKING:
    from problem.ctx import Ctx, LinExpr
    from problem.models.perf.traffic_based.traffic import Pattern
    from topology import Topology


class EnvelopeModel(PerfModel):
    """L_e = max_{r∈R} L^{(r)}_e —— 链路包络模型。

    topo: 拓扑对象，提供 terminals / links / link_index / valiant。
    patterns: 需求模式列表 R = [D^{(0)}, D^{(1)}, ...]。
    """

    def __init__(self, topo: Topology, patterns: list[Pattern]) -> None:
        if len(patterns) == 0:
            raise ValueError("需求模式列表为空")
        self._topo = topo
        self._patterns = patterns

    # ------------------------------------------------------------------
    # build
    # ------------------------------------------------------------------

    def build(self, ctx: Ctx, B: float = 1.0) -> None:
        """往 ctx 写入：分流变量 f + 包络变量 L + 三条约束。

        对每个 pattern，只处理 demand > 0 的 OD 对，
        paths 和 link_incidence 在使用点动态计算。
        """
        topo = self._topo
        terminals = topo.terminals
        li = topo.link_index

        # 包络变量 L_e —— 所有模式共享
        L = ctx.vector("L", topo.n_links)

        # ── 逐模式处理 ──────────────────────────────────────
        for r, pattern in enumerate(self._patterns):

            D = pattern.demand()
            
            prefix = f"r{r}"

            # ── 1. 对 D 稀疏化 ──
            active: list[tuple[int, int, float]] = []
            for i, src in enumerate(terminals):
                for j, dst in enumerate(terminals):
                    if i == j:
                        continue
                    d = float(D[i, j])
                    if d > 0:
                        active.append((src, dst, d))

            # ── 2. 为每个活跃 pair 计算 valiant 候选路径（link index 序列）──
            pair_paths: list[list[list[int]]] = []
            for src, dst, _ in active:
                paths = topo.valiant(src, dst)
                ppl: list[list[int]] = []
                for path in paths:
                    ppl.append(
                        [li[(path[k], path[k + 1])] for k in range(len(path) - 1)]
                    )
                pair_paths.append(ppl)

            # ── 3. 构建 link incidence（反查表）──
            inc: list[list[tuple[int, int]]] = [[] for _ in range(topo.n_links)]
            for pi, ppl in enumerate(pair_paths):
                for pj, link_idxs in enumerate(ppl):
                    for e in link_idxs:
                        inc[e].append((pi, pj))

            # ── 4. 流量守恒：Σ_k f^{k}_{p} = D[src,dst] ──
            f: dict[tuple[int, int], LinExpr] = {}
            for pi, (src, dst, d) in enumerate(active):
                K = len(pair_paths[pi])
                for k in range(K):
                    f[(pi, k)] = ctx.scalar(f"f_{prefix}_p{pi}_k{k}")

                ctx.constrain(
                    f"{prefix}_flow_p{pi}",
                    sum(f[(pi, k)] for k in range(K)), "==", d,
                )

            # ── 5. L^{(r)}_e = Σ_{(p,k): e∈path} f^{k}_{p} ──
            Lr = ctx.vector(f"Lr_{prefix}", topo.n_links)
            for e in range(topo.n_links):
                load = sum(f[(pi, pj)] for pi, pj in inc[e])
                ctx.constrain(f"{prefix}_load_e{e}", Lr[e], "==", load)

            # ── 6. L_e ≥ L^{(r)}_e ──
            for e in range(topo.n_links):
                ctx.constrain(
                    f"{prefix}_env_e{e}", L[e], ">=", Lr[e],
                    meaning=f"链路 {e} 在该模式下达最坏负载",
                )

    # ------------------------------------------------------------------
    # cache_key
    # ------------------------------------------------------------------

    def cache_key(self) -> tuple:
        return ("perf",
                tuple(p.label for p in self._patterns),
                self._topo.n_links)


class SelectedEnvelopeModel(EnvelopeModel):
    """选择器驱动的包络模型 —— builder 的入口.

    给拓扑 + selector 就生成模型，builder 不需要自己调 select_representatives。
    默认 selector 是 ConjugacySelector（共轭类代表元，当前唯一生产实现）；
    换 selector 只影响"哪些模式进包络"，模型结构不变。
    """

    def __init__(self, topo: Topology, selector: Selector | None = None):
        from problem.models.perf.traffic_based.traffic import ConjugacySelector
        sel = selector if selector is not None else ConjugacySelector()
        super().__init__(topo, sel.select(topo.n_terminals))
