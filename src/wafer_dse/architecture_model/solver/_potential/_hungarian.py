"""Hungarian 精确最坏情况 — N ≤ 64。"""

from __future__ import annotations

from ._config import PotentialConfig
from ._strategy import _LoadStrategy


class _HungarianWorstCase(_LoadStrategy):
    """对每条链路做 max-weight perfect matching，取全局最大。"""

    def compute(self, topo, route_fn, demands, terminals, cfg: PotentialConfig) -> float:
        from wafer_dse.architecture_model.solver.algorithm import (
            max_weight_derangement,
        )

        n = len(terminals)
        idx = {t: i for i, t in enumerate(terminals)}

        link_matrices: dict[tuple[int, int], list[list[float]]] = {}
        for src in terminals:
            for dst in terminals:
                if src == dst:
                    continue
                paths = route_fn(src, dst)
                if not paths:
                    continue
                w = 1.0 / len(paths)
                for path in paths:
                    for i in range(len(path) - 1):
                        link = (path[i], path[i + 1])
                        if link not in link_matrices:
                            link_matrices[link] = [
                                [0.0] * n for _ in range(n)
                            ]
                        link_matrices[link][idx[src]][idx[dst]] += w

        worst = 0.0
        for mat in link_matrices.values():
            best, _ = max_weight_derangement(mat)
            if best > worst:
                worst = best

        return cfg.lambda_scale * worst
