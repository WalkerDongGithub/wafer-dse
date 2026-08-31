# ISCA 论文结构骨架（paper-skeleton）

> Phase 0 产出（DomainExpert，2026-08-20）
> 目标会议：ISCA（双栏 10pt；正文约 12 页含图，参考文献另计）
> 故事线：两层 DSE —— 外层离散枚举（借用成熟 chiplet DSE 流程）+ 内层给定构型可行性模型（扩展比包络 + 三层实体 + 跨层耦合 C1-C4）+ 二分取最大可行 B*
> 定案表述：B = 有服务质量保证的额定出入口带宽；整体问题非凸但存在可多项式时间求解的全局最优解、不需启发式（不强调"是 LP"）；扩展比包络 = 拓扑不变量
> 权威依据：V5（唯一权威模型文档）、insight.md（7 条）、notes/INSIGHT_READING.md（解读）、notes/PAPER_TEAM_WORKFLOW.md（总纲）

## 0. 全局纪律（贯穿各章）

- 主叙事 = insight 1-7 的"道"；"术"（LP 细节、M-矩阵、二分）进理论章/附录。
- 不引复杂性战争：外层离散层保持 NP-hard（借用成熟流程），内层强调"不需启发式、存在可多项式时间求解的全局最优解"。
- 热只引 MFIT（*Multi-Fidelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures*, ACM TODAES，DOI 10.1145/3765905，作者表以核验终稿为准），不展开传热学。
- 引用纪律（Gate② 核正）：Räcke 2002 = **FOCS 2002**（非 STOC）；3D-ICE = **ICCAD 2010**；HotSpot = **IEEE TVLSI 2006**（Huang et al.）；Azar et al. = JCSS 2004；Chang/McKeown admissible-traffic = INFOCOM'00/ToN'99。
- 二分/单调性不上论文台面；"低 B 面积约束恒松（可加无逻辑硅）"为架构侧自洽叙事。
- 术语统一：B 正名"额定出入口带宽"；"无阻塞"仅作 QoS 语义（RNB）。
- 每章每段须能标注支撑的 insight 编号（Gate④ 纪律检查依据）。

## Abstract（一段，~200 词）

- 问题：晶圆级交换机设计空间（拓扑×布局×封装×互联）大、多因素（热/电/几何/性能）强耦合，而 wafer-scale 缺这样的 DSE，其交换机 DSE 更困难。
- 方法：两层 DSE——外层离散枚举复用成熟 chiplet DSE 流程；内层给定构型可行性模型（扩展比包络 + 三层物理实体 + 跨层耦合）。
- 主张：整体问题非凸，但存在可多项式时间求解的全局最优解，不需启发式；输出 B\* = 有 QoS 保证的额定出入口带宽，作为解的质量量化指标。
- 结果预览：case study 中 B\* 排序、耦合 vs 分离对比的 1-2 个数字。

## 1 Introduction

- 1.1 背景（insight 4 引子）：晶圆级系统兴起（Cerebras / Tesla Dojo / 晶圆级网络交换机 Chen ISCA'24），交换机是核心组件，设计空间爆炸。
- 1.2 问题：综合决策困难——拓扑、路由、功耗、面积、信号完整性、封装、节点布局多因素耦合；既有工具多聚焦单维或外挂热分析、晶圆级网络工作只做特定维度联合分析（gap claim 用 xxx vs xxx 框架限定，见 §4.0 与 contributions C1；由 LiteratureSearcher 坐实）。
- 1.3 gap：chiplet 界已有成熟 DSE（RapidChiplet / FireLink / FPIA），但 wafer-scale 缺这样的 DSE；面向 wafer-scale switch 的 DSE 更困难（三层实体、SerDes/I2I 跨层、晶圆级热/几何耦合）——核心论点，每环答"凭什么"。
- 1.4 我们的方法（一段）：两层 DSE 一句话 + 为什么这样分（内层数学上可全局最优，外层借用成熟流程）。
- 1.5 贡献声明（4 条，见 contributions.md）。
- 1.6 结果预览与论文组织。

## 2 Background & Motivation

- 2.1 晶圆级交换机与三层物理实体（die / Interposer / Substrate；D2D 组内 UCIe / I2I 组间 SerDes）。
- 2.2 为什么现有 DSE 不够：chiplet DSE 不覆盖 I2I/Substrate 层与跨层耦合（C1-C4 的物理必要性）；wafer-scale switch DSE 更难的难点拆解。
- 2.3 关键观察：筛选而非优化（insight 1）；B 作为解的质量量化指标（insight 2）；B = f(要求, 约束)（insight 3，旋钮直觉 + 例子：额定功耗 vs 峰值功耗工况）。
- 2.4 动机示例（可选）：一个 toy 例子展示"可行/不可行"二元判断的不足（insight 2 的灰色地带）。

## 3 Related Work（LiteratureSearcher 提供引文与对标矩阵）

- 3.1 晶圆级系统与交换机：Cerebras、Dojo、Chen ISCA'24、Feng & Ma SC'24（DOI 10.1109/SC41406.2024.00102）——差异（无 DSE / 单点设计）。
- 3.2 chiplet DSE 工具：RapidChiplet / FireLink / FPIA——外层流程的对标基线（借用而非重造）。
- 3.3 扩展比包络先例（验证而非防先例，Gate② 定稿英文表述）："Per-link worst-case load analysis under oblivious routing has a rich lineage—Valiant & Brebner's randomized load balancing [STOC'81], Räcke's congestion-competitive oblivious routing [FOCS'02, STOC'08], and Azar et al.'s polynomial-time LP for optimal oblivious routing [JCSS'04]; Birkhoff–von Neumann switching shows worst-case admissible traffic collapses to permutation matrices [Chang INFOCOM'00]. We build on these as **verification**: the expansion-ratio envelope is their per-link, topology-only specialization, and our contribution is integrating it as the performance–physics decoupling bridge in a wafer-scale switch DSE, with a per-link LP whose vertices are permutations and a full thermal/electrical/geometric constraint layer driven by B·L_e." **区分点**（防"重命名"质疑）：Räcke 竞争比是全局单标量（最坏链路拥塞对最优的比）；我们的包络是**逐链路最小扩展比向量**，用途是**与物理约束解耦的 DSE 桥梁**（性能模型独立预解 → 物理模型以 B·L\* 为输入），不是近似算法分析；Azar 的 LP 求最优路由，我们的子 LP 是固定路由下求每条链路的扩展比下界。
- 3.4 热建模：MFIT（ACM TODAES，DOI 10.1145/3765905）、HotSpot（IEEE TVLSI 2006）、3D-ICE（ICCAD 2010）——只引不展开（热单维工具独立于网络性能 DSE，属 §1.2 gap 论据）。
- 3.5 定位小结：我们填补什么（一段）。

## 4 Model（方法章，核心；以"输出与用途"为主线）

- 4.0 两层 DSE 总览（图 1：两层架构 + 物理参数接口解耦；insight 1 筛选定位）。**定位措辞（Gate② 定稿）**：不写"前人全分离决策"；表述为"chiplet DSE 多聚焦性能/成本/布局单维（热外挂或缺失）；热感知工作独立于网络性能 DSE；晶圆级网络工作（Chen ISCA'24、TickTock ISCA'25）做了特定维度联合分析，但未将热-电-几何-性能纳入单一模型并输出带 QoS 保证的 B\*"（xxx vs xxx 框架，见 contributions C1）。
- 4.1 外层：离散枚举层——拓扑族 × 布局 × 封装工艺 × 互联标准；借用成熟 chiplet DSE 流程（对标基线）；保持 NP-hard，不声称复杂度结论。
- 4.2 内层：给定构型 → 可行性模型。
  - 4.2.1 扩展比包络（性能侧，insight 6）：L\* 只依赖拓扑+路由+要求模型，与 B 及物理无关，可独立预解；逐链路子 LP + Birkhoff–von Neumann 顶点论证（细节进附录 C）。
  - 4.2.2 三层实体物理约束（模型规范，按 V5 v5.21/v5.24 完整表述；**研究对象聚焦"一个 interposer 的设计"**——立项 wafer DSE 但研究重心 = 单个 interposer 内的 die 布局/布线/热/电联合设计）：die 段（功耗/布线/热/面积）、I2I 段（C4/Substrate 热）、跨层耦合 C1-C4——热、电、几何、性能在单一模型联立（insight 4）。**布线 (2d) 与 die 面积上界 (2f) 为一级约束**：power/gnd 与信号走线共享 interposer RDL，布线饱和常先于 bump 绑定；$A_{\text{die}}(B)=d(B)^2 \le A_{\max}$（α_d>0 时面积约束直接给出 B 上界）。**标准耦合案例（作者 2026-08-21 定案，insight 4 靶子）**：Power/GND 走线需求 ∝ P(B) 增长顶满 RDL 容量 → (a) 提高散热 或 (b) 降性能（减带宽）换布线布得下——"功耗—散热—布线/性能"三方牵制。实现覆盖：C1 + die 级热 + 扩展比包络 + die 缩放 + B\* 二分 + 布线/面积（已接入 build_scenario，E3B v2 已验证）；**power 走线项（P(B) 进布线 rhs）为模型规范（V5 §2d），小实验验证中**（验证阶段策略【0】）；C2（C4 电源）/ C3（die→inter 功耗聚合）/ C4（sub→inter 温度反馈）/ sub 热方程仍标注"模型规范，接入为未来工作"。
  - 4.2.3 B\* 的确定：B 为决策标量（QoS 保证：端口负载 ≤ B 时无阻塞）；**QoS 语义来源**：BvN 交换机 admissible-traffic 框架（Chang INFOCOM'00、McKeown ToN'99，最坏流量坍缩为置换矩阵）——B\* 表述限定为"DSE 语境下的质量标尺"（同设置同端口数 B\* 排序），不写"首次提出可承诺带宽"；固定 B 可行性精确可判 → 外层二分取最大可行 B\*（二分细节不上台面）。
- 4.3 模型性质（insight 7）：整体问题（含 B）非凸（die 缩放二次项），但存在可多项式时间求解的全局最优解——不需启发式（固定 B 为 LP、多项式可解，二分 O(log) 次）。
- 4.4 求解与实现（一段 + 附录 A/B；不展开算法细节）。

## 5 Evaluation（EvalDesigner 设计实验，DataSteward 出数据）

- 5.1 实验设置：拓扑集、物理参数（YAML 对齐 UCIe/OIF-CEI）、baselines（分离决策基线、无 DSE 基线）。**实验范围覆盖主模型约束**：C1 + 热 + 包络 + die 缩放 + 布线/面积（已接入 `build_scenario`，E3B v2 已验证，git 5008ed0/f680fc5）；C2-C4/sub 热等规范约束不在实验范围（未来工作，Discussion §6.3 呼应）。
- 5.2 扩展比包络与物理解耦（概念图）：包络 = 拓扑不变量（与 B、物理无关）作为模型定义（insight 6 语义），概念示意其与物理侧解耦（性能独立预解 → 物理模型以 B·L\* 为输入）——**概念图，非数据图，无验证/演示/判据/数字**。
- 5.3 B\* 与设计点排序（insight 2/5）：同设置同端口数下按 B\* 排序；严格约束下接近目标 → 放宽后很可能可行。**口径（DataSteward 数据修订）**：ucie-32g 下热约束主导（热衰减比 ≈ 0.04-0.05，B\* 被压到 bump 档 ~4-5%），图 4 实为"热约束下排序"——图 4 标注绑定约束族（therm_d\*），避免误读为纯拓扑排序；端口 4 组 Mesh(2)/Torus(2)/KaryNCube(2,2) 图同构（2×2 网格 = 2×2 环 = 2-ary 2-cube），B\* 逐位相同属必然，该组注明"同构图"或由 EvalDesigner 换非平凡 4 端口拓扑。
- 5.4 统一模型 vs 分离基线（insight 4/7，**双阶段定稿**）：**E3B v1（已做）**——无布线/面积子集（线性物理约束、L 钉包络、α=β=0 几何恒松）下分离≡联合（rel_diff=0，B\*_joint=min(B\*_bump,B\*_therm) 解析成立），作为诚实基线（进附录）；**E3B v2（已跑，fixed_paths 分离基线，缓存键修复后冷跑定稿）——C3' 通过**：10/72 构型 rel_diff > 1%，**真分歧在布线饱和域（lanes=100）**：Mesh(3) 0.154、Torus(3) 0.190、KaryNCube(2,3) 0.352/0.266；默认域 KaryNCube(2,3) 0.087（8 条两路径链路固定首路径默认容量即拥塞）——机制 = "固定首路径拥塞 vs 联合绕行"（分离决策各因素独立固定方案、不做跨因素联合优化；Mesh(3) lanes=100：B_sep=1075 vs B_joint=1270）。**"分离决策在布线/面积下产生分歧"主张成立**。**实验核心轴（作者 2026-08-21 指令【2】）**：围绕**标准耦合案例的可量化表现**——散热增强释放多少带宽（热参数 R_vert 扫描 ↔ B\*）、降性能（减带宽）缓解多少布线饱和（power 走线项进布线后 B ↔ 布线容量松弛）——作为"功耗—散热—布线/性能"三方牵制的量化证据（小实验，验证阶段策略）。叙事：单一模型统一求解的价值 = 一致性保证 + 全局最优 B\*（insight 7）+ 布线/面积耦合要素的单一数学载体；v1 等价性推导细节进附录。**C4' 补充**：布线饱和先于 bump/therm 绑定在 Dragonfly 类（单路径拓扑）成立（另一耦合机制，与 C3' 互补，拓扑域界定如实标注）。**口径注（2026-08-21 修正）**：旧"Mesh(3) 默认域 rel=0.80"系缓存污染（缓存键未含容量数组），删除；强分歧与耦合显现域一致 = 布线饱和域（lanes=100）。
- 5.5 灵敏度分析（insight 3）：要求旋钮（QoS 严格度）× 约束旋钮（额定/峰值工况）→ B\* 变化表/图。
- 5.6 可扩展性与求解开销：规模 vs 求解时间（LP 多项式 + 二分对数次）。

## 6 Discussion

- 6.1 B\* 作为后续精调的量化基石（insight 5）：决策权从 DSE 交给设计师；排序逐点论证；"很可能/先验搜集"限定。
- 6.2 筛选哲学与边界（insight 1/7）：内层全局最优 vs 外层 NP-hard 的边界；假设 A1-A8 的诚实声明；不承诺真实物理必然可行。
- 6.3 未来工作（定稿 2026-08-21）：① D2D/I2I **分割比旋钮 ρ**（一个大 interposer vs 多个小 interposer，V5 §9 模型演进项——分割比参与决策后两层包络的负载分配变化）；② **C2/C4/sub 热全接入**（C4 电源、die→inter 功耗聚合、sub→inter 温度反馈、sub 热方程，对齐 §4.2.2 规范约束，多 interposer 场景）；③ **真实物理验证**（仿真/流片级对标，insight 5 的"很可能可行"落地）。布线/面积已进主模型（v5.21/v5.22），不在未来工作之列。

## 7 Conclusion

- 复述问题 → 方法 → 主张 → 效果；一句展望。

## 附录

- A：内层 LP 完整表述（§2 die 段 / §3 I2I 段 / §4 C1-C4，按 V5）。
- B：二分 + 复杂度论证（多项式时间、不需启发式的形式化）。
- C：Birkhoff–von Neumann 顶点论证与包络构造。

## 图清单（FigureArtist，先概念图后数据图）

- 图 1：两层 DSE 框架总览（概念图，§4.0）。
- 图 2：三层物理实体与跨层耦合示意（概念图，§2.1 / §4.2.2）。
- 图 3：扩展比包络与物理解耦（**概念图**，§5.2——包络为拓扑不变量的概念示意，非数据图）。
- 图 4：B\* 排序（数据图，§5.3）。
- 图 5：耦合 vs 分离对比（数据图，§5.4）。
- 图 6：灵敏度（数据图，§5.5）。
