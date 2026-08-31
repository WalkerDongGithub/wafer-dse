# 传热模块全景（thermal-module-catalog）

> DomainExpert 产出，2026-08-21。master（作者）指令：传热模块全景 + 散热路径变化视角 + schema 约束清单——用于核对 CodeEngineer 的 YAML schema（缺不缺模块/字段/可读性）。
> 权威基准：`thermal-g-construction.md`（G 构建逻辑）+ `thermal-network-survey.md`（调研）+ `thermal-network-raw-materials.md`（原始材料）+ 经书 V5 §2.6/§2.7 + AnalyticNetworkBuilder 现状。
> 用途：给代码加手动配置——物理配置在 config，ThermalNetwork 组装逻辑由邻接/规格配置生成；用户层一眼看懂传热网络运行逻辑；3D 与 2.5D 共享同一 schema；暂不接 Model。

---

## 0. 总形式（一切模块的落点）

$$
\mathbf{G}\mathbf{T} = \mathbf{P} + \mathbf{b}, \qquad T(\mathbf{P}) = \max_i (\mathbf{G}^{-1}(\mathbf{P}+\mathbf{b}))_i
$$

- **每个传热模块** = 一组支路（进 G 的非对角/对角）+ 边界贡献（进 b）；
- **G 是 M-矩阵的条件**：每个节点至少有一条到环境的散热路径（对地支路）⟹ 严格对角占优 ⟹ $\mathbf{G}^{-1} \ge 0$（T 是 P 的凸函数）；
- 模块 = 节点/支路/散热的**可配置声明**，组装逻辑由配置生成（作者：物理配置在 config，不硬编码）。

---

## 1. 模块目录（每个模块：物理意义 / 热阻公式 / 参数 / G 落点）

> 单位约定：热导 [W/K] 进 G；热阻 [K/W] 先取倒数。所有参数来自 config YAML 或文献（见 thermal-g-construction §5 参数来源纪律）。

### A. die 纵向散热路径（对地支路，进 G 对角 + b）

| 模块 | 物理意义 | 公式（W/K 或 K/W） | 参数 | G 落点 |
|---|---|---|---|---|
| **A1 R_vert（die→环境，基础）** | die 纵向集总散热到环境（2.5D 链 die→μbump→interposer→C4→substrate→ambient） | $g_{\text{vert}} = 1/R_{\text{vert}}$，$R_{\text{vert}} = R_{\mu\text{bump}}+R_{\text{inter}}+R_{C4}+R_{\text{sub}}$ | R_vert [K/W]（YAML） | $G_{ii} += g_{\text{vert}}$；$b_i = g_{\text{vert}} T_{\text{amb}}$ |
| **A2 散热板/heat sink（加装 → 路径变化）** | 在 die/封装上加散热板，新增一条低阻纵向路径到环境——**传热路径变化**（从 substrate 主路径变为散热板主路径）；**heatsink 是实体节点（有自身温升），非固定温度边界** | $R_{\text{hs}} = R_{\text{spread}} + R_{\text{conv}} = R_{\text{spread}} + 1/(h \cdot A_{\text{fin}} \cdot \eta_{\text{fin}})$；$g_{\text{hs} \to \text{amb}} = 1/R_{\text{hs}}$ | R_spread（Lee 扩散模型，热源面积比）；h [W/(m²·K)]；A_fin [m²]；η_fin（翅片效率 = tanh(mL)/(mL)，m=√(2h/(k_fin·t_fin))） | **heatsink 为节点**（进 G）：$G_{\text{hs,hs}} += g_{\text{hs} \to \text{amb}}$；die→heatsink 经 TIM/lid 边；$b_{\text{hs}} += g_{\text{hs} \to \text{amb}} T_{\text{amb}}$——**不消元进 b**（有自身温升 T_hs − T_amb = R_hs·Q） |
| **A3 TIM/lid（FCBGA 链）** | die→TIM→lid 的纵向链（有机封装） | $g_{\text{TIM/lid},i} = 1/(R_{\text{TIM}} + R_{\text{lid}})$ | TIM 厚度/导热率、lid 厚度/导热率 | $G_{ii} += g_{\text{TIM/lid},i}$（并入 R_vert 链或独立对地支路） |
| **A4 背面冷却 h（晶圆级）** | die 网格背面整体冷却（水冷/风冷冷板） | $g_{\text{vert},i} = h_{\text{cooling}} \cdot A_{\text{node},i}$ | h [W/(m²·K)]（自然 5-25/风冷 25-250/水冷 10³-10⁴）；A_node [m²] | $G_{ii} += g_{\text{vert},i}$；$b_i = g_{\text{vert},i} T_{\text{coldplate}}$ |

### B. die 间横向（非对角支路，进 G 非对角）

| 模块 | 物理意义 | 公式（W/K） | 参数 | G 落点 |
|---|---|---|---|---|
| **B1 面邻接（半单元串联）** | die 间横向热耦合（经 interposer + underfill） | $G_{\text{lateral},ij} = k_{\text{inter}} \cdot \text{overlap}_{ij} \cdot t_{\text{inter}} / (\frac{d_i}{2}+\frac{d_j}{2}+\text{gap}_{ij})$ | k_inter [W/(m·K)]（硅 130-150）、overlap [m]、t_inter [m]、gap [m] | $G_{ii} -= G_{\text{lateral},ij}$；$G_{ij} = -G_{\text{lateral},ij}$ |
| **B2 underfill 系数** | underfill 横向弱耦合修正 | $\alpha_{\text{underfill}} \in (0,1]$ 乘 B1（k_underfill ≈ 0.2–0.5 远小于硅） | k_underfill [W/(m·K)]（待核实） | 修正 B1 的 k_eff |

### C. 2.5D interposer 特有

| 模块 | 物理意义 | 公式 | 参数 | G 落点 |
|---|---|---|---|---|
| **C1 μbump 热阻** | die→interposer 微凸点纵向热阻 | $R_{\mu\text{bump}} = t_{\mu}/(k_{\mu} A_{\text{bump,total}})$ | pitch/高度（UCIe 45μm，YAML）、k | 并入 A1 R_vert 链 |
| **C2 C4 热阻** | interposer→substrate 焊球热阻 | $R_{C4} = t_{C4}/(k_{C4} A_{C4,\text{total}})$ | C4 pitch、k | 并入 A1 R_vert 链 |
| **C3 interposer 横向扩散** | interposer 平面内热扩散（die 间 + 边缘） | 即 B1（k_eff 含 interposer 面内扩散） | k_inter | B1 |

### D. 3D 堆叠特有

| 模块 | 物理意义 | 公式 | 参数 | G 落点 |
|---|---|---|---|---|
| **D1 TSV 垂直线链** | 层间 TSV 阵列纵向 | $R_{\text{TSV,array}} = R_{\text{via}}/N_{\text{vias}}$，$R_{\text{via}} \approx t_{\text{via}}/(k_{Cu} A_{\text{via}})$，k_Cu ≈ 400 | TSV 直径/高度/密度 | G 扩维：相邻层同位置 die 间纵向支路 |
| **D2 hybrid bonding** | 层间 HB 极低热阻（μm 间距） | $R_{HB} \approx$ 极低（待核实） | HB pitch | 同 D1（或集总近似并入 R_vert） |
| **D3 层间横向** | 各层独立横向面邻接 | 同 B1（每层） | 各层 k/layout | 每层块内非对角 |

### E. substrate/PCB 与环境边界

| 模块 | 物理意义 | 公式 | 参数 | G 落点 |
|---|---|---|---|---|
| **E1 substrate/PCB 平面扩散** | substrate/PCB 面内扩散（2.5D/FCBGA） | 平面扩散 R（多跳，同 B1 大网格） | k_sub、厚度、面积 | 节点（interposer 挂载点）横向支路 |
| **E2 环境边界（ambient 节点）** | 环境/冷板温度节点 | $b = g_{\text{vert}} \cdot T_{\text{amb}}$（对地） | T_amb [K]、T_coldplate [K] | 进 b（非变量）；不建环境节点（集总） |

---

## 2. 散热路径变化视角（用户可读逻辑）

**核心思想**：每个模块 = 一条（或一组）散热路径；加/换模块 → G、b 哪里变、热量怎么走——写成"逻辑"而非公式堆砌。

### 2.1 加散热板（A2）→ 传热路径变化

- **加之前**：die 热量走 substrate 路径（die→μbump→interposer→C4→substrate→ambient）——一条纵向链，$G_{ii}$ 只有 $g_{\text{vert}}$；
- **加散热板后**：die 顶面新增一条低阻路径（die→TIM/界面→散热板→环境）——$G_{ii} += g_{\text{sink},i}$，$b_i += g_{\text{sink},i} T_{\text{amb}}$；
- **传热路径变化**：热量从"substrate 主路径"变为"散热板主路径"（若 $g_{\text{sink}} \gg g_{\text{vert}}$，结温显著下降）——**加散热板 → 路径变化**的直观体现；
- **G/b 落点**：只动 $G_{ii}$（对角）与 $b_i$，非对角不变（横向耦合不受影响）。

### 2.2 换 3D 层间 bonding（D1 TSV → D2 HB）→ 路径变化

- **TSV**：层间纵向热阻较高（$R_{\text{TSV,array}}$ 有限）——层间传热受限，顶层散热为主；
- **换 HB**：$R_{HB}$ 极低（μm 间距大面积并联）——层间近热短路，热量横向扩散 + 双面散热可行；
- **G 落点**：层间纵向支路电导从 $1/R_{\text{TSV}}$ 变为 $1/R_{HB}$（大幅增大）——**换 bonding → 层间路径阻力变化**；
- **集总近似**：若纵向热主导，整堆叠压成一条垂直线链（$g_{\text{vert}} = 1/\sum_l R_{\text{vert}}^{(l)}$），层间细节不可见——schema 需能表达"集总 vs 显式"两种层级。

### 2.3 2.5D → 晶圆级 → 3D：模块组合差异

| 视角 | 2.5D | 晶圆级 | 3D |
|---|---|---|---|
| 节点 | N die | 大 N die 网格 | K 层 × N die |
| 纵向 | A1 R_vert（substrate 链）+ 可选 A2 散热板 | A4 背面冷却 h（整体） | D1/D2 层间链 + 顶层散热 |
| 横向 | B1 面邻接（interposer） | B1 大网格多跳 | D3 各层横向 |
| 环境 | E2 ambient（b=g_vert·T_amb） | E2 coldplate（均匀） | E2 顶层/双面 |
| b 形态 | 每节点 g_vert·T_amb | 均匀 g_vert·T_coldplate | 顶层散热 b |

**用户读法**：改 config 的"纵向模块"（A1↔A2↔A4）或"层间模块"（D1↔D2），G 的对角/层间支路变，传热路径变——schema 应让这些模块选择一目了然。

---

## 3. schema 应满足的约束清单（3D/2.5D 同一 schema）

| # | 约束 | 说明 |
|---|---|---|
| 1 | **3D/2.5D 同一 schema** | 同一 YAML 结构表达两种堆叠：2.5D = 单层（无 layers 维度）；3D = 多层（layers 数组）；纵向模块字段通用 |
| 2 | **节点/边/散热声明分离** | schema 三段：`nodes`（die/层位置）、`edges`（横向邻接/层间支路，引用节点）、`cooling`（每节点散热方式）——组装逻辑 = 三段读配置生成 G、b |
| 3 | **每节点散热方式可见** | `cooling` 段每节点显式声明（如 `{type: sink, R: ..., T_amb: ...}` / `{type: backside, h: ..., T_coldplate: ...}`）——用户一眼看到"这个 die 怎么散热" |
| 4 | **M-矩阵条件可表达** | schema 校验：每个节点必须声明 ≥1 散热路径（cooling 段非空）⟹ G 严格对角占优 ⟹ G⁻¹≥0（T 凸）——可加 schema 级检查 |
| 5 | **模块即配置项** | 每个模块 = 一个配置块（如 `vertical: {type: r_vert, R: ...}` / `lateral: {type: face_adjacency, k: ...}`）——加/换模块 = 改配置块，不碰代码 |
| 6 | **参数来源可溯** | 数值字段注明单位（W/K、K/W、W/(m²·K)、K）+ 来源（YAML/文献）——禁硬编码 |
| 7 | **集总 vs 显式层级** | 3D 可表达"显式多层"（layers + 层间支路）或"集总垂直线链"（stack_vert: R 总和）——schema 字段区分两层级（如 `3d: {mode: explicit|lumped}`） |
| 8 | **可读性** | 用户读 YAML 即懂传热网络逻辑（如"加散热板 → 路径变化"体现在 cooling 段新增 sink 块）——字段名直白（r_vert/gap/overlap/h 而非缩写鬼画符） |

---

## 4. 与 AnalyticNetworkBuilder 现状的衔接

- 现状：`AnalyticNetworkBuilder`（die 级粒度，$g_{\text{vert}}=1/R_{\text{vert}}$，$b = g_{\text{vert}} T_{\text{amb}}$，`_lateral_conductance` 面邻接）——对应模块 A1 + B1 + E2；
- 目标：组装逻辑由**邻接/规格配置文件生成**——schema（§3）把 A-E 模块变为配置块，builder 读配置组装 G、b；
- **暂不接 Model**：ThermalNetwork 构造灵活（模块任意组合），模型侧（SteadyStateModel）后续对接。

---

## 5. 建模依据注释（三件套纪律：理论依据 + 逻辑 + 局限；作者要求每个模型有依据）

> 每个建模决策必须带三件套。依据来源：`thermal-modeling-dimensions.md`（LiteratureSearcher 调研 v2）+ `thermal-network-survey.md` + `thermal-network-raw-materials.md`。

### 5.1 heatsink 节点化（作者纠正：heatsink ≠ ambient）

- **依据（理论）**：heatsink 热阻 = $R_{\text{spread}} + R_{\text{conv}}$ 串联——扩散热阻（Lee 模型，lee1995spreading/lee2008spread）+ 对流热阻（$1/(h \cdot A_{\text{fin}} \cdot \eta_{\text{fin}})$，Fourier + Newton 冷却定律，incropera）；翅片效率 $\eta_{\text{fin}} = \tanh(mL)/(mL)$，$m = \sqrt{2h/(k_{\text{fin}} t_{\text{fin}})}$（incropera 标准式）。
- **逻辑（为什么这样近似）**：紧凑 CTM 中 heatsink 普遍作为**单节点**（HotSpot 的 spreader/sink 层即单列节点；JEDEC Rθja 双热阻体系同类）——单节点取结到环境总热阻/平均温度，足以表达"加散热板 → 传热路径变化"与温升 T_hs − T_amb = R_hs·Q。
- **局限（何时不成立）**：① 自然对流（h 低、η_fin 显著 <1、非均匀）或大翅片/多热源（温度场非均匀）需**多节点/翅片级**或 CFD；② 大面积梯度显著需扩散修正（多节点 R_spread 细化）；③ 仅当 heatsink 温升可忽略（Q 小或 R_hs 极小）才可并入 b 作固定边界近似（须说明条件）。

### 5.2 3D 集总 stack（vs 显式展开）

- **依据（理论）**：纵向热主导时，层间 TSV/HB 垂直线链可串联（$R_{\text{vert}} = \sum_l R_{\text{vert}}^{(l)}$，Fourier 串联）；TSV 阵列并联（$R_{\text{TSV,array}} = R_{\text{via}}/N_{\text{vias}}$）。
- **逻辑（为什么这样近似）**：快速估计——每堆叠一条垂直线链（g_vert = 1/ΣR_vert^(l)），横向按层聚合；避免 K×N 节点扩维，秒级求解。
- **局限（何时不成立）**：① 层内温度不均；② TSV 密度低（纵向热阻不可忽略）；③ 层间横向耦合强（需显式展开 K×N + tsv/hybrid 边）；④ 需逐层结温（每层 T_max 独立约束）时须完整形态。**实现侧留判据**：层间横向电导/纵向电导比值阈值（thermal-g-construction §2，3D 扩展时加）。

### 5.3 传热图支路标注纪律

- **每张传热图**（FigureArtist）：图上**每个支路标注物理路径类型**（传导/对流/边界）+ 热阻值有几何+材料来源（如 "die→TIM→heatsink：传导，R_TIM=t/(k·A)，t=50μm k=5 W/mK"；"heatsink→ambient：对流，R=1/(h·A_fin·η_fin)，h=2000 W/m²K"）。
- **逻辑**：读者从图上一眼看懂"这条路是什么物理机制、值从哪来"——禁"看起来合理但无来源"的数字。
- **局限**：图示值为配置默认/文献标定，最终以 config YAML 为准（参数评审后更新）。

### 5.4 三件套快速参考（每模块）

| 模块 | 依据（理论） | 逻辑（近似） | 局限（不成立时） |
|---|---|---|---|
| A1 R_vert | Fourier 串联 | 纵向链集总（die 级粗粒度） | 层内温度不均/多路径 |
| A2 heatsink 节点 | R_spread+R_conv（Lee+翅片） | 单节点紧凑（CTM 标准） | 自然对流/大翅片/强梯度需多节点 |
| A3 TIM/lid | Fourier 串联（薄层） | 并入垂直链 | 层厚大/热容显著时需独立 |
| A4 背面冷却 h | Newton 冷却（h·A） | 每节点均匀 g_vert | 冷却不均/边缘效应 |
| B1 面邻接 | Fourier 横向（半单元串联） | die 级横向耦合 | 细粒度梯度/underfill 复杂 |
| C1/C2 μbump/C4 | Fourier（t/(kA)） | 并入 R_vert 链 | 高密度阵列热耦合 |
| D1/D2 TSV/HB | 并联（R_via/N_vias）/HB 低 R | 层间纵向支路 | 密度不均/三维热流 |
| E2 ambient | Dirichlet/对流 | 消元进 b 或 g·T_amb | heatsink 温升不可忽略时不得消元 |

---

## 6. 版本记录

- v0.1（2026-08-21）：传热模块全景（模块目录 A-E / 散热路径变化视角 / schema 约束清单 / 现状衔接）。
- v0.2（2026-08-21）：建模依据注释（三件套：依据+逻辑+局限；heatsink 节点化纠正、3D 集总、传热图支路标注纪律）——依据 thermal-modeling-dimensions.md（Searcher 调研 v2）。
