# Do 报告 — 领域专家分身（03a）Overview 章重写

日期：2026-08-17
任务：把 `docs/paper/Tex/Overview/` 从旧版「性能/几何/功耗三族约束 + max L_e≤1 + max B 优化」重写为 V4 结构（`notes/MATH_MODEL_COMPLETE_V4.md` 为最高权威）。

## 一、改动文件清单

| 文件 | 改动 |
|------|------|
| `docs/paper/Tex/Overview/main.tex` | 章引言重写：开头一句讲清 B\*=f(期待,约束) 语义；重排本章展开顺序 |
| `docs/paper/Tex/Overview/1_two_layer.tex` | 两层架构保留，内层改为「固定 B 可行性判定 + 二分 B\*」 |
| `docs/paper/Tex/Overview/2_performance.tex` | 性能约束：R 排列模式固定输入 + 包络 L≥L^(r) + 无阻塞潜能语义 |
| `docs/paper/Tex/Overview/3_geometry.tex` | 按物理位置约束（一）：on-die / μbump / 布线 |
| `docs/paper/Tex/Overview/4_power.tex` | 按物理位置约束（二）：热 / C4 / 组间 / die 缩放 |
| `docs/paper/Tex/Overview/5_unified.tex` | 统一 LP（固定 B 可行性）+ 线性化注记 + 二分 + B\* 语义与 sensitivity 收尾 |

## 二、每处改动 ↔ V4 对应关系

| Overview 位置 | 内容 | 对应 V4 |
|------|------|---------|
| `main.tex` 引言 | B\*=f(期待,约束)、「尽我们所能」不乐观不悲观、灵敏度=期待降低/约束放宽 → B\* 提高 | `design_sensitivity.md §0` |
| `1_two_layer.tex` | 外层选型 / 内层「固定 B 可行性判定 + 二分」分离；内层共同物理量=负载包络 L 及 lane 数 ℓ | V4 §6（二分）；旧版两层架构保留但内层语义换 |
| `2_performance.tex` | 无阻塞=潜能（最优自适应路由 + 包络而非等式）；Birkhoff 给排列模式；D^(r) 外生固定；流守恒 + L^(r)=P_r f^(r) + L≥L^(r)；min ΣL_e 压包络下界 | V4 §2.1、§0 符号；`NONBLOCKING_CONDITIONS.md §1/§3` |
| `2_performance.tex` | 群论归约只一句注（「降 LP 规模、见附录、非核心贡献」） | 背景必读第 2 条（群论归约=小 tips 非核心） |
| `3_geometry.tex` | on-die 零代价 S_bw=∞/S_dyn=0 | V4 §2.2 |
| `3_geometry.tex` | μbump：N_sig=Mℓ, N_pwr=S_in^{-1}P, 零和 ≤ N_total(B)；M 为 die-链路 incidence、S_in 功率-bump 换算 | V4 §2.3 |
| `3_geometry.tex` | 布线：Ax=ℓ, Rx≤C（边/点/pad 容量统一） | V4 §2.4 |
| `4_power.tex` | 热：GT=P+b, T≤T_max；只谈峰值功耗 P_peak + PHY 额定动态功耗，翘曲/PDN 瞬态/瞬态热不进约束集 | V4 §2.5；背景必读第 4 条 |
| `4_power.tex` | C4：1^T ℓ_SerDes ≤ N_C4^SerDes | V4 §2.6 |
| `4_power.tex` | 组间：无独立约束行，代价经 C4/动态功耗/pad 容量体现 | V4 §2.7 |
| `4_power.tex` | die 缩放：d(B)=d0+α_d B、A_die(B)=d(B)²、P_peak(B)=P0+β_P B；注明数值实验取 α_d=β_P=0 特例 | V4 §2.8 |
| `5_unified.tex` | 统一 LP：完整复刻 V4 §3 的 boxed LP（固定 B，纯线性）；标注 (2.1)–(2.6) 编号对应前文；B\*=min(B\*_intra, B\*_inter) | V4 §3 |
| `5_unified.tex` | 线性化注记：热消元 K=G^{-1}MS_dyn S_bw^{-1}、μbump 折 lane 系数、L0 粗筛 | V4 §4 |
| `5_unified.tex` | 二分伪代码 + 单调性 + log₂(Bmax/ε) 次 LP | V4 §6 |
| `5_unified.tex` | 收尾：B\*=f(期待,约束) + sensitivity 两旋钮，指向 Sensitivity 章 | `design_sensitivity.md §0` |

## 三、标签 / 引用处理

- 保留 `\label{chap:overview}`（被 `Sensitivity/main.tex` 引用）。
- 保留 `\label{eq:valiant-lp}`（被 `Experiments/4_pareto.tex` 引用），但语义从旧「min t s.t. L_e≤t」改为 V4 的「min Σ_e L_e s.t. 流守恒 + 包络」——标签名未改、含义已换，见待核实①。
- 其余旧标签（`eq:bw`/`eq:bump-budget`/`eq:geom-per-die`/`eq:thermal-l0`/`eq:unified`）均无外部引用，已随内容替换为新标签。
- 新增标签：`sec:performance`、`sec:phys-upper`、`sec:phys-lower`、`sec:unified`、`eq:route-flow`、`eq:ondie`、`eq:ubump`、`eq:wiring`、`eq:thermal`、`eq:c4`、`eq:die-scale`、`eq:unified-lp`。
- 引用键 `birkhoff1946tres`、`ucie2.0-2024`、`oif-cei-5.1` 已在 `Biblio/ref.bib` 中确认存在。
- 全程未改 `Thesis.tex`、Style、其他章节。

## 待核实汇总

① **`eq:valiant-lp` 语义漂移**：`Experiments/4_pareto.tex` 仍写「求解 Eq.~\ref{eq:valiant-lp} + 几何L1 + 功耗L1」，这是旧 V2 语义（三族分别求解）。本次只在 Overview 内把该标签挂到 V4 的「min ΣL_e 包络下界 LP」，保证 `\ref` 不断；但实验章叙述与 V4「单个可行性 LP + 二分」不一致，需父 agent 决定后续是否同步实验章。

② **Intro 章未同步**：`Intro/main.tex` 贡献部分仍称「性能、几何、功耗三族物理约束」，与 V4「按物理位置组织」分类不一致。本次范围只限 Overview，未改 Intro；建议父 agent 知悉。

③ **Sensitivity 章未同步**：`Sensitivity/main.tex` 仍是旧 V2 语义（t\*、对偶变量、B_max 解析式、`eq:bmax`），与 V4「B\*=f(期待,约束) + 二分 + KKT 事后闭式」不一致。Overview 已指向 `chap:sensitivity`，但该章需另起任务对齐（不在本次范围）。

④ **die 缩放呈现方式**：V4 §2.8 注明「代码未接入 LP（当前 α_d=β_P=0）」。我在正文按「模型约束」呈现，并加一句「本文数值实验取 α_d=β_P=0 特例」；是否要在论文里明写「未实现/待建」由父 agent 定夺。

⑤ **组间垂直热耦合未写入 Overview**：`design_joint_model.md` 的三层垂直热网络（die→interposer→substrate）在 V4 §3 里只体现为 `B* = min(B*_intra, B*_inter)`，无显式三层热方程。本次 Overview 严格按 V4 写「组间无独立约束 + B\*=min」，未引入 joint_model 的三层热耦合；若论文要讲「联合模型」需另行补一节。

⑥ **on-die 零代价是高估 B\* 的假设**：V4 §5 假设表已列「on-die 零代价 → 高估 B\*」。我在正文写了「保守抽象（其代价模型待建）」，措辞是否保留由父 agent 定夺。
