# ISCA 标题候选（title-candidates）

> Phase 0/Gate① 补充产出（DomainExpert，2026-08-20）
> 状态：master 暂定 T1（见 `.dsh/team/decisions.md`）；本文件给正式候选 3 个（含 T1 精简替代），供用户最终拍板
> 定案表述约束：B\* = 有服务质量保证的额定出入口带宽；两层 DSE；扩展比包络 = 拓扑不变量；整体非凸但存在可多项式时间求解的全局最优解、不需启发式

## 候选 1（推荐：机制辨识度最高，主打 insight 6）

**《Bandwidth Envelopes as Topological Invariants: Two-Level DSE for Wafer-Scale Network Switches》**

- 理由：把论文最独特的技术指纹——"扩展比包络 = 拓扑不变量"（只依赖拓扑+路由+要求，与 B 和物理无关）——直接立上标题；"Topological Invariants"学术分量足、记忆点强，"Two-Level DSE"保留两层框架定位。
- 主打 insight：6（扩展比联系一切；主承重），辅以 1/4（两层框架 + 多因素耦合）。
- 权衡：突出机制，淡化"不需启发式"卖点（该卖点留给摘要与 C4）。
- 术语统一（2026-08-21）：正文定案 two-level DSE（terminology-ledger），标题同步 **Two-Level**（原 Two-Layer 已改）。

## 候选 2（主打 insight 2/3：B\* 量化指标）

**《Rated Bandwidth as a Design Metric: Polynomial-Time Global-Optimal DSE for Wafer-Scale Switches》**

- 理由：直接亮出"额定出入口带宽 B\*"这一量化指标（有 QoS 保证，insight 2/3 的量化主张），同时用"Polynomial-Time Global-Optimal"带出 insight 7 的方法论卖点——量化 + 最优双主轴。
- 主打 insight：2/3（B 作为解的质量量化指标），辅以 7（可多项式全局最优）。
- 权衡：读者第一眼聚焦"带宽作为设计指标"，适合强调 DSE 量化范式转变的叙事。

## 候选 3（T1 精简替代，主打 insight 7）

**《Two-Level DSE for Wafer-Scale Network Switches: Global-Optimal Rated Bandwidth without Heuristics》**

- 理由：结构清晰（对象 + 方法 + 主张），比暂定 T1（"A Two-Level Polynomial-Time Global-Optimal Framework"）更短更聚焦；"Global-Optimal Rated Bandwidth without Heuristics"把 insight 7 卖点与 B\* 量化合一。
- 主打 insight：7（全局最优的可能性：不需启发式），辅以 2/3（B\* 量化）。
- 权衡：与 T1 同路线，是 T1 的精简替代；未突出包络机制（insight 6）。
- 术语统一（2026-08-21）：**Two-Level**（原 Two-Layer 已改，与正文 terminology-ledger 一致）。

## 与暂定 T1 的关系（供用户拍板）

- T1 = 《Wafer-Scale Switch DSE without Heuristics: A Two-Level Polynomial-Time Global-Optimal Framework》——强调"不需启发式"（insight 7）与两层框架，完整但偏长。**术语统一（2026-08-21）：Two-Level（原 Two-Layer 已改）**。
- 三条路线一览：
  | 路线 | 主打 | 标题 |
  |---|---|---|
  | 机制（包络） | insight 6 | 候选 1（推荐） |
  | 量化（B\*） | insight 2/3 | 候选 2 |
  | 无需启发式 | insight 7 | T1 或候选 3（精简） |
- 建议：若追求论文辨识度与独特性 → 候选 1；若强调范式卖点"不需启发式" → 候选 3（T1 精简）；候选 2 适合量化叙事。任何选择不影响正文结构（skeleton 已按两层 DSE 故事线组织，标题只换"门面"）。

## 推荐结论

**首选候选 1**（包络不变量最具独特性，与主承重 insight 6 强绑定）；若 master/用户更看重"无需启发式"的反直觉卖点，推荐候选 3 替换 T1（更短）。最终由用户拍板。
