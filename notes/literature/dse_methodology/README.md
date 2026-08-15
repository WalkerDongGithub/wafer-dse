# DSE 方法论对标 —— 论证"已有 DSE 模型都是我们框架的子集"

> 对应研究议程 **2.4 方法论对标** 与论文 §8 核心论点。
> 目的：给"别人把模型焊死在流程里，我们框架里他们是某个环节的一种实现"收集证据。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。
> 创建：2026-08-15。基于 notes/LITERATURE_SURVEY.md C/D 节加深 + 2023–2025 新增检索。

---

## 总对比矩阵

图例：● = 建模并驱动搜索；○ = 简化/参数级/旁路涉及；— = 无。联立 = 多族约束共享变量统一求解（不是同框架顺次报告）。

| 工具/论文 | 性能 | 功耗 | 热 | bump | 布线 | 成本 | 联立耦合 | 模型可替换 | 搜索方法 | 单次评估代价 |
|---|---|---|---|---|---|---|---|---|---|---|
| **FPIA** (TCAS-I'24, 复旦) | ○ 延迟测量 | ○ pJ/bit | — | ○ 路由终端 | ● | — | ○ 环节内 P&R 联合 | ○ 参数化流程 | 启发式 P&R | 秒~分钟 |
| **RapidChiplet** (CF'25, ETH) | ● 分析代理 | ● | ○ 简化检查 | ○ 封装参数 | ○ 拓扑输入 | ● 良率 | ○ 独立评估非联立 | ○ 参数可配 | 枚举扫描 | **毫秒** |
| **FireLink** (JCRD'25, 国防科大) | ● RTL/FPGA | ● | — | — | — | ● 良率 | ○ PPAC 同框架 | ○ 流水线可扩展 | ID3 决策树+枚举 | 分钟~小时 |
| **CHARIOT** (TODAES'26?) | ○ 通信感知 | ○ 能效 | — | — | ○ interposer | ○ | ? | ? | BO(声称) | ? 【待确认】 |
| **DSENT** (NoCS'12, MIT) | — | ● | — | — | ○ 链路长参数 | — | — | ○ 参数/模型焊死 | 手动扫描 | 秒 |
| **McPAT** (MICRO'09) | ○ cycle time | ● | — | — | — | — | — | ○ 参数/模型焊死 | 手动扫描 | 秒 |
| **BookSim/2** (ISPASS'13) | ● cycle 级 | — | — | — | — | — | — | ○ 代码扩展 | 单点评估 | **分钟~天** |
| **SuperSim** (ISPASS'18) | ● flit 级 | — | — | — | — | — | — | ● 插件架构 | 脚本扫描 | 分钟~小时 |
| **Chen ISCA'24** (UIUC) | ● 解析上限 | ● | — | ○ I/O 密度 | — | — | ○ 面积+带宽+功耗串行排除 | — 非工具 | 手工解析枚举 | 秒 |
| **TickTock/PD co-design** (ISCA'25) | ● LLM 吞吐 | ○ | — | — | ○ 物理拓扑 | — | ○ 物理↔逻辑两两耦合 | — 流程绑定 | 迭代 co-design | 分钟级起 |
| **Kannan'16** (IEEE Micro) | — | — | — | — | — | ● 良率/成本 | — | — 非工具 | 蒙特卡洛 | 秒~分钟 |
| **CATCH** (arXiv'25) | — | — | — | — | — | ● 全流程成本 | — | ○ 参数化 | 枚举 | 秒 |
| **Theseus** (TCAD'24) | ● 分层 NoC 评估 | ● | — | — | — | ○ 冗余良率 | ○ 性能-功耗 Pareto | ○ 模板参数化 | **多保真度 BO** | 快~中 |
| **WSC-LLM** (ISCA'25) | ● | ○ | — | — | — | — | ○ 架构-调度 | ○ 可配置模板 | 联合搜索 | ? |
| **AgenticDSE** (DAC'25) | ● | ● | — | — | — | — | ○ 目标级 | ○ | LLM 智能体+BO | 中 |
| **MCT-Explorer** (ICCAD'24) | ● | ● | — | — | — | — | ○ 目标级 | ○ | MCTS+BO | 中 |
| **AI bump-pitch BO** (ICCAD'24) | ○ | ○ | ○ 灵敏度 | ● 单参数 | ○ | — | ○ 单参数对多目标 | ○ | BO | 中 |
| **P2R / UCIe P&R** (TCPMT'25) | — | — | — | ○ 终端 | ● SI 眼图 | — | ○ 布线+SI | — | 分层 MDP | 分钟 |
| **UCIe ILP 逃逸布线** (TCPMT'25) | — | — | — | ○ | ● | — | ○ 布线+SI | — | ILP 求解 | 秒~分钟 |
| **GAIL SI/TI 布线** (IEEE'25) | — | — | ○ 目标 | ○ | ● | — | ○ 布线+热两两 | — | GAIL/RL | 分钟 |
| **Chisel UCIe-3D PHY** (JXCDC'24) | — | ○ | — | ● bump map | ○ PHY 布线 | — | ○ PHY 内部 | ○ 生成器 | 生成+扫描 | 秒~分钟 |
| **gem5-X** (EPFL) | ● 全系统 | ● | — | — | — | — | — | ○ 可扩展模型 | 手动/脚本 | 分钟~小时 |
| **CHASE / CASCADE / UniCNet / HexaMesh** | ● | ○ | — | — | ○ 布局(Hexa) | — | ○ 各自内部 | ○ 各异 | BO/一阶模型/cycle | 快~慢 |
| **本框架（wafer-dse LP）** | ● 联立 | ● | ● | ● | ● | ○ 外层选型 | **● 五族同变量联立** | **● Model 接口可替换** | B* 二分 + 外层枚举 | **毫秒** |

**矩阵读法**：没有一行的 "●" 覆盖超过三列；唯一五列全 ● 的是我们自己。联立列全部是 ○ 或 —。可替换列大多停在"参数可配、模型焊死"。

---

## 卡片目录

| 卡片 | 内容 | 状态 |
|---|---|---|
| [card_fpia.md](card_fpia.md) | FPIA——布线环节单一实现 | 必做 #1 |
| [card_rapidchiplet.md](card_rapidchiplet.md) | RapidChiplet——多维度独立评估 | 必做 #2 |
| [card_firelink.md](card_firelink.md) | FireLink——PPAC 无热无联立 | 必做 #3 |
| [card_chariot.md](card_chariot.md) | CHARIOT——信息待核实 | 必做 #4 |
| [card_dsent_mcpat.md](card_dsent_mcpat.md) | DSENT/McPAT——功耗/面积硬编码模型 | 必做 #5 |
| [card_booksim_supersim.md](card_booksim_supersim.md) | BookSim/SuperSim——cycle 级单点评估 | 必做 #6 |
| [card_chen_isca2024.md](card_chen_isca2024.md) | Chen ISCA'24——自顶向下 radix 上限 | 必做 #7 |
| [card_ticktock.md](card_ticktock.md) | Yang ISCA'25——NoW 两两 co-design | 必做 #8 |
| [card_cost_models.md](card_cost_models.md) | Kannan/CATCH/ChipletActuary——成本三式 | 新增 |
| [card_ml_dse.md](card_ml_dse.md) | Theseus/WSC-LLM/AgenticDSE 等——ML 搜索层 | 新增 |
| [card_ucie_dse.md](card_ucie_dse.md) | P2R/ILP/GAIL/Chisel PHY/CLIPGen——UCIe 生态 | 新增 |
| [card_open_source_tools.md](card_open_source_tools.md) | gem5-X/CHASE/CASCADE/UniCNet/HexaMesh | 新增 |

---

## 子集论证骨架（论文 §8 直接素材）

按我们五环节（对应 MATH_MODEL_COMPLETE_V4 §2：性能 2.1 / μbump 2.3 / C4 2.6 / 热 2.5 / 布线 2.4）逐环清点。

### 环节 1：性能（2.1）——覆盖者最多，无人回喂物理环节

- 仿真实现：BookSim/BookSim2、SuperSim（cycle/flit 级，分钟~天级，DSE 不可行）
- 分析代理：RapidChiplet（ms 级，误差 2.6–25%）
- 解析上限：Chen ISCA'24（radix 上限）、TickTock（LLM 吞吐）、Theseus/WSC-LLM/AgenticDSE（LLM 工作负载优化）
- **共同缺口**：性能都是"评估指标"或"优化目标"，没有一个把性能需求写成对物理变量（链路负载 ℓ / 带宽 B）的**约束不等式**回喂给物理环节。只有我们把性能当"至少需要多少带宽"的不等式族。

### 环节 2：μbump（2.3）——只有 PHY 层单参数工具，预算约束真空

- 唯一直接工作：Chisel UCIe-3D PHY 生成器（bump map pitch 为 DSE 变量，止于 PHY）；AI bump-pitch BO（单参数灵敏度）；P2R/ILP 把 μbump 当 P&R 终端
- **无人把 μbump 数写成流量驱动变量的预算约束**（信号 lane 与电源 bump 零和竞争）——这是我们的结构性发现之一，文献里没有对应物。

### 环节 3：C4（2.6）——检索范围内完全真空

- 没有工具把 C4/焊球供给建模为与带宽联立的预算（SerDes 经 C4 出口）。
- **这是五环中证据最强的"无人区"**：成本工具（CATCH）把互连计钱不算供给；封装工具算 bump 不算 C4 预算。
- 风险：负面 claim 的检索完整性需要声明边界（见缺口 2）。

### 环节 4：热（2.5）——独立热分析繁荣，联立为零

- 独立热 DSE：MFIT、Cool-3D、STAMP-2.5D、HotSpot（均为热单维度，见现有 notes 与综述检索）
- 含热的多维工具：RapidChiplet（"thermal stability"简化检查 [待确认]）、GAIL 布线（热作优化目标之一）
- **无人把温度/温差写成负载的线性约束与其它族联立**；更没有"功耗→温度→bump 预算"的闭环。

### 环节 5：布线（2.4）——工具最专业，但都是"实现"不是"判定"

- FPIA（94.5% 可布线性）、P2R/UCIe ILP/GAIL（眼图 SI 合规）、HexaMesh（布局合成）
- **共同缺口**：输入是"要连什么"，输出是"怎么布"；没有一家把"lane 数需求能否放下"当作与流量联立的容量不等式（我们的 R·x ≤ C）。它们的可布线性结果正好可以作为我们保守容量上界的精确实现对照。

### 联立论证：三级区分（论文必须给的定义）

检索证据不支持"别人完全不碰多维度"，支持的是**联立的层次差异**：

1. **同框架独立评估**（RapidChiplet、FireLink PPAC）：多维度算好并列报告，维度间无共享变量、无竞争关系
2. **两两耦合 co-design**（TickTock 物理↔逻辑；GAIL 布线↔热）：局部闭环，无统一求解
3. **同变量统一数学规划**（我们）：五族不等式共享 ℓ、联立求解 B*

若不给这三级定义，"他们也有性能+功耗+成本"会击穿"子集"论证；给了之后，前两级恰好是我们（第三级）的退化特例——**这就是"子集"的精确含义：前两级工具各自是第三级中某族约束的一种实现或某种搜索策略的实例**。

### 最强证据（按强度排序）

1. **C4 环节无人建模**（真空）——不需要引用反驳
2. **热环节无联立**：所有含热的工具都是独立热分析或优化目标，最接近的 RapidChiplet 也只是简化检查
3. **"最全面的 NoW 同行"（TickTock）仍缺热/bump/C4/布线四环**；"维度最多"的 RapidChiplet 明确是独立评估（摘要自述维度清单）
4. **搜索策略军备竞赛与物理维度正交**：Theseus/AgenticDSE 的 BO 再先进，物理模型仍是单环节——搜索层进步不构成对我们联立层的竞争

---

## 缺口与下一步

1. **[待确认] 升级**：CHARIOT（线索 A 无法复现、线索 B 待取摘要）、RapidChiplet 热模型形式、TickTock 昵称与功耗/热细节、BookSim 单点代价的原始测量、AgenticDSC/MCT-Explorer/P2R 等摘要级数字——共 6 项，引用前必须核到 [可靠]
2. **负面 claim 的检索边界声明**：为支撑"C4/热无联立"，需在论文写明检索范围（英文主渠道 + 中文少量、2023–2025 重点、工具类与论文类），并引用 EDA 综述（arXiv:2411.04410、JETCAS'25、IEEE EPS HIR）佐证"社区自己也承认无全维度工具"
3. **工业 EDA 未覆盖**：RedHawk/ANSYS/Keysight 的多物理分析是顺序的 electro-thermal/thermo-mechanical 验证，非联立判定；建议补一张工业工具小节（现有检索只碰了 Keysight PHY）
4. **实验设计联动**：BookSim 验证 LP（抽 B* 边界点精仿）与 RapidChiplet 复现（同参数下比 B*）可放进论文第 5 章对标复现
5. **成本环节的定位**：成本模型 2023–2025 大热（CATCH 等），我们的框架里成本在外层选型——需在论文交代为什么成本不进内层 LP（非线性、与 ℓ 无共享变量），否则会被追问

---

## 来源清单（索引）

- FPIA：IEEE TCAS-I 71:4156–4168, 2024, DOI 10.1109/TCSI.2024.3419579（[IEEE Xplore](https://ieeexplore.ieee.org/abstract/document/10586747)）
- RapidChiplet：ACM CF'25, DOI 10.1145/3719276.3725170；[arXiv:2311.06081](https://arxiv.org/abs/2311.06081)
- FireLink：计算机研究与发展 62(5):1108–1122, 2025, DOI 10.7544/issn1000-1239.202440082（[原文页](https://crad.ict.ac.cn/article/doi/10.7544/issn1000-1239.202440082)）
- CHARIOT：ACM TODAES, DOI 10.1145/3815192（[DOI 页](https://dl.acm.org/doi/10.1145/3815192)）
- DSENT：NoCS 2012, pp. 201–210, DOI 10.1109/NOCS.2012.31（[MIT DSpace](https://dspace.mit.edu/handle/1721.1/69050)）
- McPAT：MICRO 2009（HP Labs 存档）
- BookSim2：ISPASS 2013（[GitHub](https://github.com/booksim/booksim2)）；SuperSim：ISPASS 2018, DOI 10.1109/ISPASS.2018.00017
- Chen ISCA'24：pp. 215–229（[IDEALS](https://www.ideals.illinois.edu/items/136269)；[IEEE Micro 版](https://ieeexplore.ieee.org/abstract/document/10609578)）
- Yang ISCA'25（PD co-design）：pp. 49–64（[Semantic Scholar](https://www.semanticscholar.org/paper/d4ac0754e41ade62bce88919accfde1b14e49f63)；[researchr](https://researchr.org/publication/YangWGLSDWLWZYH25)）
- Kannan：IEEE Micro 2016, DOI 10.1109/MM.2016.53
- CATCH：[arXiv:2503.15753](https://www.alphaxiv.org/overview/2503.15753)
- Theseus：TCAD 44:4793–4806, 2024（[IEEE Xplore](https://ieeexplore.ieee.org/document/10981855)；[arXiv:2407.02079](https://arxiv.org/pdf/2407.02079v1)）
- WSC-LLM：ISCA 2025, pp. 1–17, DOI 10.1145/3695053.3731101
- AgenticDSE（DAC'25）、MCT-Explorer（ICCAD'24）、AI bump-pitch BO（ICCAD'24）：[IEEE 索引](https://ieeexplore.ieee.org/document/11126287) / [ACM](https://dl.acm.org/doi/abs/10.1145/3676536.3676746)
- UCIe 生态：P2R（[TCPMT 机构页](https://sejong.elsevierpure.com/en/publications/advanced-chiplet-placement-and-routing-optimization-considering-s/)）、GAIL（[IEEE](https://ieeexplore.ieee.org/document/11411724)）、Chisel PHY（[Berkeley](https://bwrc.berkeley.edu/publications/chisel-generator-standardized-3-d-die-die-interconnects)）、CLIPGen（arXiv:2605.27757）、Keysight（[新闻](https://chipestimate.cn/Keysight-Introduces-System-Designer-for-PCIe-and-Chiplet-PHY-Designer-for-Digital-Standards-Driven-Simulation-Workflows/)）
- gem5-X：EPFL ESL（[主页](https://www.epfl.ch/labs/esl/research/full-system-simulation-and-design/)）；in-package wireless：ASPDAC'23（[IEEE](https://ieeexplore.ieee.org/abstract/document/10044813)）
- 综述/路线图：arXiv:2411.04410（chiplet EDA 视角综述）；IEEE JETCAS 2025（chiplet 技术综述）；IEEE EPS Heterogeneous Integration Roadmap（2024-09）
