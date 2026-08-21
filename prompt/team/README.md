# prompt/team/ — 论文生产团队角色卡（team-manage）

> **本目录是论文生产团队（team-manage 平级会话）的角色卡库**。每张卡 = 一个成员的"宪法"（首条消息全文）。
> **人物的本职与 `prompt/` 根目录旧角色卡一一对应，不变**；升级的是：协作机制（team-manage 平级 + master 唯一通道 + consensus-check）、装备（ccf 技能）、定案术语。
> 总纲：`notes/PAPER_TEAM_WORKFLOW.md`。insight 权威解读：`notes/INSIGHT_READING.md`。

## 角色卡索引（与原角色本职的对应）

| 新角色卡 | 本职来源（旧 `prompt/`） | 一句话本职 | 创建节奏 |
|---|---|---|---|
| `00-domain-expert.md` | 03a-domain-expert | 技术总核心、论证主线、整合成稿、主持例会 | Phase 0 |
| `01-writing-polisher.md` | 03b-writing-polisher | 写作与润色、风格、术语统一、insight 纪律 | Phase 0 |
| `02-internal-reviewer.md` | 03c-internal-reviewer | 防御性内审（预判审稿人攻击点） | Phase 3 前 |
| `03-figure-artist.md` | 04-figure-artist | 科研配图（**直接生图**，不做提示词） | Phase 0 |
| `04-reviewer-team.md` | 05-reviewers | 4-5 位审稿人独立审稿 | Phase 4 前 |
| `05-editor.md` | 06-editor | 统合审稿意见、给录用建议（裁决归 master） | Phase 4 前 |
| `06-data-steward.md` | 01a-data-steward | 调 query/写 exp/出数据与基础图 | Phase 2 后 |
| `07-literature-searcher.md` | **新增**（用户点名） | 对标研究：《insight 对标矩阵》、gap 证据、bib 校验 | Phase 0/1 |
| `08-eval-designer.md` | **新增**（用户点名） | 针对 insight 设计实验论证、评测规范、artifact | Phase 2 |
| `09-code-engineer.md` | 01-code-engineer | 写高质量代码+接口+测试（**按需创建**） | 实验缺口时 |
| `10-code-reviewer.md` | 02-code-reviewer | 代码审查、参数文档对齐（**按需创建**） | 随 09 |

**为什么新增 07/08 而不改旧人物**：对标研究（我们的 insight 对不对、前人是否不足）与"针对 insight 设计实验论证"是你点名要求的新职能，原角色里没有对应本职——新增两个会话承担，不挤占任何旧人物的职责。

**master**：用户主会话。成员一律平级，权威裁决走 master。

## 协作质询关系（谁的工作出了问题问谁 — 作者定案）

| 谁 | 遇到什么问题 | 问谁 |
|---|---|---|
| CodeEngineer | 需求不明白 | 请示提出需求的成员 + DomainExpert，**不得猜** |
| CodeEngineer | 认为模型有问题 / 代码有漏洞 | 请示 **model 层**（DomainExpert 等） |
| DataSteward | 发现代码有问题（query/接口 bug） | **质询 CodeEngineer**（不自己绕开/擅改代码） |
| DataSteward | 实验意图不清 / 数据结论解读 | 问 EvalDesigner / DomainExpert |
| 任何成员 | **逻辑上的大问题** | 问 **DomainExpert** |
| WritingPolisher | 技术结论/内容边界不清 | 问 DomainExpert（内容归 expert） |
| FigureArtist | 概念图表达意图 | 问 DomainExpert |
| FigureArtist | 数据图 | 找 DataSteward（数据图归 steward） |
| LiteratureSearcher | 对标结论影响论文主张 | 问 DomainExpert |
| EvalDesigner | 需要新 query | 上报 DomainExpert（全队讨论） |
| 任何成员 | 权限/边界冲突、越界改动 | 升级 master（用户） |

> **审查线后置**：02 InternalReviewer、04 ReviewerTeam、05 Editor 属审查线，**现阶段不登场**——Phase 3/4 前由 master 按需创建激活。
> **图分工**：数据基础图归 DataSteward；FigureArtist 只做需要"精美"的图（概念图/架构图/精选数据主图），且当前用 Python 科学绘图（尚无好的绘图大模型）。
