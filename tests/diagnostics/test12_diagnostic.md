# test12 — 诊断原语 (src/diagnostics.py)

## 模块定位

query 层回答"可行吗 / B\* 是多少"，诊断原语回答第三个问题：**给定 B，系统的真实包络负载 L\* 是什么，每个物理约束还剩多少余量，谁在绑定？**

这是 sensitivity 的计算基础——灵敏度分析的闭式 λ_j = 1/(A_j·L\*) 里，L\* 与"A_j·L\* 是否到 rhs"都要从这里拿。

契约（与 test08 三个坑一一对应）：

1. **解 min ΣL**（`objective=sum(L), maximize=False`），不是无目标可行性——无目标求解的 duals 不可靠。
2. **binding 只在 feasible=True 时有语义**——infeasible 时 duals 是 Farkas 证书，必须返回空。
3. **binding 带模型家族归类**——按约束名前缀 `bump_/therm_/c4/route_` 归到家族，不再光秃秃地给 duals key 列表。
4. **margin ≈ 0 优先**——物理约束 rhs−lhs 接近 0 就算绑定，即使 dual=0（退化点）；duals 非零只作辅助。

返回值 `DiagnosticResult`：
- `L_star`：包络负载 `{link_idx: load}`
- `margins`：物理约束余量 `{constraint_name: rhs − lhs}`（仅物理约束）
- `binding`：`BindingInfo(name, family, dual, meaning)` 按 |dual| 降序

下面用一个手算友好的 toy 模型验证。模型里 L 是 2 维，约束系数全部写死：

```python
import sys; sys.path.insert(0, '../src')
from problem import Model
from diagnostics import solve_diagnostic, constraint_family


class ToyDiagModel(Model):
    """2 链路 toy：1 条需求下界 + 3 条物理上界，系数可手算。"""

    def build(self, ctx, B):
        L = ctx.vector("L", 2)
        # 需求下界：链路 0 至少要 2 的负载
        ctx.constrain("dem0", L[0], ">=", 2.0, meaning="链路0 需求下界")
        # 物理上界
        ctx.constrain("bump_d0", L[0] + L[1], "<=", 6.0, meaning="die0 bump 用尽")
        ctx.constrain("therm_d0", L[1], "<=", 3.0, meaning="die0 温度 T_max")
        ctx.constrain("c4", L[0] + L[1], "<=", 100.0, meaning="C4 用尽")

    def cache_key(self):
        return ("toy_diag",)
```

---

## 1. toy 场景：手算 L\* → margin → binding

**手算**。目标 `min ΣL = L0 + L1`，约束：

- `dem0`：L0 ≥ 2
- `bump_d0`：L0 + L1 ≤ 6
- `therm_d0`：L1 ≤ 3
- `c4`：L0 + L1 ≤ 100
- 非负：L0, L1 ≥ 0

ΣL 要最小，L0 被 `dem0` 顶到 2（最小），L1 没有下界 → 压到 0。所以 **L\* = (2, 0)**，ΣL = 2。

三条物理约束的 lhs 与 margin：

- `bump_d0`：lhs = 2 + 0 = 2，margin = 6 − 2 = **4**
- `therm_d0`：lhs = 0，margin = 3 − 0 = **3**
- `c4`：lhs = 2，margin = 100 − 2 = **98**

绑定：只有 `dem0` 取等（L0=2 正是它的下界）。每松 1 单位 `dem0` 的 rhs，ΣL 减 1 → dual ≈ 1。三条物理约束全 slack → dual = 0 → 不在 binding 里。

```python
diag = solve_diagnostic([ToyDiagModel()], 1.0)

assert diag.feasible, "这个 toy 场景必须可行"
assert abs(diag.L_star[0] - 2.0) < 1e-6 and abs(diag.L_star[1] - 0.0) < 1e-6, \
    f"L* 应为 (2, 0)，实际 {diag.L_star}"

assert abs(diag.margins["bump_d0"] - 4.0) < 1e-6, f"bump margin 应为 4，实际 {diag.margins['bump_d0']}"
assert abs(diag.margins["therm_d0"] - 3.0) < 1e-6, f"therm margin 应为 3，实际 {diag.margins['therm_d0']}"
assert abs(diag.margins["c4"] - 98.0) < 1e-6, f"c4 margin 应为 98，实际 {diag.margins['c4']}"
print(f"L* = {diag.L_star}")
print(f"margins = {diag.margins}")
```

margins 只含物理约束（`dem0` 是 perf 侧需求下界，不进 margins）：

```python
assert set(diag.margins) == {"bump_d0", "therm_d0", "c4"}, \
    f"margins 应只含物理约束，实际 {set(diag.margins)}"
```

binding 只有 `dem0`，且带家族 + 含义：

```python
names = [b.name for b in diag.binding]
print(f"binding = {[(b.name, b.family, round(b.dual, 3), b.meaning) for b in diag.binding]}")
assert names == ["dem0"], f"唯一绑定约束应为 dem0，实际 {names}"
b0 = diag.binding[0]
assert abs(b0.dual - 1.0) < 1e-6, f"dem0 的 dual 应为 1，实际 {b0.dual}"
assert b0.meaning == "链路0 需求下界"
assert "bump_d0" not in names and "therm_d0" not in names and "c4" not in names, \
    "物理约束全 slack，不应出现在 binding"
```

---

## 2. infeasible 时：binding 为空（Farkas 证书不是绑定约束）

**手算**。需求下界 L0 ≥ 5 与物理上界 L0 + L1 ≤ 4 冲突（L0 ≥ 5 ⟹ L0+L1 ≥ 5 > 4），不可行。

不可行时求解器返回的 duals 是 Farkas 证书（告诉你是哪组约束互相矛盾），**不代表这些约束在最优解同时绑定**。所以契约：`feasible=False` 时 `binding` 必须为空，`margins`/`L_star` 也没有意义（空）。

```python
class ToyInfeasModel(Model):
    """冲突 toy：需求下界 5 > 物理上界 4，必 infeasible。"""

    def build(self, ctx, B):
        L = ctx.vector("L", 2)
        ctx.constrain("dem0", L[0], ">=", 5.0, meaning="链路0 需求下界")
        ctx.constrain("bump_d0", L[0] + L[1], "<=", 4.0, meaning="die0 bump 用尽")

    def cache_key(self):
        return ("toy_infeas",)


diag_infeas = solve_diagnostic([ToyInfeasModel()], 1.0)

assert not diag_infeas.feasible, "L0≥5 且 L0+L1≤4 必 infeasible"
assert diag_infeas.binding == (), "infeasible 时 binding 必须为空（duals 是 Farkas 证书）"
assert diag_infeas.margins == {}, "infeasible 时无变量解，margins 无意义应为空"
assert diag_infeas.L_star == {}, "infeasible 时 L* 为空"
print("infeasible → binding 为空, margins 为空, L* 为空 ✓")
```

---

## 3. 前缀归类：bump / therm / c4 / route

归类是 binding 的"哪个模型家族"来源。关键边界：`route_c4pad_*` 属于布线家族（`route`），不能被 `c4` 前缀误捕获——所以 `route` 要在 `c4` 之前判断。

```python
cases = {
    "bump_d0": "bump",
    "therm_d1": "therm",
    "c4": "c4",
    "route_edge_e0": "route",
    "route_vert_v0": "route",
    "route_c4pad_p0": "route",   # 布线家族的 C4 pad 约束，不是 C4 家族
    "route_dem_l0": "route",
    "r0_env_e0": "other",        # perf 包络约束，不在四物理家族
    "dem0": "other",
}
for name, want in cases.items():
    got = constraint_family(name)
    print(f"  {name:>18} -> {got}")
    assert got == want, f"{name} 应归 {want}，实际 {got}"
```

---

## 4. 退化点：物理约束取等但 dual=0 也判 binding

**手算**。退化点的典型形态：物理上界与需求下界在同一点碰头，上界没有挡在 min ΣL 的方向上，所以 dual=0，但 margin 是 0。

模型：

- `dem0`：L0 ≥ 2（需求下界）
- `bump_d0`：L0 ≤ 2（die0 bump 上界）

目标 `min ΣL = L0 + L1`，L1 无下界 → **L\* = (2, 0)**。`bump_d0` 的 lhs=2、margin=0——取等；但目标方向是"把 L0 往小压"，`bump_d0` 这个上界并没有挡路，所以它的 dual=0（退化）。

默认求解器（CLARABEL 内点法）在退化点上不一定报 dual=0。为了隔离判定逻辑本身，这里用 monkeypatch 把 `CvxSolver.solve` 换成"返回 L\*=(2,0)、duals 为空"的确定性结果，模拟 dual=0 的退化点：

```python
from problem import CvxSolver, Result

class ToyMarginModel(Model):
    """退化 toy：物理上界与需求下界同值，取等但 dual=0。"""

    def build(self, ctx, B):
        L = ctx.vector("L", 2)
        ctx.constrain("dem0", L[0], ">=", 2.0, meaning="链路0 需求下界")
        ctx.constrain("bump_d0", L[0], "<=", 2.0, meaning="die0 bump 用尽")

    def cache_key(self):
        return ("toy_margin",)


real_solve = CvxSolver.solve

def fake_solve(self, ctx, objective=None, maximize=False):
    """确定性退化解：bump_d0 取等但 duals 不报它。"""
    return Result(status="optimal", solve_time_s=0.0, objective=2.0,
                  variables={"L": [2.0, 0.0]}, duals={})

CvxSolver.solve = fake_solve
try:
    diag_margin = solve_diagnostic([ToyMarginModel()], 1.0)
finally:
    CvxSolver.solve = real_solve

assert diag_margin.feasible, "退化 toy 场景必须可行"
assert abs(diag_margin.margins["bump_d0"]) < 1e-6, \
    f"bump_d0 取等，margin 应为 0，实际 {diag_margin.margins['bump_d0']}"
names_margin = [b.name for b in diag_margin.binding]
assert "bump_d0" in names_margin, \
    f"margin≈0 的物理约束即使 dual=0 也应 binding，实际 {names_margin}"
bump_info = [b for b in diag_margin.binding if b.name == "bump_d0"][0]
assert bump_info.dual == 0.0, f"退化点的 dual 应为 0，实际 {bump_info.dual}"
print(f"margin≈0 + dual=0 → binding = "
      f"{[(b.name, b.family, b.dual) for b in diag_margin.binding]}")
```

---

## 5. 含标量变量（x 类）的模型：solve_diagnostic 不崩溃

回归锚定：WiringModel 声明标量变量 x_l{li}_q{qi}（shape=1，非向量 L）。
CvxSolver 提取标量变量 value 曾返回 float（非 list），`_lhs_value` 按
`var_values[name][idx]` 访问 → 'float' object is not subscriptable。
修复：标量统一包成 `[float(v)]`（git 修复）。

真实场景：perf+bump+therm+wiring（含 WiringModel），solve_diagnostic
必须正常返回（margins 含 route_* 物理族）。

```python
from problem.builder import build_scenario
from physical.params import UCIE_32G
from topology import MeshTopology
from layout import place

topo = MeshTopology(2)
P = UCIE_32G
layout = place(topo, P)
m_w, _ = build_scenario(topo, "perf+bump+therm+wiring", P, layout)
diag_w = solve_diagnostic(m_w, 100.0)
print(f"wiring 模型: feasible={diag_w.feasible}, margins={len(diag_w.margins)}, "
      f"binding={len(diag_w.binding)}")
assert diag_w.feasible, "小 B 应可行"
assert len(diag_w.margins) > 0, "应有物理约束 margin"
assert any(n.startswith("route_") for n in diag_w.margins), \
    f"应含 route_* 族 margin，实际 {list(diag_w.margins)[:5]}"
print("✓ 含标量变量（x 类）模型 solve_diagnostic 不崩溃")
```

---

## 结论

诊断原语契约全部通过：

- `solve_diagnostic` 固定解 min ΣL，拿到真实包络 L\*（非 feasibility 的任意可行解）。
- `margins` 只报物理约束的 rhs − lhs（手算 4/3/98 全部命中）。
- `binding` 在 feasible 时：物理约束 margin≈0 优先（即使 dual=0），duals 非零辅助；infeasible 时强制为空，杜绝把 Farkas 证书误当绑定。
- `constraint_family` 按前缀归到 bump/therm/c4/route 四家族，`route_c4pad_*` 归布线不归 C4。
- 含标量变量（x 类）模型（WiringModel 场景）solve_diagnostic 正常（CvxSolver 标量提取统一 list[float]）。
