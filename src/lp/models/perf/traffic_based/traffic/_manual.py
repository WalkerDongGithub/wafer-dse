"""手工指定的排列列表（从配置文件读入）。"""

from lp.models.perf.traffic_based.traffic import PermutationRep


class ManualSelector:
    """手工指定的排列列表。"""

    def __init__(self, perms: list[tuple[int, ...]]):
        self._perms = [
            PermutationRep(f"manual_{i}", sigma)
            for i, sigma in enumerate(perms)
        ]

    def select(self, n_terminals: int) -> list[PermutationRep]:
        for p in self._perms:
            if p.n != n_terminals:
                raise ValueError(
                    f"排列长度 {p.n} ≠ n_terminals {n_terminals}"
                )
        return list(self._perms)
