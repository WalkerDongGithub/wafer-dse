"""
LinExpr + Var —— 线性表达式，支持算术运算和自动约束注册。

存在意义：
  Model 不拼 Term——太繁琐。LinExpr 让写约束像写数学：
    (c * L[links]) <= rhs   而不是   ctx.le("name", [Term("L",0,c), ...], rhs)
  Var 是已声明变量的句柄——Var[i] 创建一个指向该变量第 i 分量的 LinExpr。

用法（通常在 Model.build 中）：
  L = ctx.vector("L", 8)
  3.0 * L[0]           → 3.0·L[0] 的 LinExpr
  L[0] + L[1]          → L[0] + L[1] 的 LinExpr
  sum(L)               → ΣL 的 LinExpr（用于 sum() 内置函数）
  (c * L[links]) <= 100  → 自动注册约束

读者指南：
  - 想理解"怎么写约束" → 读本文件
  - 想理解 __add__/__mul__ 的实现细节 → 不需要，它们就是对内部 dict 做 key 合并/缩放
  - 想调试自动注册 → 看 __le__/__ge__（它们最终调 ctx.constrain）
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from lp.ctx._ir import Term

if TYPE_CHECKING:
    from lp.ctx import Ctx

_Key = tuple[str, int]  # (变量名, 索引)


# ========================================================================
# 这部分是什么？
#   LinExpr 是线性表达式的不可变表示：{ (var_name, idx): coefficient }。
#   支持 +, -, *, /, sum(), [] 索引，以及 <=, >= 自动注册。
#   所有算术返回新 LinExpr——不修改原对象。
# ========================================================================

class LinExpr:
    """Σ coeff · var[idx] —— 不可变线性表达式。"""

    __slots__ = ("_ctx", "_terms")

    def __init__(self, ctx: Ctx | None = None,
                 terms: dict[_Key, float] | None = None):
        self._ctx = ctx          # 关联的 Ctx（用于 <= 自动注册）
        self._terms: dict[_Key, float] = dict(terms) if terms else {}

    # -- 算术 ------------------------------------------------------------
    # 这部分解决：多个 LinExpr 如何组合。实现是对内部 _terms dict 合并/缩放。
    # 原理简单——读代码时扫一眼即可。

    def __add__(self, other: LinExpr | int | float) -> LinExpr:
        if isinstance(other, (int, float)):
            if other == 0:
                return self                # sum([]) 回退
            raise TypeError("不能加常数，常数放 rhs")
        r = LinExpr(self._ctx, self._terms)
        for k, v in other._terms.items():
            r._terms[k] = r._terms.get(k, 0.0) + v
        return r._prune()

    def __radd__(self, other: int | float) -> LinExpr:
        return self.__add__(other)

    def __sub__(self, other: LinExpr) -> LinExpr:
        return self + (-other)

    def __mul__(self, k: float) -> LinExpr:
        if k == 0.0:
            return LinExpr(self._ctx)
        r = LinExpr(self._ctx)
        for key, v in self._terms.items():
            r._terms[key] = v * k
        return r

    def __rmul__(self, k: float) -> LinExpr:
        return self.__mul__(k)

    def __neg__(self) -> LinExpr:
        return self.__mul__(-1.0)

    def __truediv__(self, k: float) -> LinExpr:
        return self.__mul__(1.0 / k)

    # -- 约束注册 ---------------------------------------------------------
    # 这部分解决：expr <= rhs 如何变成 ctx 中的一条约束。
    # LinExpr 通过 _ctx 透视回 Ctx.constrain()——这是"自动注册"的核心。

    def __le__(self, rhs: float) -> None:
        """expr <= rhs → 自动注册 ≤ 约束。"""
        if self._ctx is None:
            raise TypeError("LinExpr 无 ctx——用 ctx.constrain(name, expr, sense, rhs)")
        from lp.ctx._ir import Sense
        self._ctx.constrain(
            f"auto_{self._ctx._auto_name()}", self, Sense.LE, rhs)

    def __ge__(self, rhs: float) -> None:
        """expr >= rhs → 自动注册 ≥ 约束。"""
        if self._ctx is None:
            raise TypeError("LinExpr 无 ctx——用 ctx.constrain(name, expr, sense, rhs)")
        from lp.ctx._ir import Sense
        self._ctx.constrain(
            f"auto_{self._ctx._auto_name()}", self, Sense.GE, rhs)

    # -- 索引 / 迭代 ------------------------------------------------------
    # L[3] → 该分量的 LinExpr。L[[0,1,2]] → 多分量的 LinExpr。

    def __getitem__(self, idx: int | list[int]) -> LinExpr:
        if isinstance(idx, int):
            r = LinExpr(self._ctx)
            for (n, i), c in self._terms.items():
                if i == idx:
                    r._terms[(n, i)] = c
            return r
        r = LinExpr(self._ctx)
        for i in idx:
            for (n, j), c in self._terms.items():
                if j == i:
                    r._terms[(n, j)] = c
        return r

    def __iter__(self) -> Iterator[LinExpr]:
        """for e in L: 逐个分量迭代——支持 sum(L)。"""
        by_idx: dict[int, list[tuple[str, float]]] = {}
        for (n, i), c in self._terms.items():
            by_idx.setdefault(i, []).append((n, c))
        for i in sorted(by_idx):
            e = LinExpr(self._ctx)
            for n, c in by_idx[i]:
                e._terms[(n, i)] = c
            yield e

    # -- 内部（读代码时可跳过）----------------------------------------------

    def _prune(self) -> LinExpr:
        self._terms = {k: v for k, v in self._terms.items() if abs(v) > 1e-15}
        return self

    def _to_terms(self) -> list[Term]:
        return [Term(k[0], k[1], v) for k, v in self._terms.items()]

    def __repr__(self) -> str:
        if not self._terms:
            return "0"
        return " ".join(str(Term(k[0], k[1], v))
                        for k, v in sorted(self._terms.items()))


# ========================================================================
# 这部分是什么？
#   Var 是 ctx.vector() 返回的句柄。Var[i] → 指向该分量的 LinExpr。
#   它本身不存数据——只存 (ctx, var_name, shape) 三个引用。
#   读代码时可以跳过——行为很简单。
# ========================================================================

class Var:
    """已声明变量的引用句柄。Var[i] → 1.0·变量[i] 的 LinExpr。"""

    __slots__ = ("_ctx", "_name", "_shape")

    def __init__(self, ctx: Ctx, name: str, shape: int):
        self._ctx = ctx
        self._name = name
        self._shape = shape

    @property
    def name(self) -> str:
        return self._name

    @property
    def shape(self) -> int:
        return self._shape

    def __getitem__(self, idx: int | list[int] | slice) -> LinExpr:
        if isinstance(idx, slice):
            idx = list(range(idx.start or 0, idx.stop or self._shape, idx.step or 1))
        if isinstance(idx, int):
            return LinExpr(self._ctx, {(self._name, idx): 1.0})
        return LinExpr(self._ctx, {(self._name, i): 1.0 for i in idx})

    def __iter__(self) -> Iterator[LinExpr]:
        for i in range(self._shape):
            yield self[i]
