# do 报告：论文第 5–7 章 + 附录全新重写（03a 领域专家）

日期：2026-08-17
任务：按 `notes/paper_outline_v1.md` 第 5–7 章 + 附录要点，全新重写 `docs/paper/Tex/` 下 Experiments / RelatedWork / Conclusion / Appendix；实验数字一律占位「待真实数据」，禁止编造；相关工作禁止虚构文献。

## 一、改动清单

### 第 5 章 实验 — `Tex/Experiments/`（main + 5 子文件，全部覆盖写）
- `main.tex`：定义占位宏 `\providecommand{\todo}[1]{\textbf{[待真实数据：\ #1]}}`（仅实验章内部使用，用 `\providecommand` 防冲突）；章首明确「本章只写实验设计/论证逻辑/预期方向，数值一律占位，不沿用旧稿任何 B\*/Pareto 数值」。
- `1_setup.tex`（5.1）：软件栈（CVXPY~\cite{diamond2016cvxpy} + CLARABEL~\cite{goulart2024clarabel}）；两组参数组合 TOY（手算友好）/ UCIE（UCIe 16/24/32 GT/s + OIF-CEI-112G-VSR，来自 `src/physical/params.py` 真实默认值，只列维度与来源、不罗列数字）；最坏情况设定（峰值功耗 + 稳态）；die 缩放取 α_d=β_P=0 特例。
- `2_scalability.tex`（5.2）：可行性 LP 规模 vs 求解时间；规模构成分析（|R| 由群论归约从 n! 压到分拆数 p(16)=231）；预期方向全 `\todo`。
- `3_bmax.tex`（5.3）：B\* 二分 + 事后闭式 λ_j=1/(A_j·L\*)（`eq:sens-lambda`）识别瓶颈；分解 B\*_bump/B\*_thermal；预期方向（绑定归属、B\* 随 N 缩放、ν_bump/ν_thermal）全 `\todo`。
- `4_pareto.tex`（5.4）：固定 B 枚举拓扑参数空间，N–面积(–功耗) Pareto 前沿；预期方向全 `\todo`，不再沿用旧稿「DF(2,5,1) 最优」等结论。
- `5_fidelity.tex`（5.5）：热 L0/L1 判定一致性；论证逻辑（L0 集总粗筛应不乐观于 L1）；slack 阈值与升级比例全 `\todo`。
- **删除**旧稿的 figure 引用（`pareto.pdf`/`scalability.pdf`/`bmax.pdf`）：`Img/` 下无这些 pdf（仅 `.py` 脚本），保留会编译报「file not found」。

### 第 6 章 相关工作 — `Tex/RelatedWork/main.tex`（覆盖写）
- 三节 + 定位收尾：晶圆级系统（Dojo/Cerebras/Chen/Feng/Wan/TickTock）、DSE 方法论（FPIA/RapidChiplet/FireLink/MFIT + cycle-accurate 仿真）、无阻塞网络理论（SNB/WSNB/RNB 经典条件、BvN、Valiant、Dragonfly 平衡条件 a=2p/h=p、Ngo LP 对偶）。
- 逐条 `\cite`，全部取自 `Biblio/ref.bib` 已存在的 key，未虚构。

### 第 7 章 讨论与结论 — `Tex/Conclusion/main.tex`（覆盖写）
- 7.1 方法边界（约定范围：翘曲/PDN 瞬态/瞬态热/良率/时钟不讨论；无阻塞=潜能非保证；对称性假设；SI 内嵌；die 缩放退化特例）。
- 7.2 主要发现（对应 Intro 三贡献，不含群论归约）+ 局限（实验数据待回填、die 缩放/组间未接入、布线待标定、潜能需乘性松弛）+ 展望。
- 删除旧稿的编造数字（B_max∝1/N、80× 余量、N≤30 等）。

### 附录 — `Tex/Appendix.tex`（覆盖写模板测试内容）
- 附录 A 群论归约（`app:symmetry`）：定位为「术、供参考、非核心贡献」；定理 1（BvN 顶点→置换矩阵）、定理 2 + 引理 1/2（重标号=共轭、流图同构=共轭）、轨道计数（命题 1/2/3 + Burnside + 中心化子计数）、常见拓扑 Aut(H) 表、可行性（p(8)=22/p(16)=231）。
- 附录 B 热线性化（`app:thermal`）：M-矩阵结构（G 构造）、G^{-1}≥0 物理单调性、温度约束线性化（B·K·L≤rhs，K=G^{-1}MS_dynS_bw^{-1}）、L0 粗筛；热阻统一用 R_{\text{th}}。

## 二、关键决策与发现

1. **实验数字占位**：实验章与结论章不再出现任何具体结果数值；仅保留来自代码/规范的「参数维度与来源」（TOY/UCIE 两组组合的名称、UCIe 三档速率、45μm bump 等公开规范值），不写「设定值」。占位统一 `\todo{…}`。
2. **相关工作受 `Biblio/` 不动约束限制**：`ref.bib` 无 Clos/Benes/Slepian/Melen–Turner/Pippenger/Hwang 等经典条目（`NONBLOCKING_DEFINITIONS_SURVEY.md` 列出的文献）。故无阻塞理论节以 `dally2004principles`（教科书承载 SNB/WSNB/RNB 与 Clos 条件）、`ngo2010lp-nonblocking`、`valiant1982scheme`、`birkhoff1946tres`、`kim2008technology` 为引用骨架，未新增 bib 条目。
3. **附录 B 推导修正（重要）**：`THERMAL_MODEL.md` §5 的「两边左乘 G 不等号方向不变」**不严谨**——G 是 M-矩阵、非对角非正，左乘 G 不保序（反例：G=[[2,-1],[-1,2]]，T=[0.5,0.9]≤[1,1] 但 G·T=[0.1,1.3] 不≤ G·(T_max·1)=[1,1]）。附录 B 改用 V4 §4 的正确消元：直接用 `G^{-1}(P+b) ≤ T_max·1`（G^{-1} 为常数矩阵，本身即 P 的线性不等式），再代入 P/ℓ 得 `B·K·L ≤ rhs`，K=G^{-1}MS_dynS_bw^{-1}。G^{-1}≥0 的物理单调性只用于说明「功率↑→温度↑」的因果性，不用于「左乘 G 保序」。
4. **PDF bookmark 安全**：附录 section 标题避免复杂数学（`\operatorname{Aut}`/`\mathbf{G}^{-1}` 会污染 hyperref 书签），已改为纯文字标题。
5. **`\todo` 宏作用域**：仅在 `Experiments/main.tex` 定义（`\providecommand`），Mainmatter 顺序保证 Conclusion 之前已定义；Conclusion 内已不再使用 `\todo`（改为纯文字「待真实数据回填」），消除对编译顺序的隐性依赖。

## 三、每处 ↔ V4 / 大纲对应

| 论文位置 | 依据 |
|---|---|
| 5.2 规模构成（\|R\|、p(16)=231） | `SYMMETRY_REDUCTION.md` §4/§7、附录 A |
| 5.3 二分 + 事后闭式 λ 识别瓶颈 | `design_sensitivity.md` §2/§3、V4 §6 |
| 5.5 热 L0/L1 | V4 §4「L0 精度」、`THERMAL_MODEL.md` §5、`MATH_MODEL_COMPLETE_V4.md` §7 |
| 6 相关工作 | `notes/LITERATURE_SURVEY.md`、`notes/literature/NONBLOCKING_DEFINITIONS_SURVEY.md`、`notes/literature/dse_methodology/*` |
| 7.1 方法边界 | `paper_outline_v1.md` §1 措辞约定 |
| 附录 A 定理 1/2 + Burnside | `SYMMETRY_REDUCTION.md` §2/§3/§4/§5 |
| 附录 B M-矩阵热线性化 | `THERMAL_MODEL.md` §2–§5 + V4 §4 |

## 四、待核实 / 遗留

1. **Milgrom–Segal (2002)**：正文仍是文字引用（`Milgrom--Segal (2002)`），`ref.bib` 无该条目（延续前一轮遗留，`Biblio/` 本轮不动）。
2. **实验参数的具体数值**：实验章 1_setup 只列「参数维度 + 来源」，未写死任何数值（含 TOY 组的整数组合、UCIE 组的具体 die 尺寸/功耗等）；待实验确定后由 `src/physical/params.py`/YAML 回填。
3. **`Discussion/main.tex` 旧稿残留**：未被 `Mainmatter.tex` 引用（属死文件），本轮任务范围（第 5–7 章 + 附录）不含它，未动。
4. **旧图**：`Img/` 下仅有 `plot_*.py`，无 `.pdf` 成品；实验章已不引用图，若后续需要图需先跑脚本生成。

## 五、交叉引用核验

- 实验章引用 `eq:unified-lp`/`eq:valiant-lp`/`eq:sens-lambda`/`eq:thermal`/`eq:ubump`/`eq:die-scale` 及 `sec:ov-bisection`/`sec:ov-linearize`/`sec:ov-diescale`/`sec:ov-twolayer`/`sec:sens-norm`/`sec:bg-nonblocking`/`chap:sensitivity`——均已在前四章确认存在，无断裂。
- 附录 A 引用 `sec:ov-performance`/`sec:scalability`；附录 B 引用 `sec:ov-linearize`/`sec:ov-thermal`/`eq:thermal`/`eq:lane-def`/`sec:ov-unified`/`sec:fidelity`——均存在。
- Conclusion 引用 `chap:overview`/`chap:sensitivity`/`chap:experiments`/`sec:bg-thermal`/`sec:bg-nonblocking`/`sec:ov-diescale`/`sec:intro-contrib`——均存在。
- 相关工作引用 `chap:sensitivity`（唯一，存在）。
- 全文 `\cite` 仅用 `ref.bib` 已有 key（清单见改动清单第 6 章），无未定义引用。

## 六、未动（按任务约束）

`Thesis.tex`、`Style/`、`Frontmatter`、`Frontinfo`、`Mainmatter.tex`、`Biblio/`、`Prematter.tex`、第 1–4 章（Intro/Background/Overview/Sensitivity）、`Discussion/main.tex`（死文件）。
