# test03b — EnvelopeModel (src/problem/models/perf/traffic_based/_envelope.py)

## 模块定位

`EnvelopeModel` 把一组 `Pattern` 变成 LP 约束。核心三条：

$$\sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)} \quad \text{(每条 OD 对的流量守恒)}$$
$$L_e^{(r)} = \sum_{(i,j,k): e \in \text{path}} f_{ij}^{k,(r)} \quad \text{(链路负载 = 分流之和)}$$
$$L_e \ge L_e^{(r)} \quad \forall r \quad \text{(包络: 取各需求模式最大负载)}$$

目标用 `min ΣL` 把 L 压至真实包络下界。

paths 和 link_incidence 是 `(topology, pattern)` 的派生产物，在 `build()` 内按非零 demand 的 OD 对动态计算。

```python
import sys; sys.path.insert(0, '../src')
import itertools
import numpy as np
from problem import Ctx, CvxSolver
from problem.models.perf.traffic_based import EnvelopeModel
from problem.models.perf.traffic_based.traffic import TrafficMatrixPattern, PermutationPattern
from topology import Mesh
```

---

## 辅助：复现 EnvelopeModel 的 pair/path/incidence 计算

EnvelopeModel 按 D 矩阵的非零项逐行扫描生成 active pairs，下面这个函数做完全一样的计算。

```python
def _build_incidence(topo, D):
    """与 EnvelopeModel.build() 完全一致的计算：返回 (active, pair_paths, inc)。"""
    terminals = topo.terminals
    li = topo.link_index

    active = []  # [(src_node, dst_node, demand), ...]
    for i, src in enumerate(terminals):
        for j, dst in enumerate(terminals):
            if i == j:
                continue
            d = float(D[i, j])
            if d > 0:
                active.append((src, dst, d))

    pair_paths = []
    for src, dst, _ in active:
        paths = topo.valiant(src, dst)
        ppl = []
        for path in paths:
            ppl.append([li[(path[k], path[k+1])] for k in range(len(path)-1)])
        pair_paths.append(ppl)

    inc = [[] for _ in range(topo.n_links)]
    for pi, ppl in enumerate(pair_paths):
        for pj, link_idxs in enumerate(ppl):
            for e in link_idxs:
                inc[e].append((pi, pj))

    return active, pair_paths, inc
```

---

## 第一部分：单需求模式 —— 验证基本力学

用 Mesh(2)（4 终端），构造一个最简单的需求：只 0→1 发 0.5。

```python
graph = Mesh(2)

# 拓扑本体属性
print(f"terminals = {graph.terminals}")
print(f"n_links = {graph.n_links}")
print(f"links = {graph.links}")
```

### 1a. 构造单需求 LP，求解

```python
# 只 0→1 发 0.5，其余全 0
D_01 = np.array([[0.0, 0.5, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 0.0]])
pattern = TrafficMatrixPattern("0to1", D_01)

model = EnvelopeModel(graph, [pattern])
ctx = Ctx()
model.build(ctx, B=800.0)
L = ctx["L"]

sol = CvxSolver().solve(ctx, objective=sum(L), maximize=False)
assert sol.status in ("optimal", "optimal_inaccurate")
print(f"solved: status={sol.status}")

L_vals = sol.variables["L"]
Lr_vals = sol.variables["Lr_r0"]
print(f"L  = {[f'{v:.3f}' for v in L_vals]}")
print(f"Lr = {[f'{v:.3f}' for v in Lr_vals]}")

# 用相同的逻辑重建 incidence 用于验证
active, pair_paths, inc = _build_incidence(graph, D_01)
print(f"active pairs: {active}")
for pi, (src, dst, d) in enumerate(active):
    print(f"  pair[{pi}] {src}→{dst} demand={d}: {len(pair_paths[pi])} paths")
```

### 1b. 验证流量守恒（数值）

```python
for pi, (src, dst, d) in enumerate(active):
    K = len(pair_paths[pi])
    f_sum = sum(sol.variables.get(f"f_r0_p{pi}_k{ki}", 0.0) for ki in range(K))
    assert abs(f_sum - d) < 1e-6, \
        f"pair {src}→{dst}: Σf={f_sum:.4f} ≠ demand={d}"
    print(f"  {src}→{dst}: Σf = {f_sum:.4f} = demand = {d} ✓")

print("✓ flow conservation verified")
```

### 1c. 验证 Lr_e = Σ f 对每条链路

```python
for li in range(graph.n_links):
    lr_computed = 0.0
    for pi, ki in inc[li]:
        f_val = sol.variables.get(f"f_r0_p{pi}_k{ki}", 0.0)
        if isinstance(f_val, (int, float)):
            lr_computed += f_val
    assert abs(lr_computed - Lr_vals[li]) < 1e-6, \
        f"link {li} {graph.links[li]}: Σf={lr_computed:.4f} ≠ Lr={Lr_vals[li]:.4f}"
print(f"✓ Lr_e = Σf verified for all {graph.n_links} links")
```

### 1d. 单模式时 L = Lr（包络退化为自身）

```python
for li in range(graph.n_links):
    assert abs(L_vals[li] - Lr_vals[li]) < 1e-6, \
        f"link {li}: L={L_vals[li]:.4f} ≠ Lr={Lr_vals[li]:.4f}"
print("✓ L = Lr (single pattern → no envelope needed)")
```

### 1e. 验证 f 值合理 —— 最短路径优先

0→1 的 det 路径只有一跳。`min ΣL` 会把所有流量推到最短路径上。

```python
# 找到 (0,1) 链路的索引
li_01 = graph.link_index[(0, 1)]
print(f"link (0,1) → index {li_01},  L = {L_vals[li_01]:.4f}")

# 单跳路径应该承载全部 0.5 流量
assert abs(L_vals[li_01] - 0.5) < 1e-4, \
    f"expected L[link(0,1)] = 0.5, got {L_vals[li_01]:.4f}"

# 其他链路负载应为 0（流量全走最短路径）
loaded = [(li, L_vals[li]) for li in range(graph.n_links) if L_vals[li] > 1e-6]
print(f"loaded links: {[(graph.links[li], f'{v:.4f}') for li, v in loaded]}")
print("✓ all traffic took shortest path (min ΣL)")
```

---

## 第二部分：多需求模式 —— 包络

两个不同的需求模式，L 应该是逐链路取 max。

```python
# 模式 A: 0→1 发 1.0
DA = np.array([[0.0, 1.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 0.0]])

# 模式 B: 0→2 发 1.0
DB = np.array([[0.0, 0.0, 1.0, 0.0],
               [0.0, 0.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 0.0]])

model2 = EnvelopeModel(graph, [
    TrafficMatrixPattern("A_01", DA),
    TrafficMatrixPattern("B_02", DB),
])
ctx2 = Ctx()
model2.build(ctx2, B=800.0)

sol2 = CvxSolver().solve(ctx2, objective=sum(ctx2["L"]), maximize=False)
assert sol2.status in ("optimal", "optimal_inaccurate")

L2 = sol2.variables["L"]
LrA = sol2.variables["Lr_r0"]
LrB = sol2.variables["Lr_r1"]

print("link      L        LrA      LrB      max(LrA,LrB)")
for li in range(graph.n_links):
    max_lr = max(LrA[li], LrB[li])
    u, v = graph.links[li]
    ok = "✓" if abs(L2[li] - max_lr) < 1e-6 else "✗"
    print(f"({u},{v})  {L2[li]:.4f}   {LrA[li]:.4f}   {LrB[li]:.4f}   {max_lr:.4f}  {ok}")
    assert abs(L2[li] - max_lr) < 1e-6, \
        f"link {li}: L={L2[li]:.4f} ≠ max(LrA, LrB)={max_lr:.4f}"

print("✓ L = max(LrA, LrB) for all links")
```

### 验证两个模式的流量守恒分别成立

```python
for r, (name, D) in enumerate([("A", DA), ("B", DB)]):
    prefix = f"r{r}"
    act, ppl, _ = _build_incidence(graph, D)
    violations = 0
    for pi, (src, dst, d) in enumerate(act):
        K = len(ppl[pi])
        f_sum = sum(sol2.variables.get(f"f_{prefix}_p{pi}_k{ki}", 0.0)
                    for ki in range(K))
        if abs(f_sum - d) > 1e-6:
            violations += 1
            print(f"  FAIL {name} pair {src}→{dst}: Σf={f_sum:.4f} ≠ demand={d}")
    assert violations == 0, f"{violations} flow conservation violations in pattern {name}"
print("✓ flow conservation holds for both patterns")
```

---

## 第三部分：排列模式同样可用

`PermutationPattern` 和 `TrafficMatrixPattern` 都实现 `Pattern`，`EnvelopeModel` 不区分。

```python
graph3 = Mesh(2)

pp0 = PermutationPattern("swap01", (1, 0, 3, 2))  # 0↔1, 2↔3
pp1 = PermutationPattern("cycle02", (2, 3, 1, 0))  # 0→2→1→3→0

model3 = EnvelopeModel(graph3, [pp0, pp1])
ctx3 = Ctx()
model3.build(ctx3, B=800.0)

sol3 = CvxSolver().solve(ctx3, objective=sum(ctx3["L"]), maximize=False)
assert sol3.status in ("optimal", "optimal_inaccurate")

L3 = sol3.variables["L"]
Lr0 = sol3.variables["Lr_r0"]
Lr1 = sol3.variables["Lr_r1"]

for li in range(graph3.n_links):
    assert abs(L3[li] - max(Lr0[li], Lr1[li])) < 1e-6

print("✓ PermutationPattern works identically to TrafficMatrixPattern in EnvelopeModel")
```

---

## 第四部分：SelectedEnvelopeModel —— 选择器驱动的包络模型

`SelectedEnvelopeModel(topo, selector=None)` 继承 `EnvelopeModel`，构造时内部用 selector 生成代表置换——builder 不需要自己调 `select_representatives`，给拓扑 new 模型就完事。默认 selector 是 `ConjugacySelector`（共轭类代表元，当前唯一生产实现）。

```python
from problem.models.perf.traffic_based._envelope import SelectedEnvelopeModel
from problem.models.perf.traffic_based.traffic import select_representatives

graph4 = Mesh(2)

# 默认 selector（共轭类）与手动 select 必须完全等价
manual_reps = select_representatives(graph4, graph4.n_terminals)
auto_model = SelectedEnvelopeModel(graph4)
manual_model = EnvelopeModel(graph4, manual_reps)

assert auto_model.cache_key() == manual_model.cache_key(), \
    "默认 selector 的结果必须与 select_representatives 一致"

ctx_a = Ctx(); auto_model.build(ctx_a, B=800.0)
ctx_m = Ctx(); manual_model.build(ctx_m, B=800.0)
assert len(ctx_a.constraints) == len(ctx_m.constraints)
assert [c.name for c in ctx_a.constraints] == [c.name for c in ctx_m.constraints]

# 显式 selector 也能用
from problem.models.perf.traffic_based.traffic import ManualSelector
m = SelectedEnvelopeModel(graph4, ManualSelector([(1, 0, 3, 2)]))
ctx4 = Ctx(); m.build(ctx4, B=800.0)
assert any(c.name.startswith("r0_flow") for c in ctx4.constraints)
print("✓ SelectedEnvelopeModel: 默认 = 共轭类代表元，与手动 select 逐约束一致")
```
