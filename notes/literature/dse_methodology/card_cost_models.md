# 卡片 09：成本模型三式 —— Kannan 良率 / CATCH / ChipletActuary

> 新增发现：chiplet 成本模型是 2023–2025 的活跃方向，但全部是单维度（成本）模型。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## 1. Kannan et al.（IEEE Micro 2016）—— 拆分/良率成本模型的开山

### 出处
- "Exploiting Interposer Technologies to Disintegrate and Reintegrate Multicore Processors," *IEEE Micro*, 2016. DOI: 10.1109/MM.2016.53（HPCA 2015 版的前身工作）[可靠]

### 建模维度与核心数字
| 维度 | 有无 | 细节 |
|---|---|---|
| 成本 | ● | 良率模型 + 关键面积框架：A_crit = A × F_crit；300mm 晶圆 64 核 SoC：单芯片 297mm² 良率 84.5%（162 good dies/wafer）→ 拆成 4 核 chiplet（18.6mm²）良率 98.9%（209 good SoCs/wafer，+29%）；passive interposer 关键面积小→良率高；active interposer 大关键面积→近 reticle 极限良率崩 [可靠] |
| 性能/功耗/热/bump/布线 | — | 全无（speed-binning 涉及性能但只是装配策略） |

### 在我们框架里的位置
- 对应环节：**成本**——我们框架中成本目前是外层选型（封装 profile 选择）的判据，未进 LP 内约束族。Kannan 的"die 面积↔良率"模型正是我们 §2.8 die 缩放模型（d(B) → A_die(B)）的成本侧配套。

## 2. CATCH（2025）—— 全流程成本分析工具

### 出处
- "CATCH: a Cost Analysis Tool for Co-optimization of chiplet-based Heterogeneous systems," arXiv:2503.15753, 2025 [可靠]

### 建模维度与核心数字
| 维度 | 有无 | 细节 |
|---|---|---|
| 成本 | ● | 覆盖 2D/2.5D（Si/有机/玻璃 interposer）/3D（TSV）；互连技术参数（μbump/hybrid bonding/TSV 的带宽-间距-面积）；制造（wafer 成本、缺陷密度、良率、reticle）；装配（键合、基板、良率）；测试（KGD/中间/终测、故障覆盖率、逃逸）；NRE [可靠] |
| 其他 | — | 无性能/功耗/热/布线/bump 约束 |

### 关键结论（[中等]：来自摘要级信息）
- 先进节点（3/5nm）成本最优 chiplet 尺寸 ~16–25mm²，成熟节点 9–25mm²；缺陷密度高→chiplet 越小越好；最优故障覆盖率 ~0.9–0.95；<2–4mm² 有装配/NRE 惩罚，>50mm² 良率崩。

### 在我们框架里的位置
- **成本环节的最完整实现**——它把"成本"拆成制造/装配/测试/NRE 四账本，但仍是与物理环节无关的独立维度。它的"成本最优 chiplet 尺寸"可与我们的 B* 一起回答"这个拓扑该拆多碎"——外层枚举 + 内层联立的自然分工。

## 3. ChipletActuary（成本工具，来源 [中等]）

- 仅见于 RapidChiplet 的引用语境（"ChipletActuary (cost)"），作为 ICI 成本估计的配套工具；单维度成本，细节待挖 [待确认]

## 子集论证小结
**成本环节是 2023–2025 最热的单维度方向之一，但三式都是"成本只算钱"**——没有一家把成本与性能/功耗/热联立。这恰好支撑"每个环节都有专门工具、没有联立框架"的图景；同时也提醒：我们的框架里成本在哪个位置（外层选型 vs 内层约束）要在论文里交代清楚，否则会被追问"为什么不做成本约束"。

## 缺口与下一步
1. Kannan 原文的良率公式形式（Poisson/负二项）与 CATCH 的对比——若我们论文引用良率曲线，用 CATCH 更新数据
2. ChipletActuary 的出处与细节待挖（可能是 ETH 内部工具）

## 来源
- [Kannan 2016 (IEEE Micro)](https://ieeexplore.ieee.org/document/7497649)
- [CATCH alphaXiv](https://www.alphaxiv.org/overview/2503.15753)
