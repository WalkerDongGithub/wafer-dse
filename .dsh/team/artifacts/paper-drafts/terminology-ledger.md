# Terminology Ledger（Phase 3 写作术语账本）

> WritingPolisher 固化，2026-08-21。权威来源：V5（经书，唯一权威模型文档）→ DomainExpert 定案（q-faeb99a1，英文规范形式）→ paper.bib（引文键）。经书/释经拆分（2026-08-21）：模型性质见 MODEL_PROPERTIES.md、实现对表/参考文献见 IMPLEMENTATION_MAP.md、版本历史见 V5_CHANGELOG.md。
> 用途：Phase 3 全部章节（§4 先行，后续 Intro/RW/Eval 同此账本）统一用词，禁止变体混用。
> 注意：DomainExpert 定案 "two-level DSE"；**标题已统一 Two-Level**（title-candidates.md 2026-08-21 更新，T1/候选 1/候选 3 均改）——标题/正文无冲突。
> **作者 round 21+ 指令 B 风格红线（长期，2026-08-21 入总纲）**：① 朴素优先，优雅 > 高端、容易 > 困难；② 清晰矩阵表示 > 满篇鬼画符（V5 §2 标杆）；③ 灵敏度几个符号能说清就不堆砌；④ 文档越简洁越好，不做作者看不懂的东西；⑤ 术语克制——无此术语无法简洁解释清 → 用；只为显得做得好 → 重做。本账本只锁定"必须"的术语，避免为显专业而造词。

| 中文（V5/INSIGHT_READING） | Canonical English（定案） | 首次使用展开 | 禁止/避免 | 备注 |
|---|---|---|---|---|
| 两层 DSE | **two-level DSE** | — | two-layer / two-tier 混用 | DomainExpert 定案全文统一 two-level |
| 外层离散枚举层 | **outer discrete enumeration layer** | 外层枚举拓扑族 × 布局 × 封装工艺 × 互联标准 | — | 复用成熟 chiplet DSE 流程 |
| 内层可行性模型 | **inner feasibility model for a given configuration** | — | 内层命名不带 "LP" 字样 | 按 insight 纪律 |
| 额定出入口带宽（有 QoS 保证） | **rated ingress/egress bandwidth $B$ with a QoS guarantee**（首用全称） | — | "QoS-guaranteed rated bandwidth" 不作主简称（可作定语短语） | 后续简称 **rated bandwidth $B$**；解出后 **optimal rated bandwidth $B^*$** |
| 扩展比包络 | **expansion-ratio envelope** | 首用可括注 "i.e., the minimum per-link expansion ratio a topology must provision for a given performance requirement" | — | — |
| 扩展比 = 拓扑不变量 | **the expansion-ratio envelope is a topological invariant—it depends only on the topology, routing, and performance requirement, independent of $B$ and of physical parameters** | — | — | insight 6 标准表述 |
| 性能-物理解耦桥梁 | **performance–physics decoupling bridge** | — | — | — |
| 跨层耦合约束 | **cross-layer coupling constraints $\mathrm{C}_1$–$\mathrm{C}_4$** | 首用 "coupling constraints" 再列 C1-C4 | — | C1 μbump 跨层分配 / C2 C4 电源数 / C3 功耗聚合 / C4 温度反馈 |
| 筛选而非优化 | **screening, not optimizing** | 定语形式 "screening-oriented" | — | insight 1 |
| 方法主张（insight 7 定稿句式） | **the overall problem is non-convex, yet admits a polynomial-time global optimum without heuristics** | — | 不写 "is an LP" | 二分/单调性不上台面 |
| 无阻塞（QoS 语义） | **non-blocking**（仅 QoS 语义；可重排非阻塞 **rearrangeably non-blocking (RNB)**） | 端口负载 ≤ $B$ 时无阻塞交换 | 不作为 $B$ 的命名 | — |
| 静态 oblivious Valiant 路由 | **static oblivious routing with uniform splitting** | — | — | 首用可引 Valiant & Brebner |
| 双随机流量矩阵 | **doubly stochastic traffic matrix $\mathbf{D}$**（Birkhoff 多面体） | — | — | 顶点 = 置换矩阵（Birkhoff–von Neumann） |
| 三层物理实体 | **three-layer physical hierarchy**: die / interposer / substrate | — | — | die 级 / Interposer 级 / Substrate 级 |
| die-to-die / inter-interposer 链路 | **D2D / I2I links** | die-to-die (D2D), inter-interposer (I2I) | — | D2D 走 UCIe/on-die；I2I 走 SerDes 经 C4 |
| 布线一级约束 | **interposer wiring**（first-class constraint） | power/ground 与信号走线共享 RDL | — | 布线饱和常先于 bump 绑定 |
| die 面积上界 | **die-area upper bound** $A_{\text{die}}(B) = (d_0+\alpha_d B)^2 \le A_{\max}$ | — | — | $\alpha_d>0$ 时直接给 $B$ 上界 |
| 热方程 | $\mathbf{G}\mathbf{T} = \mathbf{P} + \mathbf{b}$ | 引 \cite{mfit2025}（MFIT；venue 以 paper.bib 为准 = ACM TODAES） | 不展开传热学物理 | G 为对角占优 M-矩阵 |
| 二分（内部叙事） | **outer search** / **a logarithmic number of outer iterations** | — | 主文本不写 "bisection" | 附录 B 才形式化 |
| 研究对象（round 21+ 指令【3】） | **the design of a single interposer** | 立项语境仍是 wafer DSE；正文/实验对象 = 一个 interposer 的设计（其 die、互连、与 substrate 的边界） | 不写成 whole-wafer DSE | 定位聚焦，全文一致 |
| 电源/地走线 | **power/ground (P/G) routing** | — | — | 与信号走线共享 RDL 容量 |
| 重布线层容量 | **redistribution-layer (RDL) capacity** | — | — | 布线饱和先于 bump 绑定 |
| 布线饱和 | **wiring saturation** | — | — | — |
| 标准耦合案例（round 21+ 指令【1】） | **power–cooling–wiring/performance triad** | power 需求过大 → 顶满 RDL → (a) 提高散热（增强 P/G 承载）或 (b) 降带宽（减小 power 需求） | — | 反驳"分离决策各判各的能解 DSE"的经典靶子；**正式英文措辞已定稿**（DomainExpert 2026-08-21，见 s4-model.md §4.2.2） |
| 解锁率（灵敏度，DomainExpert 认可） | **unlocking rate** | 每 1% 旋钮变化释放的带宽弹性：ΔB\*/B\* per 1% | — | 灵敏度分析输出核心；见 sensitivity-design.md |
| 绑定约束族（灵敏度，DomainExpert 认可） | **binding constraint family**（= 活跃约束集 active constraint set） | B\* 处顶住的约束集合（BmaxQuery 诊断已有） | — | 与 unlocking rate 排名并列展示 |
| 影子价格（灵敏度，DomainExpert 认可） | **shadow price** | 约束 rhs 单位放松对最优值的边际价值 | — | **= KKT 乘子在固定 B 的 LP 特例下的名字**（作者 round 21+ 指令 A：整体非线性，一般框架是 KKT/包络定理；LP 情形须说明成立条件与局限） |
| KKT 乘子 / 包络定理（round 21+ 指令 A） | **KKT multipliers** / **envelope theorem** | KKT 点 $(x^*,\lambda^*,\mu^*)$ 处 $dV/d\theta = \partial L/\partial\theta = \lambda^\top(\partial g/\partial\theta) + \mu^\top(\partial h/\partial\theta)$ | 不默认固定 B 的 LP 框架全局成立 | 模型整体非线性，灵敏度用此框架；LP 为特例 |

## 引文键（paper.bib 核验版，写作使用）

- 晶圆级交换机背景：\cite{chen2024waferscale, feng2024switchless_sc, wan2025architectural, yang2025ticktock, yu2025cramming, dojo2022hc, dojo2023micro, lie2023hcs}
- 外层 chiplet DSE：\cite{rapidchiplet2025, firelink2025, fpia2024, chariot2026}
- 包络先例（验证）：\cite{valiant1981universal, racke2002focs, racke2008stoc, azar2004jcss}
- BvN/交换理论：\cite{birkhoff1946tres, vonneumann1953, chang2000infocom, chang2001tcom, mckeown1999tcom, clos1953, benes1965}
- 热：\cite{mfit2025}（**Pfromm et al., ACM TODAES**——V5_CHANGELOG v5.20 修正，参考文献见 IMPLEMENTATION_MAP.md；角色卡旧文 "Zhang et al., ACM TACO 2025" 已过期，勿用）
- 拓扑：\cite{kim2008dragonfly, benito2018valiant, navaridas2025proxy}
- 求解/实现：\cite{diamond2016cvxpy, booksim2013, noxim2017, dsent2012}
- 数学基础：\cite{berman1994nonnegative, bertsekas1997nonlinear, dally2004principles}
- 标准：\cite{ucie2.0-2024, oif-cei}

## 版本记录

- 2026-08-21（v0.1）：初版固化（§4 起草前）；英文规范形式经 DomainExpert q-faeb99a1 逐项确认。
- 2026-08-21（v0.2）：round 21+ 指令对齐——新增研究对象（the design of a single interposer）、标准耦合案例（power–cooling–wiring/performance triad）及 RDL/P-G routing/wiring saturation 术语；实验规模基调（小实验优先）不影响措辞但约束 claim 尺度。
- 2026-08-21（v0.3）：标题统一 Two-Level（title-candidates.md 已更新，冲突解除）；耦合案例正式英文措辞定稿（DomainExpert，§4.2.2）；新增灵敏度术语候选（unlocking rate / binding constraint family / shadow price，待 DomainExpert 认可后固化）。
- 2026-08-21（v0.4）：灵敏度三术语获 DomainExpert 认可，**已固化入主表**（unlocking rate / binding constraint family / shadow price）；耦合案例措辞闭环。
- 2026-08-21（v0.5）：**作者 round 21+ 指令 A/B**——新增 KKT multipliers / envelope theorem（灵敏度一般框架）；shadow price 标注"LP 特例下的 KKT 乘子名"（含成立条件）；顶部写入 B 风格红线（朴素优先、术语克制）。
- 2026-08-21（v0.6）：**V5 经书/释经拆分对齐**——权威来源改引 V5（经书）；模型性质/实现对表/版本历史分别改引 MODEL_PROPERTIES.md / IMPLEMENTATION_MAP.md / V5_CHANGELOG.md。
