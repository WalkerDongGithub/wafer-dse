# §5 Evaluation —— 草稿（Phase 3, v0.1）

> WritingPolisher 草稿，2026-08-21。数据源：data-report-e1-e5-e6-ec.md（E1/E3A/E6/EC/E2/E7/E8，全部可复现）、experiment-design.md（判据规格）。数字未改动，照报告原文。**E5 实验（原 §5.2）已按作者指令删除（2026-08-21）：包络物理无关性 = 模型定义/构造保证，不列实验证据、不配数字。**
> 段落前 `[insight n]` = Gate④ 检查用。图 3-5 引用位按 paper-skeleton/figure-intents（包络数据图已删）。
> 诚实口径：图 3 为"热约束下排序"（标注绑定约束族）；4 端口组图同构注明；热只引 MFIT；不宣称复杂度结论（E6）。

---

## 5. Evaluation

### 5.1 Setup

We evaluate the inner feasibility model on a single interposer design. **Configurations.** Eleven topologies grouped by port count: FullMesh(2,3), Mesh(2,3,4), Torus(2,3), KaryNCube(2,2) and (2,3), Dragonfly(2,1,1) and (2,2,1) \cite{kim2008dragonfly}. Mesh(2), Torus(2), and KaryNCube(2,2) are graph-isomorphic (a $2\times2$ grid, ring, and 2-ary 2-cube are the same graph); we report them together as a consistency check. **Physical parameters.** Three parameter sets (ucie-16g/24g/32g) aligned with UCIe and OIF-CEI specifications \cite{ucie2.0-2024,oif-cei} from the shared YAML. **Scenarios.** The ablation ladder perf+bump $\rightarrow$ perf+bump+therm isolates the thermal layer; die-scaling terms ($\alpha_d$, $\beta_P$) are exercised by programmatic override. **Baselines.** (i) A separated-decision baseline that evaluates performance, thermal, and geometric feasibility factor by factor (each in its own dimension, without cross-factor backtracking); (ii) a no-DSE baseline that only checks feasibility against a fixed target $B_{\text{target}}$ (binary verdict, no continuous ranking). **Implementation coverage.** The experiments cover the main-model subset—C1 (die-side $\mu$bump allocation), die-level thermal, the expansion-ratio envelope, die scaling, interposer wiring, and die-area bounds—in the released solver \cite{diamond2016cvxpy}. Constraints C2--C4 and the substrate thermal equation are part of the model specification whose experimental coverage is future work. All runs are deterministic and reproducible from the repository.

### 5.2 $B^*$ Ranks Configurations (Fig.~\ref{fig:ranking})

**[insight 2, 5]** Under the same settings and port count, $B^*$ ranks configurations. Fig.~\ref{fig:ranking} shows $B^*$ per topology for the thermal scenario (perf+bump+therm); the ordering is stable across all three parameter sets (Spearman $\rho = 1.000$, $n=11$). The $B^*$ scale is honest about what binds: in the ucie-32g set, the thermal layer dominates—adding therm reduces $B^*$ to roughly 4--5\% of the bump-only value (a $24\times$ drop) across all topologies, and the binding constraints are almost all thermal ($\texttt{therm\_d*}$). Fig.~\ref{fig:ranking} is therefore a ranking under thermal constraints, annotated with the binding constraint family. The four-port group (Mesh(2)/Torus(2)/KaryNCube(2,2)) is graph-isomorphic, and their identical $B^*$ is a consistency check on the model, not a distinguishing result. With the no-DSE baseline, all configurations would be judged only "feasible or not" at a fixed target; $B^*$ exposes the margin each configuration actually has.

### 5.3 Coupled vs.\ Separated Decision-Making (Fig.~\ref{fig:coupling})

**[insight 4, 7]** Does the joint model matter, or is factor-by-factor evaluation equivalent? We answer in two stages. **Stage 1 (equivalence boundary).** In the subset without wiring and area constraints—linear physical constraints, envelope-pinned loads, and geometry always slack—the joint model and the separated baseline are mathematically equivalent: $B^*_{\text{joint}} = \min(B^*_{\text{bump}}, B^*_{\text{therm}})$ holds analytically and all 11 topologies show rel\_diff $= 0$. This is the honest boundary of the linear-separable subset (details in Appendix). **Stage 2 (divergence under wiring/area).** Once interposer wiring and the die-area bound are first-class constraints, the equivalence breaks. Under a separated baseline that fixes routing paths factor by factor, 10 of 72 configurations diverge from the joint model by more than 1\% in $B^*$ (geometric mean 0.264, max 0.352). The divergence concentrates on wiring-saturation points (100 lanes/mm): Mesh(3) shows rel\_diff $= 0.154$ ($B^*_{\text{sep}}=1075$ vs.\ $B^*_{\text{joint}}=1270$), Torus(3) 0.190, KaryNCube(2,3) 0.352/0.266; at default parameters KaryNCube(2,3) shows 0.087. The mechanism is path diversity: the separated baseline commits to the first candidate path, which saturates under wiring capacity, while the joint model reroutes around it. On single-path (dragonfly-class) topologies, a complementary mechanism holds: wiring saturates before the bump or thermal budget binds. The claim is therefore "separated decision-making diverges from the joint model under wiring and area constraints," demonstrated on wiring-saturation and multi-path topologies and bounded honestly on the rest.

### 5.4 Sensitivity: Which Knob Unlocks a Design Point? (Fig.~\ref{fig:sensitivity})

**[insight 3]** We first confirm the requirement $\times$ constraint framework of \S4.2.3: across 7 topologies and 3 parameter sets, the four knob combinations (QoS vs.\ peak requirement, peak vs.\ rated constraint) rank monotonically with no cross-over (M1--M3 pass). Relaxing the requirement from full QoS to per-port peak raises $B^*$ by a geometric mean of $2.64\times$; relaxing the constraint to rated power raises it further (up to $17.9\times$--$28.6\times$ with die scaling enabled). $B=f(\text{requirement},\text{constraint})$ holds directionally as claimed.

**[insight 4, 7]** The second part turns the model into a design guide. The inner model is nonlinear in $B$ (only the fixed-$B$ subproblem is a linear program), so we compute sensitivity at the optimum with KKT multipliers via the envelope theorem (Appendix~B): at a KKT point, the derivative of $B^*$ with respect to a physical parameter $\theta$ is $\lambda^{\top}(\partial g/\partial\theta) + \mu^{\top}(\partial h/\partial\theta)$, where $\lambda$, $\mu$ are the multipliers of the active constraints. Multiplying by how much each knob moves the constraints gives an \emph{unlocking rate} per knob—the first-order gain in $B^*$ per unit of knob investment. At a thermal-bound point, the estimate is accurate (per-lane power $-1\%$ yields $+1.11\%$ in $B^*$; first-order error 0.2\%, at most 0.7\% across the tested grid). The ranking is parameter-domain dependent: with no die scaling the per-lane power ranks first, while with die scaling enabled the cooling resistance overtakes it—reported per domain, not as a universal order. At a wiring-saturation point (tight RDL budget, 50 lanes/mm), the ranking is counterintuitive and matches the coupling case of \S4.2.2: improving cooling releases nothing—reducing $R_{\text{vert}}$ from 2.5 to 0.4 leaves $B^*$ at 490\,Gbps, because the power/ground traces now consume the wiring budget. The top-ranked knob is the power-wiring demand itself: cutting $c_{\text{pwr}}$ fourfold (2$\rightarrow$0.5) raises $B^*$ by 40\% (490$\rightarrow$685\,Gbps). The coupling is directly measurable: as $c_{\text{pwr}}$ grows 0$\rightarrow$2$\rightarrow$10, $B^*$ falls 685$\rightarrow$490$\rightarrow$295\,Gbps ($-28\%$, $-57\%$)—the power traces re-consume the capacity the designer is trying to free. The tool prescribes per design point: thermal-bound points rank cooling and per-lane power first; wiring-saturation points rank the power-wiring demand first. The coupling domain is bounded honestly: the power-trace term binds in the wiring-saturation regime with small die scaling (50 lanes/mm); at the default 500 lanes/mm the term does not bind, and the domain is reported as such. Structural knobs such as the C4-pad pitch are handled as design-point comparisons rather than marginal sensitivities.

### 5.5 Scalability (insight 7)

**[insight 7]** Solving one configuration is cheap: the bisection-style outer search needs 8 feasibility checks per configuration (matching $\log_2(249.5)\approx 8$ over the search range), and each check is a single linear program. End-to-end solve time grows gently with size: 0.05--2.29\,s for Mesh(2)--Mesh(6) and 0.04--7.07\,s for Torus(2)--Torus(6) on the ucie-32g set; the largest single LP is about 0.3\,s. The time-vs-size profile is approximately linear on a log--log scale—a polynomial profile, consistent with the polynomial-time claim of \S4.3. We make no formal complexity claim beyond the structural argument (Appendix~B).

---

## 中文结构说明

- 5.1 覆盖：拓扑 11、参数 3 组、场景阶梯、双基线、实现覆盖（C1+热+包络+die 缩放+布线/面积；C2-C4 规范级如实声明）。
- 5.2（图 3）：排序稳定 ρ=1.000；热主导诚实标注（24× 衰减、绑定约束族 therm_d*）；4 端口组图同构注明。
- 5.3（图 4）双阶段：v1 等价性边界（附录）+ v2 分歧实证（10/72，机制=路径多样性 1075→5363）+ C4' 单路径拓扑补充；claim 精确限定"多路径拓扑 + 布线/面积下"。
- 5.4（图 5）双面板：E2 旋钮矩阵（insight 3）+ KKT 解锁量（E7/E8，杀手锏，per-point 处方）。
- 5.5：迭代 8≈log₂(249.5)、时间-规模多项式轮廓、不宣称复杂度结论（纪律）。
- 全部数字照 data-report 原文；示例数字（685/490/295、c_pwr 0.5/2/10 试点）为 E7 试点映射，参数评审前标注。
- **E5 实验（原 §5.2 首选图）已删除**（作者 2026-08-21 指令）：包络物理无关性为模型定义/构造保证，§4.2.1 定义句保留，不配实验数字；图 3-6 → 图 3-5。

## 待办/缺口

- [ ] EvalDesigner 复核：5.1-5.5 判据陈述与 experiment-design 规格逐条对应；图 3-5 数据面板结构
- [ ] DataSteward：c_pwr 物理取值参数评审（试点值 0.5/2/10 需定稿）；数字终校
- [ ] FigureArtist：图 3-5 数据图（源数据齐；包络图已删）
- [ ] 附录 A/B 素材引用（KKT 证明、等价性推导）待 DomainExpert 定稿后补 \ref
- [x] E5 实验论述/数字全部删除（作者 2026-08-21 指令）：正文 §5.2 节删、摘要/Intro/Conclusion 相关句删；包络物理无关性仅以 §4.2.1 定义句保留
