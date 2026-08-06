# 晶圆级交换机 DSE — 文献调研

> 调研时间：2025-07-29
> 分类：A=已知晶圆级系统, B=晶圆级交换机架构研究, C=Chiplet/Wafer DSE 框架, D=NoC 建模工具, E=光学/光电

---

## A. 已知晶圆级系统（对标 Category A）

### A1. Tesla Dojo
- **来源**：Hot Chips 34 (2022), Hot Chips 2024
- **类型**：晶圆级 AI 训练超算（不是交换机，但包含 wafer-scale interconnect）
- **规模**：25 个 D1 die (TSMC 7nm, 645mm²/die) 通过 InFO_SoW 集成在一个 Training Tile 上
- **拓扑**：2D Mesh + Z-Plane（跨 mesh 的快速通道，30 跳变 4 跳）
- **带宽**：on-tile bisection 10 TB/s，off-tile 36 TB/s，per-edge 4.5 TB/s
- **关键参数**：576 SerDes lanes × 112 Gbps per die，~15 kW/tile，354 核/die
- **路由**：flat addressing，compiler-driven，可绕过坏核
- **与我们的关系**：这是**计算芯片**不是交换机。但它的 2D mesh + Z-plane 拓扑、InFO_SoW 封装、bump 密度数据是我们论文的 baseline 参考点

### A2. Cerebras WSE-2 / WSE-3 (CS-2 / CS-3)
- **来源**：IEEE Micro, Hot Chips 等（2021-2024）
- **类型**：晶圆级 AI 处理器（单 die，非多 chiplet 集成）
- **规模**：WSE-2: 46,225 mm², ~850K PEs；WSE-3: ~900K PEs
- **拓扑**：2D Mesh（toroidal，支持 wrap-around）
- **路由**：24 种"颜色"的硬件路由（每核最多 32 条路由路径），wavelet-based 通信
- **带宽**：on-chip aggregate 20-22 PB/s，per-link 17.6-32 GB/s，per-hop ~1 ns
- **关键参数**：40-44 GB on-chip SRAM，5 端口 router（N/S/E/W/local），无 cache hierarchy
- **与我们的关系**：这是**单晶圆计算芯片**，不是交换机。但它的 2D mesh 拓扑、对 mesh 路由的深入分析、以及 wafer-scale 物理约束（最大 D2D 距离 ~50mm，金属层限制等）是我们的重要数据点

### A3. TSMC InFO-SoW 平台
- **来源**：TSMC 公开技术论文
- **类型**：晶圆级封装**平台**（不是具体芯片）
- **关键参数**：InFO-SoW 支持 25+ die 集成，RDL 互联
- **SoW-X** 变体：LSI (6.5mm 短距 400Gbps/lane)、SerDes (50mm 100Gbps/lane)
- **与我们的关系**：提供了工艺参数边界——bump pitch, lane rate, 最大 die 数等。我们 `tsmc_profiles.py` 中的 InFO-SoW、SoW-X-LSI、SoW-X-SerDes 三个 profile 直接来自 TSMC 的公开数据

---

## B. 晶圆级交换机架构研究（对标 Category A+B）

### B1. Waferscale Network Switches ⭐
- **作者**：David Chen, Saptadeep Pal, Rakesh Kumar (UIUC)
- **来源**：ISCA 2024 → IEEE Micro Top Pick (2025)
- **论文**：[IDEALS](https://www.ideals.illinois.edu/items/136269), [IEEE Micro](https://ieeexplore.ieee.org/abstract/document/10609578)
- **核心思想**：系统量化了晶圆级集成对网络交换机的潜力——仅考虑面积约束时可达 **32× radix**，但实际受限于**内部带宽、外部带宽、功率密度**
- **关键发现**：
  - 真正的瓶颈不是面积，是 I/O 带宽和功耗
  - 异构交换设计降低功耗 30.8-33.5%
  - Subswitch deradixing 使 radix 翻倍
  - Area I/O + Optical I/O 解决外部带宽瓶颈
- **与我们的关系**：**最直接的对标工作。** 他们问"晶圆级交换机有多大潜力"，我们问"给定一个晶圆级交换机架构，它 feasible 吗，瓶颈在哪"。他们的分析是自顶向下的 radix 上限估计，我们的是自底向上的约束耦合 LP。**互补但不同**

### B2. Switch-Less Dragonfly on Wafers ⭐
- **作者**：Yinxiao Feng, Kaisheng Ma (IIIS, Tsinghua)
- **来源**：SC 2024, arXiv:2407.10290
- **核心思想**：在晶圆上直接实现 Dragonfly 拓扑，去掉传统的高 radix 物理交换机。利用晶圆级高密度互联替代交换机芯片
- **关键结果**：比传统 switch-based Dragonfly 在成本和性能上都更好；死锁自由的最小和非最小路由只需一个额外 VC
- **与我们的关系**：**非常相关。** 他们针对 Dragonfly on wafer 做架构设计（routing algorithm），我们做 DSE 框架（给任何一个拓扑+封装+散热组合，判断 feasible 与否）。他们关注"怎么做"，我们关注"怎么选"。理想情况下，**我们的 DSE 可以用来评估他们的架构参数选择**

### B3. Architectural Exploration for Waferscale Switching System
- **作者**：Wan et al. (Zhejiang Lab)
- **来源**：IEEE TVLSI, 2024 (DOI: 10.1109/TVLSI.2024.3455332)
- **核心思想**：在 2D mesh 物理拓扑上叠加 BFT（Butterfly Fat-Tree）逻辑拓扑，通过软件定义端口配置实现
- **规模**：~392 switch dies on 300mm wafer，28 clusters，896 ports × 10 Gbps
- **关键结果**：比 baseline 2D mesh 减少 55.6% 跳数，降低 41.4% 延迟，提高 24.2% 吞吐
- **与我们的关系**：相关但不同。他们针对**一种特定拓扑**做优化，我们提供一个**通用的可行性判断框架**。他们的物理参数（die 数、wafer 面积、最大距离）可以作为我们基线

### B4. PD Constraint-aware Physical/Logical Topology Co-Design for NoW ⭐
- **作者**：Yang et al.
- **来源**：ISCA 2025
- **核心思想**："TickTock" co-design：物理拓扑 ↔ 逻辑拓扑 ↔ 并行策略 迭代优化
- **关键参数**：50mm 最大 D2D 链路（超出则 BER 108×, 延迟 210ns），50,000 mm² 可用 wafer 面积
- **关键结果**：2.39× LLM 训练吞吐提升 vs SOTA mesh-based NoW
- **与我们的关系**：**目前最全面的 NoW DSE 框架。** 但他们的 focus 是 LLM 训练（compute-centric），我们是网络交换机（communication-centric）。他们的约束模型（面积、功率、D2D 距离）与我们有重叠。这是最接近的 **DSE 同行工作**，但目标不同

---

## C. Chiplet / Wafer-Level DSE 框架（对标 Category B）

### C1. FPIA ⭐
- **作者**：Bo Jiao et al. (Fudan University)
- **来源**：IEEE TCAS-I, 2024 (DOI: 10.1109/TCSI.2024.3419579)
- **核心思想**：在硅 interposer 上实现 field-programmable 互连 fabric（turnout box + crossover box + parallel tracks），自动做 chiplet placement + routing
- **关键结果**：94.5% 局部资源利用率下可保证可布线性，互联延迟 <2.2ns, 1.18 pJ/bit at 1Gbps
- **与我们的关系**：这是我们的**布线约束（MATH_MODEL §4）的理论 source**。FPIA 解决 chiplet 级的 placement+routing，不涉及拓扑性能或热约束。我们的四约束统一框架将 FPIA 的布线约束作为四个约束族之一纳入，同时联立性能+几何+热

### C2. RapidChiplet
- **作者**：ETH Zurich (spcl/rapidchiplet)
- **来源**：arXiv 2023 (updated 2025), open-source
- **核心思想**：chiplet 间互连（ICI）的快速 DSE——用分析模型代理替代 cycle-level 仿真，提速 427-682×
- **关键特性**：支持 15+ 拓扑，与 BookSim2 集成做精仿，含 yield model 的成本估计
- **与我们的关系**：方法论上相似（快速近似 + 可选的精确仿真），但对象不同（chiplet ICI vs 晶圆级交换机）。他们的 analytical proxy 思路可以引用为"为什么 LP 快"的论据

### C3. FireLink
- **作者**：National University of Defense Technology
- **来源**：计算机研究与发展, 2025
- **核心思想**：chiplet 全栈 DSE（微架构+互连+PPA+成本），用 ID3 决策树加速搜索
- **PPAC 指标**：Performance-Power-Area-Cost，超越传统 PPA
- **与我们的关系**：较远。面向 chiplet 通用计算而非晶圆级交换机。但他们的自动化 pipeline 思路和 PPAC 指标可以参考

### C4. CHARIOT
- **作者**：2024
- **来源**：DTIC Dimensions
- **核心思想**：2.5D/3D interposer 的 communication-aware DSE，用多目标贝叶斯优化
- **关键结果**：最佳 passive/active interposer 设计达到 1.33×/1.96× 能效提升
- **与我们的关系**：较远。面向 interposer 设计而非交换机

---

## D. NoC / 互连建模工具（方法论对比）

### D1. BookSim / BookSim2
- **类型**：cycle-accurate 互连网络仿真器
- **问题**：仿真太慢，单点就需要数分钟到数小时。对 DSE 扫描完全不可行（1000 个设计点 × 每个数分钟 = 几天）
- **与我们的关系**：**我们的速度 baseline。** LP 求解在 ms 级别，比 cycle-accurate 仿真快 3-4 个数量级。BookSim 可以作为"ground truth"来验证 LP 近似的精度

### D2. DSENT
- **类型**：NoC 功耗/面积建模工具（MIT, 已停维护）
- **限制**：仅支持到 22nm，不能区分不同链路长度（统一设 1mm），对 3D NoC 无效
- **与我们的关系**：**为什么现有工具不够的证据。** DSENT 只建模电气 NoC 的功耗/面积，没有 bump 预算、没有热约束、没有拓扑路由。它是单点评估工具，不是 DSE 框架

### D3. McPAT
- **类型**：多核处理器功耗/面积建模工具
- **限制**：同上，仅到 22nm，NoC 面积估算有 bug（ring 和 mesh 返回相同面积）
- **与我们的关系**：同上，为什么现有工具不够

---

## E. 光学/光电晶圆级

### E1. Wafer-Scale Silicon Photonic Switch (UC Patent)
- **来源**：US Patent 2024/0302598, UC Regents (Sep 2024)
- **核心思想**：reticle stitching 技术——将相同的 switch block 在 wafer 上重复拼接，突破单 reticle 尺寸限制
- **潜在规模**：>1024 port 光学开关在单 wafer 上
- **与我们的关系**：光学交换是晶圆级交换机的未来方向。我们的 LP 框架目前针对电交换，但约束结构（lane → wavelength, bump → fiber coupling）可类比扩展

### E2. 16×16 Wavelength Cross-Connect Switch
- **作者**：Ikeda et al. (AIST, Japan)
- **来源**：J. Lightwave Technology, 2024 (Top-Scored Paper)
- **规模**：256 C-DCs + 1024 MZIs on 11×26mm chip，C+L band
- **与我们的关系**：较远，但可作为光学 interposer 的物理参数来源

---

## 汇总：我们的定位

| | 现有工作 | 我们 |
|---|---|---|
| **问什么问题** | "已知晶圆级系统能做到多大？""某个拓扑怎么在 wafer 上实现？""chiplet 怎么摆怎么连？" | **"给定一个拓扑+封装+散热组合，它 feasible 吗？瓶颈在哪？往哪个方向改进？"** |
| **约束建模** | 单约束或序贯检查（先布后验热，先算性能再算面积） | **四约束联立 LP：L 是唯一桥梁** |
| **输出** | 二元判断 (feasible/infeasible) 或单一指标 | **二元判断 + 每个约束的 slack + 对偶变量 + 参数灵敏度** |
| **速度** | 仿真级（分钟-小时）或分析级（秒） | **LP 级（ms），支持大规模 DSE 扫描** |
| **物理保真度** | 高（完整仿真）或低（简单公式） | **可配置：从简单模型到 MFIT 标定的分层热网络** |
| **通用性** | 特定拓扑或特定平台 | **5 种拓扑 + 20 种互联标准 + 6 种 bump + 4 种冷却** |

**核心 gap**：现有工作中，**没有一个将性能、几何、热三个约束在同一个变量 L 上联立为一个 LP**。FPIA 只做布线，UIUC 做 radix 上限分析不做耦合约束，NoW 的 DSE 框架面向计算不做交换机。**统一 LP 框架是独特的**。

---

## 关键参考论文列表（BibTeX 备用）

1. Chen, Pal, Kumar. "Waferscale Network Switches." ISCA 2024. *(UIUC — 晶圆级交换机潜力)*
2. Feng, Ma. "Switch-Less Dragonfly on Wafers." SC 2024. *(Tsinghua — 去交换机 Dragonfly)*
3. Wan et al. "Architectural Exploration for Waferscale Switching System." TVLSI 2024. *(Zhejiang Lab — BFT on mesh)*
4. Yang et al. "PD Constraint-aware Physical/Logical Topology Co-Design for Network on Wafer." ISCA 2025. *(TickTock DSE)*
5. Jiao et al. "FPIA: Communication-Aware Multi-Chiplet Integration With Field-Programmable Interconnect Fabric on Reusable Silicon Interposer." TCAS-I 2024. *(Fudan — 布线约束 source)*
6. Tesla Dojo. Hot Chips 34, 2022; Hot Chips 2024. *(2D mesh + Z-plane on InFO_SoW)*
7. Cerebras WSE-2/WSE-3. IEEE Micro / Hot Chips. *(Monolithic wafer-scale AI)*
8. RapidChiplet. ETH Zurich, 2023. *(chiplet ICI fast DSE)*
9. DSENT. MIT. *(NoC power/area — 已停维护)*
10. Birkhoff. "Tres observaciones sobre el algebra lineal." Univ. Nac. Tucuman, 1946. *(Birkhoff–von Neumann 定理)*
11. Valiant. "A Scheme for Fast Parallel Communication." SIAM J. Comput., 1982. *(Valiant 路由)*
12. Kim, Dally, et al. "Technology-Driven, Highly-Scalable Dragonfly Topology." ISCA 2008. *(Dragonfly 拓扑原始论文)*
