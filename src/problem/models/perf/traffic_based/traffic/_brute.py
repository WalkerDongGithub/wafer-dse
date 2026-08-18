"""暴力枚举全部 derangements（仅 n ≤ 8 校验用）。"""

import itertools

from problem.models.perf.traffic_based.traffic import Pattern, Selector, PermutationPattern


def _is_derangement(sigma: tuple[int, ...]) -> bool:
    return all(sigma[i] != i for i in range(len(sigma)))


class DerangementSelector(Selector):
    """暴力枚举 S_n 中全部无不动点排列（仅 n ≤ 8，校验用）。"""

    def select(self, n_terminals: int) -> list[Pattern]:
        if n_terminals > 8:
            raise ValueError(
                f"n={n_terminals} 太大（>9!），用 ConjugacySelector 代替"
            )
        reps: list[Pattern] = []
        for idx, perm in enumerate(itertools.permutations(range(n_terminals))):
            if _is_derangement(perm):
                reps.append(PermutationPattern(f"sigma_{idx}", perm))
        return reps
