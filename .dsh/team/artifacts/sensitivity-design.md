# 灵敏度分析设计（sensitivity-design v0.3）

> DomainExpert 整合，2026-08-21（v0.3：作者 round 21+ 指令 A——数学框架改为 NLP KKT/包络定理；B——按朴素简洁风格精简）。
> 定位：论文 §5.5 灵敏度——输出"B\* + 绑定约束族 + 每旋钮解锁量排名"（别的 DSE 只给设计点/Pareto）。
> 验证阶段策略【0】：小实验验证方向，不跑大实验。

---

## 1. 定位

**作者目标形态**："根据灵敏度分析，改进走线，一切就都解决了"——定位瓶颈旋钮，改它全局解锁。

- 别的 DSE：输出设计点 / Pareto（"这个点可行"）；
- 我们：输出 **B\* + 绑定约束族 + 每旋钮解锁量**（"改这个旋钮，B\* 涨 X%"）——工程可行动结论。

三大要求：(a) 数学严谨；(b) 工程震撼（别的 DSE 做不到）；(c) 与耦合案例结合（功耗-散热-布线三方牵制下揭示**真解锁旋钮**）。

---

## 2. 数学形式：KKT/包络定理（作者 round 21+ 指令 A 定案）

### 2.1 模型整体是非线性优化（NLP），不是 LP

以 $B$ 为决策量的整体问题是**非凸 NLP**（die 缩放 $A_{\text{die}}(B)=(d_0+\alpha_d B)^2$ 引入 $B$ 的二次项；$N_{\text{pwr}}=\lceil\cdot\rceil$ 取整）。只有**固定 $B$ 时**子问题退化为 LP。

$$
\max_{B,\mathbf{z}} \; B \quad \text{s.t.} \quad \mathbf{g}(\mathbf{z},B,\theta) \le 0,\;\; \mathbf{h}(\mathbf{z},B,\theta) = 0
$$

### 2.2 灵敏度 = KKT 乘子 / 包络定理（对偶扰动定理）

在 KKT 点 $(\mathbf{z}^*, B^*, \boldsymbol{\lambda}^*, \boldsymbol{\mu}^*)$ 处，最优值 $V = B^*$ 对旋钮 $\theta$ 的导数：

$$
\boxed{\;\; \frac{dV}{d\theta} \;=\; \frac{\partial \mathcal{L}}{\partial \theta} \;=\; \boldsymbol{\lambda}^{*\top}\frac{\partial \mathbf{g}}{\partial \theta} + \boldsymbol{\mu}^{*\top}\frac{\partial \mathbf{h}}{\partial \theta} \;\;}
$$

其中 $\mathcal{L} = B + \boldsymbol{\lambda}^\top\mathbf{g} + \boldsymbol{\mu}^\top\mathbf{h}$。一个公式统一两类旋钮：
- **rhs 旋钮**（θ 只进 g 的右端）：$\lambda^\top(\partial \mathbf{b}/\partial\theta)$；
- **系数旋钮**（θ 进 g 的系数，如 ppl→S_dyn）：$\lambda^\top(\partial \mathbf{A}/\partial\theta)\,\mathbf{z}^*$（含在 $\partial\mathbf{g}/\partial\theta$ 内）。

**归一化呈现**：弹性 $\frac{\Delta B^*/B^*}{\Delta\theta/\theta}$（每 1% 旋钮变化释放多少 % 带宽），每旋钮一个标量，排序 = 解锁量排名。

### 2.3 固定 B 的 LP 退化情形（成立条件与局限）

固定 B 时子问题为 LP，KKT 乘子即 **LP 影子价格**（cvxpy `dual_value` 可读）。成立条件：LP 强对偶（固定 B 满足）＋非退化绑定。**局限（必须声明，不得默认全局成立）**：
1. 对偶单位是 $\Delta(\text{目标})/\Delta\text{rhs}$——min-ΣL 对偶是 $\Delta\Sigma L/\Delta\text{rhs}$（L 空间），**非 $\Delta B^*/\Delta\text{rhs}$**；B 空间解锁量须用完整 NLP 的 KKT 乘子（B 为决策量的包络定理）或数值验证；
2. 一阶近似在非退化绑定下局部精确；退化（多绑定）取 min 保守；
3. 取整（$N_{\text{pwr}}=\lceil\cdot\rceil$）使 rhs 分段常数——跨取整边界需重解，报告保守估计；
4. 离散结构旋钮（见 §3）不适用一阶框架。

**数值路径（现役，验证阶段）**：细步长有限差分（step=20-50）重跑 BmaxQuery，天然覆盖 NLP 全非线性（含系数旋钮）——小实验验证方向，秒级。

---

## 3. 旋钮-绑定族匹配（E8 实测修正）

**旋钮集必须按绑定约束族匹配**——不能对所有设计点用同一旋钮集：

| 绑定约束族 | 对应解锁旋钮 | 性质 |
|---|---|---|
| therm（热） | R_vert / β_P / ppl | 平滑一阶（有限差分适用） |
| route_edge/vert | lanes_per_mm（布线容量） | 平滑一阶 |
| **route_c4pad** | **C4 布局（c4_pitch）** | **离散结构旋钮——改变格点布局，非平滑一阶（作设计点对比，非边际扰动）** |

- **实测**：Dragonfly 布线绑定在 C4 pad（joint=wiring=7997）；c4_pitch ±1%/-5% 均 −25% = 离散网格效应；
- **榜首旋钮随设计点/参数档变化（per-point prescription 实证）**：Mesh(3) β=0.05 档 R_vert −5%→+6.10% 主导；默认档 ppl −1%→+3.63% 主导——**不同设计点处方不同**（D4），报告须标注参数域；
- **离散旋钮处理**：C4 布局作设计点对比（pitch 方案 A/B），不进入一阶解锁量排名；表 X 标注绑定族全名。

**分辨率陷阱**：BmaxQuery 默认 step=200 隐藏 <4% 效应（R_vert step=200→0.00%、step=20→+1.11%）——固定细步长（step=20-50），报告 step 与 B\* 规模（分辨率下限随 B\* 变化）。

---

## 4. 工程可行动翻译

- **输出**（`sensitivity_report`）：旋钮 θ | 绑定约束族 | 解锁量（弹性 per 1%）| 排名；
- **可行动结论**（数字以实测回填，防编造数据）："散热 R_vert↓ 解锁 +X%；β_P↓ 解锁 +Y%；布线容量 +50% 仅 +Z%（因 power/gnd 随功耗缩放同步占用）"——**首实测**：ppl −1%→+3.63%（Mesh(3) 默认，榜首）；
- **与 ledger 衔接**：绑定约束族（min-ΣL 诊断）→ 每旋钮解锁量（连续量化升级）。

---

## 5. 与耦合案例结合的叙事（杀手锏段）

**场景**：一个 interposer 设计在 B\* 处绑定 therm + wiring。

**灵敏度排名揭示**：
1. **表面直觉**："布线饱和 → 加布线容量"——但布线容量排名靠后：带宽涨 → 功耗涨 → power/gnd 走线需求同步涨 → 刚加的容量又被吃掉（耦合案例的数学回声）；
2. **真解锁旋钮**（实测）：**ppl 降功耗 −1%→+3.63%（榜首）**——一个旋钮、两处受益（松热约束 + 降 power 走线需求）；"**根据灵敏度分析，降功耗/提散热，一切就都解决了**"；
3. **分离决策做不到**：逐因素独立判定看不到"布线容量 ↑ 被 power 走线 ↑ 抵消"的跨约束牵制——单一模型 + KKT 乘子排名揭示真相（insight 4 终极形态）。

**叙事链条**：分析（KKT 乘子/有限差分）→ 定位瓶颈（绑定族 + 解锁量排名）→ 可行动结论 → 验证（小 Δθ 重解 vs 一阶预测）。

**§5.5 示范文字骨架**（数字以实测回填）：
- 反直觉句："expanding wiring capacity ranks near the bottom. The released bandwidth raises power demand, whose power/ground traces re-consume the very RDL capacity the knob just added."
- per-point 句："the tool prescribes per point, rather than assuming one fix fits all."
- vs Pareto 收尾："a Pareto point does not carry its own unlocking directions."

---

## 6. 实现要点

1. **现役**：数值有限差分（step=20-50），秒级，天然覆盖 NLP 非线性；cvxpy dual_value（min-ΣL 对偶）仅作绑定族识别；
2. **严谨版（后期可选）**：NLP KKT 乘子（B 为决策量）——包络定理直接给 ∂B\*/∂θ；或线性化 max-B LP（附录素材）；当前 build 把 B 当参数，需模型层支持（暂不建 query，验证阶段不阻塞）；
3. **验证**：2-3 旋钮 × 小 Δθ，一阶 vs 重解对比（实测误差 0.2%，仿射约束下一阶几乎精确）；
4. **退化处理**：多绑定报告全部候选解锁量（min 保守 + 原始信息）。

---

## 7. 与论文章节衔接

- §5.5 灵敏度：旋钮 × 解锁量条形图 + 绑定族标注（图 6）；E2 knob_matrix 实证面板（双面板：分析 vs 实测）；
- C2 强化：B\* 是灵敏度分析的量化基石（insight 5 深化）；
- Discussion：反直觉发现（改走线收益有限 vs 降功耗真解锁）= insight 4 耦合价值收官证据；
- 附录：KKT/包络定理推导 + 固定 B LP 退化情形成立条件（作者指令 A 要求明确非线性 + 局限声明）。

---

## 8. 待定

- [x] SensitivityQuery：**暂不建**（方向级用有限差分 + duals；严谨版 KKT 乘子后期评估）；
- [ ] 与 G2 双旋钮衔接：灵敏度默认在 R_qos×C_peak 最严档分析（B\* 保守下界处）；
- [ ] 一阶误差界形式化（理论章/附录素材）。

## 版本记录

- v0.1（08-21）：影子价格方案初版
- v0.2（08-21）：双分支公式 + 旋钮-绑定族匹配 + 分辨率陷阱 + 示范文字
- **v0.3（08-21，作者指令 A+B）**：数学框架改为 **NLP KKT/包络定理**（声明整体非线性；LP 影子价格降级为固定 B 退化情形并写明成立条件与局限）；按 B 风格精简（从 166 行 → 约 90 行，删堆砌、保留几个符号说清的核心公式）。
