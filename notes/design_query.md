# Query 层定案（草案 v0）

日期：2026-08-17
依据：`design_sensitivity.md`（sensitivity 叙事 B\* = f(期待, 约束)）

## 定位

query 层 = 模型能回答的问题原语。根据 B\* = f(期待, 约束)，需要支撑三个问题：

1. 固定 B、约束、期待 → 可行吗？（Feasibility）
2. 固定约束、期待 → 最大 B\* 是多少？（Bmax）
3. 在 B\* 处 → 谁瓶颈、怎么改、改多少收益？（sensitivity）

## 定案

- **保留 2 个 query 原语**：
  - `FeasibilityQuery`：固定 B 判可行 + 绑定约束。
  - `BmaxQuery`：二分找 B\*（内部调 Feasibility，共享缓存）。
- **新增 1 个诊断原语（exp 层函数，不是 query）**：`Diagnostic`——给定 B，解 min ΣL，返回 L\* + margin + binding。这是 sensitivity 的计算基础（闭式 λ_j = 1/(A_j·L\*)）。

## sensitivity 两个旋钮的实现（都在 exp 层编排，不进 query 层）

- **约束旋钮**（θ = 物理参数）：∂B\*/∂θ = Σλ·∂g/∂θ = 诊断原语的 λ × 显式 ∂g/∂θ。exp 层做参数化重跑。
- **期待旋钮**（R 集合）：改变 R（全排列 → all-reduce），重跑 Bmax，看 B\* 变化。exp 层枚举不同 R。

## 原则

- query 层保持最小：灵敏度 / Pareto / binding 归类都是「实验编排 + 结果解读」，不是新 query 原语。
- 诊断原语用 exp 层函数（`solve_diagnostic` 已有雏形），不升级为 query——它是 sensitivity 的工程辅助，非「论文走向」级功能（新增 query 需全队讨论）。

## 待定

- 诊断原语是放 `src/diagnostics.py`（现有）还是 `exp/` 层？倾向 `src/diagnostics.py`（模型层辅助，非实验编排）。
