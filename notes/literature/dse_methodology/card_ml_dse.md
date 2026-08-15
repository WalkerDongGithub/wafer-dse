# 卡片 10：ML 加速 DSE —— Theseus / WSC-LLM / AgenticDSE / MCT-Explorer / AI bump-pitch

> 新增发现：2024–2025 的 DSE 搜索策略向贝叶斯优化（BO）+ 代理模型集中，但物理维度没有随之增加。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## 1. Theseus（IEEE TCAD 2024）—— 晶圆级芯片 DSE，最接近我们的方法学邻居

### 出处
- **Jingchen Zhu, Chenhao Xue, et al.**, "Theseus: Towards High-Efficiency Wafer-Scale Chip Design Space Exploration for Large Language Models," *IEEE TCAD*, vol. 44, 2024（arXiv:2407.02079）[可靠]

### 建模维度
| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ● | 分层 NoC 评估方法（大 NoC 高效评估）；LLM 训练/推理吞吐 [可靠] |
| 功耗 | ● | Pareto 目标之一 [可靠] |
| 成本 | ○ | 扩展良率模型（含冗余增强）[可靠] |
| 热/bump/布线 | — | 无 |

### 搜索方法与代价
- **多保真度贝叶斯优化**：平衡评估成本与精度 [可靠]
- 结果：Pareto 最优设计比 GPU 集群性能高 62.8%/73.7%、功耗低 38.6%/42.4%（训练）；推理 23.2×/15.7× [可靠]

### 在我们框架里的位置
- **对应环节：性能 + 功耗的目标优化**（无物理约束联立）。它证明"晶圆级芯片 DSE + BO"是 2024 年起的公认方法论组合——但它优化目标（吞吐/功耗），我们判定可行性（五族约束）。两者的搜索方法可对话：**他们的 BO 可以拿来当我们的外层枚举策略**（离散选型层），内层联立 LP 仍是我们独有。

## 2. WSC-LLM（ISCA 2025）—— 架构与服务联合探索

### 出处
- **Zheng Xu, Dehao Kong, et al.**, "WSC-LLM: Efficient LLM Service and Architecture Co-exploration for Wafer-scale Chips," *ISCA 2025*, pp. 1–17. DOI: 10.1145/3695053.3731101 [可靠]

### 建模维度
- 可配置硬件模板（算力/存储/通信三资源权衡）+ 解耦调度策略；平均整体性能 3.12× [可靠]
- 物理维度：无热/bump/布线/C4；面积是资源预算 [中等]

### 在我们框架里的位置
- 性能环节（LLM 场景）+ 架构-调度耦合；与 TickTock 同属"wafer-scale 计算侧 co-exploration"家族——对交换机场景不可直接移植，但"三资源权衡"（compute/memory/comm）与我们的"五族权衡"叙事同构，可引为旁证。

## 3. AgenticDSE（DAC 2025）—— LLM 多智能体 + BO

- 面向 chiplet 加速器（LLM 推理）：三 LLM 智能体（探索编排/架构分析/优化工程）+ 多阶段 BO + 集成代理；距真实 Pareto 前沿平均距离 -36.9%，前沿多样性 +66%，token 消耗 -46×/18× [中等：摘要级]
- 在我们框架里的位置：纯搜索策略创新，物理模型维度更少（性能/功耗/面积目标）——**搜索方法再先进，模型还是单环节的**。

## 4. MCT-Explorer（ICCAD 2024）—— 高维 BO

- 蒙特卡洛树搜索 + 信息引导多目标优化，数百维 AI SoC 参数；cycle/area/power [中等]
- 通用微架构 DSE，无 chiplet/晶圆物理。

## 5. AI-Driven Bump Pitch 优化（ICCAD 2024）—— 单参数物理量 DSE

- ML 预测 bump pitch 对 PPA/信号完整性/电源完整性/热完整性的影响 + BO 选最优 pitch；插值误差 2.69%、外推 2.7%，优化平均改进 11%（面积/线长/SI）/9%（功耗/热）[中等]
- 在我们框架里的位置：**μbump 环节的唯一"DSE 化"工作，但只扫一个参数（pitch），不联立流量**——恰证明 μbump 环节作为独立 DSE 维度是存在的（我们不是造需求），但没人把它接进流量驱动的约束链。

## 子集论证小结
ML 加速是搜索层（外层）的军备竞赛，与物理建模层（内层）正交：Theseus/WSC-LLM/AgenticDSE/MCT-Explorer 全部止步于"目标优化"，无人把多族物理约束写成同变量的联立不等式。**我们的双夹逼（乐观性能下界 + 悲观物理上界）与它们的 BO 目标函数正交**——它们可以优化 B*，但 B* 的语义（可行性判定）只有我们能给。

## 缺口与下一步
1. AgenticDSE/MCT-Explorer/BO bump-pitch 三篇的原文细节需下载核对（现为摘要级 [中等]）
2. 考虑在论文里把 BO 列为外层离散枚举的可选实现（与 ID3、枚举并列）——引 Theseus 的多保真度 BO 为例

## 来源
- [Theseus TCAD (IEEE Xplore)](https://ieeexplore.ieee.org/document/10981855)；[arXiv:2407.02079](https://arxiv.org/pdf/2407.02079v1)
- [WSC-LLM (Semantic Scholar)](https://www.semanticscholar.org/paper/03f83325c16be16996736949dc2039d289f7c086)
- [AgenticDSE (IEEE)](https://ieeexplore.ieee.org/document/11126287)
- [MCT-Explorer (ACM)](https://dl.acm.org/doi/abs/10.1145/3676536.3676746)
- [AI Bump-pitch BO (IEEE)](https://ieeexplore.ieee.org/document/11126228)
