# 引言文献支撑映射

> 每条 = 引言中的一句论断 + 需要引用的文献 + 搜索状态

---

## 第一段：晶圆级交换机的出现

### 1. "硅interposer和先进封装技术的持续进步，使晶圆级集成从学术概念进入工业量产"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| 晶圆级集成已进入量产 | TSMC InFO-SoW / CoWoS 技术论文 | 需下载 |
| 先进封装（2.5D/3D）是行业主流趋势 | IDTechEx Advanced Packaging 2025 report | 需下载 |

### 2. "TSMC的InFO-SoW平台在Tesla Dojo中集成了25个D1裸片"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| Tesla Dojo使用InFO-SoW | Hot Chips 34: Tesla Dojo (Talpes et al., 2022) | 已有 cite:tesla2022dojo |

### 3. "Cerebras WSE-3以单晶圆级芯片集成约90万个处理核心"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| Cerebras WSE-2/WSE-3规格 | Cerebras WSE-2 paper / WSE-3 announcement | 已有 cite:cerebras2022wse2 |

### 4. "硅interposer提供的裸片间互联密度远超传统PCB——单裸片聚合IO带宽可达Pbps量级"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| Interposer vs PCB 互联密度定量对比 | Si-IF papers (UCLA/Illinois): interconnect density comparison | 需下载 |
| μbump pitch: 36--55μm | UCIe 2.0 spec, interposer technology surveys | 需下载 |
| 单裸片12×12mm, 45μm pitch → 约70k bumps → ~1 Pbps IO | 自己算的，需引用bump计算公式 + lane速率标准 | 需引用UCIe lane spec |

### 5. "互联协议灵活可配（UCIe、SerDes、光学互联），可根据裸片间距自适应选择速率和功耗等级"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| UCIe标准可选Advanced/Standard | UCIe 2.0 Specification (2024) | 需下载 |
| UCIe功耗: 0.25--0.6 pJ/bit | UCIe 2.0 + 2025 silicon papers (TSMC 3nm) | 已搜索 |
| SerDes VSR/MR/LR reach和功耗 | OIF-CEI standards, Cadence 112G/224G IP | 已搜索 |
| 光学互联 Ayar Labs TeraPHY: 8 Tbps, <5 pJ/bit | Ayar Labs product specs + IEEE papers | 已搜索 |

### 6. "UIUC的Chen等人首次量化了晶圆级交换机的radix提升潜力"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| ISCA 2024: Waferscale Network Switches | Chen, Pal, Kumar. ISCA 2024, pp. 215-229 | 已有 cite:chen2024waferscale |

### 7. "Feng和Ma提出'无交换机Dragonfly'架构"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| Switch-Less Dragonfly on Wafer | Feng & Ma. ATC 2024 (USENIX) | 已有 cite:feng2024switchless |

---

## 第二段：两个根本困难

### 8. "拓扑族与参数、路由策略、布线方案、调度策略、互联标准、封装方式、裸片规格、冷却方案——笛卡尔积超过10^6"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| Dragonfly参数空间 (a,p,h,g) | Kim et al. "Technology-Driven, Highly-Scalable Dragonfly Topology" ISCA 2008 | 需下载 |
| Chiplet DSE设计空间规模定量 | RapidChiplet (Iff et al., CF'25), FireLink (Li et al., 2025) | 已搜索 |
| 10^6设计点不是夸张 | 需引用具体DSE枚举规模的数据 | 需下载RapidChiplet |

### 9. "Cycle-accurate仿真器（如BookSim）单次评估需数分钟，在此规模下完全不可用"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| BookSim仿真规模和时间 | BookSim原始论文 + CNSim对比论文 | 已搜索 |
| BookSim不支持并行、大规模下成瓶颈 | BookSim limitations文献 | 已搜索 |
| NoC仿真成为全系统仿真瓶颈 | 多核仿真综述 | 可选 |

### 10. "chiplet DSE工具则聚焦单一物理维度，无法覆盖跨层次的联合决策"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| FPIA: chiplet placement+routing | Jiao et al. FPIA paper | 已有 cite:jiao2024fpia |
| RapidChiplet: fast chiplet DSE | Iff et al., CF'25 / arXiv:2311.06081 | 已搜索 |
| FireLink: chiplet DSE + PPAC | Li et al., JCRD 2025 | 已搜索 |
| CHARIOT: interposer DSE | DTIC paper | 已搜索 |
| 这些工具不覆盖thermal | 需确认RapidChiplet是否包含thermal | 需阅读RapidChiplet |

### 11. "在传统体系结构设计中，性能分析与物理实现可以大致分开考量。但在晶圆级交换机中，这一分离不再成立"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| 传统交换机设计流程：性能→物理是串行的 | 交换机设计教材/综述 | 需找 |
| 晶圆级需要co-design | TickTock (ISCA 2025), chiplet-package co-design papers | 已搜索 |

### 12. "四个环节构成闭环...任何单一维度的优化都可能被另一维度的约束推翻"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| 流量→bump→功耗→热→bump的耦合链 | 本文自己的argument，但耦合链上每个环节需要引用 | 见下文 |

**耦合链各环节文献：**

| 环节 | 文献需求 | 状态 |
|---|---|---|
| 链路负载→lane数→bump占用 | UCIe lane spec + bump budget公式（来源？） | 需引用 |
| lane功耗→总功耗 | UCIe 0.25-0.6 pJ/bit, SerDes ~15-20 pJ/bit | 已搜索 |
| 电源bump挤占信号bump | PDN/bump allocation papers | 需找 |
| 功耗分布→温度梯度→翘曲 | 2.5D/3D thermal-warpage reliability papers | 已搜索 |

### 13. "现有工具各自处理这一耦合链中的一个环节——性能仿真、bump计算、热分析独立运行——无法联立判断"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| 性能仿真工具: BookSim, SST, Noxim等 | 各工具的引用 | 部分已有 |
| bump/PKG分析工具 | 需确认有哪些工业工具（RedHawk? ANSYS?） | 需找 |
| 热分析工具: HotSpot, 3D-ICE等 | HotSpot paper, thermal tool surveys | 需找 |
| 没有工具覆盖全部三个维度 | 这是gap claim，需要证明"确实没有" | 需引用各工具的范围说明 |

---

## 第三段：两类约束与两层架构

### 14. "晶圆级交换机缺乏一个早期设计决策工具，能够同时考虑全部物理约束"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| 现有architecture DSE工具不覆盖wafer-scale | Architecture DSE surveys | 已搜索 |
| 现有chiplet DSE不覆盖thermal+performance simultaneously | RapidChiplet/FireLink/FPIA scope | 需确认 |

### 15. "第一类是离散选择：互联标准、裸片布局、工艺节点等"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| 互联标准是离散选择 | UCIe标准家族 (Advanced/Standard → 2D/2.5D/3D) | 需引用UCIe spec |
| 裸片布局是离散组合优化 | Chiplet placement literature | 可选 |

### 16. "第二类是带宽需求驱动的近似线性约束：bump占用、功耗、温度梯度、翘曲温差"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| bump占用是L的线性函数 | 本文推导，但需引用lane计算公式来源 | 需引用UCIe/SerDes lane spec |
| 功耗是L的线性函数 | 本文推导，需引用每lane功耗数据 | 已有UCIe/SerDes数据 |
| 热传导方程是线性的 | 标准热物理教材 + MFIT等热网络论文 | 需引用MFIT or thermal network papers |
| 翘曲温差是L的线性函数 | 本文推导，需引用thermal stress/warpage models | 需引用 |

### 17. "上层为离散枚举——通过启发式搜索或现有chiplet DSE工具进行智能选型"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| 启发式DSE在chiplet领域有效 | RapidChiplet (启发式pruning), FireLink (ID3 decision tree) | 已搜索 |
| FPIA可作为外层布局引擎 | FPIA paper | 已有 cite:jiao2024fpia |

### 18. "下层为多约束耦合线性规划——将全部线性约束表示为不等式组联立求解"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| BvN定理保证LP松弛不损失精度 | Birkhoff 1946, von Neumann 1953 | 已有 cite:birkhoff1946tres |
| LP在交换网络分析中有先例 | "Analyzing Nonblocking Switching Networks using Linear Programming (Duality)" | 已搜索 |
| Valiant路由的LP形式化 | Valiant original paper + Dragonfly Valiant analysis papers | 需下载 |

### 19. "两层通过物理参数接口解耦"

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| 两层架构在DSE中有先例 | Architecture DSE两层法综述 | 可选（我们的贡献） |

---

## 第四段：本文贡献

贡献部分是自指（claim what we did），不需要外部引用。但其中隐含的技术声索需要支撑：

| 需要支撑的子论断 | 文献 | 状态 |
|---|---|---|
| LP的影子价格 = 灵敏度 | Bertsekas非线性规划教材 (已有 cite:bertsekas1997nonlinear) | 已有 |
| B_max解析公式 | 本文推导 | 无需引用 |
| Dragonfly DSE实验 | 我们自己的实验结果 | 无需引用 |

---

## 优先下载列表

按重要性排序：

1. **UCIe 2.0 Specification** — bump占用、功耗估计的核心来源
2. **OIF-CEI standards (VSR/MR/LR)** — 复用器速率和reach
3. **Ayar Labs TeraPHY datasheet/paper** — 光学互联带宽和功耗
4. **Kim et al. "Technology-Driven Dragonfly Topology" ISCA 2008** — Dragonfly参数空间
5. **RapidChiplet (arXiv:2311.06081)** — chiplet DSE规模和性能数据
6. **FireLink (Li et al., JCRD 2025)** — chiplet DSE框架
7. **2.5D/3D thermal-warpage reliability综述** — 翘曲是线性约束的物理证据
8. **Valiant routing + Dragonfly performance papers** — 性能L1的引用链
9. **BookSim paper + limitations** — 仿真速度的引用
10. **HotSpot / 3D-ICE thermal tools** — 热分析工具的gap claim支撑
11. **MFIT paper (Berman 1994)** — M-矩阵保序性和热网络
12. **TSMC 3D Fabric / InFO-SoW technology papers** — 晶圆级平台的技术细节
