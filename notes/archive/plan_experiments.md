# 论文实验规划清单 — wafer-dse (based on MATH_MODEL_COMPLETE_V2)

> 状态标记: [有代码] = 脚本已存在; [部分] = 有底层模块但无实验脚本; [无代码] = 需新建
> 输出目录约定: `outputs/paper_experiments/` (由 `scripts/exp/_runner.py` 的 `DEFAULT_OUTPUT_DIR` 定义)
> 实验设置 (来自 `docs/paper/Tex/Experiments/1_setup.tex`): Intel i7-13700K, 32GB RAM, Linux; Python 3.13, cvxpy 1.3 + CLARABEL; 默认物理参数 12×12mm die, 50W TDP, 45μm pitch μbump (75mA/bump), 0.8V, 70% 面积利用率, 液冷 (2.0 W/mm²), UCIe-32G lane 速率, 5 mW/lane 功耗; 最坏情况 (TDP + 稳态)

---

## 关键发现：代码当前是 V1，V2 完全没有实现

当前 LP 引擎 (`src/wafer_dse/lp/engine.py`) 实现的是 V1 模型（D 为 LP 变量，最小化瓶颈 t），V2 模型（固定排列代表元 D^(r) + 包络 L + 二分搜索 B*）**完全没有代码**。`scripts/validate_lp.py` import 的是已删除的 `_potential` 模块——脚本已过期。

## A. 已有代码的实验 (5 个实验脚本 + 3 个绘图脚本)

全部在 `scripts/exp/`，公共运行器 `_runner.py`（`Trial` dataclass + `run_trials()` → CSV）。**全部基于 V1 模型。**

### A1. exp_scalability.py — 可扩展性 [有代码]
- 内容: 3 组拓扑 Valiant LP 规模扫描：Dragonfly 9 组、Mesh 2/3/4/5、KaryNCube 5 组。N ≤ 30（Valiant LP 变量 ~O(N²·g)）。
- 数据: label, n_terminals, num_vars, num_constraints, t_star, solve_time_s, nonblocking_gbps, feasible, bottleneck_link, solver, n_links, topology/a/p/h/g。
- 输出: `scalability.csv`。不含物理约束（纯性能）。
- 论文: `2_scalability.tex`（N≤27 全部 <20s 求解；N=30 实用上限；所有 Dragonfly t*=1.0000）。

### A2. exp_bmax.py — B_max 物理带宽天花板 [有代码]
- 内容: 9 个拓扑（N≤30）。先解 Valiant LP 得 L_e，再解析反解 B_max。绑定约束标注（geometry/thermal/both/none）。
- 输出: `bmax.csv`。
- 论文: `3_bmax.tex`——表格数值**硬编码**，应重跑后更新。

### A3. exp_constraint_coupling.py — 多约束耦合 [有代码]
- 内容: 6 拓扑 × 9 场景（逐步添加 bump/热约束，观察 feasible→infeasible 翻转）。
- 输出: `constraint_coupling.csv`。
- 论文 TeX 中无对应小节，待补。

### A4. exp_dse_sweep.py — DSE 扫描 + Pareto 前沿 [有代码]
- 内容: 12 组 Dragonfly × 几何+热约束。2D 非支配排序（max BW vs min area）。
- 输出: `dse_sweep.csv`。
- 论文: `4_pareto.tex`——Pareto 前沿仅 DF(1,1,1) 与 DF(2,5,1)。注意 tex 说"8 个配置"而脚本 12 个。

### A5. exp_sensitivity.py — 灵敏度分析 [有代码]
- 内容: DF(2,2,1), 800G。3 个 RHS 扫描（性能/几何/热），通过 `sensitivity.py::sweep_constraint_rhs` 重求解。
- 限制: **对偶变量未提取**——`dual_values` 恒为 0（未记录 cvxpy duals）。
- 论文: `Sensitivity/main.tex` 当前是骨架。

### A6. 绘图脚本 [有代码]
- `plot_scalability.py` → scalability.pdf（变量数 vs N + 求解时间 vs 变量数）
- `plot_bmax.py` → bmax.pdf（B_max vs N）
- `plot_pareto.py` → pareto.pdf（N vs 面积散点 + Pareto 星标）
- 输入均为 `outputs/paper_experiments/*.csv`，**outputs/ 当前不存在**。

### A7. 其他已有代码
- `scripts/validate_lp.py`: V1 demo 判据 vs LP 判据对比。**会 ImportError（import 已删除的 _potential 模块）**
- `src/wafer_dse/pareto.py`: 三维 Pareto 前沿/分层/FOM 计算
- 热求解器三档: `_simple.py` / `_mfit.py` / `_hierarchical.py`

## B. 论文需要的实验（V2 模型）

### B1. 可扩展性 — B* vs N [部分，需扩展]
- V2 B* 二分搜索曲线：B* vs N，LP 调用次数 ~log2(Bmax/ε)
- V2 LP 规模 vs N：变量数 ≈ O(R·N²·g)，R（轨道数）决定规模而非 N!
- L0 vs L1 性能约束对比
- **无代码**: B* 二分搜索、V2 包络 LP

### B2. 约束瓶颈分析 [部分，需扩展]
- B* 处逐约束绑定诊断：包络约束 / bump / 温度 / 翘曲
- B 增长时先绑定顺序 →"瓶颈演化序列"
- **无代码**: V2 引擎

### B3. 灵敏度 — 对偶变量 / 影子价格 [部分，需补对偶提取]
- 对偶提取：cvxpy constraint duals → 影子价格
- 比值 ν_v / τ（bump 边际 vs 散热边际）→ 投资优先级
- **无代码**: dual 提取、比值计算

### B4. R 轨道计数实验 [无代码]
- 理论: SYMMETRY_REDUCTION.md。K_n: p(8)=22, p(16)=231。Dragonfly ~ S_a wr S_p（远小于 231）
- Aut(G) 计算 + 轨道枚举（networkx 或 nauty）
- 正确性验证：小 N 暴力枚举 vs R 代表元——这是方法严格性的核心证据
- **无代码**: 无任何轨道/自同构实现

### B5. V1 vs V2 对比 [无代码 — V2 引擎不存在]
- 同一拓扑上 V1 和 V2 的 t* / B* 差异
- 预期 V1 过乐观——量化过乐观程度
- 可行域差异：V1 feasible 但 V2 infeasible 的设计点
- **论文最核心验证实验**

### B6. 方案一（对称+排列 LP）vs 方案二（RNB）可行域 [无代码]
- 理论: NONBLOCKING_CONDITIONS.md、SUBSTRATE_RNB.md、CLOS_DECOMPOSITION.md
- (N, M, K) 参数扫描，对比两种方案 B*
- 量化可行域间隙
- **无代码**: RNB 检查、Clos 条件检查

### B7. 热模型保真度对比 [部分，求解器有代码无实验脚本]
- simple vs hierarchical vs MFIT：T_max、可行性 margin、求解时间、误差
- LP 内热约束（当前只有 L0）vs LP 外 L1 热网络后验检查翻转率

### B8. 精度梯度（L0 vs L1）[无代码]
- N=2,6,12,18,24 Dragonfly，(0,0,0) vs (1,1,1) 精度
- 判定一致性 + slack 阈值

### B9. 路由最优性间隙 [部分，需新建仿真]
- LP 最优路由 vs 固定路由（FixedRouteSolver）
- gap = (L_fixed − t*_LP)/t*_LP
- **无 NoC/周期级路由仿真器**，需自建或引入外部

## C. 论文预期图表

已有（脚本存在）:
- Fig 1: scalability.pdf
- Fig 2: bmax.pdf
- Fig 3: pareto.pdf

需要新增:
1. B* vs N 曲线
2. R 轨道数 vs N 表/图 + 暴力枚举验证
3. V1 vs V2 双柱对比图
4. 方案一 vs 方案二可行域图
5. 约束瓶颈演化图（B 增长时切换序列）
6. 影子价格条形图 + 投资优先级排序表
7. 灵敏度曲线图（3 个 CSV → t* vs RHS 乘数）
8. 约束耦合矩阵表（拓扑 × 场景 ✓/✗）
9. 热保真度对比表
10. L0 vs L1 一致性图
11. 路由间隙条形图

## D. 缺失项汇总（按优先级）

**P0 — 一切实验的前提：**
1. **V2 LP 引擎** — 固定 D^(r) + 包络 L + 可行性形式
2. **B* 二分搜索** — V2 §6.2
3. **Aut(G) 计算与轨道枚举** — 无任何实现
4. **修复 validate_lp.py 或重写为 V1 vs V2 对比**

**P1 — 论文核心数据：**
5. 对偶变量提取
6. RNB 检查器（割条件、Clos 条件）
7. LP 内 L1 热网络约束（当前只有 L0 全局功率密度）
8. L0 性能约束（二分带宽）+ 精度梯度切换

**P2 — 加分项：**
9. 热保真度对比实验脚本
10. 路由仿真 / 最优性间隙
11. 所有新增图的绘图脚本
