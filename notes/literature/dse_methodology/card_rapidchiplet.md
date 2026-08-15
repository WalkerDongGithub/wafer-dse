# 卡片 02：RapidChiplet —— 多维度但各维度独立评估

> 对应必做清单 #2。ETH Zurich 最接近"全维度"的工具，但联立是它的结构性缺口。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## 出处

- **Patrick Iff, Benigna Bruggmann, Blaise Morel, Maciej Besta, Luca Benini, Torsten Hoefler**, "RapidChiplet: A Toolchain for Rapid Design Space Exploration of Inter-Chiplet Interconnects," *ACM Computing Frontiers (CF) 2025*, DOI: 10.1145/3719276.3725170；arXiv:2311.06081 (2023 初版, 2025 大改) [可靠]
- 开源：ETH spcl 实验室

## 建模维度清单

| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ● | 分析代理：加权图模型的延迟代理 + 基于带宽/流量的吞吐代理；可接 BookSim2 精仿 [可靠] |
| 功耗 | ● | chiplet 功耗估计（compute/memory/IO chiplet 区分）[可靠] |
| 热 | ○ | 摘要声称预测 "thermal stability"，据现有笔记为封装级简化模型，未与性能联立 [待确认：需读原文确认热模型形式与耦合方式] |
| bump | ○ | 封装技术/链路带宽是输入参数，无 bump 预算约束 |
| 布线 | ○ | ICI 拓扑由输入给定（15+ 拓扑），工具不求解布线 |
| 成本 | ● | 含良率模型的制造成本估计（yield model）[可靠] |

## 模型是否硬编码、是否可替换

- 输入统一格式（packaging/technology/chiplets/placement/topology/routing/traffic）——**参数级可配置**，但各维度模型本身是固定实现的分析代理，不提供模型替换接口 [中等]
- 与 BookSim2 的集成是"精仿验证"而非"模型替换"

## 搜索方法与单次评估代价

- 搜索：自动 DSE 工具箱对参数网格**枚举扫描**（sweep → 评估 → 可视化），非 ML 导向
- 单次评估：**毫秒级**；相对 cycle 仿真平均延迟代理快 ~1,075×（误差 ~2.57%）、吞吐代理快 ~69,079×（误差 ~25.12%）；综合 427×–137,682× 加速、0.25%–30.15% 精度损失 [可靠]

## 在我们框架里的位置

- **对应环节：性能（§2.1）为主，功耗/成本（进 §2.3/§2.5 的系数）为辅。**
- 缺：μbump 预算（§2.3）、C4（§2.6）、热联立（§2.5）、布线（§2.4）。它把性能、功耗、成本、热**分别算好并列报告**，但没有共享变量、没有约束联立——这是与我们最本质的差异：**我们让这些维度互相竞争同一个 ℓ（链路负载）；它让它们各自独立随设计点变化。**
- 耦合如何断开：RapidChiplet 的评估是"给定设计点 → 各维度独立出数"；我们的 LP 是"给定 B → 联立找可行 ℓ"。它的 DSE 扫描可以复现我们的 B* 结果（在它的模型下），但给不出"哪个约束 binding、影子价格多少"——它没有对偶结构。
- 子集论证价值：**"多维度但非联立"的代表**。论文 §8 需要明确区分三级：(a) 独立评估（RapidChiplet）；(b) 两两 co-design（TickTock）；(c) 统一数学规划联立（我们）。

## 缺口与下一步

1. 读原文确认 thermal 模型（后验检查还是约束？）——这决定它在"热环节"格子里的标记
2. 它的 yield 成本模型与 CATCH/Kannan 的差异可做"成本环节"三种实现的对标
3. 427×–137,682× 加速数据可直接引用为"为什么分析模型（LP 也是）是 DSE 正确工具"的论据

## 来源

- [arXiv:2311.06081](https://arxiv.org/abs/2311.06081)
- [ACM CF'25 版](https://dl.acm.org/doi/full/10.1145/3719276.3725170)
- [SemiEngineering 报道](https://semiengineering.com/a-fast-and-unified-toolchain-for-rapid-design-space-exploration-of-chiplet-architectures/)
