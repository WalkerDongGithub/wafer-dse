"""手工指定的排列列表（从配置文件读入）。"""

from problem.models.perf.traffic_based.traffic import Pattern, Selector, PermutationPattern


class ManualSelector(Selector):
    """手工指定的排列列表。

    用法:
        ManualSelector([(1, 0, 3, 2), (2, 3, 0, 1)])
    """

    def __init__(self, perms: list[tuple[int, ...]]):
        self._perms: list[Pattern] = [
            PermutationPattern(f"manual_{i}", sigma)
            for i, sigma in enumerate(perms)
        ]

    def select(self, n_terminals: int) -> list[Pattern]:
        for p in self._perms:
            if p.n != n_terminals:
                raise ValueError(
                    f"排列长度 {p.n} ≠ n_terminals {n_terminals}"
                )
        return list(self._perms)
