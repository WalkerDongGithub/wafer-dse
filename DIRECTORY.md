# wafer-dse 项目目录清单

## 顶层结构

| 目录 | 用途 |
|------|------|
| `src/` | 核心代码：`problem/`（LP 引擎：ctx/engine/models/queries）、`topology/`（Mesh/Torus/Dragonfly 等）、`physical/`（config/layout/placement） |
| `notes/` | 知识库：数理模型、设计文档、文献笔记（PDF 已 gitignore） |
| `docs/paper/` | 论文 LaTeX（学位论文模板 ucasthesis） |
| `prompt/` | 多角色协作 prompt 库（00-overview 协作机制 + 各角色） |
| `memory/` | 协作落盘目录（各子 agent 的 do 报告） |
| `config/` | 实验参数 YAML（`params/` 物理参数 + `problems/` 问题定义） |
| `exp/` | 实验脚本（run_matrix/run_ledger 等）+ 输出（output 已 gitignore） |
| `tests/` | 测试（`run_all.py` 驱动各 .md 测试） |
| `MFIT/` | 外部依赖（多保真热求解器，已 gitignore） |

## 关键文档（notes/，最高权威在上）

- `MATH_MODEL_COMPLETE_V4.md` —— **最高权威**：完整数理模型 v4（按物理位置组织 §2.1–2.8）
- `paper_outline_v1.md` —— 论文重写大纲（7 章 + 2 附录）
- `design_sensitivity.md` —— 灵敏度分析设计（∂B*/∂θ + 期待/约束两旋钮）
- `design_joint_model.md` —— 组内/组间联合模型（三层垂直热耦合）
- `design_query.md` —— query 层定案
- `design_realism_gap.md` —— 模型 ↔ 现实真实性 gap 盘点
- `NONBLOCKING_CONDITIONS.md` / `SYMMETRY_REDUCTION.md` / `THERMAL_MODEL.md` —— 理论支撑

## 核心语义（已定案）

- B\* = f(期待, 约束)，"尽我们所能"，不强调乐观/悲观。
- 群论归约是"术"、非核心 idea；SI 靠规范内嵌；热 = 峰值功耗 + PHY 额定功耗。

## 被 .gitignore 忽略的（不提交）

- `*.pdf` —— 文献 PDF（`notes/literature/` 下 18 个 + 根目录 2 个）
- `*.deb` —— 二进制包（libblas3/libsuperlu6）
- `MFIT/` —— 外部依赖（含编译的 .so）
- `exp/output/` —— 实验输出（含 .pkl 缓存）
- `__pycache__/`、`.venv/` 等

## 协作约定

- 子 agent 完整 do 报告落盘 `memory/<agent-id>/do-<日期>-<主题>.md`；系统级记忆只存结论快照。
- 子 agent 是 stateless 的，产出不落盘即随对话丢失（见 `prompt/00-overview.md`）。
