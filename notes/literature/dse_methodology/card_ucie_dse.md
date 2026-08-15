# 卡片 11：UCIe 驱动 DSE —— P2R / ILP SER / GAIL / Chisel PHY / CLIPGen / Keysight

> 新增发现：UCIe 成为 2024–2025 的 DSE 关键词，但成果集中在 PHY 与布线（SI 眼图）层。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## 1. P2R（IEEE TCPMT, 2025.04）—— UCIe 眼图掩膜约束的布局布线

### 出处
- "Advanced Chiplet Placement and Routing Optimization Considering Signal Integrity," *IEEE TCPMT*, 2025 [中等：摘要级]

### 建模维度
| 维度 | 有无 | 细节 |
|---|---|---|
| 布线 | ● | 布局布线优化（place-to-route, P2R 算法），UCIe eye mask 规范入目标：40mV 幅度、4–16 Gb/s 时 0.75 UI、24–32 Gb/s 时 0.65 UI（含 FFE/CTLE）[中等] |
| bump | ○ | 作为 P&R 的终端出口 |
| 热 | — | 无（GAIL 变体才有热，见下） |
| 性能/功耗/成本 | — | 无 |

### 搜索方法与代价
- 分层 MDP + 启发式（对比 1000 次迭代随机搜索/RL 提升 44.8%/71.7%）；单次 P&R 分钟级 [中等]

### 在我们框架里的位置
- **布线环节（§2.4）的 UCIe 化实现**：把"布得下"升级为"布得下且眼图合规"。它代表布线环节的当前最前沿，仍不与性能/热联立。

## 2. UCIe SI-aware ILP 逃逸布线（IEEE TCPMT 2025）

- 同时层/轨分配的 ILP 逃逸布线（SER），UCIe 标准基准上验证，最小化绕线/拐弯以降低插损、耦合长度约束抑串扰 [中等]
- 在我们框架里的位置：同 P2R——布线环节的精确求解器实现。

## 3. GAIL 布线代理（IEEE 会议, 2025.12）—— SI/热联合

- "Chiplet Placement and Routing Agent for UCIe Interfaces Considering Thermal and Signal Integrity"：生成式对抗模仿学习（GAIL），眼图 SI + 功耗感知热建模 + 转弯惩罚 [中等]
- 在我们框架里的位置：**布线环节内嵌热的少数例子**——但热是 P&R 优化目标之一，不是温度约束与流量变量的联立。可引为"布线与热的两两耦合先例"，对比我们的五环全联立。

## 4. Chisel UCIe-3D PHY 生成器（IEEE JXCDC, 2024.01; Berkeley BWRC）

- 3D D2D PHY 的 Chisel 生成器：端口表直接编译出 PHY + 自动化 PD；**DSE 变量包括 bump map pitch 与时钟架构**；4:1 空间编码冗余的 DSE 权衡 [中等]
- 在我们框架里的位置：**μbump 环节的 PHY 层实现**——唯一把 bump map pitch 当 DSE 变量的工作，但只到 PHY 层，不涉流量。

## 5. CLIPGen（arXiv 2026.05, 2605.27757）—— 链路 IP 的 PPA 建模生成

- chiplet link IP 模型自动生成：PPA 估计 + Verilog/Liberty/LEF 等设计产物，UCIe 接口案例研究，封装-架构联合早期 DSE [中等]
- 在我们框架里的位置：链路 IP 的功耗/性能系数（我们 S_bw、S_dyn 系数）的自动化取值工具——**它生成的是我们 LP 的系数，不是约束**。

## 6. Keysight Chiplet PHY Designer（商业, 2024.07）

- 首个 UCIe 仿真 EDA 方案：链路裕量预测、VTF 通道合规分析、DSE/报告功能 [中等]
- 在我们框架里的位置：布线/SI 环节的商业验证工具，说明该环节的工业工具箱已成熟——与之对比，**没有工业工具做"五环联立判定"**（商业 EDA 的多物理是顺序的 electro-thermal 分析，不是同一优化变量）。

## 子集论证小结
UCIe 驱动 DSE 的火爆证明"互连标准参数化 + DSE"是行业刚需（我们外层选型枚举的对象），但全部成果落在**布线（SI）+ PHY（bump map）**两层：UCIe 生态自己把 μbump 环节与布线环节做成独立工具岛，没有人把 lane 数接回流量需求形成预算约束。这为"环节工具化、联立真空"提供了生态级证据。

## 缺口与下一步
1. P2R/ILP/GAIL/Chisel PHY/CLIPGen 五篇均为摘要级 [中等]，引用前下载原文核数字
2. 论文 Related Work 可将 UCIe 生态（Keysight/Cadence/Synopsys 多物理顺序分析）作为"工业界同样缺联立判定"的证据

## 来源
- [P2R (Sejong 机构页)](https://sejong.elsevierpure.com/en/publications/advanced-chiplet-placement-and-routing-optimization-considering-s/)
- [Chisel UCIe-3D PHY (Berkeley)](https://bwrc.berkeley.edu/publications/chisel-generator-standardized-3-d-die-die-interconnects)
- [CLIPGen (arXiv:2605.27757)](https://www.layerthelatestinalattice.com/papers/cd98a0acfa42348d55ad91d930151d8dd1f1ecb7)
- [GAIL SI/TI 布线 (IEEE Xplore)](https://ieeexplore.ieee.org/document/11411724)
- [Keysight Chiplet PHY Designer](https://chipestimate.cn/Keysight-Introduces-System-Designer-for-PCIe-and-Chiplet-PHY-Designer-for-Digital-Standards-Driven-Simulation-Workflows/)
