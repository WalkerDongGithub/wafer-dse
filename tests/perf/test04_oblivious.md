# test04 — ObliviousValiantModel (src/problem/models/perf/traffic_based/_oblivious.py)

## 模块定位

`ObliviousValiantModel` 实现 V5 §7.3 的静态 oblivious Valiant 路由下的 L 包络。
与 `OptimalValiantModel`（原 EnvelopeModel）的关键区别：

| | OptimalValiantModel | ObliviousValiantModel |
|---|---|---|
| f（分流） | 决策变量，LP 优化以最小化 L | 固定为均匀分流 D_{ij}/K_{ij} |
| D（需求） | 外生给定（代表置换集 R） | 决策变量，在 Birkhoff 多面体上 max L_e |
| L* 含义 | 最优路由下的包络（较乐观） | 最严苛包络（最坏流量 × 固定路由） |

数学（V5 §7.3 子 LP，对每条链路 e 分别求解）：

$$
\max_{\mathbf{D}} \sum_{i \ne j} c_{ij}^e D_{ij}
\quad \text{s.t.} \quad \mathbf{D} \in \text{Birkhoff}
$$

其中 $c_{ij}^e = |\{k : e \in \text{path}_k(i,j)\}| / K_{ij}$ 是固定系数（oblivious 均匀分流下，
通过链路 e 的候选路径比例）。Birkhoff 多面体上的线性目标在顶点取到最优
（Birkhoff-von Neumann 定理），即某个置换矩阵 σ*。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from problem import Ctx, CvxSolver
from problem import ObliviousValiantModel, SelectedObliviousValiantModel
from problem import OptimalValiantModel, select_representatives
from topology import Mesh, FullMesh
```

---

## 第一部分：Mesh(2) 手工验算 —— L_0* = 3/2

Mesh(2)：4 terminal（节点 0,1,2,3），维序路由先 y 后 x。
链路按首次发现顺序编号：

```
e0:(0,1)  e1:(0,2)  e2:(2,3)  e3:(1,0)
e4:(1,3)  e5:(2,0)  e6:(3,1)  e7:(3,2)
```

### 手算 link e0 = (0,1) 的系数 c_{ij}^0

对每个 OD 对 (i,j)，valiant 返回 det + 经中间 terminal 中转的路径。
每条路径转为 link index 序列，统计含 link 0 的路径数 / K_{ij}：

| OD (i,j) | K_{ij} | 含 link 0 的路径数 | c_{ij}^0 |
|----------|--------|--------------------|----------|
| (0,1)    | 3      | 2 ([0], [1,5,0])   | 2/3      |
| (0,2)    | 3      | 1 ([0,4,7])        | 1/3      |
| (0,3)    | 2      | 1 ([0,4])          | 1/2      |
| (1,0)    | 3      | 0                  | 0        |
| (1,2)    | 2      | 0                  | 0        |
| (1,3)    | 3      | 0                  | 0        |
| (2,0)    | 3      | 1 ([5,0,3])        | 1/3      |
| (2,1)    | 2      | 1 ([5,0])          | 1/2      |
| (2,3)    | 3      | 1 ([5,0,4])        | 1/3      |
| (3,0)    | 2      | 0                  | 0        |
| (3,1)    | 3      | 2 ([6,3,0], [7,5,0]) | 2/3    |
| (3,2)    | 3      | 0                  | 0        |

自环 (i,i) 不参与（系数为 0），但仍受 Birkhoff 行/列和约束。

### 手算 max_D L_0(D)

系数矩阵（行 i，列 j，i≠j；对角=0）：

```
     j=0   j=1   j=2   j=3
i=0  0     2/3   1/3   1/2
i=1  0     0     0     0
i=2  1/3   1/2   0     1/3
i=3  0     2/3   0     0
```

在 Birkhoff 多面体上 max Σ c_{ij} D_{ij}，最优在置换 σ* 取到。
枚举 4!=24 个置换，最大值 = 3/2，由 σ=(3,2,0,1) 取到：

  L_0* = c_{03} + c_{12} + c_{20} + c_{31} = 1/2 + 0 + 1/3 + 2/3 = **3/2**

### 代码验证

```python
mesh = Mesh(2)
m = ObliviousValiantModel(mesh)
L_star = m.solve_envelope()

print(f"n_links = {mesh.n_links}")
print(f"L* = {[round(x, 6) for x in L_star]}")

# hand-computed: L_0* = 3/2
assert abs(L_star[0] - 1.5) < 1e-6, f"L_0* = {L_star[0]}, expected 1.5"

# by symmetry of Mesh(2), all 8 links have the same L*
for e in range(mesh.n_links):
    assert abs(L_star[e] - 1.5) < 1e-6, f"L_{e}* = {L_star[e]}, expected 1.5"
print("✓ Mesh(2) L_0* = 3/2 (hand-computed), all links equal by symmetry")
```

### 独立复算系数 c_{ij}^0，对照模型内部 _coeffs

```python
# independently rebuild the coefficient matrix for link 0
terminals = mesh.terminals
li = mesh.link_index
N = len(terminals)
c0_manual = np.zeros((N, N))
for i in range(N):
    for j in range(N):
        if i == j:
            continue
        paths = mesh.valiant(terminals[i], terminals[j])
        K = len(paths)
        if K == 0:
            continue
        cnt = 0
        for path in paths:
            link_seq = [li[(path[k], path[k+1])] for k in range(len(path)-1)]
            if 0 in link_seq:
                cnt += 1
        c0_manual[i, j] = cnt / K

c0_model = m._coeffs[0]
np.testing.assert_allclose(c0_manual, c0_model, atol=1e-9)
print(f"✓ coefficient matrix c^0 matches independent computation")
print(f"  c^0 =\n{c0_manual}")
```

### 验证最优 D 是置换矩阵（Birkhoff 顶点）

```python
import cvxpy as cp
# re-solve link 0 explicitly to inspect D*
N = len(terminals)
D = cp.Variable((N, N), nonneg=True)
cons = [cp.sum(D, axis=1) == 1, cp.sum(D, axis=0) == 1]
obj = cp.Maximize(cp.sum(cp.multiply(c0_model, D)))
cp.Problem(obj, cons).solve()

D_val = np.array(D.value)
print(f"D* =\n{np.round(D_val, 4)}")

# optimal should be (near) a permutation matrix σ=(3,2,0,1)
# 0→3, 1→2, 2→0, 3→1
expected = np.array([[0,0,0,1],[0,0,1,0],[1,0,0,0],[0,1,0,0]], dtype=float)
np.testing.assert_allclose(D_val, expected, atol=1e-4)
print("✓ optimal D* is the permutation σ=(3,2,0,1) — Birkhoff vertex")

# objective = 1/2 + 0 + 1/3 + 2/3 = 3/2
obj_val = float(np.sum(c0_model * D_val))
assert abs(obj_val - 1.5) < 1e-6
print(f"✓ L_0* = Σ c·D* = {obj_val:.6f} = 3/2")
```

---

## 第二部分：FullMesh(4, p=1) 手工验算

FullMesh(4, p=1)：4 个 die（router 0-3），每 die 1 个 terminal（node 4-7）。
链路分三类（各有 4/4/12 条）：
- terminal→router（如 4→0）：每条 OD 流量必经本地出口 → c_{i,j}=1 (∀j≠i)
- router→terminal（如 1→5）：每条 OD 流量必经目标入口 → c_{i,j}=1 (∀i≠j)
- router→router（如 0→1）：只被部分 oblivious 路径 traverses → c_{ij}∈{0, 1/3}

三类 L* 推导：
- terminal→router: L(D) = Σ_{j≠i} D_{ij} = 1 − D_{ii}，max=1（取 D_{ii}=0）
- router→terminal: L(D) = Σ_{i≠j} D_{ij} = 1 − D_{jj}，max=1
- router→router:  max_σ Σ c_{i,σ(i)}，手算最大 = 2/3（见下）

router→router 系数（以 link (0,1) 为例）：c_{0,1}=1/3, c_{0,2}=1/3, c_{0,3}=1/3,
c_{2,1}=1/3, c_{3,1}=1/3，其余 0。最优置换如 σ=(2,3,0,1)：
L* = c_{0,2}+c_{1,3}+c_{2,0}+c_{3,1} = 1/3+0+0+1/3 = **2/3**。

```python
fm = FullMesh(4, p=1)
m_fm = ObliviousValiantModel(fm)
L_fm = m_fm.solve_envelope()

print(f"FullMesh(4,1) n_links = {fm.n_links}")
links = fm.links

# classify links and check L* per class
tr, rt, rr = [], [], []  # terminal-router, router-terminal, router-router
for e, (u, v) in enumerate(links):
    # terminal nodes are >= a=4; router nodes are < a=4
    if u >= 4 and v < 4:
        tr.append(L_fm[e])
    elif u < 4 and v >= 4:
        rt.append(L_fm[e])
    else:
        rr.append(L_fm[e])

print(f"terminal→router ({len(tr)} links): L* = {[round(x,4) for x in tr]}")
print(f"router→terminal ({len(rt)} links): L* = {[round(x,4) for x in rt]}")
print(f"router→router  ({len(rr)} links): L* = {[round(x,4) for x in rr]}")

# hand-computed: terminal-router = 1, router-terminal = 1, router-router = 2/3
for x in tr:
    assert abs(x - 1.0) < 1e-6, f"terminal→router L* = {x}, expected 1.0"
for x in rt:
    assert abs(x - 1.0) < 1e-6, f"router→terminal L* = {x}, expected 1.0"
for x in rr:
    assert abs(x - 2/3) < 1e-6, f"router→router L* = {x}, expected 2/3"
print("✓ FullMesh(4,1): terminal-router=1, router-terminal=1, router-router=2/3")
```

---

## 第三部分：数学不变式

### 3a. L_e* ≥ 0（非负）

```python
for topo in [Mesh(2), Mesh(3), FullMesh(4, p=1), FullMesh(6, p=1)]:
    mm = ObliviousValiantModel(topo)
    Ls = mm.solve_envelope()
    assert all(x >= -1e-9 for x in Ls), f"{type(topo).__name__}: negative L*"
    print(f"✓ {type(topo).__name__}({topo.__dict__}): all L*_e ≥ 0")
```

### 3b. 不变量 Σ_e L_e* ≥ N（总负载守恒下界）

每个 terminal 在最坏置换下各发 1 单位（derangement），总流量 = N。
每单位至少走 1 跳，故 Σ_e L_e(σ) ≥ N。由于 L_e* 是逐链路独立 max，
Σ_e L_e* ≥ max_σ Σ_e L_e(σ) ≥ N（最末不等式因存在 derangement σ 使 Σ_{i≠j}D_{ij}=N）。

```python
for topo in [Mesh(2), FullMesh(4, p=1)]:
    mm = ObliviousValiantModel(topo)
    Ls = mm.solve_envelope()
    N = topo.n_terminals
    total = sum(Ls)
    print(f"  {type(topo).__name__}: Σ L* = {total:.4f}, N = {N}")
    assert total >= N - 1e-6, f"Σ L* = {total} < N = {N}"
print("✓ Σ_e L_e* ≥ N for all tested topologies")
```

---

## 第四部分：对比 OptimalValiantModel —— oblivious 一定不优于最优路由

数学保证（V5 §7.1-§7.2）：oblivious 用固定均匀分流 + 全 Birkhoff 最坏 D，
optimal 用优化分流 + 代表置换子集 R。两者关系：

  oblivious L*_e = max_{D∈Birkhoff} L_e(D, uniform_f)
                 ≥ max_{r∈R} L_e(r, uniform_f)        (R ⊆ Birkhoff)
                 ≥ min_f max_{r∈R} L_e(r, f)           (uniform_f 是某个 f)
                 = optimal L_e 的逐分量下界

而 optimal 的 min ΣL 解给出 L_opt_e = max_r L_e(r, f*)（f* 最小化 Σ），
满足 Σ L_opt ≤ Σ L_oblivious（sum-level 保证）。

```python
mesh2 = Mesh(2)

# Oblivious
obl_m = ObliviousValiantModel(mesh2)
obl_L = obl_m.solve_envelope()
obl_sum = sum(obl_L)

# Optimal (representative derangements, min ΣL)
reps = select_representatives(mesh2, mesh2.n_terminals)
opt_m = OptimalValiantModel(mesh2, reps)
ctx = Ctx()
opt_m.build(ctx, B=1.0)
sol = CvxSolver().solve(ctx, objective=sum(ctx["L"]), maximize=False)
assert sol.status in ("optimal", "optimal_inaccurate")
opt_L = sol.variables["L"]
opt_sum = sum(opt_L)

print(f"Oblivious L* = {[round(x,4) for x in obl_L]}, sum = {obl_sum:.4f}")
print(f"Optimal  L   = {[round(x,4) for x in opt_L]}, sum = {opt_sum:.4f}")

# sum-level: oblivious ≥ optimal (mathematically guaranteed)
assert obl_sum >= opt_sum - 1e-6, f"Σ oblivious {obl_sum} < Σ optimal {opt_sum}"
print("✓ Σ Oblivious L* ≥ Σ Optimal L (sum-level, guaranteed)")

# component-wise: for Mesh(2) symmetry holds (each oblivious 1.5 ≥ each optimal)
for e in range(mesh2.n_links):
    assert obl_L[e] >= opt_L[e] - 1e-6, \
        f"link {e}: oblivious {obl_L[e]} < optimal {opt_L[e]}"
print("✓ Oblivious L*_e ≥ Optimal L_e for all links (Mesh(2))")
```

---

## 第五部分：build() + cache_key —— 三段式合规

```python
m5 = ObliviousValiantModel(Mesh(2))

# build() writes L ≥ L* into ctx, nothing else
ctx5 = Ctx()
m5.build(ctx5, B=1.0)
L_var = ctx5["L"]
assert L_var.shape == 8

# exactly n_links oblivious_env constraints
env_cons = [c for c in ctx5.constraints if c.name.startswith("oblivious_env_e")]
assert len(env_cons) == 8, f"expected 8 env constraints, got {len(env_cons)}"

# each constraint is L[e] >= L*[e]
for c in env_cons:
    assert c.sense == ">="
    assert c.meaning  # meaning required for inequalities
print(f"✓ build() writes 8 L ≥ L* constraints with meaning")

# cache_key is hashable and deterministic
k1 = m5.cache_key()
k2 = ObliviousValiantModel(Mesh(2)).cache_key()
assert k1 == k2, "same topo → same cache_key"
assert hash(k1) == hash(k2)
assert isinstance(k1, tuple)
print(f"✓ cache_key = {k1[:3]}... (hashable, deterministic)")
```

---

## 第六部分：SelectedObliviousValiantModel —— builder 入口

```python
from problem.models.perf.traffic_based._oblivious import SelectedObliviousValiantModel

topo6 = Mesh(2)
sel = SelectedObliviousValiantModel(topo6)
assert isinstance(sel, ObliviousValiantModel)

# same L* as direct ObliviousValiantModel (no selector needed — oblivious is uniform)
direct = ObliviousValiantModel(topo6)
assert sel.solve_envelope() == direct.solve_envelope()
assert sel.cache_key() == direct.cache_key()
print("✓ SelectedObliviousValiantModel: no-selector entry, identical to direct construction")
```
