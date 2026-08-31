# V5 修正日志（v5 版本历史）

> **释经文档**：本文件承载 `notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md`（经书）的版本历史——2026-08-21 经书/释经拆分时从 v5 移出。
> v5（经书）只回答"模型是什么"；本文件只记录"模型改过什么"。
> 决策上下文见 `.dsh/team/decisions.md`；实现状态见 `notes/IMPLEMENTATION_MAP.md`。

---

**v5.30（2026-08-21，§2 新增 (2g) die 侧 μbump 预算——作者：完完整整加回 Die 级模型）**：
1.  **§2 新增 (2g)**：$\mathbf{M}_{\text{D2D} \to \text{die}}\,\boldsymbol{\ell}_{\text{D2D}} + \mathbf{M}_{\text{I2I} \to \text{die}}\,\boldsymbol{\ell}_{\text{I2I}} + \mathbf{N}_{\text{die}}^{\text{pwr}}(B) \le \mathbf{N}_{\text{die}}^{\text{total}}(B)$——die 侧信号 lane（D2D + I2I 出 die 侧）与电源 μbump 共享 μbump 总量；含 $N^{\text{pwr}}=\lceil P^{\text{peak}}(B)/(V_{dd} I_{\text{bump}}) \rceil$ 与 $N^{\text{total}}=\eta A_{\text{die}}(B)/p^2$ 完整定义（同 §2.8/C1 口径）。
2.  **§4 C1 改为指向 (2g)**（跨层耦合含义保留：I2I SerDes PHY 挤压 D2D 信号预算），消除"约束只在耦合段"的结构缺陷。
---

**v5.29（2026-08-21，§2(2d) 修正：布线容量补功耗 lane——作者指出的模型窟窿）**：
1.  **窟窿**：原 (2d) 布线容量只计信号 lane（$\mathbf{W}\,\mathbf{x} \le \mathbf{C}$），漏了 Power/GND 供电走线占 RDL——布线容量被高估，布线绑定处 $B^*$ 偏乐观。此前"power 走线项"（c_pwr）是对此窟窿的过度参数化尝试（非经书表述），已回退。
2.  **修正（进经书，与 C1 电源 μbump 同口径）**：(2d) 容量改为 $\mathbf{W}\,\mathbf{x} + \mathbf{W}_{\text{pwr}}\,\mathbf{n}_{\text{wiring}}^{\text{pwr}}(B) \le \mathbf{C}$（信号 lane 与功耗 lane 共享 edge/vert/pad 容量）；新增 (2d') 功耗 lane 定义 $n_{\text{wiring},v}^{\text{pwr}}(B) = \lceil P_{\text{die},v}^{\text{peak}}(B)/(V_{dd}\,I_{\text{metal}}) \rceil$（$P^{\text{peak}}(B)=P_0+\beta_P B$，固定 $B$ 为常数，LP 结构不变）。
3.  **符号表**：删 $c_{\text{pwr}}$，新增 $I_{\text{metal}}$ / $\mathbf{n}_{\text{wiring}}^{\text{pwr}}(B)$ / $\mathbf{W}_{\text{pwr}}$。
4.  **影响（如实）**：布线绑定处的 $B^*$ 需在实现后重核——原数据未含功耗 lane，高估布线容量。
---

**v5.28（2026-08-21，经书/释经拆分）**：
1.  **v5 定位净化**（作者指令）：v5 只保留 ① 唯一参考符号体系 ② 唯一参考模型标准 ③ 必要符号解释 ④ 必要约束项物理意义。
2.  **派生内容全部移出**（不删除，各归其位）：求解策略/模型性质讨论 → `notes/MODEL_PROPERTIES.md`；实现对应表、参考文献、power 走线推导细节 → `notes/IMPLEMENTATION_MAP.md`；待定案 → `.dsh/team/decisions.md` 待决项；本修正日志 → 本文件；insight 相关内容 → `notes/INSIGHT_READING.md`。

**v5.27（2026-08-21，§8 power 走线项实现状态）**：
1.  **§8 §2(2d) 行更新**：power 走线项实现（git 3ac0c50，test20 锚定）——`c_pwr_lane_per_w` 构造参数（默认 0 关闭）、`_link_pwr` 预计算（1+c_pwr·s_dyn）、`pwr_rhs` 扣减（c_pwr·(P0+β_P·B)）、fixed/optimize 两模式同源（防不公平基线）；run_all 21/21 全绿。
2.  参数域观察（CodeEngineer 诚实报告）：默认 β_P=0 时 rhs 扣减为常数（等价全边容量等量减，B\* 位置不变）；"power 顶满 RDL"可量化演示需布线饱和参数域（lanes_per_mm 小 + β_P 大）——E7 实验设计在该域找可量化表现（作者 round 21【2】）。

**v5.26（2026-08-21，power 走线项双分支表述修正）**：
1.  **§2 (2d) power 走线项 v5.25 表述修正**：原"固定 B 下 $P_{\text{die}}(B)$ 为常数"不准确——$P_{\text{dyn}} = \sum_l s^{\text{dyn}}_l \frac{B}{\text{lr}_l} L_l$ 依赖 $L$（非常数）。**双分支定案**：$P_{\text{dyn}}$ 折进 L 系数（$(1 + c_{\text{pwr}} s^{\text{dyn}}_l)$ 乘 $\frac{B}{\text{lr}_l} L_l$），$P_0 + \beta_P B$ 为 rhs 扣减；固定 B 下仍线性（LP 结构不变）。参数契约：`c_pwr_lane_per_w`（默认 0 = 关闭，ucie 谱系 YAML）；构造参数开关（非场景 token）；**fixed_paths 分离基线同用**（防不公平基线）。
2.  背景：CodeEngineer 实现语义请示（q-f153a487，DomainExpert 定案选型 (a)）；E7 power 耦合实验前置。

**v5.25（2026-08-21，power 走线项定义——作者 round 21+ 指令【1】）**：
1.  **§2 (2d) 新增 power 走线项**：$\sum (B/\text{lr}_l) L_l + c_{\text{pwr}} P_{\text{die}}(B) \le \text{cap}_e$——Power/GND 走线与信号 lane 共享 RDL 容量；$c_{\text{pwr}}$ 为 lane 当量系数（参数 YAML）；$\beta_P>0$ 时"功耗—散热—布线/性能"三方牵制数学成立；固定 B 下 LP 结构不变。
2.  背景：作者 round 21+ 指令【1】标准耦合案例（INSIGHT_READING §4）——E7 实验（EvalDesigner 设计）前置缺口 G7（DomainExpert 拍板，model-ruling §十一）；CodeEngineer 小实现（WiringModel power_trace 参数）+ DataSteward E7 小实验（验证阶段策略【0】）。

**v5.24（2026-08-21，§8 布线 fixed_paths 模式标注）**：
1.  **§8 §2(2d) 行更新**：`WiringModel` 增加 `fixed_paths: bool = False` 构造参数（默认 = optimize 行为，回归锚点 B\*=11211 不变）+ 公开 helper `build_wiring_fixed`（problem.builder 导出）——固定候选路径模式（git f680fc5/ed15196，E3B v2 分离基线布线因素，test19 锚定）。固定路径 = L 形最短路径（曼哈顿，候选集与联合同源，仅去掉 x 分流自由度）——分离基线公平性依据（防"不公平基线"攻击）。
2.  **E3B v2 数据关联**：DataSteward 用该模式重跑产出 `sep_vs_joint_v2_fixedpath_ucie-32g.csv`（C3' 10/72 分歧通过，model-ruling §十）。

**v5.23（2026-08-20，§8 实现对表状态同步）**：
1.  **§8 实现对表更新**：§7.3b R_peak 单对流量包络（`ObliviousValiantModel requirement="peak"`）、§2.8 C_rated（`rated` token + `beta_p` 程序化覆盖）标 ✅（git 5008ed0）；§2 (2d) 布线（`WiringModel`）、§2 (2f) 面积上界（`DieAreaModel`）标 ✅ 已接入 `build_scenario`（git 459a6ed，V5 v5.21 一级约束）。次随机方案确认未实现（作废）。
2.  实现与文档一致性：CodeEngineer 交付（run_all 19/19 全绿）经抽查与 V5 §7.3b/§2.8/§2(2d)(2f) 语义一致，无冲突。

**v5.22（2026-08-20，双旋钮定义——要求 R × 约束 C）**：
1.  **§0.1 新增双旋钮档位表**：四档（R_qos/R_peak × C_peak/C_rated）正交可组合；R 只作用于性能包络（§7.3），C 只作用于物理 rhs（§2.8），无交叉项。默认档 R_qos × C_peak 保持最严（原 §0.1 语义不变）。
2.  **§7.3b 新增 R_peak 单对流量包络**：$L_e^{*}(\text{R\_peak}) = \max_{(i,j)} c_{ij}^{e} \le 1$——闭式解（O($|E|N^2$)），替代 Birkhoff 子 LP 结果；并论证为何不采用次随机放宽（次随机与双随机包络最大值相等，无区分度）。
3.  **§2.8 新增 C_rated rhs 定义**：$P_{\text{peak}}^{\text{rated}} = P_0$（$\beta_P := 0$）；BumpModel rhs 变常数 $\lceil P_0/(V_{dd} I_{\text{bump}}) \rceil$，热方程 (2e) 去掉 $\beta_P B$ 项、保留链路动态功耗。
4.  背景：G2 场景参数化（EvalDesigner 实验设计 §2 E2/§4 G2、CodeEngineer 实现）；论文 §5.5 灵敏度（insight 3）的模型侧落点。

**v5.21（2026-08-20，布线/面积一级化——作者推翻 G4 默认裁决）**：
1.  **新增 §2 (2f) die 面积上界约束**：$A_{\text{die}}(B) = d(B)^2 \le A_{\max}$（$A_{\max}$ 随布局而定，粗上界 ≈ $A_{\text{interposer}}/N_{\text{dies}}$）；$\alpha_d > 0$ 时给出 $B$ 的上界。
2.  **布线 (2d) 明确为一级约束**：power/gnd 与信号走线共享 RDL，布线饱和常先于 bump 绑定——布线预算/布线面积共享纳入主优化模型（原 G4 裁决"限缩 claim"被作者推翻）。
3.  **面积上界 + 布线共享是"真正会绑定"的耦合要素**：二者约束下耦合 vs 分离决策可真正分出差异——重估 §4 E3B 等价性结论（作者指令，实验由 DataSteward 重跑，大实验走 `ssh walker` 远机）。
4.  §8 实现对表更新：布线/面积两行标"🚧 一级约束，CodeEngineer 接入中"。

**v5.20（2026-08-20，引用核验修正）**：
1.  **§10 MFIT 引用修正**："Zhang et al., ACM TACO 2025" → "*MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures*, ACM TODAES（DOI 10.1145/3765905；arXiv:2410.09188）"——作者/venue 经 web 核验 + LiteratureSearcher DBLP 交叉确认（作者表以其 `ccf-ref-verifier` 终稿为准）。作者表终稿：ccf-ref-verifier 三源核验（DBLP/CrossRef/arXiv），2026-08-20（§10 已由 "Pfromm et al." 补全为完整 9 位作者：Lukas Pfromm, Alish Kanani, Harsh Sharma, Parth Solanki, Eric Tervo, Jaehyun Park, Janardhan Rao Doppa, Partha Pratim Pande, Ümit Y. Ogras）。
2.  **代码 docstring 同步**：`src/physical/layout/thermal_network/builder/_analytic.py` 的 MFIT 引用同改。
3.  **Feng & Ma venue 修正**：Switch-Less Dragonfly on Wafers 为 **SC 2024**（DOI 10.1109/SC41406.2024.00102），非 USENIX ATC 2024——`notes/literature/LITERATURE_MAP.md` 同步。

**v5.19（2026-08-20，整体问题定位）**：
1.  **§5.3 改写**：明确"整体问题（含 $B$）**非凸**，但**无需启发式、存在可多项式时间求解的全局最优解**"——固定 $B$ 为 LP（可行性精确可判、多项式可解），外层二分搜索（`BmaxQuery`）取最大可行 $B$，二分 + LP 即得 $B^*$，总复杂度多项式。这是 insight 7 的形态（作者 2026-08-20 澄清，见 `notes/INSIGHT_READING.md`）。
2.  **单调性注意降级**为"内部验证，不上论文台面"；补入低 $B$ 恒可行论证（面积约束为松上界，可加无逻辑硅）。

**v5.18（2026-08-20，B 正名）**：
1.  **$B$ 正名**："无阻塞带宽" → "**有服务质量保证的额定出入口带宽**"（即 insight 2/3 的"额定带宽"；QoS 语义：端口负载不超过 $B$ 时无阻塞交换）。作者 2026-08-20 定案，解读见 `notes/INSIGHT_READING.md`。
2.  **措辞同步**：§0.1、§1 符号表、§7.2、§7.3 更新；"无阻塞"保留为 QoS 保证的语义描述（可重排非阻塞，RNB），**不再作为 $B$ 的命名**。

**v5.17（2026-08-20，并入 V4，确立唯一权威）**：
1.  **删除前置文档**：`MATH_MODEL_COMPLETE_V4.md` 已删除——本文档成为**全文唯一权威模型文档**，符号表自包含，不再依赖任何其他模型文档。
2.  **符号表吸收**：并入 $V_{dd}$、$I_{\text{bump}}$、$I_{\text{C4}}$、$p/\eta$、$p_{\text{C4}}/\eta_{\text{C4}}$、$T_{\text{amb}}$ 及链路族定义（$\mathcal{E}_{\text{on-die}}/\mathcal{E}_{\text{UCIe}}/\mathcal{E}_{\text{SerDes}}$）；原"链路集定义见 V4"改为内联。
3.  **确立 insight.md 为唯一上位意图**：头部明确本文档、代码、测试、论文与 `STYLE.md` 共同贯彻 `insight.md` 的 7 条 critical insight（字节级不变，口语化为其本来面貌）。
4.  **同步引用清理**：README、AGENTS.md、`tests/die_scaling/test11_die_scaling.md`、`docs/paper/Tex/Appendix.tex`、`prompt/01-code-engineer.md`、`STYLE.md` 中所有 V4 引用改为 V5 或删除。

**v5.16（2026-08-20，全面润色）**：
1.  **符号表增补与量纲修正**：
    *   补入 $B$、$\mathbf{L}^{*}$、$\mathbf{D}$、$\mathbf{f}$、$\mathcal{P}$、$K_{ij}$、$\mathbf{x}_{\text{D2D}}$、$d_0/\alpha_d$、$P_0/\beta_P$ 等符号
    *   $\mathbf{L}$ 单位改为"—"，明确为**扩展比向量（无量纲）**（insight 6：链路实际带宽 $= B\,L_e$）；修正原"Gbps"标法
    *   $\mathbf{P}_{\text{die}}^{\text{peak}}(B)$ 改为**线性** $P_0 + \beta_P B$（原误标二次）；$\mathbf{N}_{\text{die}}^{\text{total}}(B)$ 明确二次来源（$A_{\text{die}}(B) = d(B)^2$）
    *   $\mathcal{E}_{\text{I2I}}$ 修正为 $\subseteq \mathcal{E}_{\text{SerDes}}$（原误写为 UCIe/on-die）
2.  **§7 性能模型显式化**：§7.3 补均匀分流定义 $f_k(i,j) = D_{ij}/K_{ij}$（$f$ 非决策变量，代码已如此实现），补 $c_{ij}^{e}$ 系数表达式与 Birkhoff–von Neumann 顶点论证
3.  **§3 (3c) 聚合修正**：C4 预算经 $\mathbf{M}_{\text{I2I} \to \text{inter}}$ 聚合（link 级向量与 interposer 级向量不可直接相加）
4.  **新增 §2.8 die 缩放**（V4 §2.8 移入，代码注释沿用编号）：$d(B)$、$A_{\text{die}}(B)$、$P_{\text{peak}}(B)$、$N_{\text{total}}(B)$ 的定义与量纲
5.  **新增 §5.3 模型类别**：固定 $B$ 为纯 LP；$B^*$ 二分及缩放启用时的单调性前提
6.  **新增 §8 与实现的对应**：文档 § ↔ 代码模块映射与实现状态
7.  **§6 假设表重写**：修正"Interposer 内部热均匀"自相矛盾（A2），补 A4–A8（动态/静态分通道、无焦耳热源、温度上限分层、SI 靠规范内嵌、两段可同时满载）
8.  **§5.2 闭合性改为论证**：热约束链 → 功耗上界 → lane/负载上界（原为断言）
9.  **待定案与文献**：新增 §9 待定案（分割比、单调性验证等）、§10 依据与参考文献；修正待定案中 $\mathbf{G}_{\text{inter}}^{\text{amb}}$ 命名（原误写 $\mathbf{G}_{\text{die}}^{\text{amb}}$）
10. **find 列表清理**：§2 移除 $\mathbf{b}$（常数/共享变量非决策变量）、§3 find 只留自由变量；修正 §0.2 重复编号

**v5.15 修正日志**：
1.  **用块矩阵形式表示 die 和 interposer 两个温度场的耦合**：
    *   $\mathbf{G}_{\text{die-inter}}[\mathbf{T}_{\text{die}}; \mathbf{T}_{\text{inter}}] = [\mathbf{P}_{\text{die}}; \mathbf{0}] + \mathbf{b}_{\text{die-inter}}$
    *   引入 $\mathbf{G}_{\text{die} \to \text{inter}}$ 和 $\mathbf{G}_{\text{inter} \to \text{die}}$ 热耦合矩阵
    *   引入 $\mathbf{T}_{\text{inter}}$ 和 $\mathbf{b}_{\text{inter}}$ 新符号
2.  **恢复第 3 节 sub 热方程**：Substrate 的热源来自 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$
3.  **恢复第 4 节 C3、C4**：
    *   C3: $\mathbf{P}_{\text{inter}} = \mathbf{M}_{\text{die} \to \text{inter}}\mathbf{P}_{\text{die}}$（die → Interposer 功耗聚合）
    *   C4: $\mathbf{b}_{\text{inter}} = \mathbf{G}_{\text{inter}}^{\text{amb}}\mathbf{T}_{\text{sub}}$（sub → Interposer 温度反馈）

**v5.14 修正日志**：
1.  **用块矩阵形式统一热方程**（清晰展示 die 和 sub 温度场的耦合）：
    *   $\mathbf{G}[\mathbf{T}_{\text{die}}; \mathbf{T}_{\text{sub}}] = [\mathbf{P}_{\text{die}}; \mathbf{0}] + \mathbf{b}$
    *   耦合项（Substrate → die）和 $-\mathbf{M}_{\text{die} \to \text{inter}}$（die → Substrate）整合到块矩阵中
2.  **简化第 3 节**：移除 sub 热方程，保留 I2I 路由和 C4 约束
3.  **简化第 4 节**：移除 C3、C4（已整合到块矩阵），保留 C1、C2（资源耦合）

**v5.13 修正日志**：
1.  **引入 Interposer 物理层级**（明确 agg 是操作不是物理层级）：
    *   $\mathbf{P}_{\text{die}}^{\text{agg}}$ → $\mathbf{P}_{\text{inter}}$：明确是 Interposer 层级的总功耗
    *   $\mathbf{M}_{\text{die} \to \text{agg}}$ → $\mathbf{M}_{\text{die} \to \text{inter}}$：明确映射是 die → Interposer
2.  **更新物理图像**：将两层热网络更新为三层实体（die / Interposer / sub）
3.  **全面更新文档**：更新了 0.3、0.4、0.5、1、3、4、5 节中所有相关符号。

**v5.12 修正日志**：
1.  **统一映射矩阵命名**（所有映射矩阵统一用 M，明确映射方向）：
    *   $\mathbf{A}_{\text{die}}^{\text{agg}}$ → $\mathbf{M}_{\text{die} \to \text{agg}}$：明确是 die 功耗到聚合功耗的映射
    *   $\mathbf{A}$ → $\mathbf{M}_{\text{route} \to \text{D2D}}$：明确是路径流量到 D2D 链路的映射
2.  **全面更新文档**：更新了 1、2、4 节中所有相关符号。

**v5.11 修正日志**：
1.  **修正 M 矩阵命名**（明确映射方向）：
    *   $\mathbf{M}$ → $\mathbf{M}_{\text{D2D} \to \text{die}}$：明确是 D2D lane 到 die 侧的映射
    *   $\mathbf{M}_{\text{PHY}}$ → $\mathbf{M}_{\text{I2I} \to \text{die}}$：明确是 I2I SerDes lane 到 die 侧的映射
2.  **全面更新文档**：更新了 1、2、4 节中所有相关符号。

**v5.10 修正日志**：
1.  **修正 agg 符号命名**（明确聚合主体层级）：
    *   $\mathbf{P}_{\text{agg}}$ → $\mathbf{P}_{\text{die}}^{\text{agg}}$：明确是 die 层级的聚合功耗
    *   $\mathbf{A}_{\text{agg}}$ → $\mathbf{A}_{\text{die}}^{\text{agg}}$：明确是 die 层级的聚合矩阵
2.  **全面更新文档**：更新了 0.4、0.5、1、3、4、5 节中所有相关符号。

**v5.9 修正日志**：
1.  **修正 LaTeX 渲染问题**：
    *   修复了上标堆叠导致的渲染失败（如 $\mathbf{S}_{\text{D2D}}^{\text{bw}}^{-1}$ → $\left(\mathbf{S}_{\text{D2D}}^{\text{bw}}\right)^{-1}$）
    *   修复了第 94 行多余的 `"` 符号
2.  **严格执行命名约定**（下标表层级/主体，上标表属性/修饰符）：
    *   ${\mathbf{P}}^{\text{peak}}(B)$ → $\mathbf{P}_{\text{die}}^{\text{peak}}(B)$
    *   $\mathbf{N}^{\text{total}}_{\text{die}}(B)$ → $\mathbf{N}_{\text{die}}^{\text{total}}(B)$
    *   $\mathbf{N}^{\text{total}}_{\text{C4}}$ → $\mathbf{N}_{\text{C4}}^{\text{total}}$
3.  **符号表更新**：在符号表中添加了 $\mathbf{P}_{\text{die}}^{\text{peak}}(B)$、$\mathbf{N}_{\text{C4}}^{\text{total}}$、$\mathbf{N}_{\text{die}}^{\text{total}}(B)$ 等符号。
