# Do 报告 — 代码工程师（01）

日期：2026-08-18
任务：性能包络模型改名 + 新增 ObliviousValiantModel（V5 §7.3 静态 oblivious 路由包络）

## 总览

本次任务分两部分：

1. **改名**：`EnvelopeModel` → `OptimalValiantModel`，`SelectedEnvelopeModel` → `SelectedOptimalValiantModel`。
   原模型把 f 当决策变量优化（最小化 L），对应"最优路由下的包络"，旧名 EnvelopeModel 语义模糊，改名后与新增的 oblivious 模型形成对照。
2. **新增 `ObliviousValiantModel`**：严格按 V5 §7.3 实现"静态 oblivious Valiant 路由下的 L 包络"。
   f 固定为均匀分流（D_{ij}/K_{ij}），D 是决策变量（Birkhoff 多面体），对每条链路 e 求 max L_e(D)。
   L* 与 B 无关（纯拓扑量），在 `__init__` 一次性预解，`build()` 只注入 L ≥ L*。

数学对照：

| | OptimalValiantModel | ObliviousValiantModel |
|---|---|---|
| f（分流） | 决策变量，LP 优化以最小化 L | 固定为均匀分流 D_{ij}/K_{ij} |
| D（需求） | 外生给定（代表置换集 R） | 决策变量，在 Birkhoff 多面体上 max L_e |
| L* 含义 | 最优路由下的包络（较乐观） | 最严苛包络（最坏流量 × 固定路由） |

## 改动清单

### 1. 改名（_envelope.py，只动名+docstring，逻辑不动）

| 文件 | 改动 |
|------|------|
| `src/problem/models/perf/traffic_based/_envelope.py` | `EnvelopeModel` → `OptimalValiantModel`；`SelectedEnvelopeModel` → `SelectedOptimalValiantModel`；模块/类 docstring 改述为"最优路由下的 L 包络——f 作为决策变量" |

### 2. 引用同步

| 文件 | 改动 |
|------|------|
| `src/problem/models/perf/traffic_based/__init__.py` | 导出名同步；docstring 增补 ObliviousValiantModel 一行说明 |
| `src/problem/models/perf/__init__.py` | 同步导出 |
| `src/problem/__init__.py` | 同步导出 `OptimalValiantModel` / `ObliviousValiantModel` |
| `src/problem/builder/_scenario.py` | `SelectedEnvelopeModel` → `SelectedOptimalValiantModel` |
| `exp/_helpers.py` | 实验会话用 `OptimalValiantModel` |
| `tests/perf/test03b_envelope.md` | 引用从 `EnvelopeModel` 改为 `OptimalValiantModel` |

### 3. 新增 _oblivious.py（严格 V5 §7.3）

| 文件 | 改动 |
|------|------|
| `src/problem/models/perf/traffic_based/_oblivious.py` | 新建：`ObliviousValiantModel` + `SelectedObliviousValiantModel` |

模型三段式（STYLE.md 合规）：

- `__init__`：预计算 oblivious 路由系数 c_{ij}^e（`_precompute`）+ 预解 L*（`_solve_envelope`）
- `build`：只做 B 缩放 + 写约束（L ≥ L*，B 不参与，性能包络与端口带宽无关 V5 §7.2）
- `cache_key`：`("oblivious_valiant", topo类名, n_links, L*元组)`，hashable 可缓存

关键算法：

- **`_precompute`**：枚举所有 OD 对 (i,j), i≠j → `topo.valiant(src,dst)` 取候选路径 → 转链路索引序列；对每条链路 e 累加 c_{ij}^e = |{k : e ∈ path_k(i,j)}| / K_{ij}（均匀 oblivious 分流下每条路径承载 D_{ij}/K_{ij}）。
- **`_solve_envelope`**：对每条链路 e 解子 LP `max_D Σ c_{ij}^e D_{ij}` s.t. D ∈ Birkhoff（D ≥ 0, D·1=1, D^T·1=1）。线性目标在顶点取到最优（Birkhoff-von Neumann 定理），即某个置换矩阵 σ*。每条链路独立建 `cp.Variable`（避免 cvxpy 变量复用副作用）。
- **`SelectedObliviousValiantModel`**：builder 入口，不需要 selector（oblivious 路由对所有 OD 对一视同仁），命名与 `SelectedOptimalValiantModel` 对齐便于 builder 互换性能模型。

### 4. 测试

| 文件 | 改动 |
|------|------|
| `tests/perf/test04_oblivious.md` | 新建：六部分（手算 + 不变式 + 对比 + 三段式合规 + builder 入口） |

测试覆盖：

1. **Mesh(2) 手算 L_0* = 3/2**：枚举 24 个置换验证最大值 = 3/2（σ=(3,2,0,1)），独立复算系数矩阵 c^0 对照模型内部 `_coeffs`，验证最优 D* 是置换矩阵（Birkhoff 顶点）。
2. **FullMesh(4, p=1) 手算**：三类链路（terminal→router=1，router→terminal=1，router→router=2/3）分别验证。
3. **数学不变式**：L_e* ≥ 0（非负）；Σ_e L_e* ≥ N（总负载守恒下界，derangement σ 使 Σ_{i≠j}D_{ij}=N）。
4. **对比 OptimalValiantModel**：Σ oblivious L* ≥ Σ optimal L（sum-level 数学保证）；Mesh(2) 对称性下逐分量 oblivious L*_e ≥ optimal L_e。
5. **build() + cache_key 三段式合规**：build() 只写 n_links 条 L ≥ L* 约束（带 meaning）；cache_key 可哈希且确定性。
6. **SelectedObliviousValiantModel**：无 selector 入口，与直接构造结果一致。

### 5. 缓存脚本

| 文件 | 改动 |
|------|------|
| `scripts/compute_oblivious_envelopes.py` | 新建：对 9 个拓扑从小到大算 L* 并缓存 |
| `cache/oblivious_envelopes.json` | 生成：9 个拓扑的 L* 缓存（结构见下） |

缓存结构（每条目）：

```json
{
  "label": {
    "n_terminals": int,
    "n_links": int,
    "L_star": [float, ...],
    "max_L_star": float,
    "mean_L_star": float,
    "sum_L_star": float,
    "topo_class": str,
    "topo_args": dict
  }
}
```

## 测试结果

```
cd tests && PYTHONPATH=../src python run_all.py
```

结果：`17 files, 14 passed, 3 failed`（test04_oblivious.md 全绿）。

3 个失败为基线预存（与本次改动无关，do-20260818-refactor-lp-to-problem.md 已记录）：
1. `benchmark/test13_contracts.md` — Python 3.10+ 类型泛型问题
2. `benchmark/test14_classify_bounds.md` — 校准特例未在论文网格中
3. `benchmark/test15_rc_repro.md` — 外部依赖 `rapidchipet_checker` 未安装

## 缓存脚本运行结果（9 拓扑汇总）

| Topology | N | \|E\| | max(L*) | mean(L*) | Σ(L*) |
|----------|---|----|---------|----------|-------|
| mesh_2x2 | 4 | 8 | 1.5000 | 1.5000 | 12.0000 |
| mesh_3x3 | 9 | 24 | 2.0190 | 1.8970 | 45.5286 |
| torus_2x2 | 4 | 8 | 1.5000 | 1.5000 | 12.0000 |
| torus_3x3 | 9 | 36 | 0.8571 | 0.8571 | 30.8571 |
| kary_2_2 | 4 | 8 | 1.5000 | 1.5000 | 12.0000 |
| kary_2_3 | 8 | 24 | 1.4667 | 1.4444 | 34.6667 |
| fullmesh_4 | 4 | 20 | 1.0000 | 0.8000 | 16.0000 |
| fullmesh_6 | 6 | 42 | 1.0000 | 0.5714 | 24.0000 |
| dragonfly_s | 6 | 24 | 2.3333 | 1.5833 | 38.0000 |

观察：
- **Mesh(2)/Torus(2)/Kary(2,2) 三者 L* 全 1.5**：N=4 的小拓扑结构等价（同构于 4-cycle），oblivious 包络一致。
- **Torus(3) L* = 6/7 ≈ 0.857**：双向环绕使每条链路被更少 OD 对的路径 traversed，oblivious 包络显著低于 Mesh(3) 的 2.019。
- **FullMesh 的 router→router 链路 L* = 2/3**：与手算一致（test04 第二部分）；terminal↔router 链路 L* = 1（必经本地出口/入口）。
- **Dragonfly(a=2,p=1,h=1) max L* = 7/3**：全局链路（h 链路）是瓶颈，oblivious 路由下最坏置换把流量集中到 global link。

## 关键设计决策

1. **不继承、新添文件**：按用户要求"不要动原来的代码，新添一个 model"，`_oblivious.py` 是独立新文件，`OptimalValiantModel` 逻辑一字未改（只改名+docstring）。
2. **L* 在 `__init__` 预解**：oblivious 包络与 B 无关（纯拓扑量），`__init__` 一次性解完所有子 LP，`build()` 只做约束注入。这与 `OptimalValiantModel`（build 时随 f 一起解）形成对比，但符合 STYLE.md 三段式——`__init__` 预计算系数、`build` 写约束、`cache_key` 哈希。
3. **每条链路独立 `cp.Variable`**：避免 cvxpy 变量复用的副作用（早期实现共用 D 导致 solve 状态污染），牺牲少量性能换正确性。
4. **`SelectedObliviousValiantModel` 不带 selector**：oblivious 路由对所有 OD 对一视同仁（均匀分流），不需要选择代表置换；类名与 `SelectedOptimalValiantModel` 对齐仅为 builder 互换便利。
5. **cache_key 编码 L***：L* 完全决定约束，把 L* 元组放入 cache_key 可让 Runner 缓存命中精确到数值。

## 数学严谨性要点（V5 §7.3 对齐）

1. **Birkhoff 多面体定义**：D ∈ R^{N×N}, D ≥ 0, D·1 = 1, D^T·1 = 1（行和=列和=1）。自环 D_{ii} 系数为 0（不贡献流量），但仍受行/列和约束——代码中 `cp.Variable((N,N), nonneg=True)` + 两条 sum 约束精确实现。
2. **Birkhoff-von Neumann 定理**：线性目标在 Birkhoff 多面体的顶点取到最优，顶点 = 置换矩阵。test04 第一部分验证 Mesh(2) link 0 的 D* = σ=(3,2,0,1) 的置换矩阵。
3. **系数 c_{ij}^e 定义**：`|{k : e ∈ path_k(i,j)}| / K_{ij}`，K_{ij} = OD 对 (i,j) 的候选路径数。均匀 oblivious 分流下每条路径承载 D_{ij}/K_{ij}，故 L_e(D) = Σ_{(i,j)} c_{ij}^e · D_{ij}。代码 `_precompute` 先累加后除 K 精确实现。
4. **与 OptimalValiantModel 的关系**（V5 §7.1-§7.2）：oblivious L*_e = max_{D∈Birkhoff} L_e(D, uniform_f) ≥ max_{r∈R} L_e(r, uniform_f) ≥ min_f max_{r∈R} L_e(r, f) = optimal L_e 的逐分量下界。test04 第四部分 sum-level 验证 Σ oblivious ≥ Σ optimal。

## 待核实

1. **`SelectedObliviousValiantModel` 是否需要接入 builder**：当前 `builder/_scenario.py` 仍用 `SelectedOptimalValiantModel`。若要让 DSE 实验切换到 oblivious 包络，需在 builder 增加 perf model 选择参数。本次未动 builder 选择逻辑（用户只要求"新添 model"）。
2. **cache/ 目录的 .gitignore 状态**：`cache/oblivious_envelopes.json` 是预计算产物，应检查是否已纳入 .gitignore（与 `outputs/` 同处理原则）。若需入库可手动 `git add -f`。
3. **Dragonfly(a=2,p=1,h=1) 的 L* = 7/3 尚未手工独立验证**：当前依赖 LP 求解器输出，建议后续补一个小拓扑手算锚点（与 Mesh(2)/FullMesh(4) 同级 rigor）。
