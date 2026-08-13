"""
流量需求模式 —— Pattern ABC + 排列生成器。

Pattern 是流量需求矩阵 D_{ij} 的抽象。排列只是其中一种生成策略。
EnvelopeModel 只依赖 Pattern 接口，不关心 D 是怎么来的。

接口: select_representatives(topo, n_terminals) → list[Pattern]

排列生成策略:
  - ConjugacySelector   S_n 共轭类 (当前默认, 保守近似)
  - DerangementSelector 暴力枚举全部 derangement (n ≤ 8)
  - ManualSelector      手工指定排列
  - TODO                Aut(G) 轨道计算 (精确归约)

R 是*外生固定输入*——不是 LP 变量.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from topology import Topology

# 类型别名
Matrix = np.ndarray  # 2D 需求矩阵, D[i][j] = i → j


# ═══════════════════════════════════════════════════════
# Pattern ABC
# ═══════════════════════════════════════════════════════

class Pattern(abc.ABC):
    """流量需求模式 —— 一个需求矩阵 D, D[i][j] = i 发往 j 的流量.

    排列 (PermutationPattern) 是特例: 每行每列恰好一个 1.
    也可以有均匀负载、热点、任意浮点矩阵.
    """

    @property
    @abc.abstractmethod
    def label(self) -> str:
        """人类可读标签, 用于约束命名和诊断."""
        ...

    @property
    def n(self) -> int:
        """终端数."""
        return len(self.demand())

    @abc.abstractmethod
    def demand(self) -> Matrix:
        """需求矩阵 D (n×n), D[i][j] = i 发往 j 的流量."""
        ...


class Selector(abc.ABC):
    """流量模式选择器 —— 给定终端数, 返回 Pattern 列表.

    不同策略实现同一接口, 彼此可互换:
      - SConjugacyReps    S_n 共轭类 (保守近似)
      - AllDerangements   暴力枚举全部 derangement (n ≤ 8)
      - ManualSelector    手工指定排列
      - TODO              Aut(G) 轨道计算 (精确归约)
    """

    @abc.abstractmethod
    def select(self, n_terminals: int) -> list[Pattern]:
        """给定终端数, 返回需求模式列表 R.

        R 是*外生固定输入*——不是 LP 变量.
        """
        ...


# ═══════════════════════════════════════════════════════
# 具体 Pattern 实现
# ═══════════════════════════════════════════════════════

class TrafficMatrixPattern(Pattern):
    """任意需求矩阵 —— 最通用的 Pattern.

    用法:
        TrafficMatrixPattern("uniform_0.5", [[0, 0.5], [0.5, 0]])
    """

    def __init__(self, label: str, D: np.ndarray | list[list[float]]) -> None:
        self._label = label
        self._D = np.array(D, dtype=float)

    @property
    def label(self) -> str:
        return self._label

    @property
    def n(self) -> int:
        return self._D.shape[0]

    def demand(self) -> Matrix:
        return self._D.copy()

    def __repr__(self) -> str:
        return f"TrafficMatrixPattern({self._label})"


# backward compat
TrafficMatrix = TrafficMatrixPattern


class PermutationPattern(Pattern):
    """排列流量模式 —— 每终端发 1 单位到恰好一个目标.

    sigma[i] = i 发往的目标终端索引.
    和 TrafficMatrix 不同: 冻结 (hashable), 带 sigma 访问.
    """

    def __init__(self, label: str, sigma: tuple[int, ...]) -> None:
        self._label = label
        self._sigma = sigma
        self._hash = hash((label, sigma))

    @property
    def label(self) -> str:
        return self._label

    @property
    def sigma(self) -> tuple[int, ...]:
        return self._sigma

    @property
    def n(self) -> int:
        return len(self._sigma)

    def demand(self) -> Matrix:
        n = self.n
        D = np.zeros((n, n), dtype=float)
        for i, j in enumerate(self._sigma):
            if i != j:
                D[i, j] = 1.0
        return D

    # backward compat
    def as_flow_matrix(self) -> Matrix:
        return self.demand()

    def __repr__(self) -> str:
        return f"Perm({self._label})"

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PermutationPattern):
            return NotImplemented
        return (self._label == other._label
                and self._sigma == other._sigma)


# backward compat alias
PermutationRep = PermutationPattern


# ═══════════════════════════════════════════════════════
# 选择器
# ═══════════════════════════════════════════════════════

def select_representatives(
    topo: "Topology | None" = None,
    n_terminals: int = 4,
    derangements_only: bool = True,
    max_reps: int = 30,
    selector: "Selector | None" = None,
) -> list[Pattern]:
    """给定拓扑和终端数, 返回排列代表元集合 R.

    Args:
      topo: 拓扑对象 (当前未使用, 预留给 Aut(G) 轨道计算)
      n_terminals: 终端总数
      derangements_only: 仅 derangement (排除自环)
                       只在 selector 未指定时生效
      max_reps: 最大代表元数 (截断保护)
      selector: 自定义选择器. 未指定时用 SConjugacyReps.

    返回类型是 list[Pattern], 调用方不感知具体 Pattern 子类.
    """
    if selector is None:
        from lp.models.perf.traffic_based.traffic._conjugacy import ConjugacySelector
        selector = ConjugacySelector(derangements_only)

    reps = selector.select(n_terminals)
    if len(reps) > max_reps:
        reps = reps[:max_reps]
    return reps


# 向后兼容别名
from lp.models.perf.traffic_based.traffic._conjugacy import ConjugacySelector  # noqa: E402
from lp.models.perf.traffic_based.traffic._brute import DerangementSelector    # noqa: E402
from lp.models.perf.traffic_based.traffic._manual import ManualSelector         # noqa: E402

SConjugacyReps = ConjugacySelector
AllDerangements = DerangementSelector
