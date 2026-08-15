# 卡片 08：Yang et al. ISCA 2025 —— NoW 物理/逻辑拓扑 co-design（"TickTock"）

> 对应必做清单 #8。现有笔记称其为"TickTock"，本卡片标注该昵称的核对状态。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## 出处

- **Qize Yang, Taiquan Wei, Sihan Guan, Chengran Li, Haoran Shang, Jinyi Deng, Huizheng Wang, Chao Li, Lei Wang, Yan Zhang, Shouyi Yin, Yang Hu**, "PD Constraint-aware Physical/Logical Topology Co-Design for Network on Wafer," *ISCA 2025*, pp. 49–64 [可靠]
- 作者单位：检索未直接确认（dblp 上 Yang Hu / Shouyi Yin 关联清华 BNRist 系，但本论文单位需核对）[待确认]
- ⚠️ **"TickTock"昵称未在检索中复现**——论文标题与摘要均无此字样。现有 LITERATURE_SURVEY.md B4 用该昵称，引用时用正式标题，昵称仅作内部代号 [待确认]

## 建模维度清单

| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ● | LLM 训练吞吐目标；mesh-switch 物理拓扑 + 双粒度逻辑拓扑；vs SOTA mesh-based NoW 提升 2.39× [可靠] |
| 功耗 | ○ | PD 约束含功率（具体形式待核对原文）[中等] |
| 热 | — | 检索未见热约束 [待确认] |
| bump | — | 无 |
| 布线 | ○ | "物理拓扑"即 D2D 连接方案；50mm 最大 D2D 链路（超出则 BER 108×、延迟 210ns）——这是**链路级 PD 约束**，非布线容量模型 [可靠] |
| 成本 | — | 无 |

## 模型是否硬编码、是否可替换

- 针对 NoW 定制流程（mesh-switch 物理拓扑 + 双粒度逻辑拓扑 + 并行策略），**流程绑定场景**，非通用可替换接口 [中等]

## 搜索方法与单次评估代价

- 迭代 co-design（物理 ↔ 逻辑 ↔ 并行策略 交替优化），启发式；评估代价 [待确认]（LLM 训练吞吐仿真，分钟级起）

## 在我们框架里的位置

- **对应环节：性能（§2.1）+ 链路级 PD 约束（接近 §2.4/§2.6 的简化版）。**
- 缺：μbump 预算（§2.3）、C4（§2.6）、热（§2.5）、布线容量（§2.4 的完整形式）。
- 耦合如何断开：他们的 co-design 是**两两耦合**（物理↔逻辑↔并行策略三环互锁的迭代优化）；我们是**五族同变量联立求解**。他们的"50mm 链路、50,000mm² 面积"物理参数与我们同源（TSMC wafer 尺寸），可直接作为我们 baseline 参数交叉验证。
- 子集论证价值：**最全面的 NoW DSE 同行，仍然只有性能+部分 PD 约束**——它面向 LLM 训练（compute-centric），我们是交换机（communication-centric）；它无热、无 bump、无 C4、无联立 LP。"最全面的同行"缺四环，是 §8 最强的一行。

## 缺口与下一步

1. 下载原文确认：功耗约束形式、热有无、搜索/评估代价
2. 确认作者单位与 "TickTock" 昵称出处（可能来自会议演示或二手资料），必要时勘误 LITERATURE_SURVEY.md B4

## 来源

- [ACM ISCA 2025 论文集](https://dl.acm.org/doi/proceedings/10.1145/3695053)
- [Semantic Scholar 条目](https://www.semanticscholar.org/paper/PD-Constraint-aware-Physical-Logical-Topology-for-Yang-Wei/d4ac0754e41ade62bce88919accfde1b14e49f63)
- [researchr 页面](https://researchr.org/publication/YangWGLSDWLWZYH25/bibliographies)
