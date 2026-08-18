# Do 报告 — 代码审查员（02）

日期：2026-08-18
任务：严厉审查 ObliviousValiantModel（V5 §7.3 静态 oblivious Valiant 路由包络）
审查对象：`src/problem/models/perf/traffic_based/_oblivious.py` + 对照 `tests/perf/test04_oblivious.md` + 缓存脚本
审查重点：**数学严谨性（最高优先级）**，对照 V5 §7.3 唯一权威定义

## 审查方式

- **怀疑优先**——所有数学 claim 一律独立用 Python 重算（不依赖 ObliviousValiantModel 的实现）
- **举证**——见 `memory/02-code-reviewer/_tools/verify_oblivious_math.py` + `verify_dragonfly_and_invariants.py`
- **铁律**：不替工程师改代码，只提问题 + 给证据

---

## 一、数学严谨性结论：**严格符合 V5 §7.3**

### 1.1 V5 §7.3 子 LP 对照（逐条核对）

V5 §7.3 子 LP：

$$\max_{\mathbf{D}}\ L_e(\mathbf{D}) \quad \text{s.t.}\quad \mathbf{L} = \mathcal{P}\,\mathbf{f}(\mathbf{D}),\ \mathbf{M}_{\text{f} \to \text{D}}\,\mathbf{f} = \mathbf{D},\ \mathbf{D} \in \text{Birkhoff}$$

| V5 §7.3 要求 | 代码实现位置 | 核对结果 |
|---|---|---|
| **f 固定为均匀分流** `f_k(i,j) = D_{ij}/K_{ij}` | `_precompute` L101-104 `coeffs[e][i,j] /= K` | ✓ 正确：每条 OD 对 (i,j) 的 K_{ij} 条候选路径各分 D_{ij}/K_{ij}，故 c_{ij}^e = (#path 含 e)/K_{ij} |
| **D ∈ Birkhoff 多面体** | `_solve_envelope` L129-130 `cp.Variable((N,N), nonneg=True)` + `cp.sum(D, axis=1)==1` + `cp.sum(D, axis=0)==1` | ✓ 精确实现 Birkhoff 多面体 = {D ≥ 0, D·1=1, D^T·1=1}（行和=列和=1） |
| **对每条链路 e 分别求解** | `_solve_envelope` L127 `for e in range(topo.n_links)` | ✓ 独立建 LP，每条链路一个 `cp.Variable`，无变量复用 |
| **自环 (i,i) 不参与流量** | `_precompute` L77-78 `if i==j: continue` | ✓ 自环系数为 0，不贡献流量；但 Birkhoff 行/列和约束仍含 D_{ii}（正确——V5 要求 D ∈ Birkhoff 整体约束） |
| **c_{ij}^e 定义** = |{k : e ∈ path_k(i,j)}| / K_{ij} | `_precompute` L98-104 | ✓ 先累加 +1.0（通过 e 的路径数），再除 K——正确 |
| **K_{ij} = 候选路径数** | `_precompute` L95 `K = len(ppl)` | ✓ 等于 `len(topo.valiant(src, dst))` |

### 1.2 Birkhoff 顶点性质（Birkhoff-von Neumann 定理）

V5 §7.3 隐含：线性目标在 Birkhoff 多面体顶点取到最优，顶点 = 置换矩阵。

**代码用 LP 求解，是否会给出非顶点解？**

理论上 LP 求解器可能返回非顶点解（多面体面上的任何点）。但**这不影响 L_e\* 的正确性**：
- 线性目标在多面体上**一定存在顶点最优解**（Birkhoff-von Neumann 定理）
- 即使 LP 返回非顶点 D\*，目标值 L_e(D\*) 仍等于最大值（顶点最优解的目标值）
- 代码用 `prob.value`（目标值），不是 `D.value`（决策变量值）——所以 L_e\* 永远正确

test04 第一部分验证了 Mesh(2) link 0 的 D\* 确实是置换矩阵 σ=(3,2,0,1)——独立 Python 枚举 24 个置换证实。

### 1.3 与 OptimalValiantModel 关系（V5 §7.1-§7.2）

V5 §7.1-§7.2 隐含 oblivious L\* ≥ optimal L（oblivious 更悲观）。

**逐链路关系是否在所有拓扑上成立？**

数学推导（test04 L247-254 的推导）：
- oblivious L\*_e = max_{D∈Birkhoff} L_e(D, f_uniform)
- ≥ max_{r∈R} L_e(r, f_uniform)   （R ⊆ Birkhoff）
- ≥ min_f max_{r∈R} L_e(r, f) = optimal L_e   （f_uniform 是某个 f，min_f ≤ 任意特定 f）

**结论：逐链路 oblivious L\*_e ≥ optimal L_e 是数学保证，不限拓扑对称性**。
test04 L282-286 验证 Mesh(2) 上成立——独立复算通过（见 verify_oblivious_math.py claim 5）。

### 1.4 L\* 与 B 无关（V5 §7.2）

V5 §7.2："L 包络在此固定路由下计算得到，不依赖 B——性能模型可独立于物理模型单独求解。"

- 代码 `build(ctx, B=1.0)` 中 B 完全不参与（参数保留仅为符合 Model 三段式接口） ✓
- `__init__` 预解 L\* 时也未使用 B ✓

### 1.5 数学严谨性总体结论

**严格符合 V5 §7.3。所有数学 claim 经独立 Python 枚举验算通过**：

| Claim | 验算结果 |
|---|---|
| Mesh(2) L_0\* = 3/2，σ=(3,2,0,1) | ✓ 独立枚举 24 个置换，max=1.5，argmax σ=[3,2,0,1] |
| Mesh(2) 8 链路全 1.5（对称性） | ✓ 8 链路独立枚举均=1.5 |
| FullMesh(4,p=1) tr=1, rt=1, rr=2/3 | ✓ 4+4+12 链路独立验算 |
| Torus(3) 全 36 链路 = 6/7 ≈ 0.857143 | ✓ 独立枚举 9!=362880 个置换，36 链路均=6/7 |
| Dragonfly(a=2,p=1,h=1) max L\* = 7/3 | ✓ 独立枚举 6!=720 个置换，max=2.333333，sum=38（do 报告"待核实"项已补完） |
| Σ_e L_e\* ≥ N 不变式 | ✓ Mesh(2) 12≥4，FullMesh(4) 16≥4，Torus(3) 30.857≥9 |
| 逐链路 oblivious ≥ optimal (Mesh(2)) | ✓ 8 链路均 oblivious 1.5 ≥ optimal |
| 9 拓扑 L\* 与 cache JSON 数值对照 | ✓ 全部一致（容差 1e-5） |
| 两次跑 ObliviousValiantModel 可复现 | ✓ 数值完全一致（容差 1e-9） |

---

## 二、可攻击点清单（按严重程度排序）

### 🟢 Minor-1：`.gitignore` 缺 `cache/` —— 缓存产物会误入库

- **位置**：`c:/Users/ASUS/wafer-dse/.gitignore`
- **问题**：`.gitignore` 已含 `outputs/`、`dse_results/`、`exp/output/`，但**未含 `cache/`**。`cache/oblivious_envelopes.json` 是预计算产物（9 拓扑的 L\* 数值），属于 DSE 运行结果类产物，按 `AGENTS.md §9`「实验输出不入库」原则应被忽略。
- **举证**：
  ```
  # .gitignore 当前内容（无 cache/）
  outputs/
  dse_results/
  exp/output/
  ```
  ```
  # cache/oblivious_envelopes.json 存在
  $ ls cache/
  oblivious_envelopes.json
  ```
- **严重程度**：低（不会污染代码逻辑，但会让 `git add .` 误纳入 1.5KB 缓存文件）
- **修补建议**：在 `.gitignore` 中追加 `cache/`（与 `outputs/` 同处理原则）。do 报告 §"待核实" 第 2 条已自查到这一点，但未给出修补。
- **结论**：要求修补（一行 `.gitignore` 改动）。

### 🟢 Minor-2：`_solve_envelope` 中 `prob.value is None` 兜底 0.0 违反 STYLE.md §0

- **位置**：`src/problem/models/perf/traffic_based/_oblivious.py` L135
- **代码**：`val = float(prob.value) if prob.value is not None else 0.0`
- **问题**：该 LP（max Σ c·D, D ∈ Birkhoff）**总是可行**（单位矩阵可行）且**有界**（c ≥ 0, D 有界），故 `prob.value` 永远不为 None。兜底 `0.0` 是无意义的防御性代码，违反 STYLE.md §0「论文没提到的（产品级校验、异常处理、边界检查）→ 可以删」。
- **更严重的隐患**：如果未来真的出现 LP 求解失败（cvxpy 版本升级、求解器配置异常），静默返回 0.0 会**让 L\* 错为 0**——性能约束变成 L ≥ 0（无效约束），DSE 会给出虚假可行的解。这违背审查员"怀疑优先"原则：**应该让失败显式抛出**。
- **严重程度**：低（当前无 bug，但是反模式）
- **修补建议**：删除 `if prob.value is not None else 0.0`，直接 `val = float(prob.value)`。如果担心 cvxpy 异常，应该 `assert prob.status in ("optimal", "optimal_inaccurate"), f"LP solve failed: {prob.status}"` 让失败可见。
- **结论**：要求修补（删除兜底，改为显式状态检查或直接抛）。

### 🟢 Minor-3：test04 第四部分注释措辞误导——逐链路 ≥ 是数学保证

- **位置**：`tests/perf/test04_oblivious.md` L282-286
- **问题**：注释写 `# component-wise: for Mesh(2) symmetry holds (each oblivious 1.5 ≥ each optimal)`，"for Mesh(2) symmetry holds" 措辞暗示逐链路 ≥ 仅在 Mesh(2) 对称性下成立，**但这是误导**——逐链路 oblivious L\*_e ≥ optimal L_e 在**所有拓扑**上都成立（见 §1.3 数学推导）。
- **严重程度**：低（注释错误，非代码错误；测试断言本身正确）
- **修补建议**：改为 `# component-wise: mathematically guaranteed on all topologies (proven above); verified numerically on Mesh(2)`
- **结论**：建议修补注释（让数学保证的普遍性明确）。

### 🟢 Minor-4：审查员工具 `src_compliance_check.py` L106 豁免清单含旧名 `EnvelopeModel`

- **位置**：`memory/02-code-reviewer/_tools/src_compliance_check.py` L106
- **代码**：
  ```python
  if parent in {"PerfModel", "PhysModel", "ThermalModel", "EnvelopeModel", "OptimalValiantModel", "ObliviousValiantModel"} and cls.endswith("Model"):
      continue
  ```
- **问题**：`"EnvelopeModel"` 是改名前的旧类名，已被 `OptimalValiantModel` 取代。该清单用于豁免"二级 Model 子类只需带 Model 后缀"——旧名残留不会导致误报（因为 src/ 已无 `EnvelopeModel` 类，没有 class 会以它为父类），但 stale 引用会让后续审查员困惑。
- **严重程度**：极低（仅审查员工具内部，不影响生产代码）
- **修补建议**：从清单中删除 `"EnvelopeModel"`。
- **结论**：建议修补（一行删除）。

### 🟢 Minor-5：`cache_key` 用 `round(x, 9)` —— 跨 cvxpy 版本理论上有碰撞风险

- **位置**：`src/problem/models/perf/traffic_based/_oblivious.py` L165
- **代码**：`lstar = tuple(round(x, 9) for x in self._L_star)`
- **问题**：实测两次运行 L\* 完全一致（容差 1e-9），当前无碰撞。但理论上 cvxpy 求解器精度微抖（如 1.4999999984 vs 1.5000000001）可能让 `round(, 9)` 落到不同整数位（前者→1.499999998，后者→1.500000000），导致 cache_key 不一致，缓存未命中。
- **严重程度**：极低（实测无碍，纯理论问题）
- **修补建议**：可选——把容差放宽到 `round(x, 6)`（与 cache JSON 的精度对齐），或在 cache_key 中用 `tuple(int(round(x * 1e6)) for x in self._L_star)` 转整数避免浮点边界。
- **结论**：判定合理（实测无碍），仅记录。

---

## 三、改名完整性

### 3.1 EnvelopeModel / SelectedEnvelopeModel 残留扫描

`grep "EnvelopeModel|SelectedEnvelopeModel"` 全项目结果：

| 文件 | 性质 | 处理 |
|---|---|---|
| `src/**` 全部代码 | **0 命中** | ✓ 改名彻底 |
| `memory/01-code-engineer/do-20260818-oblivious-valiant-model.md` | do 报告里引用旧名作历史说明 | ✓ 合理（描述改名动作） |
| `memory/02-code-reviewer/_tools/src_compliance_check.py` L106 | 审查员工具的豁免清单 | 🟡 见 Minor-4 |
| `tests/perf/test04_oblivious.md` L6 | 对比表格中提"原 EnvelopeModel" | ✓ 合理（说明对照关系） |
| `STYLE.md` L91 | 多级继承示例 | ✓ 合理（文档示例） |
| `notes/MATH_MODEL_COMPLETE_V4.md`、`notes/INTERFACE_DESIGN.md`、`notes/MODEL_CODE_TRACE.md` | 历史/参考文档 | ⚠ 旧名残留但属历史文档 |
| `memory/02-code-reviewer/do-20260818-*.md`（既有） | 既有审查记录 | ✓ 历史快照，不改 |

### 3.2 `__init__.py` 各级导出同步

- `src/problem/__init__.py` L23-24, L53-54：导出 `OptimalValiantModel`/`SelectedOptimalValiantModel`/`ObliviousValiantModel`/`SelectedObliviousValiantModel` ✓
- `src/problem/models/__init__.py` L16-17, L43-44：同步 ✓
- `src/problem/models/perf/__init__.py` L22-23, L27-28：同步 ✓
- `src/problem/models/perf/traffic_based/__init__.py` L8-13, L25-26：同步 ✓
- `src/problem/builder/_scenario.py` L22, L55：使用 `SelectedOptimalValiantModel` ✓

### 3.3 backward compat alias 检查

- grep `EnvelopeModel = OptimalValiantModel` / `EnvelopeModel =` 全项目：**0 命中** ✓
- do 报告声称"不引入 alias"——属实。

**改名完整性结论：src/ 完全干净；唯一 stale 是审查员工具自己的豁免清单（见 Minor-4）和 notes/ 历史文档（不入审）。**

---

## 四、build() 三段式合规性

按 STYLE.md §1 三段式硬规则核对：

| 规则 | 代码核对 | 结果 |
|---|---|---|
| `__init__` 不调用 `ctx`，不声明变量，不写约束，只做数学运算 | `__init__` 调 `_precompute()`（系数）和 `_solve_envelope()`（LP 预解） | ✓ LP 求解属于"数学运算"，且 V5 §7.2 明确 L\* 与 B 无关（纯拓扑量），预解合理 |
| `build()` ≤ 30 行 | `build()` 主体 5 行（L152-156） | ✓ 远低于上限 |
| `build()` 不 import | `build()` 无 import | ✓ |
| `build()` 不做复杂循环 | `build()` 只一个 `for e, lstar in enumerate(self._L_star)` | ✓ |
| `cache_key()` 返回可哈希元组（非 None） | `("oblivious_valiant", str, int, tuple_of_floats)` | ✓ 全部可哈希 |
| `__init__` 预计算全部系数 | `_coeffs` 完整预解，`_L_star` 完整预解 | ✓ |

**注意点**：`__init__` 调用 LP 求解器是"较重"的 `__init__`（与典型 Model 子类只算系数不同）。但 V5 §7.2 明确"L 包络在此固定路由下计算得到，不依赖 B"——L\* 是纯拓扑量，预解在 `__init__` 是数学合理且必要的（否则每次 `build()` 都重解 LP，性能浪费）。`cache_key()` 编码 L\* 让 Runner 可 L1/L2 缓存。**判定合理**。

---

## 五、测试覆盖

### 5.1 test04_oblivious.md 六部分核对

| 部分 | 内容 | 独立复算 |
|---|---|---|
| 一：Mesh(2) 手算 L_0\* = 3/2 | 枚举 24 置换 + σ=(3,2,0,1) + 系数矩阵对照 | ✓ Python 枚举验证 max=1.5, σ=[3,2,0,1]，系数矩阵 c^0 与模型 `_coeffs[0]` 一致 |
| 二：FullMesh(4,p=1) 三类链路 | tr=1, rt=1, rr=2/3 | ✓ 独立枚举 4!=24 个置换，三类链路 L\* 验证通过 |
| 三：数学不变式 | L_e\* ≥ 0、Σ_e L_e\* ≥ N | ✓ Mesh(2) 12≥4, FullMesh(4) 16≥4, Torus(3) 30.857≥9 |
| 四：对比 OptimalValiantModel | Σ oblivious ≥ Σ optimal + Mesh(2) 逐链路 ≥ | ✓ Mesh(2) oblivious sum=12 vs optimal sum=6，逐链路 1.5 ≥ 各 optimal |
| 五：build() + cache_key 三段式 | 8 约束 + meaning + 可哈希 | ✓ build() 写 8 条 L ≥ L\*，cache_key 确定性 + 可哈希 |
| 六：SelectedObliviousValiantModel | 无 selector 入口，与直接构造一致 | ✓ isinstance + L\* 一致 + cache_key 一致 |

### 5.2 test04 不变式 3b 推导核对

test04 L227-229 推导 `Σ_e L_e\* ≥ N`：
- "每个 terminal 在最坏置换下各发 1 单位（derangement），总流量 = N"
- "每单位至少走 1 跳，故 Σ_e L_e(σ) ≥ N"
- "由于 L_e\* 是逐链路独立 max，Σ_e L_e\* ≥ max_σ Σ_e L_e(σ) ≥ N"

**推导核对**：
- Σ_e max_σ L_e(σ) ≥ max_σ Σ_e L_e(σ)：✓（和的最大 ≥ 最大的和，因对每个 e 有 max_σ L_e(σ) ≥ L_e(σ\*)，对任意固定 σ\* 求和即得）
- max_σ Σ_e L_e(σ) ≥ N：✓ 取 derangement σ（无不动点），Σ_{i≠j} D_{ij} = N（行和=1 + 对角=0），且 OD 对路径长度 ≥ 1，故 Σ_e L_e(σ) ≥ Σ_{i,j} D_{ij} × avg_path_len ≥ Σ_{i,j} D_{ij} = N

**推导正确，不变式成立**。

### 5.3 测试结果

```
$ cd tests; $env:PYTHONPATH="../src"; python run_all.py
18 files, 15 passed, 3 failed
  FAIL  benchmark\test13_contracts.md  —  TypeError: isinstance() argument 2 cannot be a parameterized generic
  FAIL  benchmark\test14_classify_bounds.md  —  AssertionError: Mesh+toy should be TRUE
  FAIL  benchmark\test15_rc_repro.md  —  ModuleNotFoundError: No module named 'rapidchipet_checker'
  OK    perf\test04_oblivious.md
  ...（其余 14 个 OK）
```

3 个失败为基线预存（do-20260818-refactor-lp-to-problem.md 已记录，与本次改动无关）。**test04_oblivious.md 全绿**，无回归。

---

## 六、缓存脚本核对

### 6.1 `scripts/compute_oblivious_envelopes.py`

- 9 拓扑全部跑通 ✓
- 缓存 JSON 结构完整（label / n_terminals / n_links / L_star / max / mean / sum / topo_class / topo_args）✓
- 独立 Python 枚举对照 9 拓扑 L\* 与 cache JSON 数值：**全部一致**（容差 1e-5）✓
- 两次跑 ObliviousValiantModel：L\* 完全一致（容差 1e-9）✓ 可复现

### 6.2 `cache/` 目录 gitignore 状态

**见 Minor-1**：`cache/` 未在 `.gitignore` 中，需要补一行。

---

## 七、修补建议汇总（按优先级）

| 优先级 | 项 | 文件 | 修补动作 |
|---|---|---|---|
| 中 | Minor-1 | `.gitignore` | 追加 `cache/` 一行 |
| 中 | Minor-2 | `_oblivious.py` L135 | 删除 `if prob.value is not None else 0.0` 兜底，改为 `val = float(prob.value)` 或加显式 `assert prob.status in ("optimal", "optimal_inaccurate")` |
| 低 | Minor-3 | `tests/perf/test04_oblivious.md` L282 | 注释改为"逐链路 ≥ 是数学保证，不限 Mesh(2) 对称性" |
| 低 | Minor-4 | `memory/02-code-reviewer/_tools/src_compliance_check.py` L106 | 从豁免清单删除 `"EnvelopeModel"` |
| 极低 | Minor-5 | `_oblivious.py` L165（可选） | `round(x, 9)` → `round(x, 6)` 或转 int |

**全部为低/中优先级修补，无任何阻塞性问题。**

---

## 八、总体结论

### **有条件通过**

**条件**（必须修补，否则打回）：
1. **Minor-1**：`.gitignore` 加 `cache/`（一行改动，避免缓存产物误入库）

**建议修补**（不阻塞，但应跟进）：
2. Minor-2：删除 `prob.value is None` 兜底（避免静默掩盖 LP 失败）
3. Minor-3：test04 L282 注释措辞修正

**判定合理并明确承认**（无需修补）：
- **数学严谨性**：严格符合 V5 §7.3，5 项核心 claim + Dragonfly 待核实项全部经独立 Python 枚举验算通过
- **改名完整性**：src/ 完全干净，各级 `__init__.py` 同步导出，无 backward compat alias
- **三段式合规**：build() ≤ 30 行，cache_key 可哈希，`__init__` LP 预解符合 V5 §7.2 "L\* 与 B 无关"
- **测试覆盖**：六部分齐备，不变式推导正确，无回归
- **缓存脚本**：9 拓扑全跑通，数值与 cache JSON 一致，可复现

### 验算脚本（落盘可复现）

- `memory/02-code-reviewer/_tools/verify_oblivious_math.py` —— 5 项核心 claim（Mesh(2)/FullMesh(4)/Torus(3)/Σ≥N/obl≥opt）
- `memory/02-code-reviewer/_tools/verify_dragonfly_and_invariants.py` —— Dragonfly=7/3 + 9 拓扑 cache 对照 + 可复现性

跑法：
```powershell
cd c:\Users\ASUS\wafer-dse
$env:PYTHONPATH="src"; python memory/02-code-reviewer/_tools/verify_oblivious_math.py
$env:PYTHONPATH="src"; python memory/02-code-reviewer/_tools/verify_dragonfly_and_invariants.py
```
