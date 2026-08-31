# 热阻网络调研（thermal-network-survey）

> **产出**：LiteratureSearcher（master 分派调研）
> **日期**：2026-08-21
> **边界**：定向轻量调研（串行、小规模），引用经 DBLP/CrossRef 核验；以经书 §2.6 与 `notes/IMPLEMENTATION_MAP.md` 为准。
> **核心问题**：不同封装构型的热阻网络长什么样，能否直接映射进 G·T=P+b（G 为 M-矩阵、G⁻¹≥0、die 级粒度）？

---

## 0. 模型形式锚定（经书 §2.6 + IMPLEMENTATION_MAP）

- 模型：$\mathbf{G}\mathbf{T}=\mathbf{P}+\mathbf{b}$，$\mathbf{G}$ 由**网格粒度**（die 级最粗）与**封装方式**（传热路径）两旋钮决定；$\mathbf{b}_{\text{die}}$ 常数（die 向散热板），$\mathbf{b}_{\text{inter}}$ 变量（Interposer 向 Substrate）。
- 实现：`AnalyticNetworkBuilder` = **MFIT 式面邻接（die 间 lateral）+ 集总 $R_{\text{vert}}$**，die 级粒度，$b = g_{\text{vert}}T_{\text{amb}}$，无显式 $\mathbf{T}_{\text{inter}}$/$\mathbf{T}_{\text{sub}}$ 回路（L1 稳态约化）。
- **M-矩阵性质的一般性**：任意无源电阻网络（节点间电导 + 节点对地电导）的导纳矩阵 = 图拉普拉斯 + 对角阵，严格对角占优 → M-矩阵、$\mathbf{G}^{-1}\ge 0$。四种封装构型的网络都是这类电阻网络——**形式总是可映射**，问题只在于节点/参数保真度。

## 1. HotSpot 热网络结构

- **形态**：网格化 compact R-C 模型——每个网格单元一个节点；每列一条**纵向支路链**（chip → TIM → heat spreader → heat sink → ambient，逐层 $R_{\text{vert}}$）；相邻单元间**横向支路**（面内扩散 $R_{\text{lateral}}$）。稳态求解 = 组装线性系统 $\mathbf{A}\mathbf{T}=\mathbf{P}+\mathbf{b}$ 后矩阵求解（$\mathbf{A}$ 即热导矩阵，正定/严格对角占优，M-矩阵性质成立）。
- **与我们的一致性**：HotSpot 的稳态形式**就是** $\mathbf{G}\mathbf{T}=\mathbf{P}+\mathbf{b}$；差异在粒度（单元级 vs 我们 die 级）与每列分层数（HotSpot 每列 chip/TIM/spreader/sink 四段 vs 我们集总单段 $R_{\text{vert}}$）。
- 引用：hotspot2006（Huang et al., TVLSI 2006，已入 bib）。结构描述为 HotSpot 标准叙述（论文 + 开源手册），细节公式待全文核对。

## 2. MFIT 网络形态（已被我们采用）

- **形态**（MFIT: Multi-FIdelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures, Pfromm et al., ACM TODAES, DOI 10.1145/3765905；arXiv:2410.09188）：2.5D/3D chiplet 的**多保真度**热模型族（16/36/64 个 2.5D chiplet、16×3 3D chiplet 上验证；"reduce execution times from days to mere seconds and milliseconds"）。die 为节点：**die 间 lateral 面邻接（经 interposer/underfill）+ 纵向集总热阻**（die→interposer→substrate 链）——正是 `AnalyticNetworkBuilder` 采用的"面邻接 + 集总 $R_{\text{vert}}$"形态。
- **一致性确认**：✅ 一致。我们实现的 die 级面邻接 + 集总 $R_{\text{vert}}$ + $b=g_{\text{vert}}T_{\text{amb}}$ 是 MFIT 网络的一个 die 级约化（L1 稳态、无显式 inter/sub 温度回路）；经书 §2.6 的"封装方式旋钮"对应 MFIT 中不同封装假设的支路参数。
- 引用：mfit2025（已入 bib）。

## 3. 封装构型 → 热阻网络对照表

| 构型 | 网络形态（节点/支路） | 关键热阻参数 | 边界条件 |
|---|---|---|---|
| **传统 2D organic（FCBGA）** | 单 die（或 die 网格）：纵向链 die→TIM→lid→heat sink→ambient；substrate 平面扩散（横向小） | $R_{\theta jc}$（die→case）、TIM $R$、sink $R_{\theta sa}$；CTM 按 JEDEC JESD51 系/BCI-CTM 提取 | die 顶面结温 $T_{\max}$ 上限；底面/ambient 恒定；单散热路径为主 |
| **2.5D interposer**（我们的目标） | die 网格节点：**die 间 lateral 面邻接**（经 interposer + underfill 横向耦合）+ 纵向 die→μbump→interposer→C4→substrate→ambient 链 | interposer 横向 $R$（面邻接，MFIT 式）、μbump/C4 纵向 $R$、underfill 横向耦合系数、substrate 扩散 | die 结温上限；interposer 侧向边缘 + substrate 底面散热（b_inter 变量，§4 C4）；underfill 提升横向耦合 |
| **3D 堆叠（TSV / hybrid bonding）** | 多层垂直线链：每层 die 节点（纵向 TSV/HB 链 die₁→…→dieₖ→substrate）+ 层间横向（各层独立 lateral） | TSV 纵向 $R$（含阵列）、hybrid bonding 低 $R$（μm 间距）、各层横向扩散 | 每层结温上限；顶层主散热或双面散热；TSV 密度决定纵向热导 |
| **晶圆级（Cerebras/Dojo 类）** | 大面积 die 网格（成百上千节点）：面内大范围扩散 + **多点/背面整体散热**（水冷板/背面冷板） | 大面积横向 $R$（面内扩散）、背面冷却 $g_{\text{vert}}$（水冷 vs 风冷）、功率密度上限 | 背面整体冷却（ambient = 冷板温度）；功率密度是 radix 限制因子（Chen ISCA'24：radix 受 power density 限制） |

引用锚点：FCBGA/CTM → lasance2008ctm + JEDEC JESD51（白名单外产品文档）；2.5D → mfit2025 + chen2025survey2p5d + feng2024chiplet2p5d + lau2023chiplet；3D → 3dice2010；晶圆级 → lie2023hcs + dojo2022hc/dojo2023micro + chen2024waferscale（功率密度限制）。

## 4. 核心结论：能否直接映射进 G·T=P+b（die 级粒度）

| 构型 | 分档 | 说明 |
|---|---|---|
| **FCBGA（2D）** | ✅ **可直接采用**（需补参数） | 就是我们的单 die 级 $b=g_{\text{vert}}T_{\text{amb}}$ 形式（die 网格 + 垂直线链）；参数：$R_{\theta jc}$/TIM/sink（JEDEC/CTM 数据）。横向项可加可不加（早期不加） |
| **2.5D interposer** | ✅ **可直接采用**（已是设计目标） | 即 `AnalyticNetworkBuilder` 现状（MFIT 式面邻接 + 集总 $R_{\text{vert}}$）；待补参数：interposer 横向 $R$、μbump/C4 纵向 $R$、underfill 耦合系数（config YAML 对齐） |
| **3D 堆叠** | ⚠️ **需改造**（或按近似条件使用） | 需多层 die 节点（每层 $\mathbf{T}_{\text{die}}$）或**早期按"每堆叠一条垂直线链"集总近似**（把 TSV/HB 链压成 $R_{\text{vert}}$，横向按层聚合）——近似成立条件：纵向热主导、层间横向弱耦合时可用；精确多层需 G 扩维 |
| **晶圆级** | ✅ **可直接采用**（需补参数/粒度） | 大 die 网格 + 每节点 $g_{\text{vert}}$（背面水冷/风冷）+ 面内横向扩散——正是 G 的 die 级网格形式；参数：大面积横向 $R$（面内扩散系数）、冷却 $g_{\text{vert}}$、功率密度上限（Chen ISCA'24 数据支撑 radix/power-density 耦合）。**验证阶段建议首试此构型对照**（与 2.5D 一起，覆盖"大面积平面散热"与"interposer 横向耦合"两种网络形态） |

**验证阶段建议（小模型先试）**：1) 2.5D interposer（现状，mf 参数待补）；2) 晶圆级背面冷却（大网格 + 均匀 $g_{\text{vert}}$）——两种都能直接跑现有 `SteadyStateModel`，只需换参数组（config YAML），不改造求解器。3D 堆叠改造留后期（需求明确再动）。

## 5. 引用（新增入 paper.bib，定向核验）

| 键 | 文献 | 核验 |
|---|---|---|
| lasance2008ctm | Lasance, "Ten Years of Boundary-Condition-Independent Compact Thermal Modeling of Electronic Parts: A Review", Heat Transfer Engineering 29(2):149-168, 2008, DOI 10.1080/01457630701673188 | ✅ CrossRef |
| lau2023chiplet | Lau, "Recent Advances and Trends in Chiplet Design and Heterogeneous Integration Packaging", ASME J. Electronic Packaging 146(1), 2023, DOI 10.1115/1.4062529 | ✅ CrossRef |
| feng2024chiplet2p5d | Feng, Zhou, Chen, Wang, Cao, "Thermal Interaction and Cooling of Electronic Device with Chiplet 2.5D Integration", Applied Sciences 14(18):8114, 2024, DOI 10.3390/app14188114 | ✅ CrossRef（MDPI，白名单外） |
| （已有）hotspot2006 / mfit2025 / 3dice2010 / chen2025survey2p5d / lie2023hcs / dojo2022hc / dojo2023micro / chen2024waferscale | — | 已核验 |

**待核实**：JEDEC JESD51 具体标准号与页（产品文档，白名单外）；HotSpot 结构细节公式（论文/手册全文核对）；晶圆级冷却参数（Cerebras/Dojo 白皮书级数据，白名单外）。
