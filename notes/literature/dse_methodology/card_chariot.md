# 卡片 04：CHARIOT —— 信息待核实的 interposer 通信感知 DSE

> 对应必做清单 #4。现有 LITERATURE_SURVEY.md C4 信息最薄弱且无法复现，本卡片标注核对状态。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## 出处（两条线索，尚未合拢）

- **线索 A（现有笔记 C4）**：CHARIOT，2024，"2.5D/3D interposer 的 communication-aware DSE，多目标贝叶斯优化，最佳 passive/active interposer 设计达 1.33×/1.96× 能效提升"，来源标注"DTIC Dimensions"。**两次英文检索（含 DTIC 关键词、具体数字 1.33/1.96）均无法复现该条目，链接失效** [待确认]
- **线索 B（检索新发现）**："CHARIOT: A Communication-Aware Exploration Framework for 2.5D/3D Silicon Interposer Design," *ACM TODAES*, DOI: 10.1145/3815192，状态 "JUST ACCEPTED"（2026-04 接收，2026-05-09 挂网），作者 Xiankui Xiong（ACM 作者主页关联 ZTE 机构访问）。摘要未公开，检索无法确认其方法与数字 [待确认]

两线索可能是同一工作从预印/机构库到期刊的演变，也可能是两个同名不同工作。**引用前必须核对。**

## 建模维度清单（基于线索 A 的声称，全部 [待确认]）

| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ○ | "communication-aware"：通信开销/能效为目标 |
| 功耗 | ○ | 能效提升 1.33×（passive）/ 1.96×（active）为声称结果 |
| 热 | — | 未提及 |
| bump | — | 未提及 |
| 布线 | ○ | interposer 设计（passive/active 结构）为决策对象 |
| 成本 | ○ | interposer 类型（passive/active）隐含成本取舍 |

## 模型是否硬编码、是否可替换

- 未知 [待确认]

## 搜索方法与单次评估代价

- 声称：多目标贝叶斯优化 [待确认]
- 评估代价：未知 [待确认]

## 在我们框架里的位置

- 若线索 A 属实：interposer 设计环节的 DSE，对应我们的布线/封装侧（§2.4/§2.6），缺性能、μbump、热、联立。
- 但在核对之前，**本卡片不进入对比矩阵的论证性引文**——只占矩阵一行并标注 [待确认]。

## 缺口与下一步

1. 用 DOI 10.1145/3815192 向 ACM 图书馆通道（或 ZTE 机构访问）取摘要，确认方法（是否 BO、是否 passive/active 对比、数字 1.33/1.96 是否存在）
2. 若线索 A 是笔误（可能混淆了另一篇 DTIC 论文），在 LITERATURE_SURVEY.md C4 上标注勘误
3. 注意检索到的无关同名项（Chiplever、CLIPGen 等）不要误引

## 来源

- [ACM TODAES DOI 页](https://dl.acm.org/doi/10.1145/3815192)
- [作者 ACM 主页](https://dl.acm.org/profile/99660880500)
