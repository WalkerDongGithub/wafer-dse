# 论文生产工作流（team-manage 总纲）

> **目标**：把 `insight.md`（7 条 critical insight）推进为一篇顶级 CCF 体系结构会议论文（ISCA / MICRO / ASPLOS / HPCA 之一，目标会议待定）。
> **团队**：team-manage 平级会话；master = 用户主会话。
> **权威层级**：`insight.md`（字节级不变）→ `notes/INSIGHT_READING.md`（作者意图解读）→ `notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md`（唯一权威模型文档）→ 代码/测试/论文（实现与下游产物）。

## 🔒 三份灵魂文档边界（作者硬规则，长期强制）

> 任何人在做的过程中出现**超出三份灵魂文档（V5 经书 / `insight.md` / `STYLE.md`）的技术术语或论证体系**，除非作者新增一个灵魂文档，否则**不得擅作主张**。新术语/新论证/新模型要素要么写入三份之一（经作者确认），要么等作者新增灵魂文档；例子/动机只服务论文叙事与实验设计，不自动变成模型参数或代码实现。

---

## ⚡ 验证阶段执行策略（短期约定，作者 2026-08-21，全员强制；Phase 2-4 期间生效，结束即删）

1. **当前处于多轮迭代的验证阶段，离最终版还很远**。原则：**先验证想法，不要铺大规模**。
2. **实验尺度**：优先跑**小规模、小模型、快速验证**——足以检验"耦合/等价/分歧"这些核心思想是否成立即可；**不必上大模型、不必做大规模网格扫描**。
3. **大实验（需要才跑）**：仅在想法被小实验验证、确需量化时才上；且**一律走 `ssh walker` 远机分流**（chenmz，257GB），不在 WSL 本地扛。
4. **尺度判断**：能回答"方向对不对"就用小实验回答；**精确数值/全面覆盖率留到后期**。
5. **各角色遵守**：DataSteward 实验以轻量验证为主；EvalDesigner 判据先测方向；CodeEngineer 能做通即止，不为流程完备性过度实现。

---

## 📐 文档质量红线（作者核心原则，长期强制，全员开工前必读）

1. **朴素优先**：不做花里胡哨的事。模型优雅重于高端，容易好于困难。
2. **清晰的矩阵表示 > 满篇"鬼画符"**：以 V5 §2 风格为标杆——能用清晰的矩阵/结构表达，就不要堆砌符号。
3. **灵敏度亦然**：几个符号能说清就不要堆砌。
4. **简洁明了**：所有文档越简洁越好。不要做一大堆东西结果作者看不懂；更不要"作者费很大劲弄懂后发现做错了"。
5. **术语克制**：唯一原则——"没有这个术语就无法简洁明了地解释清这个问题 → 鼓励用；只是为了显得自己做得很好 → 建议重做"。不过于朴实，也不滥用术语。
6. **红线执行**：任何文档/模型/公式交付前自查：是否过度堆砌、能否更简明；评审（DomainExpert/InternalReviewer）以此为准打回。
7. **必要性测试（作者定案，动手前必自问）**：我做的这件事，如果我不做，整个任务能不能继续推进？能 → **不做**。可做可不做的一律不做，精准切题。

---

## 1. 论文故事线：两层 DSE

论文不写"我们有一个 LP 模型"，而写**"晶圆级交换机缺一个完整的两层 DSE"**：

```
上层（离散枚举层）：拓扑族 × 布局 × 封装工艺 × 互联标准
    └─ 借用成熟 chiplet DSE 流程（RapidChiplet / FireLink / FPIA 为外层引擎或对标基线）
下层（连续约束层）：给定构型 → 可行性 LP（扩展比包络 + 三层实体 + 跨层耦合 C1-C4）
    └─ 外层二分搜索取最大可行 B* —— 整体非凸，但无需启发式
两层经物理参数接口解耦
```

- V5 是 DSE 的关键一步（下层），嵌入完整流程而非孤立玩具；
- 外层直接对标成熟 chiplet DSE 工具——对标抓手。

## 2. 术语与主张定案（2026-08-20）

| 项 | 定案 |
|---|---|
| $B$ 正名 | **有服务质量保证的额定出入口带宽**（insight 2/3 的"额定带宽"；"无阻塞"仅作 QoS 语义：端口负载 ≤ $B$ 时无阻塞，RNB） |
| 方法主张 | **整体问题（含 $B$）非凸，但存在可多项式时间求解的全局最优解**（二分 + LP：固定 $B$ 可行性为 LP 精确可判且多项式可解，二分 $O(\log)$ 次）——**不需要启发式**；论文**不强调"是 LP"** |
| 性能语言 | 用"包络/预期"（L 包络 = 该构型需支撑额定带宽 $B$ 的负载包络） |
| 热 | 只引 G·T=P+b（MFIT, ACM TACO 2025），不展开传热学物理 |
| 算法/对偶 | 核心论证 = "模型输出什么 + 为什么有用"；LP/对偶细节最多进附录 |
| 二分/单调性 | 不上论文台面（B 只有上限没有下限；低 B 面积约束恒松）；die 缩放单调性只作内部良心检查 |

## 3. 团队构成（平级成员 + master；**本职与旧 `prompt/` 一一对应，不变**）

| 角色卡 | 本职来源（旧 prompt/） | 一句话本职 | 创建节奏 |
|---|---|---|---|
| `00-domain-expert.md` | 03a-domain-expert | 技术总核心、论证主线、整合成稿、主持例会 | Phase 0 |
| `01-writing-polisher.md` | 03b-writing-polisher | 写作润色、风格、术语统一、insight 纪律 | Phase 0 |
| `02-internal-reviewer.md` | 03c-internal-reviewer | 防御性内审（预判审稿人攻击点） | Phase 3 前 |
| `03-figure-artist.md` | 04-figure-artist | 科研配图（**直接生图**，不做提示词） | Phase 0 |
| `04-reviewer-team.md` | 05-reviewers | 4-5 位审稿人独立审稿 + rebuttal 预演 | Phase 4 前 |
| `05-editor.md` | 06-editor | 统合审稿意见、给录用建议（裁决归 master） | Phase 4 前 |
| `06-data-steward.md` | 01a-data-steward | 调 query/写 exp/出数据与基础图 | Phase 2 后 |
| `07-literature-searcher.md` | **新增**（作者点名） | 对标矩阵、gap 证据、bib 校验 | Phase 0/1 |
| `08-eval-designer.md` | **新增**（作者点名） | 针对 insight 设计实验论证、评测规范、artifact | Phase 2 |
| `09-code-engineer.md` | 01-code-engineer | 写高质量代码+接口+测试 | 实验缺口时 |
| `10-code-reviewer.md` | 02-code-reviewer | 代码审查、参数文档对齐 | 随 09 |

> **本职不变原则**：新角色卡保留旧人物的本职（各卡注明"本职源自旧 `prompt/xx`"）；只升级机制（team-manage 平级 + master 唯一通道 + ccf 装备 + 定案术语 + 直接生图）。07/08 是作者点名的新职能，不挤占任何旧人物。
> **协作质询关系（ask 关系，作者定案）**：DataSteward 发现代码问题 → 质询 CodeEngineer；CodeEngineer 需求不明/怀疑模型 → 请示 DomainExpert（model 层）；任何人逻辑大问题 → 问 DomainExpert；权限冲突 → master。完整表见 `prompt/team/README.md`。
> **审查线后置**：InternalReviewer / ReviewerTeam / Editor 现阶段不创建，Phase 3/4 前再登场。
> **图分工**：数据基础图归 DataSteward；FigureArtist 只做精美图（当前用 Python 科学绘图，尚无好的绘图大模型）。
> **旧 `prompt/` 根目录角色卡**仍在，服务代码开发任务；其 insight 10/17 等旧编号引用已过期，使用前注意。

## 4. 阶段流水线

```
Phase 0 立项骨架 ── DomainExpert
  产出: 目标会议、贡献声明(3-4条,每条挂 insight)、CCF 骨架、insight 编排表
  Gate①: master 呈决策单 → 用户确认
        ↓
Phase 1 对标文献 ── LiteratureSearcher（与 Phase 0 并行）
  产出: 《insight 对标矩阵》(每条带原文引文)、gap 证据链、相关工作、.bib
  Gate②: 对标矩阵过 master——被削弱的 insight 提前降级/限定
        ↓
Phase 2 实验设计 ── EvalDesigner（+ DataSteward 进场）
  产出: 《实验设计文档》(每条 insight → 实验)、可行性评估(query 缺口)
  Gate③: 决定是否需要 CodeEngineer/CodeReviewer 进场
        ↓
Phase 3 写作 ── WritingPolisher + DomainExpert + FigureArtist（并行）
  产出: 各章节草稿(方法章先写/Intro+Motivation 后写)/真实图文件(概念图先行)
  Gate④: insight 纪律检查(每段对应哪条 insight) + 中期防御性内审(InternalReviewer)
        ↓
Phase 4 自审迭代 ── ReviewerTeam + Editor + ccf-statistics + ccf-ref-verifier
  产出: 独立审稿意见+评分 → DomainExpert 修改 → 再审 1-2 轮
  Gate⑤: 无未解决 Major → master 放行
        ↓
Phase 5 成稿交付 ── DomainExpert 整合（Editor 复核）
  产出: 完整 LaTeX 草稿(docs/paper/)、图文件清单、bib、附录、artifact 声明
  Gate⑥: 用户终裁(投稿/再改/搁置)
```

## 5. 关键产出物（落盘位置）

| 产出 | 位置 |
|---|---|
| 工作流总纲 | `notes/PAPER_TEAM_WORKFLOW.md`（本文件） |
| insight 作者意图解读 | `notes/INSIGHT_READING.md`（已存在） |
| 对标矩阵 | `.dsh/team/artifacts/benchmark-matrix.md` |
| 实验设计文档 | `.dsh/team/artifacts/experiment-design.md` |
| insight 编排表 | `.dsh/team/artifacts/insight-orchestration.md` |
| 论文草稿 | `docs/paper/`（LaTeX 工程）+ `.dsh/team/artifacts/`（中间稿） |
| 图文件 | `docs/paper/Img/`（真实图像，PDF/SVG/PNG） |
| 共识文档 | `.dsh/team/consensus.md`（master 维护） |

## 6. 用户决策点（master 只上报这些）

1. 目标会议（ISCA / MICRO / ASPLOS / HPCA）与标题方向
2. 贡献声明（3-4 条）定稿
3. 对标矩阵中被削弱的 insight 如何处理（降级/限定/换 claim）
4. 实验范围（哪些 insight 实验先做、需补哪些实现）
5. 最终投稿决定

## 7. 启动清单（team-manage 执行步骤）

1. `session-directory` 看现状（缓存优先）
2. 解析 workspaceId（`curl /api/workspace.list`，取 path == 工作区根）
3. **分阶段创建**（按角色卡"创建节奏"，不批量空转）：
   - Phase 0 首批：DomainExpert、WritingPolisher、LiteratureSearcher、FigureArtist
   - Phase 2 前：EvalDesigner、DataSteward
   - Phase 3 前：InternalReviewer
   - Phase 4 前：ReviewerTeam、Editor
   - 实验缺口时：CodeEngineer、CodeReviewer
4. 每建一个：`session.create`（传 workspaceId）→ `session.prompt` 发角色卡全文（`prompt/team/xx.md`）→ 确认可用再建下一个；建完清 `session-directory` 缓存
5. 首批就位 → Phase 0 立项（DomainExpert 出骨架 → Gate① 决策单）
