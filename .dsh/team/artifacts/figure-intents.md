# 图意图规格（figure-intents）

> DomainExpert 定内容与表达意图，2026-08-21（v0.2 更新：图 1 语义与 s4-model.md §4.0 对齐，图 2 与 §4.2.2 对齐；Two-Level DSE 术语统一）。FigureArtist 直接据此绘图（docs/paper/Img/）。
> 数据图（图 3-6）归 DataSteward 基础图 + FigureArtist 精美图；本文件只定**概念图**（图 1/图 2）意图。
> 权威依据：paper-skeleton §4.0/§4.2.2、V5 v5.25、INSIGHT_READING（术语纪律：B = 有 QoS 保证的额定出入口带宽；包络 = 拓扑不变量；不强调"是 LP"；two-level DSE 全文统一）。

## 图 1 —— Two-Level DSE 框架总览（§4.0，概念图，论文第一张图）

**表达意图**：让读者一眼看到"两层解耦的 DSE 架构"——外层离散枚举（借用成熟 chiplet DSE 流程）+ 内层给定构型可行性模型（耦合四约束族），两层经物理参数接口解耦。这是论文故事的骨架图，必须突出"筛选定位"、"单 interposer 聚焦"（round 21+ 指令【3】）与"解耦"。

**语义对齐（s4-model.md §4.0）**：
- 研究对象 = **the design of a single interposer**（一个 interposer 的设计——其 die、互连、与 substrate 的边界）；图面中心应是一个 interposer（含 die），而非整 wafer。
- 外层 = outer discrete enumeration layer：拓扑族 × 布局 × 封装工艺 × 互联标准（复用成熟 chiplet DSE 流程，不 reinvent）；
- 内层 = inner feasibility model for a given configuration：单一可行性模型耦合 performance / thermal / electrical / geometric 四族，输出 **optimal rated bandwidth B\***（有 QoS 保证）；
- 性能包络（expansion-ratio envelope）独立于物理计算（图内虚线框，拓扑不变量语义）；
- 筛选定位：输出"按 B\* 排序的可行构型集合"，**非 Pareto 面**。

**要素清单（自上而下）**：
1. **顶层：设计空间输入**——四个维度盒子：拓扑族（Mesh/Torus/KaryNCube/FullMesh/Dragonfly）× 布局（die 排布）× 封装工艺（2.5D/3D、RDL）× 互联标准（UCIe/OIF-CEI）。横向排列 4 盒 + "×" 表示笛卡尔积。
2. **外层（上）离散枚举层**：盒子标注"outer discrete enumeration（复用成熟 chiplet DSE 流程：RapidChiplet/FireLink 等对标基线）"——产出候选构型，保持 NP-hard、不 claim 复杂度。
3. **物理参数接口（中间解耦带）**：明确分隔带/接口符号，标注"physical-parameter interface（解耦）"——两层只传物理参数（die 尺寸、pitch、热阻、功耗系数），不传优化逻辑。
4. **内层（下）可行性模型**：盒子标注"inner feasibility model for a given configuration（性能 + 热 + 电 + 几何 四族耦合）"——内部可画三个小层（die 段 / I2I 段 / 跨层耦合段）示意三层实体。
5. **性能包络（侧边虚线框）**：标注"expansion-ratio envelope（拓扑不变量，独立预解）"——与物理侧解耦（insight 6）。
6. **输出（右下）**：B\* 标注"optimal rated bandwidth B\*（有 QoS 保证）"+ 箭头表示"按 B\* 排序 → 设计师逐点论证"（insight 5）。
7. **循环箭头**：外层枚举 ↔ 内层可行性检查之间的反馈（每个候选构型过内层 → 得 B\* → 排序），细箭头表示"筛选而非优化"（insight 1）。

**布局要点**：纵向三段式（输入 → 外层 → 内层 → 输出），物理参数接口作水平分隔带居中；离散枚举用"×"强化"空间大"；中心突出"一个 interposer"（die 阵列 + substrate 边界示意）；学术图干净风格（无 3D 装饰、无渐变、统一线宽、黑白可打印 + 少量强调色）。

**禁止**：不出现 "LP"/"linear programming"（按纪律不强调"是 LP"）；不出现二分搜索图示（二分不上台面）；不画 Pareto 前沿；不画整 wafer 全景（聚焦单 interposer）。

## 图 2 —— 三层物理实体与跨层耦合 C1-C4（§4.2.2，概念图）

**表达意图**：让读者理解"为什么单一模型"——三层物理实体（die / Interposer / Substrate）+ 四组跨层耦合（C1-C4）把热、电、几何、性能绑进同一模型；同时体现"布线饱和/面积上界是真正会绑定的耦合要素"（v5.21 定案）与"功耗—散热—布线/性能三方牵制"（作者 round 21+ 指令【1】）。

**语义对齐（s4-model.md §4.2.2）**：
- 三层 = die（D2D/UCIe）/ interposer（RDL 布线 power/gnd + 信号共享、C4）/ substrate（I2I SerDes、挂载点温度）；
- C1 μbump 跨层分配 / C2 inter 功耗→C4 数 / C3 die 功耗聚合→inter / C4 sub 温度→inter Ambient；
- 布线 (2d) + 面积上界 (2f) = 一级约束（"真正会绑定的耦合要素"）；
- 标准耦合案例（round 21+ 指令【1】）：power/ground 走线占用 RDL → 顶满 → (a) 提散热 (b) 降带宽——"power–cooling–wiring/performance triad"。

**要素清单**：
1. **三层实体（纵向堆叠）**：die 层（若干 die 方块，D2D UCIe 连接，标注"die 级：功耗/温度/μbump/面积上界"）；Interposer 层（平台承载 die，标注"RDL 布线 power/gnd + 信号共享、C4"）；Substrate 层（标注"I2I SerDes、挂载点温度"）。
2. **四组跨层耦合标注（带编号箭头）**：C1（die 侧 μbump 分配：I2I lane 挤压 D2D 信号预算）；C2（inter→C4 电源数）；C3（die→inter 功耗聚合）；C4（sub→inter 温度反馈 Ambient）。
3. **真绑定耦合要素（强调框）**：RDL 布线饱和（power/gnd + 信号共享）与 die 面积上界（A_die(B) ≤ A_max）——加粗/强调标注"一级约束：布线饱和 + 面积上界（先于 bump 绑定）"。
4. **标准耦合案例（标注环）**：power/ground 走线 ∝ P_die(B) 占用 RDL → 顶满 → (a) 提散热 (b) 降带宽——用箭头/环标注三方牵制（作者 round 21+ 指令【1】）。
5. **旁注**：性能侧（扩展比包络 L\*）虚线独立框一侧，标注"包络 = 拓扑不变量（与 B、物理无关，独立预解）"（insight 6）。

**布局要点**：纵向三层堆叠为主轴，C1-C4 带编号箭头横跨层间（C1/C4 斜跨、C2/C3 垂直）；虚线框放性能包络于侧边；强调框放布线/面积；标注环放三方牵制；学术图风格（同图 1）。

**禁止**：不出现具体数值/参数；不出现温度场云图（结构示意非数据图）；不画 G 矩阵/M 矩阵（数学细节进附录）。
