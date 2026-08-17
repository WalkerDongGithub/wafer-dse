# do 报告：论文第 1–4 章全新重写（03a 领域专家）

日期：2026-08-17
任务：按 `notes/paper_outline_v1.md` + `notes/MATH_MODEL_COMPLETE_V4.md` 等，删除旧稿（V2 语义）并全新重写 `docs/paper/Tex/` 下第 1–4 章。

## 一、改动清单

### 第 1 章 引言 — `Tex/Intro/main.tex`（覆盖写）
- 结构对齐大纲 1.1–1.4：背景问题 → 两个困难 → 核心洞察 B\*=f(期待,约束)+统一 LP → 贡献。
- 贡献重排为 3 项：①联立可行性判定（统一 LP）②B\* 统一筛选指标 ③灵敏度分析。**不含群论归约**（满足措辞约定 2）。
- 新增 `eq:intro-bstar`（B\*=f(期待,约束)），后续第 3 章开头引用。
- 措辞落实：``尽我们所能``、SI 靠 UCIe/OIF-CEI 内嵌、热 = 芯片峰值功耗 + PHY 额定功耗（均写入 1.3）。

### 第 2 章 背景 — `Tex/Background/main.tex` + 子文件
- `main.tex`（覆盖写）：改为三部分导入。
- 新建 `1_three_layer.tex`（2.1 三层物理架构）：Die–Interposer / Interposer–Substrate / 晶圆级集成（垂直热网络）。
- 删除旧 `1_wafer_scale.tex`（V2 遗留）。
- `2_physical_constraints.tex`（覆盖写）：七组约束按物理位置，只留**定性**物理本质 + 建模思路，形式化推到第 3 章；含「翘曲/PDN 瞬态/瞬态热/良率/时钟不在讨论范围」。
- 新建 `3_nonblocking.tex`（2.3 无阻塞潜能语义）：潜能 vs 保证 vs RNB；对称性作方法边界；群论归约一句带过→附录 A。

### 第 3 章 统一 DSE 框架 — `Tex/Overview/main.tex` + 子文件
- `main.tex`（覆盖写）：导入顺序改为 1_two_layer / 2_performance / 3_physical / 4_unified / 5_semantics。
- `1_two_layer.tex`（覆盖写）：3.1 两层架构（外层选型/内层判定），`\ref{sec:ov-unified}` 已更新。
- `2_performance.tex`（覆盖写）：3.2 性能约束，保留 `eq:route-flow`、`eq:valiant-lp`（实验章仍引用），群论归约一句注→附录 A。
- 新建 `3_physical.tex`（3.3 物理约束按位置，合并旧 geometry+power）：`eq:lane-def`（ℓ=B·S_bw^{-1}·L 桥梁）、`eq:ondie`、`eq:ubump`、`eq:wiring`、`eq:thermal`、`eq:c4`、`eq:die-scale`，组间无独立约束行。
- 删除旧 `3_geometry.tex`、`4_power.tex`、`5_unified.tex`。
- 新建 `4_unified.tex`（3.4 统一 LP + 二分）：`eq:unified-lp`（实验章仍引用）、线性化注记、二分算法；label 由 `sec:unified` → `sec:ov-unified`。
- 新建 `5_semantics.tex`（3.5 B\* 语义收尾）。

### 第 4 章 灵敏度分析 — `Tex/Sensitivity/main.tex`（覆盖写）
- 结构对齐大纲 4.1–4.4：目标 ∂B\*/∂θ → 数学（参数化优化/包络定理/非凸处理/事后闭式 λ_j=1/(A_j·L\*)/Milgrom–Segal/退化）→ 两个旋钮（约束 p,η,R_th,α_d,β_P,d_0 + 期待 R 集合）→ 归一化。
- label 全部重命名：`sec:sens-objective`/`sec:sens-math`/`sec:sens-envelope`/`sec:sens-posthoc`/`sec:sens-degenerate`/`sec:sens-knobs`/`sec:sens-norm`；方程 `eq:sens-param`/`eq:sens-kkt`/`eq:sens-lambda`/`eq:sens-single`/`eq:sens-dtheta`。
- 保留 `eq:sens-lambda`（实验章 `3_bmax.tex` 仍引用）；`\ref{sec:unified}` → `\ref{sec:ov-unified}`。

## 二、每处 ↔ V4 / 大纲对应

| 论文位置 | 依据 |
|---|---|
| 2.2 / 3.3 七组约束 | V4 §2.1–2.8 |
| `eq:lane-def`（ℓ=B·S_bw^{-1}·L → P） | V4 §1 变量桥梁 |
| `eq:ondie`/`eq:ubump`/`eq:wiring`/`eq:thermal`/`eq:c4`/`eq:die-scale` | V4 §2.2/2.3/2.4/2.5/2.6/2.8 |
| `eq:unified-lp`（固定 B 可行性）+ 二分 | V4 §3、§6 |
| 3.2 排列固定 + 包络 L≥L^{(r)} | `NONBLOCKING_CONDITIONS.md` §1/§3 |
| 2.3 无阻塞潜能语义 | `NONBLOCKING_CONDITIONS.md` §0/§1/§5 |
| 4.2 事后闭式 λ_j=1/(A_j·L\*) + Milgrom–Segal | `design_sensitivity.md` §2/§2.1/§3/§4/§5/§8 |
| 4.3 两个旋钮 | `design_sensitivity.md` §0/§8 |
| 2.1 三层物理架构/垂直热耦合 | `design_joint_model.md` §3 |
| 措辞约定（B\*=f(期待,约束)、群论是术、SI 内嵌、热范围、潜能） | `paper_outline_v1.md` §1 |

## 三、待核实

1. **「Wafer–Wafer」语义**：大纲 2.1 写「Die-Interposer / Interposer-Substrate / Wafer-Wafer」。我按 `design_joint_model.md` §3 三层垂直热网络诠释为「晶圆级集成尺度（die→interposer→substrate→ambient）」，未直译 wafer-to-wafer 键合。需 03a/领域确认口径。
2. **Milgrom–Segal (2002)**：正文文字引用（``Milgrom--Segal (2002) 包络定理``），未加 `\cite`——`Biblio/ref.bib` 本轮不动、且无该条目。若需正式引用，后续需补 bib 条目（下一轮）。
3. **附录 A 引用**：正文多处写「见附录 A」（群论归约、热 M-矩阵线性化）。当前 `Tex/Appendix.tex` 仍是模板测试内容，附录本体待后续轮次补写（大纲约定附录 A/B 尚未落稿）。
4. **期待旋钮的定量梯度**：`design_sensitivity.md` §8 对物理参数 θ 给了 ∂B\*/∂θ=Σλ_i·∂g_i/∂θ 闭式，但对「期待旋钮（R 集合）」只定性（R 变小→L 变小→B\* 提高）。4.3 相应保持定性表述，待理论补充后细化。
5. **`sec:sens-objective` 未被引用**：该 section label 目前无 `\ref` 指向（属自描述章节标题），无碍编译，仅提示。

## 四、未动（按任务约束）

`Thesis.tex`、`Style/`、`Frontmatter`、`Frontinfo`、`Mainmatter.tex`、`Biblio/`、`Prematter.tex`（符号列表仍为 CFD 模板符号，非本轮范围）、第 5–7 章（Experiments/RelatedWork/Conclusion/Discussion）、`Appendix.tex`。

## 五、交叉引用核验

- 实验章仅引用 `eq:unified-lp`、`eq:sens-lambda`、`eq:valiant-lp`，三者均保留未改名 → 无断裂。
- 全文 grep `\ref/\label` 确认无残留旧标签（`sec:unified`/`sec:performance`/`sec:phys-upper`/`sec:phys-lower`/`sec:sens-phys`/`sec:sens-multi`/`sec:sens-shadow`/`sec:sens-nonconvex`/`sec:sens-dual-note` 等均已消除）。
