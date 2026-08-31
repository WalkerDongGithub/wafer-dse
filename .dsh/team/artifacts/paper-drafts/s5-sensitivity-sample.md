# §5.4 灵敏度叙事示范 + 写作侧审阅（WritingPolisher 贡献）

> WritingPolisher，2026-08-21。**不覆盖** DomainExpert 主持的 `sensitivity-design.md`（方法内容归它）；本文件只补 master 指派我的两块：① 叙事形态示范文字（§5.4 灵敏度节 + 案例框，等 DomainExpert 定稿方法后落地）；② 写作/严谨性侧审阅意见（供 DomainExpert 参考，非裁决）。
> 术语：unlocking rate（解锁率）/ binding constraint family（绑定约束族）/ shadow price（影子价格）——**DomainExpert 2026-08-21 全部认可，已固化入 terminology-ledger v0.4**。
> 审阅状态：**4 条意见 DomainExpert 全部采纳**（2026-08-21，已并入 sensitivity-design.md §3.2/§3.3/§4），本文件 §3 仅为归档记录。

---

## 1. §5.4 示范文字（英文论文散文，数字已按 E7/E8 实测回填）

> 结构 = 分析 → 定位瓶颈 → 可行动结论。**框架 = KKT 乘子 / 包络定理**（作者 round 21+ 指令 A：模型整体非线性，固定 B 子问题才是 LP）。**数字来源**：E7 完整版（data-report 附录 E，Mesh(3)/lanes=50 布线饱和域）与 E8 定稿（附录 D，热绑定一阶误差 0.2%）；单位 Gbps，与 data-report 口径一致。待 DomainExpert 定稿方法后落地正文。

---

**5.4 Sensitivity Analysis: Which Knob Unlocks a Design Point?**

The inner model is nonlinear in $B$; only its fixed-$B$ subproblem is a linear program. At the optimum, the sensitivity of $B^*$ to a physical parameter $\theta$ follows from the envelope theorem for constrained optimization: at a KKT point $(x^*, \lambda^*, \mu^*)$, $dV/d\theta = \partial L/\partial\theta = \lambda^{\top}(\partial g/\partial\theta) + \mu^{\top}(\partial h/\partial\theta)$, where $\lambda$, $\mu$ are the KKT multipliers of the active inequality and equality constraints and $g$, $h$ are the constraint functions. Each multiplier is the marginal value of one unit of its constraint's right-hand side; multiplying by how much a knob moves the affected constraints gives an \emph{unlocking rate} per knob—the first-order gain in $B^*$ per unit of knob investment. When the fixed-$B$ subproblem is used, KKT multipliers reduce to LP dual variables (shadow prices) and the formula is exact for that subproblem; in the general nonlinear case the estimate is first-order, and we confirm it by re-solving at the relaxed point (first-order error 0.2\% at a thermal-bound point). Monotonicity of $B^*$ in constraint relaxation bounds the direction of every result.

Table~\ref{tab:sensitivity} reports the ranked unlocking rates at a wiring-saturation design point—a tight RDL budget shared by signal traces and power/ground traces (Mesh(3), 50 lanes/mm). The ranking is counterintuitive: improving cooling releases nothing. Reducing $R_{\text{vert}}$ from 2.5 to 0.4 leaves $B^*$ unchanged at 490\,Gbps: the thermal bound stops binding, but the wiring budget, now consumed by power/ground traces, hard-blocks any gain. The top-ranked knob is the power-wiring demand itself: cutting the P/G demand coefficient fourfold ($c_{\text{pwr}}$: 2$\rightarrow$0.5) raises $B^*$ by 40\% (490$\rightarrow$685\,Gbps). The coupling is directly measurable: as $c_{\text{pwr}}$ grows 0$\rightarrow$2$\rightarrow$10, $B^*$ falls 685$\rightarrow$490$\rightarrow$295\,Gbps ($-$28\%, $-$57\%)—the power traces re-consume the very capacity the designer is trying to free. This is the power–cooling–wiring coupling of \S4.2.2 in numbers: on the cooling side it fails, on the power side it unlocks.

The actionable conclusion is prescriptive and point-dependent. At this wiring-saturation point, "improve the cooling" is the wrong first move; the analysis ranks the power-wiring demand first and quantifies its gain. At a thermal-bound point, the same analysis ranks per-lane power and $R_{\text{vert}}$ first—a $1\%$ cut in per-lane power yields $+1.11\%$ in $B^*$—so the tool prescribes per point rather than assuming one fix fits all. Structural knobs such as the C4-pad pitch are handled as design-point comparisons, not marginal sensitivities. Sensitivity analysis thus turns the DSE from a scoring oracle into a design guide: for every candidate configuration, the designer receives not only $B^*$ but the ranked set of physical knobs that move it—something a Pareto-front DSE cannot provide, because a Pareto point does not carry its own unlocking directions.

---

## 2. 案例框（Case Box，备选形态）

**Power–Cooling–Wiring: When "Improve the Cooling" Is Not the Fix**（数字 = E7/E8 实测，data-report 附录 D/E）

| 直觉动作 | 实测 | 机制 | 真解锁旋钮 |
|---|---|---|---|
| 提散热 $R_{\text{vert}}$（2.5→0.4） | **B\* 恒 490 = 零释放** | therm 绑定消失，布线被 power 走线顶住（绑定迁移 therm→route/power） | 降功耗走线需求 $c_{\text{pwr}}$ |
| 降功耗走线需求 $c_{\text{pwr}}$（2→0.5） | 490→685（**+40%**） | P/G 走线需求下降，布线约束直接放松 | — |
| 耦合量化 $c_{\text{pwr}}$（0→2→10） | 685→490→295（−28%/−57%） | power 走线 ∝ 功耗重吃 RDL，带宽涨→功耗涨→容量被吃回 | — |
| 热绑定点 per-lane 功耗（−1%） | B\* +1.11%（一阶误差 0.2%，E8） | 降功耗同时松热与 P/G 需求 | ppl / $R_{\text{vert}}$ |

（c_pwr 物理取值 0.5/2/10 为试点映射耦合敏感度，待参数评审；C4-pad 离散结构旋钮走"设计点对比"非边际灵敏度。）

---

## 3. 写作侧审阅意见（归档：DomainExpert 2026-08-21 全部采纳，已并入 sensitivity-design.md）

> **作者 round 21+ 指令 A 修正（2026-08-21，优先级高于本文件 3.1/3.2 的 LP 表述）**：模型本质非线性（只有固定 B 子问题是 LP）——灵敏度框架 = NLP 的 **KKT 乘子 / 包络定理**：KKT 点 $(x^*,\lambda^*,\mu^*)$ 处 $dV/d\theta = \partial L/\partial\theta = \lambda^\top(\partial g/\partial\theta) + \mu^\top(\partial h/\partial\theta)$。要求：① 明确整体非线性；② 用 KKT/包络框架；③ 退化为固定 B 的 LP 处说明成立条件与局限，不默认全局成立。本文件 3.1 的 max-B LP 是 LP 特例的局部线性化、3.2 的系数公式是包络定理在 LP 情形的展开——**均被 A 吸收为特例**；正式方法以 DomainExpert 更新后的 sensitivity-design.md 为准。

### 3.1 数学表述的可选强化（对应 sensitivity-design.md §8 开放项"误差界形式化"）
- 现有方案（B\* 处松弛可行性 LP，min Σs_i，λ = 边际不可行性，再除以约束的 B-系数 α_i 换算 ΔB\*）作为**一阶方案**成立、且 cvxpy 直接可读。
- 更干净的理论表述（可作附录素材）：在 B\* 处把 die 缩放二次项固定为常数，解**线性化 max-B LP**（目标 = max B），其对偶 λ\* **直接**给出 ∂B\*/∂rhs_i（包络定理），无需除以 α_i；误差 O(Δθ²)（被排除项光滑、在 B\* 处一阶变分为零）。两方案在非退化下等价，前者实现近、后者表述严——**由 DomainExpert 定**。

### 3.2 系数旋钮的公式缺口（建议补）
- sensitivity-design.md §2 旋钮表含"每 lane 动态功耗 p_e（S_dyn 对角元）"、"供电 V_dd / 载流 I_bump"——这些进入**系数矩阵 A(θ)** 而非仅 rhs；现有 §3.2 公式只覆盖 rhs 旋钮。通用形式（对系数+rhs 旋钮都成立）：
  $$
  s_\theta = \lambda^{\top}\Big(\frac{\partial \mathbf{b}}{\partial \theta} - \frac{\partial \mathbf{A}}{\partial \theta}\,\mathbf{z}^*\Big)
  $$
  建议并入，否则系数旋钮的解锁量无法算。

### 3.3 取整天花板（严谨性边界）
- $\mathbf{N}_{\text{die}}^{\text{pwr}}=\lceil P/(V_{dd}I)\rceil$、$\mathbf{N}_{\text{C4}}^{\text{pwr}}$ 等取整使 rhs/系数**分段常数**——一阶公式在阈值间有效，跨阈值需重解；建议在 §3.3 边界一节如实声明（同 IMPLEMENTATION_MAP.md 的代码口径）。

### 3.4 ⚠ 示例数字必须标注来源（伦理/准确性）
- sensitivity-design.md §4 "可行动结论"示例（"R_vert 2.5→0.4（+6×）解锁 +380%、β_P 降 50% 解锁 +210%、布线容量 +50% 仅 +8%"）若为**示意数字**，请标注 [示例，待小验证回填]；若已有实测来源，请注明出处——摘要/正文引用前须与实验表可复现对齐（CCF 纪律 + 禁编造数据）。

---

## 4. 待办

- [x] 审阅意见闭环：DomainExpert 全部采纳（2026-08-21）——max-B LP 路径 B 已入 §8 附录素材、系数旋钮公式已并入 §3.2、取整边界已入 §3.3、示例数字已标注 [示例，待回填]
- [x] 术语固化：unlocking rate / binding constraint family / shadow price → terminology-ledger v0.4
- [ ] **作者 round 21+ 指令 A**：sensitivity-design.md 框架改为 **KKT/包络定理**（DomainExpert 更新）；本文件示范文字已按 KKT 重写；3.1/3.2 标注被 A 吸收
- [ ] DomainExpert 整合时合并本文件（§5.4 示范文字 + 案例框骨架）进 sensitivity-design.md / 论文
- [ ] **数据回填完成**：§5.4 示范文字已按 E7/E8 实测替换 [X] 占位（E7：c_pwr 2→0.5 → +40% 解锁、R_vert 零释放、c_pwr 0→2→10 → −28%/−57%；E8：ppl −1% → +1.11%、一阶误差 0.2%）；此前初测锚点 ppl +3.63% 已被 E8 定稿 +1.11% 取代
- [ ] c_pwr 物理取值待参数评审（0.5/2/10 试点）；单位 Gbps 与 data-report 口径一致（落地前最后核对）
- [ ] DomainExpert 定稿方法表述后落地 §5.4 正文
- [ ] EvalDesigner：表 X 结构 + 判据（"排序方向一致、一阶误差 < 阈值"）
- [ ] DataSteward：小验证扩展（热绑定/布线绑定设计点 + 系数旋钮细步长）

## 版本记录
- 2026-08-21（v0.1）：示范文字 + 审阅意见。
- 2026-08-21（v0.2）：审阅 4 条全部采纳归档；术语固化；数据锚点登记（ppl −1% → +3.63%）。
- 2026-08-21（v0.3）：**作者 round 21+ 指令 A/B**——示范文字按 KKT/包络定理重写（非线性 + LP 特例条件声明）；3.1/3.2 标注被 A 吸收；B 风格自查（朴素优先、术语克制）。
- 2026-08-21（v0.4）：**E7/E8 实测回填**——[X] 占位全部替换（R_vert 零释放 490 / c_pwr +40% 685 / 耦合 −28%/−57% / ppl +1.11%）；案例框改实测版；初测锚点 +3.63% 由 E8 定稿取代。
