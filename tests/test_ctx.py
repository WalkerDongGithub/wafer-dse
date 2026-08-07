"""ctx —— 变量声明、表达式算术、约束注册。"""

from lp.ctx import Ctx, Sense, LinExpr


def test_variable_declaration():
    ctx = Ctx()
    L = ctx.vector("L", 4)
    x = ctx.scalar("x")

    assert L.name == "L"
    assert L.shape == 4
    assert len(ctx.variables) == 2


def test_lin_expr_arithmetic():
    ctx = Ctx()
    L = ctx.vector("L", 3)

    # 标量乘
    e = 3.0 * L[0]
    assert len(e._terms) == 1

    # 加法
    e2 = L[0] + L[1]
    assert len(e2._terms) == 2

    # sum
    e3 = sum(L)
    assert len(e3._terms) == 3

    # 减法
    e4 = L[0] - L[1]
    assert len(e4._terms) == 2

    # 多索引
    e5 = L[[0, 2]]
    assert len(e5._terms) == 2


def test_constraint_auto_register():
    ctx = Ctx()
    L = ctx.vector("L", 3)

    # 数学式
    (2.0 * L[0] + L[1]) <= 10.0
    sum(L) >= 0

    assert len(ctx.constraints) == 2
    assert ctx.constraints[0].sense == "<="
    assert ctx.constraints[1].sense == ">="


def test_constraint_explicit():
    ctx = Ctx()
    L = ctx.vector("L", 2)

    ctx.constrain("eq_test", L[0] - L[1], Sense.EQ, 0.0)

    assert ctx.constraints[0].sense == "=="
    assert ctx.constraints[0].name == "eq_test"


def test_variable_reference():
    ctx = Ctx()
    ctx.vector("L", 3)

    # ctx["L"] 引用已存在变量
    L = ctx["L"]
    assert L.shape == 3
    assert L[0]._terms is not None
