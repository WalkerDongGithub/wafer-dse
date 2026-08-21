# V5 实现对应与参考文献（释经）

> **释经文档**：本文件承载 `notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md`（经书）的**派生内容**——2026-08-21 经书/释经拆分时从 v5 移出：
> ① §8 与实现的对应表 ② §10 依据与参考文献 ③ §2(2d) power 走线项的双分支推导细节 ④ fixed_paths 分离基线说明。
> 经书只回答"模型是什么"；本文件回答"模型怎么落的代码、物理依据是什么、推导细节怎么来的"。

---

## 1. 与实现的对应（原 v5 §8）

| 本文档（V5 经书） | 代码 | 状态 |
|--------|------|------|
| §7.3 性能子 LP + 均匀分流 | `src/problem/models/perf/traffic_based/_oblivious.py`（`ObliviousValiantModel`） | ✅ 已实现，test04 锚定 |
| §7.3b R_peak 单对流量包络 | 同上（`ObliviousValiantModel` `requirement="peak"`：闭式 $L_e^{*}=\max_{(i,j)} c_{ij}^{e}$，V5 v5.22） | ✅ 已实现（git 5008ed0），test 锚定 |
| §2.8 C_rated（$\beta_P:=0$） | `src/problem/builder/_scenario.py`（`rated` token，`beta_p` 程序化覆盖 BumpModel/SteadyStateModel；未动共享 YAML） | ✅ 已实现（git 5008ed0） |
| §2 (2c) + §4 C1（μbump） | `src/problem/models/phys/bumps/_bump.py`（`BumpModel`） | ✅ 已实现，test09/test10 手算锚点 |
| §2.8 die 缩放 | `src/physical/params.py`（`DieParams`）、`src/physical/config/spec_bump.py`（`DieBumpBudget`） | ✅ 已实现，test11 锚定 |
| §2 (2e) 热方程（L1 稳态） | `src/problem/models/phys/therm/_steady_state.py`（`SteadyStateModel`）+ `src/physical/layout/thermal_network/`（`AnalyticNetworkBuilder`，MFIT 式面邻接 + 集总 $R_{\text{vert}}$） | ✅ 已实现（die 级约化：$b = g_{\text{vert}}T_{\text{amb}}$，无显式 $\mathbf{T}_{\text{inter}}$/$\mathbf{T}_{\text{sub}}$ 回路） |
| L0 全局功率密度 | `src/problem/models/phys/therm/_temp_limit.py`（`GlobalPowerModel`） | ✅ 已实现（初筛用） |
| §3 (3c) + §4 C2（C4） | `src/problem/models/phys/bumps/_c4.py`（`C4Model`，$B\sum_e \frac{1}{\lambda_e}L_e \le N_{\text{SerDes}}$，$\lambda_e$ 为 lane 速率） | ⚠️ 已实现但未接入 `build_scenario` |
| §2 (2d) interposer 布线 | `src/problem/models/phys/wiring/`（`WiringModel`，edge/vert/C4-pad 三维容量；`fixed_paths: bool = False` 构造参数，`build_wiring_fixed` helper 公开导出；**power 走线项 `c_pwr_lane_per_w` 构造参数**） | ✅ 已接入 `build_scenario`（git 459a6ed，V5 v5.21 一级约束）；固定候选路径模式（git f680fc5/ed15196，E3B v2 分离基线布线因素，test19 锚定）；power 走线项（git 3ac0c50，V5 v5.25/v5.26，作者 round 21 耦合案例，test20 锚定） |
| §2 (2f) die 面积上界 | `src/problem/models/phys/area/`（`DieAreaModel`，$A_{\max}$ = interposer 面积 ÷ 芯粒数，随布局而定） | ✅ 已接入 `build_scenario`（git 459a6ed，V5 v5.21 一级约束） |
| §3 (3d) sub 热方程 + §4 C4 | — | ❌ 规范先行（多 interposer 场景启用） |
| $B^*$ 二分 | `src/problem/queries/bmax/__init__.py`（`BmaxQuery`） | ✅ 已实现 |

## 2. 依据与参考文献（原 v5 §10）

**物理/数学依据**：
- 稳态热传导线性性、M-矩阵保序性（$\mathbf{G}^{-1} \ge 0$）：传热学标准结果；热网络构建参考 Lukas Pfromm, Alish Kanani, Harsh Sharma, Parth Solanki, Eric Tervo, Jaehyun Park, Janardhan Rao Doppa, Partha Pratim Pande, and Ümit Y. Ogras, *MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures*, ACM TODAES（DOI 10.1145/3765905；arXiv:2410.09188）（`AnalyticNetworkBuilder` 的面邻接 + 集总垂直热阻公式）
- Birkhoff–von Neumann 定理（V5 §7.3 的顶点论证）：Birkhoff, *Three Observations on Linear Algebra*, Univ. Nac. Tucumán Rev. A 5 (1946) 147–151; von Neumann, *A Certain Zero-Sum Two-Person Game Equivalent to the Optimal Assignment Problem*, 1953
- 静态 oblivious Valiant 路由：Valiant & Brebner, *Universal Schemes for Parallel Communication*, STOC 1981

**参数数值依据**：`config/params/*.yaml` 为唯一参数源（不硬编码），与 UCIe 1.1/2.0 Spec（45μm bump、16/24/32 GT/s）、OIF-CEI-112G-VSR 对齐——见 `src/physical/config/spec_*.py` docstring。

**背景文献**：晶圆级交换机设计空间背景见 `notes/literature/LITERATURE_MAP.md`（含 Chen et al., *Waferscale Network Switches*, ISCA 2024 等 19 条论断的逐句支撑映射）。

**优先级约定**：V5（经书）> 代码 > `docs/paper/` LaTeX（下游产物）。冲突时改代码与论文，不改经书语义。

## 3. §2(2d) power 走线项推导细节（原 v5 说明，2026-08-21 移出）

Power/GND 走线占用 RDL 容量，与信号 lane 走线共享 edge/vert 容量：

$$
\sum_{l \in \text{经过 } e} \frac{B}{\text{lr}_l}\left(1 + c_{\text{pwr}} s^{\text{dyn}}_l\right) L_l + c_{\text{pwr}}\left(P_0 + \beta_P B\right) \le \text{cap}_e
$$

- $P_{\text{die}}(B) = P_0 + \beta_P B + P_{\text{dyn}}$（与 V5 (2c) 同源），$c_{\text{pwr}}$ 为 power 走线 lane 当量系数（W→RDL 容量占用，参数 YAML `c_pwr_lane_per_w`，默认 0 = 关闭）。
- **双分支（v5.26 修正，CodeEngineer 实现语义）**：$P_{\text{dyn}} = \sum_l s^{\text{dyn}}_l \frac{B}{\text{lr}_l} L_l$ 依赖 $L$（非常数）——折进 L 系数（信号 lane 越多 → P_dyn 越大 → power 走线越多，耦合完整）；$P_0 + \beta_P B$ 为常数（固定 B）→ rhs 扣减。固定 B 下仍线性（LP 结构不变，V5 §5.3/insight 7）。
- **耦合机制**：$\beta_P > 0$ 时 power 走线占用随 $B$ 增长 → 顶满 RDL → 必须 (a) 提高散热（$R_{\text{vert}}$↓ 松热约束）或 (b) 降性能（减 $B$ → 减 power 需求）——"功耗—散热—布线/性能"三方牵制（作者 round 21+ 指令【1】，insight 4 靶子，见 `notes/INSIGHT_READING.md` §4）。
- **fixed_paths 分离基线模式同用此项**（同一 $c_{\text{pwr}}$、同一 $P_{\text{die}}$ 口径——否则联合有 power 项、分离没有，不公平基线）。
- **参数域观察（v5.27，CodeEngineer 诚实报告）**：默认 β_P=0 时 rhs 扣减为常数（等价全边容量等量减，B\* 位置不变）；"power 顶满 RDL"可量化演示需布线饱和参数域（lanes_per_mm 小 + β_P 大）——E7 实验设计在该域找可量化表现。

## 4. 待定案去向（原 v5 §9 → `.dsh/team/decisions.md` 待决项）

- $\mathbf{G}_{\text{inter}}^{\text{amb}}$ 构建；$\mathcal{P}$ 显式矩阵形式；sub 热方程/C4 接入；D2D/I2I 分割比 $\rho$；die 缩放单调性验证——全部移入 `.dsh/team/decisions.md` 待决项（2026-08-21）。
