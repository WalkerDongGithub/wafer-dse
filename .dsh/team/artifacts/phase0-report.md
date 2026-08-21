# Phase 0 立项报告（phase0-report）

> DomainExpert 最终汇报落盘（2026-08-20）
> 前置：Gate① 决策单此前以会话消息交付 master；本文件将其结论固化落盘（stateless 约定），并附 Phase 0 完成情况
> 决策记录见 `.dsh/team/decisions.md`（master 维护，暂定默认可推翻）

## 1. Phase 0 产出清单（均已落盘 `.dsh/team/artifacts/`）

| 产出 | 文件 | 要点 |
|---|---|---|
| ISCA 结构骨架 | `paper-skeleton.md` | Abstract→7 章+附录；每章每节一句要点；两层 DSE 故事线；全局纪律（道术分层/术语定案）+ 图清单 6 张 |
| 贡献声明草案 | `contributions.md` | C1-C4 共 4 条，各标注 insight 编号 + 定案表述；附 3 条合并备选 |
| insight 编排表 | `insight-orchestration.md` | insight 1-7 → 主/辅落点 + 作用 + 备注；道术分层检查；Gate④ 纪律依据 |
| 标题候选 | `title-candidates.md` | 正式候选 3 个（机制/量化/无需启发式三路线）+ 与 T1 关系 + 推荐 |

## 2. 例会 Do 汇总

- **做了什么**：通读 4 份灵魂文档（V5 全文 / insight 7 条 / INSIGHT_READING / PAPER_TEAM_WORKFLOW）→ consult-team 查团队目录（wafer-dse 4 平级会话，LiteratureSearcher 已并行开工）→ 产出 Phase 0 四件套 → 应答 LiteratureSearcher 开工前咨询（q-ed34a255，已 complete）。
- **谁的问题被谁解决**：V5 §5.3 整体问题定位（非凸但可多项式全局最优、不强调"是 LP"）、B 正名（有 QoS 保证的额定出入口带宽）、二分/单调性不上台面、insight 6/7/4 的 claim 定案——全部内化进骨架、贡献与编排表；LiteratureSearcher 对标口径已确认（分档 + 结论分档 + 引文）。
- **谁的问题没解决**：C1"首个/填补空缺"措辞——等 Gate② 对标矩阵回来定稿（decisions.md #4，已如此记录）；Related Work 引文证据链归 LiteratureSearcher（Phase 1 主任务）。
- **满意度自评**：结构骨架完整、贡献 4 条逻辑自洽（C2/C3 是 C1 两大支点，C4 是方法论卖点）、编排表可直接支撑 Gate④ 纪律检查。待拍板项见下。

## 3. Gate① 决策单（结论固化）

| # | 决策点 | 推荐/暂定 | 状态 |
|---|---|---|---|
| 1 | 目标会议 | ISCA（用户已定） | ✅ 定案 |
| 2 | 贡献声明 | 4 条（C1-C4）定稿；3 条合并为备选 | 暂定（decisions.md #2） |
| 3 | 标题 | 候选 1《Bandwidth Envelopes as Topological Invariants: Two-Layer DSE for Wafer-Scale Network Switches》首选；T1/候选 3（无需启发式路线）备选 | 暂定 T1（decisions.md #3），可改 |
| 4 | C1 措辞 | 去"首个"；"填补空缺"待 Gate② 对标矩阵 | 待 Gate② |
| 5 | 篇幅与风格 | 正文约 12 页（双栏含图，参考文献另计）；图 6 张；方法章"输出与用途"为主线；LP/对偶/二分附录化；不引复杂性战争；热只引 MFIT（ACM TODAES，DOI 10.1145/3765905） | 待用户确认（无异议即按此执行） |
| 6 | 阶段时序 | Phase 1（LiteratureSearcher 对标）与 Phase 2（EvalDesigner 实验设计，已放行）并行推进 | ✅ 已放行 |

## 4. 需用户最终拍板的点

1. 标题：候选 1（包络机制）/ 候选 2（B\* 量化）/ 候选 3 或 T1（无需启发式）——`title-candidates.md` 有推荐与权衡。
2. 贡献声明：4 条定稿 or 合并 3 条（`contributions.md` 末尾有合并选项）。
3. 篇幅风格：正文约 12 页规模、图 6 张是否认可。

> 以上拍板前均按暂定默认执行（decisions.md）；用户可随时推翻。
