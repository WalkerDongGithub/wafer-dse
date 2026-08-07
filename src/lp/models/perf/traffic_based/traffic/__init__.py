"""
流量模式选择器——选择排列代表元集合 R。

不同的选择策略实现同一个 `select(n) → list[PermutationRep]` 接口，
彼此可互换。群论归约、暴力枚举、手工指定都是合法的。

R 是*外生固定输入*——不是 LP 变量。排列由群论归约预先确定。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PermutationRep:
    """一个排列代表元。sigma[i] = 节点 i 发送到的目标节点。"""

    label: str
    sigma: tuple[int, ...]

    @property
    def n(self) -> int:
        return len(self.sigma)

    def as_flow_matrix(self) -> list[list[float]]:
        n = self.n
        D = [[0.0] * n for _ in range(n)]
        for i, j in enumerate(self.sigma):
            if i != j:
                D[i][j] = 1.0
        return D

    def __repr__(self) -> str:
        return f"Perm({self.label})"


from lp.models.perf.traffic_based.traffic._conjugacy import SConjugacyReps  # noqa: E402
from lp.models.perf.traffic_based.traffic._brute import AllDerangements    # noqa: E402
from lp.models.perf.traffic_based.traffic._manual import ManualSelector     # noqa: E402
