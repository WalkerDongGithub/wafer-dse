"""暴力枚举全部 derangements（仅 n ≤ 8 校验用）。"""

import itertools

from lp.models.perf.traffic_based.traffic import PermutationRep


def _is_derangement(sigma: tuple[int, ...]) -> bool:
    return all(sigma[i] != i for i in range(len(sigma)))


class AllDerangements:
    """枚举 S_n 中全部无不动点排列（仅 n ≤ 8）。"""

    def select(self, n_terminals: int) -> list[PermutationRep]:
        if n_terminals > 8:
            raise ValueError(
                f"n={n_terminals} 太大（>9!），用 SConjugacyReps 代替"
            )
        reps: list[PermutationRep] = []
        for idx, perm in enumerate(itertools.permutations(range(n_terminals))):
            if _is_derangement(perm):
                reps.append(PermutationRep(f"sigma_{idx}", perm))
        return reps
