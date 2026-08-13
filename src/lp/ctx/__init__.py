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
    ctx.constrain("flow", sum(f)-d, "==", 0)   # 约束必须显式写，sense 是字符串

读者指南：
  - 想理解"怎么写约束" → 读本文件
  - 想理解 LinExpr 的算术怎么实现 → 读 _expr.py
  - 想理解底层表示 → 读 _ir.py（通常在 IDE 中跳转到足够）
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lp.ctx._ir import VarSpec, Term, LinearC
from lp.ctx._expr import LinExpr, Var
from lp.ctx._model import Model


# ========================================================================
# 这部分是什么？
#   Ctx 是唯一你需要关心的类——所有约束操作通过它完成。
#   变量声明（vector/scalar/var）、约束注册（constrain）、变量引用（ctx["L"]）。
#   其余 _to_terms 是内部方法，读代码时可以跳过。
# ========================================================================

@dataclass
class Ctx:
    """LP 问题构造上下文——只做两件事：声明变量、收集约束。"""

    _vars: dict[str, VarSpec] = field(default_factory=dict)
    _cons: list[LinearC] = field(default_factory=list)

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
    # 写约束的唯一方式：ctx.constrain(name, lhs, sense, rhs, meaning)。
    #   lhs / rhs 都接受 LinExpr——rhs 是表达式时内部移到左边（rhs=0）。
    #   sense 是字符串 "<=" / ">=" / "=="，非法值当场 ValueError。
    #   meaning：不等式取等号时的物理含义——不等式必须给，缺了 ValueError；
    #            等式不强制。绑定诊断按 name + meaning 读出瓶颈语义。

    _SENSES = {"<=", ">=", "=="}

    def constrain(self, name: str,
                  lhs: LinExpr | list[Term],
                  sense: str,
                  rhs: LinExpr | float = 0.0,
                  meaning: str = "",
                  ) -> None:
        """添加显式约束。name 用于诊断（出现在 binding_constraints 中）。"""
        if sense not in self._SENSES:
            raise ValueError(
                f"sense 必须是 {sorted(self._SENSES)} 之一，收到 '{sense}'")
        if sense in ("<=", ">=") and not meaning:
            raise ValueError(
                f"不等式约束 '{name}' 缺少 meaning——说明取等号时的物理含义")
        if isinstance(rhs, LinExpr):
            lhs = lhs - rhs
            rhs = 0.0
        self._cons.append(LinearC(name, tuple(self._to_terms(lhs)), sense,
                                  float(rhs), meaning))

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

    def __repr__(self) -> str:
        return f"Ctx(vars={len(self._vars)}, constraints={len(self._cons)})"
