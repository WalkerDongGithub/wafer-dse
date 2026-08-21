# V5 模型性质讨论（释经）

> **释经文档**：本文件承载 `notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md`（经书）的**派生讨论**——2026-08-21 经书/释经拆分时从 v5 移出：
> ① 原 §5.2 闭合性与有界性论证 ② 原 §5.3 模型类别（整体非凸、固定 B 为 LP、二分求解）③ 单调性注意。
> 经书只回答"模型是什么"；本文件回答"模型有哪些可证明的性质、怎么解"。

---

## 1. 闭合性与有界性（原 v5 §5.2）

- **无自由变量**：$\mathbf{b}_{\text{inter}}$、$\mathbf{P}_{\text{inter}}$、$\mathbf{N}_{\text{C4}}^{\text{pwr}}$ 均由经书 §4 的等式定义；§2/§3 的 find 列表只含真正可变的量。
- **有界性论证**（不是断言）：
  1. 热约束链给功耗上界：$\mathbf{T} \le T_{\max}\mathbf{1}$ 且 $\mathbf{G}$ 为 M-矩阵（$\mathbf{G}^{-1} \ge 0$，对角元 $> 0$）$\Rightarrow$ $\mathbf{G}^{-1}\mathbf{P} \le T_{\max}\mathbf{1} - \mathbf{G}^{-1}\mathbf{b}$ 逐分量有界 $\Rightarrow$ $\mathbf{P}_{\text{die}}$ 逐分量有界。
  2. $\mathbf{P}_{\text{die}}$ 有界 $\Rightarrow$ $\mathbf{P}_{\text{dyn}}$ 有界 $\Rightarrow$ $\boldsymbol{\ell}$ 有界 $\Rightarrow$ $B\,\mathbf{L}$ 有界；$\mathbf{L} \ge \mathbf{L}^*$ 给出下界。故固定 $B$ 下模型有界。

## 2. 模型类别：整体非凸，但存在可多项式时间求解的全局最优（原 v5 §5.3）

把 $B$ 一并作为决策量的**整体问题**是**非凸**的：die 缩放（经书 §2.8）在约束 rhs 中引入 $B$ 的二次项（如 $N_{\text{die}}^{\text{total}}(B) = \eta(d_0+\alpha_d B)^2/p^2$），可行性区域对 $B$ 不是凸集。

但整体问题**不需要启发式，存在可多项式时间求解的全局最优解**（insight 7）：
1. **固定 $B$ 是纯 LP**：所有约束（经书 §2/§3/§4）关于 $\mathbf{L}$、$\boldsymbol{\ell}$、$\mathbf{P}$、$\mathbf{T}$ 线性（die 缩放的二次项在固定 $B$ 下退化为常数）——可行性检查**精确可判**，不是 MILP/QCP，也不是近似；LP 多项式可解（经典结果）。
2. **外层二分搜索**（`BmaxQuery`：`FeasibilityQuery` 单调二分）：$B^*$ = 最大可行 $B$，二分迭代 $O(\log)$ 次。

二分 + LP 即得 $B^*$，**总复杂度多项式**——这是 insight 7 的形态：**问题非凸，但不需启发式；只要要求不过分苛刻、考量不过分包罗万象，存在可多项式时间求解的全局最优解。**（论文不强调"这是 LP"，强调"不需要启发式、存在可多项式时间求解的全局最优解"，见 `notes/INSIGHT_READING.md`。）

## 3. 单调性注意（内部验证，不上论文台面）

二分假设"可行性在 $B$ 上单调"。低 $B$ 侧恒可行——$B$ 低时面积约束是松上界（面积不够可扩大 die、外围加无逻辑硅，见 `notes/INSIGHT_READING.md` insight 3）；默认 $\alpha_d = \beta_P = 0$ 时单调性严格成立。启用 die 缩放后建议验证（作为良心检查）。

## 4. 灵敏度分析（论文杀手锏）

灵敏度分析的完整设计见 `.dsh/team/artifacts/sensitivity-design.md`（KKT/包络定理框架）与 `experiment-design.md` §2 E8；实验数据见 `.dsh/team/artifacts/data-report-*.md`。本文件不重复。
