# 卡片 12：开源仿真/探索器 —— gem5-X / CHASE / CASCADE / UniCNet / HexaMesh

> 新增发现：开源生态补全（注意 gem5-X 属 EPFL 而非 ETH，现有检索语境有混淆）。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## 1. gem5-X（EPFL ESL 的 gem5 扩展）—— 全系统仿真

### 出处
- EPFL Embedded Systems Lab 维护的 gem5 扩展（2020 起）；代表应用：**"System-Level Exploration of In-Package Wireless Communication for Multi-Chiplet Platforms," ASPDAC 2023** [可靠]

### 建模维度
| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ● | 全系统仿真（硬件 + Linux 栈），流量/应用驱动 [可靠] |
| 功耗 | ● | gem5 功耗统计（配合 McPAT 类工具）[中等] |
| 热/bump/布线/成本 | — | 无 |

### 搜索方法与代价
- 手动/脚本场景扫描；**全系统 cycle 级，分钟~小时级** [中等]
- 案例结论：无线 chiplet 互连与有线竞争，DNN 最多 2.64× 加速，token-passing MAC 最优 [可靠]

### 在我们框架里的位置
- 性能环节的**全系统实现**（比 BookSim 更重——含 OS/应用）；ASP-DAC 2023 的无线互连探索是"互连技术选项评估"，对应我们外层选型（把无线互连加入互连标准清单时的验证工具）。

## 2. CHASE —— chiplet 架构仿真 + 解耦多保真度优化

- 出处：chiplet architecture simulation and exploration framework（会议待定位）[中等]
- 维度：性能仿真为主；搜索：解耦多保真度优化（decoupled multi-fidelity）提升早期寻优概率 [中等]
- 在我们框架里的位置：ML 搜索策略（同 Theseus 家族），物理维度无新增。

## 3. CASCADE —— 异构 chiplet SiP 早期 DSE（边缘 AI）

- 出处：Adiletta et al.（会议待定位）[中等]
- 快速一阶性能模型 + 工具生成 trace，评估宏架构权衡；Hetero-chiplet 相对 GPU chiplet 基线 3–5× [中等]
- 在我们框架里的位置：性能环节的早期评估实现——"快速一阶模型"与我们同思路，但只做性能，无物理约束。

## 4. UniCNet —— 统一 cycle-accurate chiplet 网络仿真

- 出处：2026（arXiv 待定位）[中等]
- 可组合 chiplet 网络的统一 cycle 仿真 + 模块化设计集成流程 [中等]
- 在我们框架里的位置：BookSim 类仿真器的 chiplet 化升级，性能环节实现。

## 5. HexaMesh（DAC 2023）—— 大规模 chiplet 布局合成

- 出处：Iff et al., ETH（RapidChiplet 同组）[可靠]
- 数百 chiplet 的布局优化（六边形网格，性能目标）；属于**性能驱动的布局合成**（我们 §2.4 布线环节的上游——先摆后布）[可靠]
- 在我们框架里的位置：外层 placement 枚举的候选工具（与 FPIA 同层：给定 chiplet 集求布局），不涉约束判定。

## 子集论证小结
开源仿真器家族（gem5-X/CHASE/CASCADE/UniCNet/HexaMesh + BookSim/SuperSim）共同构成**性能环节的完整工具谱系**（全系统→flit 级→分析代理→布局合成），与功耗（DSENT/McPAT）、布线（FPIA/UCIe 族）、成本（Kannan/CATCH）、热（MFIT/Cool-3D，见现有笔记）各成孤岛。**谱系越完整，"没有联立"的缺口越醒目。**

## 缺口与下一步
1. gem5-X 与 ETH 的归属纠正：现有调研语境常把 gem5-X 归 ETH（可能因 RapidChiplet 同组），实际是 EPFL ESL
2. CHASE/CASCADE/UniCNet 三者的原文与完整出处待定位（当前 [中等]）
3. 论文 Related Work 可按"环节谱系"组织：性能谱系 / 功耗谱系 / 布线谱系 / 成本谱系 / 热谱系 → 每个谱系各自繁荣 → 交叉处（我们）真空

## 来源
- [EPFL ESL full-system simulation](https://www.epfl.ch/labs/esl/research/full-system-simulation-and-design/)
- [In-package wireless (IEEE)](https://ieeexplore.ieee.org/abstract/document/10044813)
- [RapidChiplet 综述引 HexaMesh/CHASE/CATCH](https://dl.acm.org/doi/full/10.1145/3719276.3725170)
