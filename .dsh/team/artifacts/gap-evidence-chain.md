# gap claim 证据链（gap-evidence-chain）

> **产出**：LiteratureSearcher（Phase 1）
> **日期**：2026-08-20
> **用途**：论文动机段（Intro §1.2-1.3）与 Background §2.2 的"缺口主张"逐条证据链；标注每条 gap 有据 / 需弱化 / 待核实。
> **关联**：`notes/literature/LITERATURE_MAP.md`（19 条论断映射）为起点；本文件是#8/#9/#10/#13/#14 等 gap 类论断的证据收口。
> **校验**：DBLP/CrossRef/arXiv 第一源；原文引句见 [benchmark-matrix.md](benchmark-matrix.md) §4/§6。

---

## 1. 总表：gap 论断 → 证据强度

| LITERATURE_MAP # | 论断 | 证据强度 | 关键证据 |
|---|---|---|---|
| #8 | 设计空间笛卡尔积 > 10^6 | **有据（数量级需自证）** | RapidChiplet 摘要："hundreds of thousands of design points"（CF 2025）；我们自己的枚举规模需 DataSteward 补数 |
| #9 | cycle-accurate 仿真单点数分钟、10^6 点不可用 | **有据（"分钟级"需弱化为引用级）** | RapidChiplet 原文："While ICI simulators are important… they are not fast enough to explore hundreds of thousands of design points"；"such simulations take orders of magnitude longer than our novel, high-level latency and throughput proxies"（arXiv v2）——"orders of magnitude"可引，"单点数分钟"是我们自测（不写死具体分钟数，或标注内部数据） |
| #10 | chiplet DSE 工具聚焦单一物理维度，无法覆盖跨层次联合决策 | **有据（需 xxx vs xxx 限定）** | RapidChiplet 原文把 thermal 外挂 HotSpot（"There exist numerous DSE-tools for other metrics, such as… the HotSpot thermal simulator"）；CHARIOT/FireLink/FPIA 摘要无 thermal；**但** TickTock ISCA'25（PD+逻辑拓扑协同）与 Chen ISCA'24（radix 带宽+功率密度联合分析）是"部分联合"——措辞见 benchmark-matrix §4 |
| #11 | 传统流程性能→物理串行；晶圆级需要 co-design | **有据（定性）** | Chen ISCA'24 摘要："the actual radix… is not area-limited. Rather, it is limited by a combination of internal bandwidth, external bandwidth, and power density"——晶圆级性能与物理强耦合的直接佐证；TickTock ISCA'25 标题即 "PD Constraint-aware Physical/Logical Topology Co-Design" |
| #12 | 四环节闭环（流量→bump→功耗→热→bump） | **有据（各环节可引）** | UCIe 2.0 Spec（lane/功耗，白名单外产品文档）；HotSpot/MFIT（热）；PDN 文献（RedHawk/2.5D PDN 论文，见下）；链路功耗→温度→翘曲链条引用见 §3 |
| #13 | 性能仿真/bump 计算/热分析独立运行，无法联立判断 | **有据** | 性能：BookSim ISPASS'13、Noxim TOMACS 2016；热：HotSpot TVLSI'06、3D-ICE ICCAD'10、MFIT TODAES；布局：FPIA TCAS-I'24、RapidChiplet CF'25；电/PDN：RedHawk-SC（Synopsys 工业工具，白名单外）+ 2.5D PDN 学术文献（见 §4）——各工具独立存在且互不联立 |
| #14 | 晶圆级交换机缺乏同时考虑全部物理约束的早期决策工具 | **有据（检索未见 + 邻近工作均非 DSE 工具）** | 检索（DBLP/OpenAlex/arXiv，2026-08-20）：未检索到 wafer-scale 交换机 DSE 工具；Chen ISCA'24（radix 分析）、Feng&Ma SC'24（架构）、Wan TVLSI'25（架构探索）、TickTock ISCA'25（PD+拓扑协同）均为特定问题分析/架构研究，非"热-电-几何-性能单模型联立 + B\* 量化"的 DSE 工具。**"检索未见"以检索日期为准**，若审稿人指出新工具，需复审 |

---

## 2. 分离决策基线的可引用链条（E3 实验用，EvalDesigner 已取）

**分离流水线基线**（每环节引用独立工具，模拟"前人多因素分离决策"）：
```
性能评估：BookSim 2.0（Jiang et al., ISPASS 2013, pp.86-96, DOI 10.1109/ISPASS.2013.6557149）
  → 热检查：HotSpot（Huang et al., TVLSI 2006, DOI 10.1109/TVLSI.2006.876103）
          或 MFIT（Pfromm et al., TODAES, DOI 10.1145/3765905）
  → 布局/物理：FPIA（Jiao et al., TCAS-I 2024, DOI 10.1109/TCSI.2024.3419579）
          或 RapidChiplet（Iff et al., CF 2025, DOI 10.1145/3719276.3725170；thermal 外挂 HotSpot）
  → 电/PDN：RedHawk-SC（Synopsys，工业工具，白名单外）
```
vs 单一模型：内层 LP（扩展比包络 + 三层实体 + C1-C4）联立热-电-几何-性能，输出 B\*。

**对比口径（xxx vs xxx）**：每个分离环节的工具"只在其维度内最优/判定"，无跨维度回退（如热不满足时无法回改性能分配）；单一模型可同时收紧。这正是 insight 4 的实验论证（§5.4）。

---

## 3. 耦合链各环节文献（#12 的环节引用）

| 环节 | 引用 | 状态 |
|---|---|---|
| 链路负载 → lane 数 → bump 占用 | UCIe 2.0 Specification (2024)（lane 速率/功耗，白名单外产品文档）；V5 §2(2b) 公式 | 有据（规范全文不可公开引用页码，标 Spec 引用） |
| lane 功耗 → 总功耗 | UCIe 2.0 Spec（0.25-0.6 pJ/bit）；SerDes：OIF-CEI（规范号待核实） | 有据（数字需以 Spec 原文为准，待核实页码） |
| 电源 bump 挤占信号 bump | 2.5D PDN 文献：如 "Electrical Performance Analysis of High-Speed Interconnection and Power Delivery Network (PDN) in Low-Loss Glass Substrate-Based Interposers"；"Thermal Analysis of Dual-sided Cooling for Backside Power Delivery Networks (BSPDN) on 2.5D Glass/Silicon Interposer Package"（S6 检索命中；**待核实**完整元数据）；RedHawk-SC（工业） | 部分有据（建议正文以 V5 的 bump 预算模型自证为主，外部引用作佐证） |
| 功耗分布 → 温度梯度 → 翘曲 → bump 失效 | 热-翘曲可靠性：Li et al. "Thermal Cycling Reliability Analysis of 2.5D Chiplet Based on Silicon Interposer"（**待核实**完整元数据）；2.5D/3D thermal-warpage 综述（**待核实**）；MFIT（TODAES）作线性热网络 | 部分有据（物理链条定性成立，定量需引综述或自证；正文按纪律"热只引 MFIT"展开） |

---

## 4. "无工具覆盖全维度"检索记录（#14 反证扫描，S6）

检索式（2026-08-20，DBLP/OpenAlex/arXiv）：
- "wafer-scale design space exploration" —— 未命中 DSE 工具类文献（命中为架构/系统论文：Chen ISCA'24、Yu ISCA'25 等）
- "wafer-scale floorplanning" / "wafer-scale NoC design" —— 未命中 DSE 工具类文献
- "chiplet DSE" / "interposer DSE" —— 命中 RapidChiplet/CHARIOT/FireLink/FPIA（均非 wafer-scale，且无热-电-几何-性能单模型）
- 热感知布局：ATPlace2.5D、TDPNavigator-Placer、ASPDAC'23 chiplet placement（热单维物理设计，非网络性能 DSE）

**结论**：wafer-scale 交换机 DSE（热-电-几何-性能单模型 + B\*）检索未见。此"检索未见"证据在论文中以"to the best of our knowledge / 据检索（日期）"表述，留防御余地。

---

## 5. LITERATURE_MAP 状态更新摘要

（详细逐条状态见 `notes/literature/LITERATURE_MAP.md` 内嵌标注，本次会话已按核验结果更新下列关键项）

| 原状态 | 现状态 | 变化 |
|---|---|---|
| #6 Chen ISCA'24 "已有 cite:chen2024waferscale" | ✅ 已核验（ISCA 2024, pp.215-229, DOI 10.1109/ISCA59077.2024.00025） | — |
| #7 Feng & Ma "ATC 2024 (USENIX)" | ✅ 已核验但 **venue 修正为 SC 2024**（DOI 10.1109/SC41406.2024.00102） | 修正 |
| #10 chiplet DSE 工具 | ✅ 已核验（RapidChiplet CF'25/arXiv、FireLink JCRD'25、FPIA TCAS-I'24、CHARIOT TODAES'26）+ thermal 覆盖结论 | 确认"不覆盖 thermal+performance 联合"（RapidChiplet 原文铁证） |
| #14 wafer-scale DSE 缺位 | ✅ 检索未见（以 2026-08-20 为准） | 有据 |
| MFIT（V5 §10 / ref.bib） | ⚠️ 引用错误：实为 Pfromm et al. TODAES（DOI 10.1145/3765905） | 修正（V5 需 DomainExpert 确认） |

---

## 6. 一句话给写作（Intro §1.3 的 gap 段落素材）

> "Chiplet 界已有成熟 DSE（RapidChiplet / FireLink / FPIA / CHARIOT），但多聚焦性能/成本/布局单维：RapidChiplet 明确把热分析外挂给 HotSpot [CF'25]，CHARIOT 只优化 performance/energy [TODAES'26]，FireLink 覆盖 PPAC 无热 [JCRD'25]，FPIA 只做通信感知布局 [TCAS-I'24]；热建模工具（HotSpot/3D-ICE/MFIT）独立存在、不与网络性能 DSE 联立。晶圆级网络工作（Chen ISCA'24、Feng&Ma SC'24、Wan TVLSI'25）量化/探索了特定维度，TickTock（ISCA'25）做了 PD 约束与逻辑拓扑的协同设计，但均未把热-电-几何-性能纳入单一模型、输出带 QoS 保证的额定出入口带宽 B\*——wafer-scale 交换机缺这样的早期 DSE 工具（据检索，2026-08）。"
