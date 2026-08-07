"""S_n 共轭类代表元——对 K_n 精确，对对称 Dragonfly 近似。

每个 S_n 共轭类 = 一个 cycle type（整数分拆 λ ⊢ n）。
p(10)=42, p(16)=231——n ≤ 16 时可接受。
"""

from lp.models.perf.traffic_based.traffic import PermutationRep


def _partitions(n: int) -> list[tuple[int, ...]]:
    """生成 n 的所有整数分拆（降序）。"""
    result: list[tuple[int, ...]] = []

    def _recurse(remaining: int, max_part: int, current: list[int]) -> None:
        if remaining == 0:
            result.append(tuple(current))
            return
        for k in range(min(max_part, remaining), 0, -1):
            current.append(k)
            _recurse(remaining - k, k, current)
            current.pop()

    _recurse(n, n, [])
    return result


def _canonical_permutation(cycle_type: tuple[int, ...]) -> tuple[int, ...]:
    """给定 cycle type λ，构造该共轭类的标准代表元。

    例: λ=(3,2), n=5 → (1,2,0, 4,3)。
        前 3 个 3-cycle (0→1→2→0)，后 2 个 2-cycle (3→4→3)。
    """
    n = sum(cycle_type)
    sigma = list(range(n))
    offset = 0
    for length in cycle_type:
        for k in range(length):
            sigma[offset + k] = offset + (k + 1) % length
        offset += length
    return tuple(sigma)


def _is_derangement(sigma: tuple[int, ...]) -> bool:
    return all(sigma[i] != i for i in range(len(sigma)))


class SConjugacyReps:
    """S_n 共轭类代表元。

    当 Aut(G) = S_n 时精确；当 Aut(G) < S_n 时是保守近似（代表元数 ≥ 真实轨道数）。
    待 dse/orbit.py 实现真正的 Aut(G) 轨道计算后替换。
    """

    def __init__(self, derangements_only: bool = True):
        self._derangements = derangements_only

    def select(self, n_terminals: int) -> list[PermutationRep]:
        reps: list[PermutationRep] = []
        for lam in _partitions(n_terminals):
            sigma = _canonical_permutation(lam)
            if self._derangements and not _is_derangement(sigma):
                continue
            label = "λ=" + ",".join(map(str, lam))
            reps.append(PermutationRep(label, sigma))
        return reps
