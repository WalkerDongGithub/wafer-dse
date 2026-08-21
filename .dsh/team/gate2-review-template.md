# Gate② 评审框架（master 审 benchmark-matrix 用）

> 用途：LiteratureSearcher 的《insight 对标矩阵》落盘后，master 按本框架逐条审查 → 汇成 Gate② 决策单呈用户。
> 依据：`notes/INSIGHT_READING.md`（claim 定案）、`contributions.md`（C1-C4）、`paper-skeleton.md` §3（Related Work）。

## 逐条审查模板（insight 1-7 各一遍）

| 字段 | 检查 |
|---|---|
| 结论分档 | 成立 / 需限定 / 需弱化 / 有反例（LiteratureSearcher 已给） |
| 覆盖度分档 | 完全没有 / 部分覆盖（哪里不足）/ 已有先例（=验证） |
| 证据质量 | 是否带**原文引文**？"待核实"是否过多？ |
| 对贡献的影响 | 影响 C1-C4 哪条？需要软化/强化措辞？ |
| Related Work 落点 | 进 §3 哪小节（3.1 晶圆级 / 3.2 chiplet DSE / 3.3 包络先例 / 3.4 热） |

## 重点交叉核验（Gate② 必查）

1. **C1 gap claim（insight 4）**：RapidChiplet / FireLink / FPIA 是否真的不覆盖 thermal+performance 联合判断？
   - 若"部分覆盖"→ C1 措辞从"填补空缺"降级为"未覆盖 I2I/Substrate 跨层与联合判断"，保留"xxx vs xxx"评价空间（INSIGHT_READING §二.5）。
2. **C3 先例定位（insight 6）**：oblivious routing 负载因子/dilation（Valiant & Brebner 1981、Räcke 2002）证据是否到位？
   - 先例=验证：进 §3.3，正文区分"概念先例"与"集成贡献"（物理-拓扑解耦桥梁、BvN 逐链路 LP、晶圆级落地）。
3. **C4 复杂度表述（insight 7）**：是否有文献声称该问题 NP-hard？
   - 若有→正文必须区分内外层（外层 NP-hard 借用成熟流程；内层可多项式全局最优），避免正面冲突。
4. **B 术语映射**：对标遇"无阻塞带宽/throughput/额定带宽"概念时，是否做了术语映射（防误判覆盖度）？
5. **insight 1/2/3/5**：定位性主张证据需求低，重点确认没有"反例"级发现。

## 输出：Gate② 决策单（呈用户）

- 每条 insight 一行结论（分档 + 覆盖度 + 证据），标绿/黄/红
- 需要**软化/降级**的条目：给建议替换表述（可直接进 contributions.md）
- 需要用户拍板的点：C1 措辞定稿（decisions.md #4）、被削弱的 insight 处理
- 放行 Phase 3 的条件：红色条目（有反例）已处理、黄条（需限定）已给替换表述
