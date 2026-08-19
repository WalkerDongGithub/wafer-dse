# test08 — query 层 (src/problem/queries/)

## 模块定位

模型把约束写进 Ctx，engine 把 Ctx 解成 Result。query 层在这两者之上问"问题"：

- **FeasibilityQuery** —— 给定 B，这个构型可行吗？返回可行与否 + 包络负载 + 绑定约束。
- **BmaxQuery** —— 能支撑的最大端口带宽 B* 是多少？内部反复问 feasibility，二分 B 轴。

两者共享缓存：bmax 用 `"feasibility"` 作为 query_id 调 runner，所以 bmax 的中间结果全部落在 feasibility 的缓存 key 下，反过来也一样。这个设计让"先扫可行性曲线，再算 B*"的两次实验只解一次 LP。

**契约要点**：

1. `interpret(sol, ctx, B)`：status ∈ {optimal, optimal_inaccurate} 才算可行；`worst_load = max(L)`，L 为空时是 inf（infeasible 没有变量解）。
2. `binding_constraints` 来自 `sol.duals` 的 key——哪些约束在 B* 处是绑定的。
3. bmax：lo 不可行 → 立刻返回 `B_star=0`；hi 可行 → 翻倍扩展；二分到 `hi - lo <= step`，返回 lo（保守端）。
4. 可行性关于 B 单调：B 越大约束越紧。这是二分正确的前提，测试里显式验证。

**最小 session**：MeshTopology(2)（4 节点全 terminal）+ 性能包络 + μbump + 热网络。必须带物理模型——纯 ObliviousValiantModel 下 B 不影响可行性，bmax 会无限翻倍。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from problem import Ctx, CvxSolver, Runner
from problem import ObliviousValiantModel, BumpModel, SteadyStateModel
from physical.layout.thermal_network import ThermalNetworkBuilder
from problem.queries import FeasibilityQuery, BmaxQuery
from topology import MeshTopology
from physical.config.spec_bump import UBUMP_45UM, DieBumpBudget

topo = MeshTopology(2)  # 4 节点全 terminal，4 个 die

perf = ObliviousValiantModel(topo)

d2l = {}
for li, (u, v) in enumerate(topo.links):
    d2l.setdefault(u, []).append(li)
    d2l.setdefault(v, []).append(li)
budgets = [DieBumpBudget(f'd{i}', UBUMP_45UM, 12, 12, 50, 0.8, 0.7) for i in range(4)]
bump = BumpModel(budgets, d2l, topo.n_links)

# 1D 链式热网络（smoke 用；正经使用换成 hierarchical 求解器输出）
G = np.eye(4) * 0.9 - np.eye(4, k=1) * 0.1 - np.eye(4, k=-1) * 0.1
b = np.full(4, 0.8 * 300.0)
net = ThermalNetworkBuilder.precompute(G, b, 358.15, d2l, topo.n_links)
therm = SteadyStateModel(net)

models = [perf, bump, therm]
runner = Runner(CvxSolver())

def ok(B):
    return runner.solve("feasibility", float(B), Ctx(), models).status in ("optimal", "optimal_inaccurate")
```

---

## 1. FeasibilityQuery：固定 B 判定

小 B 可行，大 B 不可行。中间有个翻转点——这就是 B*。

```python
q = FeasibilityQuery()

r_lo = q.interpret(runner.solve(q.query_id, 100.0, Ctx(), models), Ctx(), 100.0)
r_hi = q.interpret(runner.solve(q.query_id, 1e6, Ctx(), models), Ctx(), 1e6)

print(f"B=100:    feasible={r_lo.feasible}  worst_load={r_lo.worst_load:.1f}")
print(f"B=1e6:    feasible={r_hi.feasible}  worst_load={r_hi.worst_load}")
assert r_lo.feasible, "小 B 应该可行"
assert not r_hi.feasible, "大 B 应该不可行（bump/热约束绑定）"
```

### 1b. infeasible 时没有变量解 → worst_load = inf

```python
assert r_hi.envelope_L == {}, "infeasible 无变量解，L 应为空"
assert r_hi.worst_load == float("inf"), "空 L 时 worst_load 应为 inf"
print("infeasible → worst_load = inf ✓")
```

### 1d. 坑：infeasible 时 duals 是"不可行性证书"，不是绑定约束

求解器在 infeasible 时返回的 duals 是 Farkas 证书里的约束集合，**不代表这些约束同时绑定**。所以 `binding_constraints` 只在 feasible=True 时有语义，feasible=False 时请忽略它。

```python
print(f"infeasible 时 duals 数量: {len(r_hi.binding_constraints)}")
assert r_hi.feasible is False
# 契约：binding_constraints 只在 feasible 时有语义，这里不 assert 其内容
```

### 1e. 无目标求解的 duals 不可靠——绑定诊断必须用 min ΣL

feasibility 是"任意可行解"，CLARABEL 对无目标 LP 可能不返回 duals（实测同一 B 下 duals=0）。而 min ΣL 求解稳定返回（实测 32 个）。所以 binding_constraints 在无目标求解结果上**不可依赖**——瓶颈诊断的流程必须是：feasibility 判定 + min ΣL 求解拿 binding。

```python
ctx = Ctx()
for m in models: m.build(ctx, 100.0)
sol_noobj = CvxSolver().solve(ctx, objective=None)
ctx2 = Ctx()
for m in models: m.build(ctx2, 100.0)
sol_minL = CvxSolver().solve(ctx2, objective=sum(ctx2["L"]), maximize=False)
n_noobj = len(sol_noobj.duals) if sol_noobj.duals else 0
n_minL = len(sol_minL.duals) if sol_minL.duals else 0
print(f"无目标: duals={n_noobj}  |  min ΣL: duals={n_minL}")
assert n_minL >= n_noobj, "min ΣL 的 duals 应不比无目标少"
```

### 1c. 可行时 worst_load 是真实包络最大值

```python
assert r_lo.envelope_L, "可行时 L 非空"
assert r_lo.worst_load == max(r_lo.envelope_L.values())
print(f"可行时 worst_load = max(L) = {r_lo.worst_load:.1f} ✓")
```

---

## 2. BmaxQuery：二分找 B*

### 2a. 单调性——二分正确的前提

```python
B_star_guess = None
sweep = [100, 500, 1000, 5000, 1e4, 5e4, 1e5, 5e5, 1e6]
for B in sweep:
    f = ok(B)
    print(f"B={B:>8.0f}: {'✓' if f else '✗'}")
    if f:
        B_star_guess = B
assert B_star_guess is not None and B_star_guess >= 100
# 单调性：遍历中一旦出现 ✗，之后必须全是 ✗
seen_infeasible = False
for B in sweep:
    f = ok(B)
    if not f:
        seen_infeasible = True
    else:
        assert not seen_infeasible, f"B={B} 可行但更大 B 已不可行——单调性破坏"
print("可行性随 B 单调 ✓")
```

### 2b. lo 不可行 → 快速失败

```python
bad = BmaxQuery().solve(runner, lambda b: (Ctx(), models), lo=1e6, hi=2e6, step=10)
print(f"lo=1e6 不可行 → B_star={bad.B_star}, notes={bad.notes}")
assert bad.B_star == 0.0 and bad.notes == ["lo 不可行"]
assert bad.iterations == 0
```

### 2c. 正常二分

```python
bq = BmaxQuery()
r = bq.solve(runner, lambda b: (Ctx(), models), lo=100, hi=1e6, step=50)

print(f"B* = {r.B_star:.0f} Gbps, 区间 [{r.lo:.0f}, {r.hi:.0f}], {r.iterations} 次 LP")
assert r.B_star > 0, "B* 应为正"
assert r.hi - r.lo <= 50, "收敛精度 = step"
assert r.iterations <= 16, f"迭代数应 ≈ log2(1e6/50) = 15, 实际 {r.iterations}"

# B* 落在真实翻转区间：B_star 可行，B_star + 2*step 不可行
assert ok(r.B_star), "B* 本身必须可行"
assert not ok(r.hi), "收敛时 hi 不可行"
```

### 2d. 迭代数符合 log2 理论

```python
import math
lo, hi = 100, 1e6
r2 = bq.solve(runner, lambda b: (Ctx(), models), lo=lo, hi=hi, step=50)
expect = math.ceil(math.log2((hi - lo) / 50))
print(f"实际 {r2.iterations} 次 vs 理论 ≤ {expect} 次")
assert r2.iterations <= expect
```

---

## 3. 缓存共享：bmax 的中间结果落在 feasibility 的缓存 key 下

同一 runner 再跑一遍 bmax——所有二分点都已在 L1 缓存里。第二遍不再产生新的 LP 求解：hits 增长数 = 二分迭代数 + 2 次边界探测（lo、hi）。

```python
hits_before = runner.hits
r3 = bq.solve(runner, lambda b: (Ctx(), models), lo=100, hi=1e6, step=50)
hits_gained = runner.hits - hits_before
print(f"第二遍 bmax：{r3.iterations} 次二分，L1 命中 {hits_gained} 次")
assert hits_gained == r3.iterations + 2, "第二遍应全部缓存命中，无新 LP 求解"
```

---

## 结论

query 层契约全部通过。设计要点：

- feasibility 是所有 query 的基础——bmax 只是它的一个调用模式，两者共享缓存 key（`"feasibility"`），实验脚本先扫曲线再算 B* 不花第二遍钱。
- infeasible 时 `worst_load = inf` 是个容易踩的坑：画曲线时 inf 点不会画出来，但数据里它存在。
- `binding_constraints` 目前只是 duals 的 key 列表——还没做"哪个模型家族的约束绑定"的归类。瓶颈诊断实验（B 增长时绑定序列）需要它。
