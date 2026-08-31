# 完整论文草稿整合计划（draft-integration-plan）

> DomainExpert 主持，2026-08-21。作者纪律：可做可不做→不做；精准切题；**当前关键路径 = 论文本体成文**（数据/调研/建模已齐，缺完整草稿）。
> 骨架：`paper-skeleton.md`（ISCA 结构）。目标：整合成完整可读草稿（正文 + 附录骨架），供 Gate④ insight 纪律检查与后续打磨。

---

## 1. 素材盘点（已就绪 vs 缺口）

| 章节 | 素材现状 | 缺口 |
|---|---|---|
| Abstract | `paper-drafts/abstract.md`（v0.1，数字已定） | 微调（整合时同步最新口径） |
| 1 Intro | — | **缺整章**（背景/问题/gap/贡献/预览） |
| 2 Background & Motivation | — | **缺整章**（三层实体/为什么现有不够/关键观察） |
| 3 Related Work | `related-work-draft.md`（LiteratureSearcher，76 行）+ `benchmark-matrix.md`（239 行，引文核验） | 整合润色 |
| 4 Model | `paper-drafts/s4-model.md`（v0.1 方法章草稿） | 内容已核（技术复核通过）；占位段已定稿 |
| 5 Evaluation | `experiment-design.md`（E1-E8 判据）+ `data-report-e1-e5-e6-ec.md`（数据）+ `sensitivity-design.md`（§5.5） | **缺整章草稿**（5.1-5.6 组织 + 数字回填） |
| 6 Discussion | — | **缺整章**（6.1-6.3） |
| 7 Conclusion | — | **缺整章** |
| 附录 | 素材散落（附录 A-C 素材在 V5/IMPLEMENTATION_MAP） | 骨架先立，正文定后补 |

## 2. 分派（WritingPolisher 主笔 + DomainExpert 审）

| 章节 | 主笔 | 素材输入 | 状态 |
|---|---|---|---|
| Abstract 微调 | WritingPolisher | abstract.md | 待整合 |
| 1 Intro | WritingPolisher | skeleton §1 + contributions C1-C4 + benchmark-matrix gap 证据 | 待写 |
| 2 Background & Motivation | WritingPolisher | skeleton §2 + INSIGHT_READING + 标准耦合案例 | 待写 |
| 3 Related Work | WritingPolisher | related-work-draft.md + benchmark-matrix（引文核验版） | 待整合 |
| 4 Model | WritingPolisher | s4-model.md（已核）+ §4.2.2 正式措辞 | 已草稿，待整合 |
| 5 Evaluation | WritingPolisher | experiment-design（E1-E8 判据）+ data-report（数字）+ sensitivity-design（§5.5） | 待写（数字回填） |
| 6 Discussion | WritingPolisher | skeleton §6 + sensitivity 叙事 + 未来工作 | 待写 |
| 7 Conclusion | WritingPolisher | skeleton §7 | 待写 |

**DomainExpert 职责**：审每章内容（技术结论/claim 边界/与 V5 与数据一致）+ 统一口径（10/72 主口径、术语按 terminology-ledger、数字一致性）。

## 3. 统一口径（整合纪律，全员一致）

1. **10/72 主口径**：耦合分歧 = 10/72 构型 rel_diff>1%，max 0.80（Mesh(3)），机制 = 固定路径拥塞 vs 联合绕行——论文所有章节此数字唯一；
2. **术语**：terminology-ledger v0.5（two-level DSE / rated bandwidth B / expansion-ratio envelope / KKT multipliers / unlocking rate）；
3. **数字一致性**：摘要数字与 §5 表可复现对齐（ρ=1.0 / 10-72 / 灵敏度误差 ≤0.7%）；
4. **边界诚实**：C2-C4/sub 热 = 规范未来工作；耦合域 = 布线饱和 + β_P 小（如实界定）；B\* 排序 = 热约束下排序（标注绑定族）。

## 4. 整合进度表（关键路径每日推进）

| 章节 | 负责人 | 状态 | 完成标准 |
|---|---|---|---|
| 1 Intro | WritingPolisher | 🔲 待写 | 贡献 4 条清晰 + gap 有证据 |
| 2 Background | WritingPolisher | 🔲 待写 | 三层实体 + 耦合案例入 |
| 3 Related Work | WritingPolisher | 🔲 待整合 | 引文核验版 + xxx vs xxx 框架 |
| 4 Model | WritingPolisher | ✅ 草稿已核 | 整合进主稿 |
| 5 Evaluation | WritingPolisher | 🔲 待写 | 数字回填 + 判据对应 |
| 6 Discussion | WritingPolisher | 🔲 待写 | 灵敏度叙事 + 未来工作 |
| 7 Conclusion | WritingPolisher | 🔲 待写 | 复述主线 |
| 全稿审 | DomainExpert | 🔲 待审 | 每章内容/口径/数字一致 |

**执行方式**：WritingPolisher 按章节产出（每章落盘 `paper-drafts/`），我逐章审（内容 + 口径），成稿合并为完整草稿 `paper-drafts/draft-v0.md`。

## 5. 待决点清单（给 master 呈作者）

1. **标题**：title-candidates.md 三候选（候选 1 包络机制推荐 / 候选 3 T1 精简 / 候选 2 量化）——Gate① 未终决，写作可用占位，投稿前定；
2. **贡献声明 4 vs 3 条**：当前 4 条（C1-C4）；3 条合并备选（C2+C3 或 C3+C4）——影响 Intro/Conclusion 表述，**建议尽快定**（写作前）；
3. **目标会议**：ISCA 已定（12 页正文），写作按 ISCA 篇幅。

## 6. 版本记录

- v0.1（2026-08-21）：整合计划（素材盘点 + 分派 + 口径 + 进度表 + 待决点）。
