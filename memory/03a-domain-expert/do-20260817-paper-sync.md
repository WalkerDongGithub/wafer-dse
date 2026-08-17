# Do 报告 — 领域专家分身（03a）Intro / Sensitivity / Experiments 对齐 V4

日期：2026-08-17
任务：把 `docs/paper/Tex/Intro`、`docs/paper/Tex/Sensitivity`、`docs/paper/Tex/Experiments` 三章从旧 V2 语义对齐到 V4（`notes/MATH_MODEL_COMPLETE_V4.md` 为最高权威，`notes/design_sensitivity.md`、`notes/NONBLOCKING_CONDITIONS.md` 为辅）。

## 一、改动文件清单

| 文件 | 改动 |
|------|------|
| `docs/paper/Tex/Intro/main.tex` | 深度耦合链改「PHY 额定功耗 + 芯片峰值功耗」、删翘曲；「第二类约束」改为按物理位置组织七组；贡献 1/2/3 同步 V4 分类与灵敏度语义 |
| `docs/paper/Tex/Sensitivity/main.tex` | 全章重写：从旧「t\* / 对偶变量 / B_max 解析式」改为「B\*=f(期待,约束) + 二分 B\* + 事后闭式 λ + Milgrom–Segal 包络定理 + 物理参数梯度」 |
| `docs/paper/Tex/Experiments/2_scalability.tex` | Valiant LP→可行性 LP（性能侧 min ΣL + μbump/热 L1）；删「t\*=1.0000」；图注改可行性 LP |
| `docs/paper/Tex/Experiments/3_bmax.tex` | 全文件重写：B_max 解析公式→二分 B\* + 事后闭式 λ 识别先绑定约束；表列名 B\*_bump / B\*_thermal；绑定标签 geometry→μbump |
| `docs/paper/Tex/Experiments/4_pareto.tex` | 「Eq valiant-lp + 几何L1 + 功耗L1」→「性能侧 min ΣL + 物理约束（μbump + 热 L1，式 unified-lp）」 |
| `docs/paper/Tex/Experiments/5_fidelity.tex` | (0,0,0)/(1,1,1)→热 L0/L1；t\*→B\*；L0 更保守=更低 B\*（集总功耗粗筛更早收紧） |

## 二、每处改动 ↔ V4 / design 对应关系

| 位置 | 内容 | 对应依据 |
|------|------|---------|
| Intro §2.2 | 「lane 的 PHY 额定功耗与芯片峰值功耗共同决定裸片总功耗」；删「翘曲风险」 | 背景必读「热=峰值功耗+PHY 额定功耗」；V4 §2.5 |
| Intro §2.2 | 「热分析工具处理温度」删「和翘曲」 | V4 翘曲移出约束集 |
| Intro §3 第二类约束 | 「按物理位置组织为 on-die、μbump、布线、热、C4、组间、die 缩放七组（信号完整性已内嵌于互连标准）」 | V4 §2；背景必读「SI 靠规范内嵌」 |
| Intro 贡献 1 | 「内层将按物理位置组织（…七组）的物理约束统一为线性不等式组」 | V4 §2 |
| Intro 贡献 2 | 「二分求 B\* 后，用事后闭式 λ_j=1/(A_j·L\*) 提取绑定约束影子价格，给出 B\* 对物理参数与期待旋钮的梯度（Milgrom–Segal 包络定理）」 | `design_sensitivity.md §2.1/§8` |
| Intro 贡献 3 | 「二分 B\* 与事后灵敏度分析」替代「B_max 分析」 | `design_sensitivity.md §0` |
| Sensitivity 章引言 + §sens-semantics | B\*=f(期待,约束)、两个旋钮（约束旋钮 p/η/R_th/α_d/β_P + 期待旋钮 R 集合）、叙事「期待降低或约束放宽 → B\* 提高」 | `design_sensitivity.md §0` |
| Sensitivity §sens-shadow | 目标=∂B\*/∂b_i（每松弛 1 单位 rhs 换多少 Gbps） | `design_sensitivity.md §1` |
| Sensitivity §sens-kkt | 参数化 max-B + 拉格朗日 + 包络定理 ∂B\*/∂b_i=λ_i\*；KKT Σλ_i(A_i·L\*)=1；互补松弛 | `design_sensitivity.md §2` |
| Sensitivity §sens-nonconvex | B·(A_i·L) 双线性→非凸；B\* 用二分 + 固定 B 可行性 LP（凸）求得；λ 事后闭式 λ_j=1/(A_j·L\*)；挂 Milgrom–Segal（不要求凸性） | `design_sensitivity.md §2.1`；V4 §6 |
| Sensitivity §sens-single | 单约束绑定闭式 ∂B\*/∂b_j=1/(A_j·L\*) | `design_sensitivity.md §3` |
| Sensitivity §sens-multi | 多约束绑定退化不唯一，先改哪个由绑定演化序列回答 | `design_sensitivity.md §4` |
| Sensitivity §sens-dual-note | feasibility 对偶=∂(min ΣL)/∂b_i ≠ ∂B\*/∂b_i，实现用闭式 λ | `design_sensitivity.md §5` |
| Sensitivity §sens-norm | 归一化与投资优先级比值 | `design_sensitivity.md §6` |
| Sensitivity §sens-phys | ∂B\*/∂θ=Σλ_i\*·∂g_i/∂θ；统一 rhs 常数 b_i 与物理参数两种情况；期待旋钮 R 变小→L 变小→同一梯度结构传至 B\* | `design_sensitivity.md §8` |
| Experiments 2 | 可行性 LP（式 unified-lp）+ 性能侧 min ΣL + μbump/热 L1；删 t\*=1.0 改为「性能侧需求下界相同」 | V4 §3/§6；Overview `eq:unified-lp` |
| Experiments 3 | 二分 B\* + 事后闭式 λ 识别先绑定约束；B\*_bump/B\*_thermal；μbump 先触顶 | V4 §6；`design_sensitivity.md §3` |
| Experiments 4 | 性能侧 min ΣL（eq:valiant-lp）+ 物理约束（μbump+热 L1，eq:unified-lp） | V4 §2.1/§3 |
| Experiments 5 | 热 L0（全局功耗模型）/热 L1（稳态热网络）；B\* 比较；L0 更保守=更低 B\* | V4 §7（热 L0/L1 两档）；V4 §4（L0 粗筛） |

## 三、标签 / 引用处理

- 保留 `\label{chap:sensitivity}`（被 Overview `4_power.tex`、`5_unified.tex` 引用）。
- 保留 Experiments 的 `sec:setup/sec:scalability/sec:bmax/sec:pareto/sec:fidelity`、`fig:scalability/fig:bmax/fig:pareto`、`tab:bmax`。
- **删除旧标签 `eq:bmax`**（B_max 解析式），已 grep 确认全文无 `\ref{eq:bmax}` / `\label{eq:bmax}` 残留，无断引用。
- Sensitivity 新增标签：`sec:sens-semantics/sens-shadow/sens-kkt/sens-nonconvex/sens-single/sens-multi/sens-dual-note/sens-norm/sens-phys`、`eq:sens-param/sens-kkt/sens-lambda/sens-single/sens-dtheta`。
- Experiments 3 现引用 `\eqref{eq:unified-lp}`、`\eqref{eq:sens-lambda}`（均存在）。
- 引用键 `ucie2.0-2024`、`oif-cei-5.1`、`mfit2025`、`electrical-thermal-chiplet2024` 已在 `Biblio/ref.bib` 确认存在。
- 全程未改 `Thesis.tex`、Style、Overview。

## 待核实汇总

① **热阻符号冲突**：`design_sensitivity.md §8` 写物理参数含「热阻 R」，但 V4 §0 里 `\mathbf{R}` 是布线 incidence（`Rx≤C`），热阻由 `G` 的逆承载。我在论文里改用 `R_{\text{th}}` 表示热阻（Sensitivity §sens-semantics、§sens-phys），避免与布线 incidence 冲突。待父 agent 确认：是否在 V4 §0 补「热阻」符号，或维持论文用 `R_{\text{th}}`。

② **Milgrom–Segal 无 bib 条目**：Sensitivity 正文用文字「Milgrom--Segal (2002) 包络定理」未加 `\cite`（避免断引用）。若需正式引用，建议在 `Biblio/ref.bib` 补 `milgrom2002envelope`（Milgrom & Segal, "Envelope Theorems for Arbitrary Choice Sets", *Econometrica* 70(2), 2002）；KKT/灵敏度的一般性引用可复用已有 `bertsekas1997nonlinear`。

③ **3_bmax 表数据与「9 个拓扑」计数不符**：表只有 8 行（DF×6 + Mesh + Torus），正文说「9 个拓扑」。这是原文件就有的不一致；本次只改列名与绑定标签（geometry→μbump），未补/删数据。待父 agent 确认是否补第 9 个拓扑。

④ **范围外残留（未改）**：`Conclusion/main.tex`（「LP 对偶变量提供影子价格」「B_max 解析公式」「t\*≤1 必要条件」）、`Discussion/main.tex`（「t\*≤1」）、`RelatedWork/main.tex`（「对偶变量提供精确灵敏度」）仍是旧 V2 语义。本次任务范围只限 Intro/Sensitivity/Experiments，这三章未动，建议父 agent 后续安排同步。

⑤ **g_i 符号约定**：`design_sensitivity.md §8` 正文写「g_i(B,L,θ)≤0」，但其「∂g_i/∂b_i=1」与 ≤0 约定不自洽。我在论文统一为 `g_i = b_i(θ) − B·(A_i(θ)·L) ≥ 0`，使 `∂g_i/∂b_i=1` 与 `∂B\*/∂b_i=λ_i` 自洽。待父 agent 确认最终符号约定。

⑥ **Intro 贡献 2 引入 A_j·L\* 符号**：`A_j`（约束 j 消元后对 L 的系数行）在 V4 §0 未单独定义（V4 用 K、G^{-1}M S_dyn S_bw^{-1} 等具体系数）。Sensitivity §sens-kkt 已给出「A_i 为约束 i 消元后对 L 的系数行」的定义；Intro 直接使用该缩写。若父 agent 希望符号表补 A_j，可同步 V4 §0。
