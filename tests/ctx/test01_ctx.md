# test01 — LP 问题构造上下文 (src/lp/ctx/)

## 模块定位

这是整个 DSE 框架的"语言层"。所有模型（性能、bump、热、布线）都通过它来声明变量和约束。它隔离了"约束的数学表达"和"用什么求解器"——模型永远不碰 cvxpy。

**写约束的唯一方式**是显式 `ctx.constrain(name, lhs, sense, rhs, meaning="")`，sense 用字符串 `"<="` / `">="` / `"=="`。操作符重载（`expr <= rhs`）已删除——匿名约束（auto_N）让瓶颈诊断失去语义，显式写强迫每条约束带名字。

**lhs 和 rhs 都接受表达式**——`constrain("n", A, "==", B)` 和 `constrain("n", A - B, "==", 0.0)` 等价，内部把 rhs 移到左边。**不等式必须给 meaning**：一个字符串说明取等号时的物理含义（"die 0 温度达到 T_max"），缺了抛 ValueError。binding 诊断时按约束名 + meaning 读出瓶颈语义。

LinExpr 内部是 `{ ("变量名", 索引): 系数 }` 的字典，不存值——它是符号表达式。Solver 编译时才把符号变成 cvxpy 变量。

```python
import sys; sys.path.insert(0, '../src')
from lp.ctx import Ctx
```

---

## 1. 声明标量

`ctx.scalar("x")` 返回一个 LinExpr，内部只有一项：`1.0·x[0]`。这是所有模型写约束的起点。

```python
x = Ctx().scalar("x")
print(x._terms)
assert x._terms == {("x", 0): 1.0}
```

---

## 2. 线性组合

`2·x + 3·y` 的内部表示是 `{x:2, y:3}`。模型在 `__init__` 中预计算系数，`build()` 时拼出这样的表达式，然后 `ctx.constrain(...)` 注册约束。

```python
ctx = Ctx()
expr = 2.0 * ctx.scalar("x") + 3.0 * ctx.scalar("y")
print(expr._terms)
assert expr._terms == {("x", 0): 2.0, ("y", 0): 3.0}
```

---

## 3. 显式不等式 + meaning

约束必须显式写，sense 是字符串。不等式必须带 meaning——取等号的物理含义，绑定诊断时读出瓶颈语义。

```python
ctx = Ctx()
ctx.constrain("bump_d0", 2.0 * ctx.scalar("x"), "<=", 5.0,
              meaning="die d0 的信号+功率 bump 用尽预算")
c = ctx.constraints[0]
print(f"name={c.name}, sense={c.sense}, rhs={c.rhs}")
print(f"meaning={c.meaning}")
assert c.name == "bump_d0" and c.sense == "<=" and c.rhs == 5.0
assert "用尽" in c.meaning
```

## 3b. 不等式缺 meaning 当场报错

不带 meaning 的不等式是诊断盲区——模型写约束时漏了，测试就该拦住。

```python
ctx = Ctx()
try:
    ctx.constrain("unnamed", ctx.scalar("x"), "<=", 1.0)
    assert False, "应抛 ValueError"
except ValueError as e:
    print(f"ValueError: {e}")
```

## 3c. rhs 可以是表达式——两边都是 expr

`constrain("n", A, "==", B)` 等价于 `constrain("n", A - B, "==", 0.0)`。数学上习惯"两边写表达式"，接口层支持。

```python
ctx = Ctx()
A = 2.0 * ctx.scalar("x")
B = 1.0 * ctx.scalar("y")
ctx.constrain("eq_both_sides", A, "==", B, meaning="")
c = ctx.constraints[0]
# 内部: A - B == 0，terms = {x:2, y:-1}
print(f"terms={[(t.var, t.idx, t.coeff) for t in c.terms]}")
assert c.rhs == 0.0
assert {("x", 0): 2.0, ("y", 0): -1.0} == {("x", 0): 2.0, ("y", 0): -1.0}
xs = {t.var: t.coeff for t in c.terms}
assert xs.get("x") == 2.0 and xs.get("y") == -1.0
```

## 4. 显式等式

布线模型的需求约束 `Σx = ℓ` 用 `"=="`。Python 的 `==` 不能重载成约束（哈希语义锁死），等式只能显式写。

```python
ctx = Ctx()
ctx.constrain("flow_conservation",
              ctx.scalar("x") + ctx.scalar("y"), "==", 0.0)
c = ctx.constraints[0]
print(f"sense={c.sense}, rhs={c.rhs}")
assert c.sense == "==" and c.rhs == 0.0
```

## 4b. 非法 sense 必须当场报错

拼错 `"=>"` 在运行时抛 ValueError，错误信息列出合法值——不静默吞掉。

```python
ctx = Ctx()
try:
    ctx.constrain("bad", ctx.scalar("x"), "=>", 1.0)
    assert False, "应抛 ValueError"
except ValueError as e:
    print(f"ValueError: {e}")
    assert ">=" in str(e) or "==" in str(e)
```

## 4c. 操作符已删除——`expr <= rhs` 是 TypeError

LinExpr 不再有 `__le__` / `__ge__`。模型里写操作符会当场 TypeError，编译期（import 时）发现不了但第一次 build 就炸——这是有意的：写约束只有显式一条路。

```python
ctx = Ctx()
try:
    (2.0 * ctx.scalar("x")) <= 5.0
    assert False, "应抛 TypeError"
except TypeError as e:
    print(f"TypeError: 操作符写法已删除")
assert len(ctx.constraints) == 0, "TypeError 前不应注册任何约束"
```

---

## 5. 向量索引

`L = ctx.vector("L", 3)` 声明了三个独立分量。每个 `L[i]` 是独立的 LinExpr，指向同一个变量的不同索引。EnvelopeModel 用 `L[0]..L[n_links-1]` 表示每条链路的包络负载。

```python
L = Ctx().vector("L", 3)
print(f"L[0]._terms = {L[0]._terms}")
print(f"L[1]._terms = {L[1]._terms}")
assert ("L", 0) in L[0]._terms and ("L", 1) not in L[0]._terms
assert ("L", 1) in L[1]._terms and ("L", 0) not in L[1]._terms
```

---

## 6. 数值求值——不建 LP, 直接算

`LinExpr` 同时是符号表达式（可写进 LP 约束）和数值求值器（可单独计算）。给一组变量值，`evaluate()` 做加权求和：

$$\text{value} = \sum_i \text{coeff}_i \times \text{var\_value}_i$$

这和 LP 求解完全解耦——不需要 cvxpy，不需要 solver。query 层可以直接用它扫参数曲线。

```python
# 表达式: 2·L[0] + 3·L[1]
ctx = Ctx()
L = ctx.vector("L", 2)
expr = 2.0 * L[0] + 3.0 * L[1]

# 给定 L = [5.0, 2.0]
result = expr.evaluate({"L": [5.0, 2.0]})
print(f"2×5 + 3×2 = {result}")
assert result == 16.0
```

同样的表达式，既可以 `ctx.constrain(...)` 注册 LP 约束，也可以 `.evaluate()` 拿数值——一份代码，两种用法。
