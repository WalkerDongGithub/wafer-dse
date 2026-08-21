# interposer/chiplet 布局算法调研小结（layout-algorithms-note）

> **产出**：LiteratureSearcher（作者 round 21+ 指派工作项【4】）
> **日期**：2026-08-21
> **边界**：调研 + 引用即可，不自研实现（经典 NP-hard，作者明确不造轮子）；定向小核验（DBLP 第一源，8+1 条已核验），不扩张规模。
> **用途**：Related Work §3.2 外层布局工具域支撑；§4.1 外层"借用成熟流程"依据；耦合案例【1】（功耗走线占用 RDL 布线容量）的布线资源文献落点。

---

## 1. 结论速览（可辩护的一句话）

> interposer/chiplet 布局是经典 NP-hard 组合优化问题，EDA 社区已有成熟表示模型（sequence-pair）与大量专用求解器（热感知 / 线长感知 / 成本感知 / 学习式），**但均以物理单目标或物理双目标为主，未与网络性能 DSE 及 B\* 量化联立**——这既支持我们"外层借用成熟布局流程、不自研"的定位，也再次印证 insight 4 的"分离决策"（布局与性能/热分开做）。

## 2. 布局表示与经典模型

| 文献 | 内容 | 核验 |
|---|---|---|
| Murata, Fujiyoshi, Nakatake, Kajitani, "VLSI module placement based on rectangle-packing by the sequence-pair", **IEEE TCAD 15(12):1518-1524, 1996**（DOI 10.1109/43.552084） | sequence-pair 矩形装箱表示——经典 floorplan 表示，可多项式时间判定可行性；chiplet 布局工具（Chiou ASP-DAC'23）直接沿用 | ✅ DBLP |
| （B\*-tree, Chang et al. DAC 2000） | 非切片 floorplan 的另一经典表示 | 本轮未核验，如引用需补 DBLP 核验 |

## 3. chiplet 布局专用算法（2.5D，热/线长/成本/学习式）

| 文献 | 目标/方法 | 核验 |
|---|---|---|
| Ma, Delshadtehrani, Demirkiran, Abellán, Joshi, Coskun, "TAP-2.5D: A Thermally-Aware Chiplet Placement Methodology for 2.5D Systems", **DATE 2021, pp.1246-1251**（DOI 10.23919/DATE51398.2021.9474011） | 热感知 chiplet 布局（物理单目标：峰值温度） | ✅ DBLP（第 6 作者以 DBLP 为准，如与出版方不一致待核实） |
| Wang, Li, Jia, Lin, Wang, Huang, "ATPlace2.5D: Analytical Thermal-Aware Chiplet Placement Framework for Large-Scale 2.5D-IC", **ICCAD 2024, pp.39:1-39:9**（DOI 10.1145/3676536.3676648） | 解析式热感知布局（大规模） | ✅ DBLP |
| Chiou, Jiang, Chang, Lee, Pan, "Chiplet Placement for 2.5D IC with Sequence Pair Based Tree and Thermal Consideration", **ASP-DAC 2023, pp.7-12**（DOI 10.1145/3566097.3567911）；期刊版 Lee, Chiou, Jiang, ACM TODAES 2026（DOI 10.1145/3716893） | sequence-pair + 热考虑 | ✅ DBLP |
| Hou, Zhuang, Kundu, Ata Kircali, Wang, Rotaru, Rahul, James, "TDPNavigator-Placer: Thermal- and Wirelength-Aware Chiplet Placement in 2.5D Systems Through Multi-Agent Reinforcement Learning", **EPTC 2025**（DOI 10.1109/EPTC67330.2025.11392651；arXiv:2602.11187） | MARL 热+线长双目标 | ✅ OpenAlex/DOI |
| ChipletPart: "Scalable Cost-Aware Partitioning for 2.5D Systems"（**arXiv:2507.19819**） | 成本感知划分 | ⚠️ 待核实完整作者/发表状态 |

## 4. interposer 级布局/信号分配与 EDA 综述

| 文献 | 内容 | 核验 |
|---|---|---|
| Liu, Chang, Wang, "Floorplanning and Signal Assignment for Silicon Interposer-based 3D ICs", **DAC 2014, pp.5:1-5:6**（DOI 10.1145/2593069.2593142） | interposer 布局 + 信号分配（布线资源与信号分配到 interposer 的联合）——**与耦合案例【1】直接相关**（布线容量/RDL 资源建模） | ✅ DBLP |
| Chen, Zhang, Ling, Zhai, Yu, "The Survey of 2.5D Integrated Architecture: An EDA perspective", **ASP-DAC 2025, pp.285-293**（DOI 10.1145/3658617.3703134；arXiv:2411.04410） | 2.5D 集成 EDA 综述（布局/布线/热/PDN 全覆盖）——**一站式引用** | ✅ DBLP |
| Kannan, Enright Jerger, Loh, "Enabling interposer-based disintegration of multi-core processors", **MICRO 2015, pp.546-558**（DOI 10.1145/2830772.2830808） | interposer 多核拆解（chiplet 集成动机） | ✅ DBLP |

## 5. 架构-芯片-封装 co-design（对照我们"两层 DSE"定位）

| 文献 | 内容 | 核验 |
|---|---|---|
| Kim, Murali, Park, Qin, Kwon, Venkataramani, et al., "Architecture, Chip, and Package Co-design Flow for 2.5D IC Design Enabling Heterogeneous IP Integration", **DAC 2019**（DOI 10.1145/3316781.3317775） | 架构-芯片-封装联合设计流程（2.5D）——"co-design 有先例"的定位引用 | ✅ DBLP |

## 6. 与论文各处的连接

1. **Related Work §3.2**：外层布局工具域 = FPIA（TCAS-I'24，通信感知布局路由）+ TAP-2.5D/ATPlace2.5D/Chiou（热感知布局）+ TDPNavigator（MARL）——均为"物理单目标/双目标"启发式/学习式求解器；我们不自研（NP-hard），作为外层离散层的成熟工具候选/对标（xxx vs xxx：它们不做网络性能 DSE 联立）。
2. **§4.1 外层**：布局算法经典 NP-hard（sequence-pair 等表示下仍为组合爆炸），支撑"外层借用成熟流程、保持 NP-hard、不引复杂性战争"的定位（配合 insight 7 纪律）。
3. **耦合案例【1】**：功耗/电源走线占用 RDL 布线容量——布线资源建模引用 Liu DAC'14（interposer 信号分配/布线资源）+ ASP-DAC'25 综述（布线/RDL 章节）+（如需）PDN/RDL 封装文献（ECTC，白名单外）。
4. **方法对比（"xxx vs xxx"）**：现有布局工具以热/线长/成本为目标、逐因素分离；我们以外层布局 + 内层"热-电-几何-性能单模型 + B\*"联立——布局算法文献反衬内层联立的缺位。
5. **RapidChiplet 的布局处理方式**（EvalDesigner 点名角度）：RapidChiplet 把 chiplet 数量/大小/**布局**作为 ICI 设计空间的自由度（输入参数/探索轴，原文"The ICI design space is huge as there are many degrees of freedom such as the number, size, and placement of chiplets…"），自身不做布局求解（它是 latency/throughput 代理模型，thermal 外挂 HotSpot）——布局环节仍需借用成熟布局器，正好落在外层。
6. **FPIA 类物理设计流程的布局环节**（EvalDesigner 点名角度）：FPIA 是"通信感知布局 + 布线"引擎（placement+routing，TCAS-I'24），即物理设计流程中承担布局/布线环节的成熟求解器，可作为外层布局引擎候选/对标；其目标为 latency/energy/routability，不与网络性能 DSE 联立。

## 7. 引用键（已入 paper.bib）

`murata1996seqpair` / `tap2p5d2021` / `atplace2p5d2024` / `chiou2023chiplet` / `tdpnavigator2025` / `chiplettpart2025`(待核实) / `liu2014interposerfloorplan` / `chen2025survey2p5d` / `kannan2015interposer` / `kim2019codesign`

## 8. 待核实（轻量收口，Phase 3 前不扩张）

- B\*-tree（Chang et al., DAC 2000）若需引用补 DBLP 核验；
- ChipletPart 完整作者；
- TAP-2.5D 第 6 作者（DBLP 5 人 vs 出版方 6 人）；
- Kim DAC 2019 完整作者（DBLP 显示 7+ 人）。
