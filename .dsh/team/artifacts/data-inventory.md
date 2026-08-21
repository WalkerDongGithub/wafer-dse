# 数据盘点（data-inventory）

> Phase 2 产出（DataSteward，2026-08-20）
> 用途：EvalDesigner 实验设计的执行侧底账——现有 query / 场景 / 参数 / exp 入口 / 可跑性缺口。
> 依据：V5（唯一权威模型文档）；实现对表见 `notes/IMPLEMENTATION_MAP.md`（V5 经书净化后派生）；`src/problem/queries/*`、`src/problem/builder/_scenario.py`、`exp/*`、`config/*` 实测；`insight.md` + `notes/INSIGHT_READING.md`。
> 可追溯原则：每个实验/表/图可溯源到「query_id × params_name × scenario × topo × git hash × 数据文件」。

---

## 1. 现有 query 清单

| query | query_id | 输入 | 输出 | 说明 |
|---|---|---|---|---|
| `FeasibilityQuery` | `feasibility` | `runner.solve(query_id, B, ctx, models)`；`interpret(sol, ctx, B)` | `FeasibilityResult{B, feasible, solve_time_s, envelope_L: {链路idx: L}, binding_constraints, worst_load}` | 固定 B 的可行性判定（LP status ∈ optimal/optimal_inaccurate）；**`envelope_L` 直接给出逐链路 L 包络值**——insight 6 图数据无需新 query |
| `BmaxQuery` | `bmax` | `solve(runner, ctx_factory, lo=100, hi=10000, step=50, verbose, log_file)`；`ctx_factory(B) → (Ctx, models)` | `BmaxResult{B_star, lo, hi, iterations, notes}` | 二分 partition 取最大可行 B*（指数扩展 hi + 二分，约 8-13 次 feasibility LP）；确定性；内部走 feasibility 缓存 |

- 底层：`Runner.solve(query_id, B, ctx, models) → Result{status, variables["L"], duals, solve_time_s}`；`Query` ABC 定义 `query_id/objective/interpret`（`src/problem/queries/__init__.py`）。
- 锚点测试：`tests/queries/test08_queries.md`（feasibility/bmax）、`tests/perf`（包络）、`tests/bump`（μbump）、`tests/die_scaling/test11`。
- 实测（当前代码）：Mesh(2)/UBUMP_45UM smoke → B\*=15109 Gbps（8 LP）；Mesh(2)/ucie-32g/perf+bump+therm → B\*=11221.7 Gbps（9 LP，确定性）。

## 2. 场景清单（对照 V5 § / C1-C4）

入口：`src/problem/builder/_scenario.py::build_scenario(topo, scenario, P, layout)`。

| 场景 | 模型列表 | V5 对应 | 跨层耦合 | 说明 |
|---|---|---|---|---|
| `perf` | `[ObliviousValiantModel]` | §7 L 包络 + §7.3 逐链路子 LP（均匀分流） | 无 | B 不约束 → B\* 无界，run_matrix 直接跳过（作基线） |
| `perf+bump` | `[ObliviousValiantModel, BumpModel]` | §2(2c) + **§4 C1**（μbump 预算） | C1 | on-die 链路（router↔terminal 同 die）不走 interposer：lane_rate=∞、零 bump/热代价 |
| `perf+bump+therm` | `[ObliviousValiantModel, BumpModel, SteadyStateModel]` | §2(2c) C1 + **§2(2e)** 热方程（L1 稳态 per-die T≤T_max，`AnalyticNetworkBuilder` 面邻接 + 集总 R_vert，MFIT 式） | C1 + 热 | 当前默认全场景；`GlobalPowerModel`（L0 初筛）已实现但**未接入**场景 |

**未接入场景的模型（`notes/IMPLEMENTATION_MAP.md` ⚠️/❌，代码侧缺口）**：

| 模型 | V5 对应 | 状态 |
|---|---|---|
| `C4Model` | §3(3c) + **§4 C2**（SerDes lane 数约束） | 已实现，未接入 `build_scenario` |
| `WiringGrid`（interposer 布线） | §2(2d) 三维容量 | 已实现，未接入 |
| sub 热方程 | §3(3d) + **§4 C4** | ❌ 未实现（多 interposer 场景启用） |
| D2D/I2I 分割比 ρ | — | ❌ 未引入（DSE 核心旋钮，待决项见 `.dsh/team/decisions.md`） |
| die 缩放（α_d, β_P） | §2.8 | 实现就绪，但**所有 params YAML 均未启用**（无 alpha_d/beta_p 值） |

> 论文 §4.2.2 声称"三层实体 + 跨层耦合 C1-C4 联立"——当前代码实际只联立 C1 + 热。实验设计与论文措辞需对表：**跨层耦合的"完整 C1-C4"尚未全部落地**（模型缺口，非执行缺口）。

## 3. 参数组清单

### 3.1 `config/params/*.yaml`（16 组，唯一参数源，不硬编码）

| params | die (mm, P0, vdd) | link (lane G) | bump | R_vert (K/W) | T_max (K) | 谱系/用途 |
|---|---|---|---|---|---|---|
| `toy` | 10×10, 10W, 1.0 | toy-10G | toy-100μm, util 1.0 | 1.0 | 400.0 | 手算友好（B\* 锚点 4500）；run_matrix 可跑 |
| `ucie-16g` | 12×12, 5W, 0.8 | UCIe-16G | μbump-45μm, 0.9 | 1.5 | 358.15 | UCIe 谱系；run_matrix 可跑 |
| `ucie-24g` | 12×12, 5W, 0.8 | UCIe-24G | μbump-45μm, 0.9 | 1.5 | 358.15 | 同上 |
| `ucie-32g` | 12×12, 5W, 0.8 | UCIe-32G-Advanced (0.016 W/lane) | μbump-45μm, 0.9 | 1.5 | 358.15 | 默认参数组（run_matrix/run_ledger） |
| `ucie-12g` | 12×12, 3W, 0.8 | UCIe-12G | μbump-45μm, 0.9 | 1.5 | 358.15 | UCIe 谱系低速端 |
| `ucie-32g-air` | 12×12, 5W, 0.8 | UCIe-32G | μbump-45μm, 0.9 | **2.5** | 358.15 | 约束旋钮：空气散热（悲观） |
| `ucie-32g-microfluidic` | 12×12, 5W, 0.8 | UCIe-32G | μbump-45μm, 0.9 | **0.4** | 358.15 | 约束旋钮：微流散热（乐观） |
| `3d-tsv-1um` | 4×4, 5W, 0.65 | TSV-3D-4G | μbump-25μm, 0.95 | 0.4 | 348.15 | 3D 堆叠细 pitch |
| `3d-tsv-5um` | 6×6, 10W, 0.7 | TSV-3D-4G | μbump-25μm, 0.9 | 0.6 | 358.15 | 3D 堆叠中 pitch |
| `3d-tsv-9um` | 8×8, 15W, 0.7 | TSV-3D-4G | μbump-45μm, 0.9 | 0.8 | 358.15 | 3D 堆叠粗 pitch |
| `optical-cpo` | 12×12, 20W, 0.8 | Optical-1.6T-8λ, 200G | μbump-45μm, 0.9 | 1.0 | 358.15 | 光互连（CPO） |
| `sow-info` | 15×15, 50W, 0.8 | InFO-SoW, 200G | μbump-25μm, 0.85 | 0.3 | 358.15 | 晶圆级 InFO |
| `sow-x` | 10×10, 30W, 0.8 | SoW-X, 400G | μbump-25μm, 0.85 | 0.3 | 358.15 | 晶圆级 SoW-X |
| `trad-air-112g` | 20×20, 50W, 0.8 | SerDes-112G-VSR, 106.25G | C4-200μm, 0.6 | 0.4 | 358.15 | 传统 2.5D 空气 |
| `trad-air-ucie-std` | 15×15, 30W, 0.8 | UCIe-16G-Std | μbump-110μm, 0.7 | 0.5 | 358.15 | 传统 UCIe 标准 |
| `trad-liquid-224g` | 18×18, 60W, 0.75 | SerDes-224G-VSR, 212.5G | C4-130μm, 0.65 | 0.25 | 358.15 | 传统 2.5D 液冷 |

- 加载：`physical.params.load_yaml_params(dir)` 读全部 16 组；**`exp/run_matrix.py` 已接线**（2026-08-20，`PARAM_SETS = load_yaml_params(...)`，全 16 组按文件名可用；另加每组合 try/except——布局/求解失败落 `error` 列，不中断整轮）。
- ⚠️ 无任何 YAML 提供 `alpha_d/beta_p`（§2.8 die 缩放）→ die 缩放实验需先补参数值。

### 3.2 `config/problems/*.yaml`（2 个，CLI `make run PROBLEM=…` 实验实例）

| problem | params | 拓扑 | 场景 | query |
|---|---|---|---|---|
| `toy_fullmesh2` | `toy` | FullMesh(2,1) | perf+bump+therm | bmax(lo=100, hi=20000, step=100) |
| `ucie32g_mesh3` | `ucie-32g` | Mesh(3) | perf+bump+therm | bmax(lo=100, hi=100000, step=200) |

- `main.py` 支持 query type ∈ {bmax, feasibility}；problem 里的 `selector: conjugacy` 键**未被 src/ 消费**（残留键，无害）。

## 4. exp 脚本清单

| 入口 | 用法 | 内容 | 产物 |
|---|---|---|---|
| `exp/run_matrix.py` | `make matrix PARAMS=<name>`（默认 ucie-32g） | 11 拓扑 × 3 场景 → B\* + B\* 处绑定约束（min ΣL 解 duals，物理约束按 bump_/therm_/c4_/route_ 前缀归类） | `exp/output/matrix_<params>_<ts>.csv` + `bmax_<params>.log`（每次运行清空重写） |
| `exp/run_ledger.py` | `make ledger TOPOS="Mesh(2)"`（默认全部 11） | 对每个拓扑：bmax 后沿 B\*/4, B\*/2, 3B\*/4, B\* 四点解 min ΣL，输出每点 perf(max L) / μbump(占用率) / 热(T 与 margin) / 绑定约束 duals | 控制台账本 + `bmax_ledger.log`（**无 CSV 落盘**）；⚠️ 硬编码 `UCIE_32G` |
| `exp/smoke_feasibility.py` | 手动 | Mesh(2)+UBUMP_45UM，B∈{100..3200} 逐点可行性 | 控制台 |
| `exp/smoke_bmax.py` | `make smoke` | Mesh(2)+UBUMP_45UM 找 B\* | 控制台（实测 B\*=15109） |
| `exp/_helpers.py` | smoke 用 | `session(topo, bump_spec, ...)` 组 perf+bump+therm 模型（**默认热网络为 1D 链式占位，非正式**） | — |
| `src/main.py` | `make run PROBLEM=…` | problems YAML → params+拓扑+场景+query | CLI + 缓存 |

- ⚠️ `src/walker_handoff.py` **已缺失**（旧 08-18 数据管线的聚合/批量入口，仅在 Windows 旧树存在）；`latest_summary.md` 中 walker 命令不可执行，统一走 run_matrix/run_ledger。
- 缓存：`exp/output/.cache`（ResultStore）加速重跑；⚠️ 混合年代（08-18 旧树 + 08-19 本地），论文级重跑建议清空重建。

## 5. 可跑性说明

### 5.1 现在就能跑（✅，当前代码已实测/可直接跑）

1. **FeasibilityQuery / BmaxQuery 单点**：smoke 脚本、任意 `ctx_factory` 组合。
2. **run_matrix**（4 参数组 × 11 拓扑 × 3 场景）：perf 无界跳过，实跑 88 次 BmaxQuery；小拓扑 <1s/组合，mesh4（16 dies）无缓存可达数分钟/组合（旧数据实测 mesh4/optical-cpo 300-417s）→ 建议重拓扑单独排队。
3. **run_ledger**（已实测 Mesh(2)：B\*≈11211，热绑定 margin +0.2K、μbump 占用 4.2%、包络 duals 正常）。
4. **CLI**（2 个 problems）。

### 5.2 部分可跑（⚠️，缺 exp 接线/参数值，属我维护范围）

| 缺口 | 现状 | 需要 |
|---|---|---|
| 包络 L\* 数据（insight 6 首选图：同拓扑 × 多参数 → 包络不动） | `FeasibilityResult.envelope_L` 已直接给出逐链路 L，**无需新 query** | 新 exp：逐链路 L\* 向量导出 + 跨参数组对比（等 EvalDesigner 定规格） |
| 11 组 YAML 参数接入实验 | ✅ 已完成（2026-08-20）：run_matrix `PARAM_SETS` 改 YAML 全量加载 + error 列容错 | 已接线，实测 ucie-12g 可跑、trad 系列 placement 失败落 error |
| ledger 全量落盘 | run_ledger 只打控制台 | 增加 CSV 落盘 + 全量跑 |
| die 缩放档位（§2.8） | 模型就绪，参数无值 | YAML 补 `alpha_d/beta_p` + exp 定义缩放档位（内部良心检查用，不上论文台面） |

### 5.3 跑不了（❌，模型/实现缺口——上报 DomainExpert/CodeEngineer，非执行缺口）

1. **跨层耦合 C1-C4 完整落地**：C4Model（§4 C2）、WiringGrid（§2(2d)）、sub 热（§3(3d)+§4 C4）未接入 `build_scenario` → 含 C4/布线/Substrate 热的实验当前无法跑。
2. **D2D/I2I 分割比 ρ 旋钮**（"一个大 interposer vs 多个小 interposer"）未引入模型。
3. `GlobalPowerModel`（L0 初筛）未接入任何场景。

### 5.4 数据口径红线（数据结论）

- **`exp/output/` 2026-08-18 数据集不可引用，仅作参考**：生成于 Windows 机器（`C:\Users\ASUS\...`），早于 V5 定稿（08-18 21:55）、Valiant 包络数值修正（08-19 02:54 d58f9ed）、lp→problem 重构（08-19 02:03）。**实测同组合（Mesh(2)/ucie-32g/perf+bump+therm）：旧 B\*=32 Gbps vs 当前代码 11221.7 Gbps，差约 350 倍**。
- 论文所有数字须按当前代码全量重跑（跑前清缓存）；正式输出附加 git 短 hash + params 名锁定口径。
- 确定性：LP 无随机、无需种子；同输入同输出（版本锁定前提）。

---

## 附：给 EvalDesigner 的规模参考（实验设计控规模用）

- BmaxQuery 每次 8-13 次 feasibility LP；run_matrix 全量 88 次 BmaxQuery。
- 求解时间：小拓扑（Mesh2/3、Torus2/3、FullMesh2）<1s/组合；KaryNCube/Dragonfly 中等；Mesh(4)（16 dies）最重（无缓存可达数分钟-十分钟级/组合）。
- 建议：正文实验优先小拓扑 × 关键参数组（ucie 谱系 + 3d-tsv + optical），可扩展性实验（§5.6）单独用规模轴。
