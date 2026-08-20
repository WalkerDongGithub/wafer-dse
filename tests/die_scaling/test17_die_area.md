# test17 — die 面积上界接入 build_scenario (V5 §2(2f))

## 模块定位

V5 v5.21（作者推翻 G4）把 die 面积上界 (2f) 升为一级约束：

$$
A_{\text{die}}(B) = d(B)^2 \le A_{\max},
\qquad d(B) = d_0 + \alpha_d B
$$

- $A_{\max}$ 随布局而定，粗上界 ≈ interposer 面积 ÷ 芯粒数；
- $\alpha_d > 0$ 时面积约束直接给出 $B$ 的上界：$B \le (\sqrt{A_{\max}} - d_0)/\alpha_d$；
- 默认 $\alpha_d = 0$ 时退化为静态判定：$d_0^2 \le A_{\max}$（恒可行/恒不可行，见
  model-ruling §七：$d_0^2 > A_{\max}$ 为"全 B 不可行"的静态构型淘汰）。

本测试验证 `build_scenario` 的 `+area` 档位把面积约束接入模型列表，且
约束 rhs 随 B 正确缩放（常数约束：$0 \le A_{\max} - d(B)^2$，忠实 V5 原式）。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from problem.builder import build_scenario
from problem import Ctx, CvxSolver
from problem.models.phys.area import DieAreaModel
from physical.params import TOY
from topology import MeshTopology
from layout import place
```

---

## 1. DieAreaModel 手算：rhs = A_max − d(B)²

toy 参数：die 10×10mm（d0=10, α_d=0 默认），interposer 100×100mm，
Mesh(2) 4 芯粒 → A_max = 10000/4 = 2500 mm²。

α_d=0 时 d(B)=10 恒等 → A_die = 100，rhs = 2500 − 100 = 2400 恒正
（恒可行，面积约束恒松）。

```python
model = DieAreaModel(d0_mm=10.0, alpha_d=0.0, a_max_mm2=2500.0)
ctx = Ctx(); ctx.vector("L", 1)
model.build(ctx, B=100.0)
c = ctx.constraints[0]
print(f"面积约束: {c.name} {c.sense} rhs={c.rhs}")
assert c.name == "area_die"
assert c.sense == "<="
assert abs(c.rhs - 2400.0) < 1e-9, f"rhs 应为 2500 − 10² = 2400, 实际 {c.rhs}"
assert len(c.terms) == 0, "面积约束不含 L 变量（纯 B 门槛）"
print("✓ α_d=0: rhs = A_max − d0² = 2400 恒正（恒松）")
```

---

## 2. 非退化 α_d>0：rhs 随 B 二次下降，B 有闭式上界

α_d=0.1, d0=10, A_max=2500 → B ≤ (√2500 − 10)/0.1 = (50−10)/0.1 = 400。

B=0:   rhs = 2500 − 10² = 2400
B=200: rhs = 2500 − (10+0.1·200)² = 2500 − 900 = 1600
B=400: rhs = 2500 − (10+0.1·400)² = 2500 − 2500 = 0   ← 临界
B=401: rhs = 2500 − 50.1² = 2500 − 2510.01 = −10.01  ← 不可行

```python
m = DieAreaModel(d0_mm=10.0, alpha_d=0.1, a_max_mm2=2500.0)
for B, expect in [(0.0, 2400.0), (200.0, 1600.0), (400.0, 0.0), (401.0, -10.01)]:
    ctx = Ctx(); ctx.vector("L", 1)
    m.build(ctx, B=B)
    c = ctx.constraints[0]
    print(f"B={B:>5.0f}: rhs={c.rhs:>8.2f} (期望 {expect:>8.1f})")
    assert abs(c.rhs - expect) < 1e-9
print("✓ 面积约束 rhs = A_max − (d0 + α_d·B)²，B 上界 = 400")
```

---

## 3. 约束效果：B 超上界 → LP 不可行

面积约束是常数约束（无 L 项），CvxSolver 把空表达式编译为 0 ≤ rhs：
rhs<0 时 LP 无解（infeasible），rhs≥0 时恒满足。

```python
def area_feasible(B):
    ctx = Ctx(); ctx.vector("L", 1)
    m.build(ctx, B=B)
    return CvxSolver().solve(ctx).status in ("optimal", "optimal_inaccurate")

assert area_feasible(400.0), "B=400（临界）应可行"
assert not area_feasible(401.0), "B=401（超上界）应不可行"
print("✓ B=400 可行、B=401 不可行——面积约束作为 B 上界正确生效")
```

---

## 4. build_scenario 接入：+area 档位

`perf+bump+therm+area`（无 wiring）与 `perf+bump+therm+wiring+area`（E3 完整阶梯）
都应在模型列表末尾追加 DieAreaModel。

```python
topo = MeshTopology(2)
P = TOY
layout = place(topo, P)

models_a, meta = build_scenario(topo, "perf+bump+therm+area", P, layout)
types_a = [type(m).__name__ for m in models_a]
print(f"perf+bump+therm+area: {types_a}")
assert types_a[-1] == "DieAreaModel"
assert len(models_a) == 4  # perf, bump, therm, area

models_wa, meta2 = build_scenario(topo, "perf+bump+therm+wiring+area", P, layout)
types_wa = [type(m).__name__ for m in models_wa]
print(f"perf+bump+therm+wiring+area: {types_wa}")
assert types_wa == ["ObliviousValiantModel", "BumpModel", "SteadyStateModel",
                    "WiringModel", "DieAreaModel"]
print("✓ +area 档位接入，E3 完整阶梯 = perf+bump+therm+wiring+area")
```

---

## 5. A_max 随布局而定：interposer 面积 ÷ 芯粒数

build_scenario 应把 A_max 算成 interposer 面积 ÷ n_dies：
toy interposer 100×100 = 10000 mm²，Mesh(2) 4 dies → A_max = 2500 mm²。

```python
models_a2, _ = build_scenario(topo, "perf+bump+therm+area", P, layout)
area_model = models_a2[-1]
# 从模型内部取出构造参数核对（面积上界来自布局）
assert isinstance(area_model, DieAreaModel)
# 构建时 A_max = P.pkg.interposer_w_mm * P.pkg.interposer_h_mm / n_dies
a_max_expect = P.pkg.interposer_w_mm * P.pkg.interposer_h_mm / layout.n_dies
print(f"A_max = {P.pkg.interposer_w_mm}×{P.pkg.interposer_h_mm} / {layout.n_dies} = {a_max_expect:.0f} mm²")
ctx_chk = Ctx(); ctx_chk.vector("L", 1)
area_model.build(ctx_chk, B=0.0)
assert abs(ctx_chk.constraints[0].rhs - (a_max_expect - P.die.base_side_mm**2)) < 1e-9
print("✓ A_max = interposer 面积 ÷ 芯粒数，rhs = A_max − d0² 一致")
```

---

## 6. cache_key 可哈希

```python
k = area_model.cache_key()
assert isinstance(k, tuple) and len(k) > 0
assert k == area_model.cache_key(), "cache_key 必须幂等"
assert DieAreaModel(10.0, 0.1, 2500.0).cache_key() != DieAreaModel(10.0, 0.0, 2500.0).cache_key()
print(f"✓ cache_key = {k} 可哈希，不同 α_d 区分")
```

---

## 结论

`build_scenario` 的 `+area` 档位接入成功：DieAreaModel 实现 V5 §2(2f)
（A_die(B) ≤ A_max，常数约束，纯 B 门槛）；rhs = A_max − d(B)² 手算一致；
α_d>0 时给出 B 闭式上界（B=400 临界）；A_max 随布局 = interposer 面积 ÷ 芯粒数；
E3 完整阶梯 perf+bump+therm+wiring+area 可构造。
