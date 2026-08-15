# 卡片 01：FPIA —— 布线环节的单一实现

> 对应研究议程 2.4 方法论对标必做清单 #1。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## 出处

- **Bo Jiao, Lei Xu, Xinyu Yu, et al.**, "FPIA: Communication-Aware Multi-Chiplet Integration With Field-Programmable Interconnect Fabric on Reusable Silicon Interposer," *IEEE TCAS-I*, vol. 71, pp. 4156–4168, 2024. DOI: 10.1109/TCSI.2024.3419579 [可靠]
- 单位：复旦大学芯片与系统前沿技术研究院 + 中科院计算所；基金：国家重点研发 2023YFB4404402
- 关联：现有 notes 已把它当作布线约束（MATH_MODEL §2.4）的物理来源，本卡片补方法论细节

## 建模维度清单

| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ○ | 不建模拓扑性能（无流量/无阻塞分析）；只给互连延迟电学测量：最大 2.2 ns；比 SOTA NoP 可复用 interposer 省 16.5×–53.4× 时钟周期 [可靠] |
| 功耗 | ○ | 能量密度 1.18 pJ/bit @ 1 Gbps 为 fabric 电学测量，非设计变量 |
| 热 | — | 无 |
| bump | ○ | μbump 是布线网络的终端（bump-to-bump routing），但**不建模 bump 预算约束**（信号与电源不竞争） |
| 布线 | ● | 核心：turnout box + crossover box + parallel tracks 的可编程 fabric；自动 chiplet placement + bump-to-bump routing [可靠] |
| 成本 | — | 无（"reusable interposer 省钱"是动机陈述，无量化的成本模型） |

## 模型是否硬编码、是否可替换

- 工具形态：自动物理集成流程（placement + routing 算法），参数化但**流程固定**——它是"布线环节的一种求解器"，不是可插拔模型接口。模型不可替换 [中等]
- 验证：9 种集成场景，局部资源利用率 94.5% 时可保证可布线性 [可靠]

## 搜索方法与单次评估代价

- 搜索：启发式 placement + 布线（非枚举、非 ML）；单次 P&R 秒~分钟级 [中等]
- 无 DSE 概念：不扫参数空间，给定集成方案出 P&R 结果

## 在我们框架里的位置

- **对应环节：布线（§2.4）——五环节之一。**
- 缺：性能（§2.1）、μbump 预算（§2.3）、C4（§2.6）、热（§2.5）、成本。五个环节它只碰一个，且该环节内它做"实现"（怎么布），不做"判定"（流量驱动的 lane 数能不能放下）。
- 耦合如何断开：FPIA 的输入是"要连哪些 chiplet 对、带宽多少"——这正是我们 LP 解出的 ℓ（链路负载 → lane 数）。我们输出 ℓ 后，FPIA 可作为 §2.4 的一种**实现级验证**（我们的容量不等式 C 是保守上界，FPIA 是精确实现检查）。方向是单向的：我们的 ℓ 喂给它，它的结果不回喂我们的 LP。
- 子集论证价值：**"布线环节工具只做布线"的最干净例子**——作者自己声明 scope 限于 layout+routing，不涉性能/热。

## 缺口与下一步

1. 原文的 94.5% 可布线性定义（拥塞度量）需下载核对，作为我们 C 容量保守性论证的对照
2. 可考虑与 FPIA 作者版本的可编程 fabric 参数（track 数、turnout 粒度）对齐我们的 R 矩阵系数

## 来源

- [IEEE Xplore 摘要页](https://ieeexplore.ieee.org/abstract/document/10586747)
- [Semantic Scholar 条目](https://www.semanticscholar.org/paper/c5fc77bcc8bb504f42067a0c3f0222dfb818a21a)
