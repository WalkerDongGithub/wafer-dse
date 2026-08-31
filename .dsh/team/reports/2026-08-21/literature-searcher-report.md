# LiteratureSearcher 工作汇报（给作者）

> 2026-08-21 ｜ 文献与对标研究员

## ① 为什么做

论文要论证"前人没做过 / 做得不够"，而且每句话都得有文献依据——否则审稿人一查引用就露馅。我的工作就是**把论文的"背景、动机、相关工作"这些立论基础查清楚、查扎实**：7 条 insight 前人到底做没做过、缺在哪；论文要引的每一篇文献真实存在、信息准确。

## ② 做了什么

- **7 条 insight 逐条对标**：每条回答"前人有没有、是部分覆盖还是验证"，写成《insight 对标矩阵》（`.dsh/team/artifacts/benchmark-matrix.md`）；
- **引言 19 条论断的文献支撑核查**：哪些论断有证据、哪些要弱化措辞（`.dsh/team/artifacts/gap-evidence-chain.md`）；
- **Related Work 英文初稿**：按论文结构写好 §3.1-3.5（`.dsh/team/artifacts/related-work-draft.md`）；
- **全量参考文献 .bib**：62 条，逐条经 DBLP（计算机论文第一数据库）/CrossRef/arXiv 核对（`.dsh/team/artifacts/paper.bib` + `bib-verification-report.md`）；
- **两项专项调研**：① chiplet/晶圆布局算法（外层布局不自己造轮子，调研+引用）；② 热阻网络与散热建模（不同封装/散热方式怎么建模进 G·T=P+b）——供模型和论文用；
- **纠正了 7 处引用错误**（例：热模型 MFIT 原来是"Zhang 某会议 2025"，实际是 Pfromm 等人发在 ACM TODAES；Switch-Less Dragonfly 原来是"USENIX ATC 2024"，实际是 SC 2024）。

## ③ 达到什么效果

- **insight 6（扩展比包络）**：找到扎实的先例链（Valiant 1981 负载均衡 → Räcke 2002/2008 路由竞争比 → Azar 2004 可用线性规划求解）——先例=验证，相关工作里直接引用定位；
- **insight 4（多因素耦合）**：坐实"现有工具把热和性能分开做"（RapidChiplet 原文自己写"热分析用外部工具 HotSpot"），但发现两篇论文（TickTock、Chen ISCA'24）已做部分联合——措辞已按"xxx vs xxx"限定，避免审稿人抓；
- **引用全部核验**：62 条无编造；7 处错误已修正，V5 模型文档里的 MFIT 引用也同步修正闭环；
- **模型有物理依据**：热建模的"散热板是节点不是固定边界"、3D 堆叠按层还是按堆叠建模等结论，都有文献和公式支撑（`thermal-network-survey.md` / `thermal-modeling-dimensions.md`），DomainExpert 构建 G 时直接对照，物理量经逐条核对无错。

**一句话**：论文的"别人没做过"和"我们引的都对"这两件事，已经查实、落盘、可复核。
