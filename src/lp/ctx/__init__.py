"""
Ctx —— LP 问题构造上下文。

存在意义：
  这是框架的"语言层"。所有 Model 用它声明变量、写约束，
  Solver 把它编译为数学规划问题。Ctx 隔离了"约束的数学表达"
  和"用什么求解器"——Model 永远不碰 cvxpy。

用法：
    ctx = Ctx()
    L = ctx.vector("L", 8)          # 声明向量 → Var 句柄
    x = ctx.scalar("x")             # 声明标量 → LinExpr
    (3 * L[0] + L[1]) <= 100        # 数学式（自动注册）
    ctx.constrain("flow", sum(f)-d, Sense.EQ, 0)  # 等式

读者指南：
  - 想理解"怎么写约束" → 读本文件
  - 想理解 LinExpr 的算术怎么实现 → 读 _expr.py
  - 想理解底层表示 → 读 _ir.py（通常在 IDE 中跳转到足够）
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lp.ctx._ir import VarSpec, Term, LinearC, Sense
from lp.ctx._expr import LinExpr, Var
from lp.ctx._model import Model


# ========================================================================
# 这部分是什么？
#   Ctx 是唯一你需要关心的类——所有约束操作通过它完成。
#   变量声明（vector/scalar/var）、约束注册（constrain）、变量引用（ctx["L"]）。
#   其余 _auto_name / _to_terms 是内部方法，读代码时可以跳过。
# ========================================================================

@dataclass
class Ctx:
    """LP 问题构造上下文——只做两件事：声明变量、收集约束。"""

    _vars: dict[str, VarSpec] = field(default_factory=dict)
    _cons: list[LinearC] = field(default_factory=list)
    _auto_cnt: int = 0

    # -- 变量声明 ---------------------------------------------------------
    # 这部分解决：如何声明一个 LP 变量，拿到它的句柄以便后续引用。
    # 三个方法对应三种使用场景：通用(var)、标量(scalar)、向量(vector)。

    def var(self, name: str, shape: int = 1, nonneg: bool = True) -> Var:
        """声明变量，返回 Var 句柄。同名重复报错。"""
        if name in self._vars:
            raise ValueError(f"变量 '{name}' 已存在")
        self._vars[name] = VarSpec(name, shape, nonneg)
        return Var(self, name, shape)

    def scalar(self, name: str, nonneg: bool = True) -> LinExpr:
        """声明标量，直接返回 LinExpr（可立即参与算术）。"""
        return self.var(name, 1, nonneg)[0]

    def vector(self, name: str, n: int, nonneg: bool = True) -> Var:
        """声明 n 维向量，返回 Var：L = ctx.vector("L", 8); L[3] 是 LinExpr。"""
        return self.var(name, n, nonneg)

    def __getitem__(self, name: str) -> Var:
        """ctx["L"] —— 引用已声明变量。典型场景：perf 声明 L 后，phys 引用它。"""
        if name not in self._vars:
            raise KeyError(f"变量 '{name}' 未声明")
        s = self._vars[name]
        return Var(self, name, s.shape)

    # -- 约束 -------------------------------------------------------------
    # 这部分解决：如何添加一条线性约束。
    # 两种方式：(a) 数学式 expr <= rhs（推荐），(b) 显式 constrain()（等式专用）。
    # const ineq 会走到 LinExpr.__le__()，内部调 constrain()——最终都是这里。

    def constrain(self, name: str, expr: LinExpr | list[Term],
                  sense: Sense, rhs: float = 0.0) -> None:
        """添加显式约束。name 用于诊断（出现在 binding_constraints 中）。"""
        s = {Sense.LE: "<=", Sense.GE: ">=", Sense.EQ: "=="}[sense]
        self._cons.append(LinearC(name, tuple(self._to_terms(expr)), s, rhs))

    @staticmethod
    def _to_terms(expr: LinExpr | list[Term]) -> list[Term]:
        """把 LinExpr 转为 Term 列表——Engine 编译时用。"""
        if isinstance(expr, LinExpr):
            return expr._to_terms()
        return list(expr)

    # -- 只读（Engine 用）-------------------------------------------------
    # 这部分解决：Engine 如何获取已编译好的约束列表。
    # Model 不需要关心——只在 build() 阶段写入。

    @property
    def variables(self) -> dict[str, VarSpec]:
        return dict(self._vars)

    @property
    def constraints(self) -> list[LinearC]:
        return list(self._cons)

    # -- 内部 -------------------------------------------------------------

    def _auto_name(self) -> int:
        """数学式 <= 自动注册时生成名称 auto_0, auto_1, ..."""
        n = self._auto_cnt
        self._auto_cnt += 1
        return n

    def __repr__(self) -> str:
        return f"Ctx(vars={len(self._vars)}, constraints={len(self._cons)})"
