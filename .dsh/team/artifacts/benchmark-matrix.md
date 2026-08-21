# 《insight 对标矩阵》（benchmark-matrix）

> **产出**：LiteratureSearcher（Phase 1 第一交付）
> **日期**：2026-08-20（本轮会话）
> **依据**：`notes/INSIGHT_READING.md`（作者意图解读，2026-08-20）分档口径；`.dsh/team/artifacts/contributions.md`（Phase 0 贡献声明 C1-C4，DomainExpert 已确认主承重排序：insight 6 > 7 > 4 > 2/3 > 1/5）；`insight.md`（字节级不变）。
> **校验**：所有引文经 DBLP（第一源）/ CrossRef / arXiv 逐条核验（`docs/paper/Biblio/ref.bib` 与 `notes/literature/LITERATURE_MAP.md` 中的错误已在下文标注）；未核验项标"待核实"。
> **分档口径**：完全没有 / 部分覆盖（注明哪里不足）/ 已有先例（**先例 = 验证**，进 Related Work §3.3 定位）。
> **结论口径**：成立 / 需限定 / 需弱化 / 有反例。对"需弱化/有反例"条目给出建议替换表述（供 Gate② 决策）。

---

## 0. 总览表

| # | insight | 邻近工作扫描 | 覆盖度分档 | 结论 | 一句话证据 |
|---|---|---|---|---|---|
| 1 | 筛选而非优化 | chiplet DSE（RapidChiplet/CHARIOT/FireLink/FPIA）均为"优化/探索"范式 | 部分覆盖（优化范式有先例，筛选定位无） | **成立**（需限定与 Pareto 优化区分） | RapidChiplet 原文以"DSE/cost function"为定位；无"可行性筛选+质量量化"范式 |
| 2 | B 作为解的质量量化指标 | BvN 交换机 guaranteed-rate、100% 吞吐（admissible traffic） | 部分覆盖（"可承诺带宽"有先例；"B\* 作 DSE 质量标尺并排序"无） | **成立**（需限定） | Chang et al. INFOCOM 2000 保证 admissible traffic 下吞吐；无 DSE 语境 B\* 排序先例 |
| 3 | B = f(要求, 约束) | 灵敏度/对偶（Bertsekas）、QoS 调度 | 完全没有（作为双旋钮框架） | **成立**（贡献点） | 未检索到"以 B 为标量、要求×约束双旋钮"的 DSE 框架 |
| 4 | 多因素耦合 vs 分离决策 | chiplet DSE 无 thermal；热单维工具独立；TickTock/Chen 部分联合 | 部分覆盖（分离确凿；TickTock/Chen 属"部分联合"需 xxx vs xxx） | **成立**（需限定） | RapidChiplet 原文把 thermal 外挂 HotSpot；CHARIOT/FireLink/FPIA 摘要无 thermal |
| 5 | B 是精调量化基石 | 快速粗筛+精调哲学（RapidChiplet 加速比）；分层 DSE | 完全没有（作为可辩护主张） | **成立**（定位性） | 无"按 B\* 排序逐点论证"先例；RapidChiplet"427x-137,682x speedup"支撑粗筛哲学 |
| 6 | 扩展比包络 = 拓扑不变量 | oblivious routing 负载因子/竞争比（Valiant/Räcke/Azar）；BvN 最坏流量=置换矩阵 | **已有先例 = 验证** | **成立**（先例进 RW §3.3） | Valiant STOC'81；Räcke FOCS'02/STOC'08；Azar et al. JCSS'04（LP 可多项式求最优 oblivious 路由） |
| 7 | 全局最优的可能（筛选哲学） | LP 求解网络设计（Azar/Ngo）；chiplet DSE 全用启发式 | 部分覆盖（LP 精确可解网络问题有先例；"二分+LP 全局最优 DSE 框架"无） | **成立**（需限定，不引复杂性战争） | Ngo arXiv:1204.3180 用 LP 对偶分析无阻塞网络；RapidChiplet/FireLink/CHARIOT 均为启发式 |

---

## 1. insight 1 —— 筛选而非优化

**主张**：DSE 目的 = 筛出满足"无阻塞 + 物理可行"等严苛基础条件的构型，不是找 Pareto 面。

**可能被质疑的点**：
- 现成 chiplet DSE 都以多目标优化/Pareto 为范式，"筛选"是否只是"优化"的一个特例（单目标可行性）？
- 若论文把"筛选"作为贡献卖点，须明确与 Pareto DSE 的差异，否则审稿人视为包装。

**邻近工作扫描**：
| 工作 | 范式 | 证据（原文/摘要引句） |
|---|---|---|
| RapidChiplet（Iff et al., CF 2025；arXiv:2311.06081） | ICI latency/throughput 预测工具链，定位为 "DSE / cost function for optimization algorithms or ML models" | 摘要："they are not fast enough to explore hundreds of thousands of design points **or to be used as a cost function for optimization algorithms or machine learning models**. To address this issue, we present RapidChiplet…" |
| CHARIOT（ACM TODAES 2026, DOI 10.1145/3815192） | 多目标 Bayesian 优化 + Pareto 前沿 | 摘要："A multi-objective Bayesian optimization-based DSE framework… The **Pareto frontiers** of competitive design choices enable selecting the most suitable option…" |
| FireLink（Li et al., JCRD 2025, 62(5):1108-1122, DOI 10.7544/issn1000-1239.202440082） | PPAC 评估 + ID3 决策树剪枝探索 | 摘要评估性能/功耗/面积/成本，ID3 提升 DSE 效率 |
| FPIA（Jiao et al., IEEE TCAS-I 2024, 71:4156-4168, DOI 10.1109/TCSI.2024.3419579） | 物理设计（placement+routing）启发式 | 摘要：latency/energy/routability，communication-aware |

**覆盖度**：**部分覆盖**——"优化/探索范式 DSE"已有大量先例；"以可行性筛选 + 质量量化（B\*）为输出的 DSE 定位"未检索到先例（说明：我们区别于 Pareto 探索的正是 insight 2 的 B\* 质量标尺与 insight 1 的筛选定位，二者绑定使用）。

**结论**：**成立**（需限定：§4.0 定位段须写明与 Pareto 优化 DSE 的差异——筛选输出"可行+质量量化"，而非 Pareto 解集；RapidChiplet 等作为"外层借用/对标基线"进 RW §3.2）。

---

## 2. insight 2 —— B 作为解的质量量化指标

**主张**：DSE 输出从二元"可行/不可行"提升为连续量化；同一组 DSE 设置、相同端口数下，可承诺 B\* 更高的设计点质量更优。

**可能被质疑的点**：
- 交换机领域早已有"额定带宽/line rate/交换容量"量化——B\* 是否只是重新包装？
- "可承诺吞吐"在 BvN 交换机（admissible traffic）与 guaranteed-rate 调度中已有形式化——先例如何区分？

**邻近工作扫描**：
| 工作 | 内容 | 与 B\* 的关系 |
|---|---|---|
| Chang, Chen, Huang, "Birkhoff-von Neumann input-buffered crossbar switches for guaranteed-rate services", INFOCOM 2000, pp.1614-1623（DOI 10.1109/INFCOM.2000.832560；ToN 2001 短文 DOI 10.1109/26.935153） | 用 BvN 分解做 crossbar 调度，**guaranteed-rate services**：在行/列和 ≤ 1 的 admissible traffic 下逐时隙保证吞吐 | "可承诺带宽"的学术先例：admissible 流量（相当于端口负载 ≤ B 的归一化）下无阻塞保证——与我们的 QoS 语义同构 |
| McKeown, Mekkittikul, Anantharam, Walrand, "Achieving 100% throughput in an input-queued switch", IEEE Trans. Commun. 47(8):1260-1267, 1999（DOI 10.1109/26.780463；INFOCOM 1996 版） | 在 admissible traffic 下达到 100% 吞吐 | "吞吐保证"先例 |
| McKeown, "The iSLIP scheduling algorithm for input-queued switches", IEEE/ACM ToN 7(2):188-201, 1999（DOI 10.1109/90.769767） | 调度算法 + 吞吐保证 | 同 |
| 交换机 datasheet（白名单外，非学术） | "switching capacity / line rate / non-blocking" | 行业"额定带宽"表述，无形式化保证 |

**覆盖度**：**部分覆盖**——"可承诺带宽 / QoS 保证"的形式化先例充分（BvN/guaranteed-rate/100% 吞吐）；**"把可承诺 B\* 用作 DSE 的解质量排序指标（同设置同端口数比较）"未检索到先例**（这是我们的量化贡献）。

**结论**：**成立**（需限定：§4.2.3 B\* 定义处明确引用 BvN/admissible-traffic 框架作为 QoS 语义来源，并把贡献表述为"DSE 语境下的质量标尺"，而非"首次提出可承诺带宽"）。

---

## 3. insight 3 —— B = f(要求, 约束)

**主张**：要求越严（QoS 保证 vs 仅出入口峰值）、约束越悲观（峰值工况 vs 额定功耗）→ 可承诺 B 越低；双旋钮单调框架。

**可能被质疑**：单调性直观；"要求×约束双旋钮"作为 DSE 设计框架是否有先例或只是常识？

**邻近工作扫描**：
- LP 对偶/灵敏度（影子价格）是标准工具（Bertsekas, *Nonlinear Programming*, Athena Scientific, 1997；已有 cite:bertsekas1997nonlinear）——灵敏度分析有先例。
- guaranteed-rate / QoS 调度文献（见 insight 2）把"要求"作为调度目标，但不以"要求×约束→可承诺带宽"的 DSE 旋钮框架呈现。
- 未检索到"以 B 为设计点标量、要求与约束为双旋钮"的 DSE 框架。

**覆盖度**：**完全没有**（作为双旋钮 DSE 框架；灵敏度/对偶工具层面有先例）。

**结论**：**成立**（贡献点。注意 INSIGHT_READING 纪律：二分/单调性不上论文台面；§2.3 用"旋钮直觉+例子"呈现，不写形式化单调性证明）。

---

## 4. insight 4 —— 多因素耦合（热、电、几何、性能）vs 前人分离决策

**主张**：前人多各因素分离决策；本文把热-电-几何-性能在单一模型联立。**（主承重 gap claim，C1 支撑）**

**可能被质疑的点（本矩阵最重要的核对项）**：
1. RapidChiplet 是否已联合 thermal+performance？（DOWNLOAD_LIST 曾写"覆盖 thermal"）
2. TickTock（ISCA 2025）已做 NoW 物理/逻辑拓扑协同设计——是否已算"联合"？
3. Chen（ISCA 2024）已分析 radix 受 internal/external bandwidth + power density 联合限制——是否已算"多因素联合"？
4. 热感知布局工具（ATPlace2.5D 等）是否已把热与性能联立？

**邻近工作扫描（含原文证据）**：

**A. chiplet DSE 工具——thermal 明确缺失或外挂（分离决策的直接证据）**
| 工具 | 覆盖维度 | 原文证据 |
|---|---|---|
| RapidChiplet（CF 2025） | latency/throughput 联合；power/area/cost 高估；**thermal 外挂** | 原文："There exist numerous DSE-tools for other metrics, such as the Orion 2.0 power and area model, the ChipletActuary cost model, **or the HotSpot thermal simulator**. RapidChiplet focuses on the latency and throughput of the ICI and **only provides very high-level power, area, and cost estimates**…"（Related Work 段，arXiv v2）——**工具自身把热划给外部 HotSpot** |
| CHARIOT（TODAES 2026, DOI 10.1145/3815192） | performance + energy 多目标 Bayesian 优化；**abstract 无 thermal** | 摘要："…performance and energy consumption… roofline model… multi-objective Bayesian optimization-based DSE…"（全文未提 thermal） |
| FireLink（JCRD 2025, 62(5)） | PPAC（性能/功耗/面积/成本）+ ID3 剪枝；**摘要无 thermal** | 官方摘要评估 PPAC 四维，无热 |
| FPIA（TCAS-I 2024） | latency/energy/routability（placement+routing）；**无 thermal** | 摘要："communication-aware… latency, energy, and routability" |

**B. 热单维工具独立存在（证明"热"是独立维度，但都与网络性能 DSE 分离）**
| 工具 | 维度 | 引用 |
|---|---|---|
| HotSpot | 芯片热建模（稳态/瞬态） | Huang, Ghosh, Velusamy, Sankaranarayanan, Skadron, Stan, "HotSpot: A Compact Thermal Modeling Methodology for Early-Stage VLSI Design", IEEE TVLSI 14(5):501-513, 2006（DOI 10.1109/TVLSI.2006.876103） |
| 3D-ICE | 3D IC 瞬态热建模 | Sridhar, Vincenzi, Ruggiero, Brunschwiler, Atienza, "3D-ICE: Fast compact transient thermal modeling for 3D ICs with inter-tier liquid cooling", **ICCAD 2010**, pp.463-470（DOI 10.1109/ICCAD.2010.5653749；注意是 ICCAD 非 DATE） |
| MFIT | 2.5D/3D 多芯粒热建模（M-矩阵线性热网络） | Pfromm, Kanani, Sharma, Solanki, Tervo, Park, Doppa, Pande, Ogras, "MFIT: Multi-FIdelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures", ACM TODAES（DOI 10.1145/3765905；arXiv:2410.09188；**非 Zhang/TACO**——见 §8 风险 2） |
| ATPlace2.5D（"Analytical Thermal-Aware Chiplet Placement Framework for Large-Scale 2.5D-IC"） | thermal-aware 布局（物理单维） | Semantic Scholar 收录（Wang, Li et al.）；**待核实**完整元数据 |
| TDPNavigator-Placer（"Thermal- and Wirelength-Aware Chiplet Placement in 2.5D Systems Through Multi-Agent Reinforcement Learning"） | thermal+wirelength MARL 布局 | IEEE（doc 11392651）；**待核实**完整元数据 |
| ChipletPart（"Scalable Cost-Aware Partitioning for 2.5D Systems"） | cost-aware 划分 | arXiv:2507.19819 |

**C. 部分联合的先例（必须承认，用 xxx vs xxx 措辞）**
| 工作 | 联合了什么 | 没做什么 |
|---|---|---|
| Chen, Pal, Kumar, "Waferscale Network Switches", ISCA 2024, pp.215-229（DOI 10.1109/ISCA59077.2024.00025） | radix 潜力的联合分析（area/internal bandwidth/external bandwidth/power density 共同限制 radix） | 非 DSE 工具；不做拓扑/路由/封装设计空间探索、不做 B\* 量化。摘要原文："…the actual radix of a waferscale network switch is **not area-limited**. Rather, it is limited by a combination of **internal bandwidth, external bandwidth, and power density**…" |
| Yang et al., "PD Constraint-aware Physical/Logical Topology Co-Design for Network on Wafer"（TickTock）, ISCA 2025, pp.49-64（DOI 10.1145/3695053.3731045） | PD（布线/物理设计）约束与逻辑拓扑的**协同设计** | 聚焦 PD 约束+逻辑拓扑；未做热-电-几何-性能单模型联立、无 B\* QoS 量化、无热模型 |
| Yu et al., "Cramming a Data Center into One Cabinet, a Co-Exploration of Computing and Hardware Architecture of Waferscale Chip", ISCA 2025, pp.631-645（DOI 10.1145/3695053.3731016） | 晶圆级芯片的计算+硬件架构协同探索 | 需精读确认其探索维度（**待核实**：是否含热/几何/性能单模型） |

**覆盖度**：**部分覆盖**。坐实结论：
- **"分离决策"成立**：RapidChiplet 自身把 thermal 外挂 HotSpot（工具内分离）；CHARIOT/FireLink/FPIA 均无 thermal；热单维工具（HotSpot/3D-ICE/MFIT/ATPlace2.5D/TDPNavigator）独立存在且不与网络性能 DSE 联立。
- **但"前人多分离决策"不能写成"前人完全没做联合"**：Chen ISCA'24（radix 的带宽+功率密度联合限制分析）与 TickTock ISCA'25（PD 约束+逻辑拓扑协同）是"部分联合"先例。

**结论**：**成立（需限定）**。建议表述（供 DomainExpert/Gate②）：
> "Chiplet 界已有成熟 DSE（RapidChiplet/FireLink/FPIA/CHARIOT），但多聚焦性能/成本/布局单维，热分析或外挂（RapidChiplet 引 HotSpot）或缺失；热感知工作（HotSpot/3D-ICE/MFIT/ATPlace2.5D）独立于网络性能 DSE；晶圆级网络工作（Chen ISCA'24、TickTock ISCA'25）做了特定维度的联合分析，但**没有**把热-电-几何-性能纳入单一模型并输出带 QoS 保证的 B\* 的 DSE。"

**替代（若需更强）：** 在 §5.4 实验（耦合 vs 分离）中用"分离流水线基线"：BookSim(性能)→HotSpot/MFIT(热)→FPIA/RapidChiplet(布局)分步判定 vs 单一 LP 联立——量化分离决策的失效点（见 gap-evidence-chain §2）。

---

## 5. insight 5 —— B 是后续精调的量化基石

**主张**：严格约束下的 B\* 排序给设计师提供论证顺序；"严格下接近目标 → 放宽后很可能可行"；决策权从 DSE 交给设计师。

**可能被质疑**：方法论主张难以直接对标；"先严格筛选后放宽精调"是否只是常见工程流程？

**邻近工作扫描**：
- 快速粗筛+精调哲学有先例：RapidChiplet 明确以"数百上千设计点快速评估 + 作为优化/ML 成本函数"为定位（摘要原文见 §1 表）——"快速先验 + 后续精调"被该社区接受。
- 分层 DSE（外层粗筛/内层精调）在体系结构 DSE 综述中有类似结构（S6 检索中；**待核实**代表综述）。
- 未检索到"按解质量（B\*）排序、逐点论证放宽可行性"的直接先例。

**覆盖度**：**完全没有**（作为可辩护主张；快速粗筛哲学有先例可借力）。

**结论**：**成立**（定位性主张，证据需求低；表述保持"很可能/先验搜集"限定，不承诺真实物理必然可行——INSIGHT_READING 纪律）。

---

## 6. insight 6 —— 扩展比包络 = 拓扑不变量（主承重，先例 = 验证）

**主张**：每条链路扩展比剥离额定带宽 B 后构成包络 L\*（链路实际带宽 = B·L_e），只依赖拓扑 + 路由 + 性能要求模型，与 B 及物理无关；逐链路子 LP（决策变量 D ∈ Birkhoff 多面体）解出，顶点 = 置换矩阵（Birkhoff–von Neumann 定理）。

**可能被质疑**：这不就是 oblivious routing 的负载因子/竞争比吗？先例是否已把"逐链路最小超配向量"做过了？

**邻近工作扫描（先例链，全部 DBLP/CrossRef 核验）**：
| 工作 | 概念 | 与本包络的关系 |
|---|---|---|
| Valiant & Brebner, "Universal Schemes for Parallel Communication", STOC 1981, pp.263-277（DOI 10.1145/800076.802479） | 随机化两阶段负载均衡；**负载因子** | 负载均衡先例：任意流量模式下链路负载可控——包络的"最坏流量下最小扩展比"思想源头 |
| Räcke, "Minimizing Congestion in General Networks", **FOCS 2002**, pp.43-52（DOI 10.1109/SFCS.2002.1181881） | oblivious routing 存在 O(log³ n) 拥塞竞争比 | "固定路由应对任意流量"的近似保证；注意 venue 是 **FOCS 2002 非 STOC**（角色卡/解读中 "Räcke 2002" 未写 venue，写稿勿标 STOC） |
| Räcke, "Optimal hierarchical decompositions for congestion minimization in networks", STOC 2008, pp.255-264（DOI 10.1145/1374376.1374415） | 竞争比改进至 O(log n) | 同 |
| Azar, Cohen, Fiat, Kaplan, Räcke, "Optimal oblivious routing in polynomial time", J. Comput. Syst. Sci. 68(2):383-394, 2004（DOI 10.1016/j.jcss.2004.04.010；会议版 STOC 2003） | **最优 oblivious 路由竞争比可多项式时间计算（LP）** | 与包络子 LP 最同构的先例：网络路由性能指标用 LP 精确求解 |
| Kim, Dally, Scott, Abts, "Technology-Driven, Highly-Scalable Dragonfly Topology", ISCA 2008, pp.77-88（DOI 10.1109/ISCA.2008.19） | Dragonfly + Valiant 模式（2-hop 负载均衡，最坏流量不劣化） | 拓扑-路由-最坏流量联合设计先例 |
| Benito, Fuentes, Vallejo, Beivide, "Analysis and Improvement of Valiant Routing in Low-Diameter Networks", HiPINEB@HPCA 2018, pp.1-8（DOI 10.1109/HIPINEB.2018.00009） | Valiant 路由在低直径网络的分析与改进 | 同 |
| Navaridas, Pascual, "Improving the performance of Dragonfly networks through restrictive Proxy routing strategies", Computer Networks, 2025, art.111334（DOI 10.1016/j.comnet.2025.111334） | Valiant/代理路由改进 | 同 |
| Chang, Chen, Huang, "Birkhoff-von Neumann input-buffered crossbar switches for guaranteed-rate services", INFOCOM 2000, pp.1614-1623（DOI 10.1109/INFCOM.2000.832560） | admissible traffic（行/列和 ≤ 1）下 BvN 调度保证；最坏流量 = 置换矩阵 | **"最坏情形流量模式 = Birkhoff 顶点 = 置换矩阵"的先例**（BvN 交换机文献），与 §7.3 顶点论证同构 |
| Birkhoff 1946 / von Neumann 1953 | Birkhoff–von Neumann 定理 | 数学基础（cite:birkhoff1946tres；von Neumann 1953 标准引用） |

**覆盖度**：**已有先例 = 验证**（按 INSIGHT_READING insight 6 澄清：包络概念有先例是好事，是验证与定位依据）。

**结论**：**成立**。Related Work §3.3 定位（建议表述）：
> "Per-link worst-case load analysis under oblivious routing has a rich lineage—Valiant & Brebner's randomized load balancing [STOC'81], Räcke's congestion-competitive oblivious routing [FOCS'02, STOC'08], and Azar et al.'s polynomial-time LP for optimal oblivious routing [JCSS'04]; Birkhoff–von Neumann switching shows worst-case admissible traffic collapses to permutation matrices [INFOCOM'00]. We build on these as **verification**: the expansion-ratio envelope is their per-link, topology-only specialization, and our contribution is integrating it as the performance–physics decoupling bridge in a wafer-scale switch DSE, with a per-link LP whose vertices are permutations and a full thermal/electrical/geometric constraint layer driven by B·L_e."

**区分点（防审稿人"重命名"质疑）**：Räcke 竞争比是**全局单标量**（最坏链路拥塞对最优的比）；我们的包络是**逐链路最小扩展比向量**，且用途是**与物理约束解耦的 DSE 桥梁**（性能模型独立预解 → 物理模型以 B·L\* 为输入），不是近似算法分析。Azar et al. 的 LP 是"求最优路由"，我们的子 LP 是"固定路由下求每条链路的扩展比下界"。

---

## 7. insight 7 —— 全局最优的可能（筛选哲学）

**主张（INSIGHT_READING 澄清版）**：不默认上启发式；要求不过分苛刻时大量约束是线性的/可证明存在全局最优；整体问题（含 B）非凸，但固定 B 可行性为 LP（精确可判、多项式可解），外层二分取最大可行 B\*，总复杂度多项式——**不需启发式**；外层离散层保持 NP-hard（借用成熟流程），**不引复杂性战争**。

**可能被质疑**：
- DSE（布局/拓扑）公认 NP-hard，LP 化是否回避了本质困难？
- "非凸但可多项式全局最优"的表述是否会被审稿人要求证明？

**邻近工作扫描**：
| 工作 | 内容 | 关系 |
|---|---|---|
| Azar et al., JCSS 2004（DOI 10.1016/j.jcss.2004.04.010） | 最优 oblivious 路由（网络性能问题）可多项式时间 LP 求解 | "网络性能问题不必然启发式"的最强先例 |
| Ngo, Rudra, Le, Nguyen, "Analyzing Nonblocking Switching Networks using Linear Programming (Duality)", arXiv:1204.3180（2012；会议版 NgoRLN10，researchr.org 收录，**INFOCOM 2010 版待核实**） | 用 LP（对偶）分析无阻塞交换网络 | "LP 用于交换网络可行性/非阻塞分析"的直接先例 |
| RapidChiplet / FireLink / CHARIOT / FPIA | 全部启发式（剪枝/ID3/Bayesian/布局启发式） | "现有 DSE 默认启发式"的现状证据（反衬"不需启发式"主张的差异点） |
| 布局/布线 NP-hard（FPIA 等物理设计） | 外层离散问题 | 我们承认外层 NP-hard，借用成熟流程——不与复杂性战争冲突 |

**覆盖度**：**部分覆盖**——"LP 精确可解网络/交换问题"有先例（Azar、Ngo）；"整体非凸但二分+LP 全局最优的 DSE 框架（含 B 决策量）"未检索到先例。

**结论**：**成立（需限定）**。纪律（INSIGHT_READING §一.7）：
- 论文措辞按筛选哲学："这个问题不需要启发式，存在可多项式时间求解的全局最优解"，**不强调"是 LP"**；
- 外层离散层（布局/布线/拓扑族）保持 NP-hard，借用成熟 chiplet DSE 流程；
- 若审稿人引用"布局 NP-hard"质疑，回应 = 内外层边界（内层给定构型可行性的复杂度主张与外层 NP-hard 不冲突）。

---

## 8. 三项优先验证的专项结论

### 8.1 ① insight 6 先例定位 —— ✅ 成立（见 §6）
Valiant & Brebner STOC'81 / Räcke FOCS'02、STOC'08 / Azar et al. JCSS'04 全部 DBLP 核验；**Räcke 2002 为 FOCS 非 STOC**（写作注意）。BvN 交换机（Chang INFOCOM'00）提供"最坏流量 = 置换矩阵"同构先例。

### 8.2 ② insight 4 "前人分离决策" —— ✅ 坐实（需限定，见 §4）
RapidChiplet 原文把 thermal 外挂 HotSpot（工具内分离的铁证）；CHARIOT/FireLink/FPIA 摘要均无 thermal；热单维工具独立。**但** Chen ISCA'24 与 TickTock ISCA'25 是"部分联合"先例——gap claim 用"xxx vs xxx"限定后可辩护。

### 8.3 ③ "额定带宽 QoS 保证 / 无阻塞"表述 —— 术语映射清楚（见 §2）
- 学术先例：BvN 交换机 admissible traffic（行/列和 ≤ 1）+ guaranteed-rate services（Chang INFOCOM'00 / ToN'01）；100% 吞吐（McKeown ToN'99）；iSLIP（ToN'99）。
- 无阻塞理论源头：Clos, "A Study of Non-Blocking Switching Networks", Bell Syst. Tech. J. 32(2):406-424, 1953（DOI 10.1002/j.1538-7305.1953.tb01433.x）；Benes, *Mathematical Theory of Connecting Networks and Telephone Traffic*, Academic Press, 1965（书，标准引用）。
- 我们表述"端口负载 ≤ B 时无阻塞（可重排非阻塞 RNB）"与 BvN/admissible-traffic 框架语义一致；B 正名"有服务质量保证的额定出入口带宽"（V5 v5.18 定案）与 guaranteed-rate 语义对齐。**写作时在 §4.2.3 引用 Chang INFOCOM'00 + McKeown ToN'99 作为 QoS 语义来源即可。**

---

## 9. 风险清单（Gate② / 用户决策点，按严重度排序）

1. **【高】insight 4 的"分离决策"必须限定**：TickTock（ISCA 2025，PD 约束感知物理/逻辑拓扑协同设计）与 Chen（ISCA 2024，radix 受带宽+功率密度联合限制）是"部分联合"先例。若 contribution C1 写"前人多分离决策"而不加限定，审稿人必抓。建议表述见 §4 结论段（xxx vs xxx 框架）。**需 DomainExpert 定夺 C1 措辞。**
2. **【高】MFIT 引用错误**：V5 §10 与 `docs/paper/Biblio/ref.bib` 均写 "Zhang et al., ACM TACO 2025"；真实文献为 **Pfromm et al., "MFIT: Multi-FIdelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures", ACM TODAES**（DOI 10.1145/3765905，arXiv:2410.09188；TODAES 2025/26, v31, pp.4:1-4:27）。V5 为唯一权威文档，我不改——**需 DomainExpert 确认后修正 V5 §10 引用**（bib 我可直接修正）。
3. **【中】Feng & Ma 的 venue 错误**：LITERATURE_MAP 与 ref.bib 标 "USENIX ATC 2024"；DBLP 实为 **SC 2024**（"Switch-Less Dragonfly on Wafers: A Scalable Interconnection Architecture based on Wafer-Scale Integration", DOI 10.1109/SC41406.2024.00102；arXiv:2407.10290）。相关工作中稿已按 SC 2024 写。
4. 【低】Räcke 2002 是 **FOCS 2002**（非 STOC）——写作勿标错。
5. 【低】3D-ICE 是 **ICCAD 2010**（非 DATE 2010）；HotSpot 规范引用是 **IEEE TVLSI 2006**（Huang et al.，非 TCAD/ISCA'03 版）。

---

## 10. 校验说明与"待核实"清单

**已核验（DBLP 第一源 / CrossRef / arXiv）**：Chen ISCA'24、Feng&Ma SC'24、Wan TVLSI'25、Yang TickTock ISCA'25、Yu ISCA'25、Dojo（HC34 + IEEE Micro'23）、Sean Lie HC35、Kim ISCA'08、Valiant & Brebner STOC'81、Räcke FOCS'02 / STOC'08、Azar et al. JCSS'04、Birkhoff 1946、Clos 1953、iSLIP ToN'99、McKeown ToN'99、Chang INFOCOM'00/ToN'01、Ngo arXiv:1204.3180、RapidChiplet（arXiv:2311.06081 + CF'25 DOI 10.1145/3719276.3725170）、CHARIOT（DOI 10.1145/3815192）、FireLink（JCRD DOI 10.7544/issn1000-1239.202440082）、FPIA TCAS-I'24、MFIT（DOI 10.1145/3765905）、HotSpot TVLSI'06、3D-ICE ICCAD'10、BookSim ISPASS'13、DSENT NoCS'12、Benito HiPINEB'18、Navaridas ComNet'25。

**待核实**：
- Ngo et al. 是否确有 INFOCOM 2010 会议版（researchr.org 记 NgoRLN10；arXiv 为 2012 全文版）——bib 暂标 arXiv 版，会议版待确认。
- ATPlace2.5D / TDPNavigator-Placer 完整元数据（作者/venue 完整列表）——供 insight 4 佐证引用，非主引。
- Yu et al. ISCA'25（Cramming a Data Center）的探索维度细节（是否含热/几何单模型）。
- OIF-CEI 规范号（ref.bib 现写 "OIF-CEI-05.1"，DOWNLOAD_LIST 写 OIF-CEI-112G/224G——需确认规范版本号）。
- UCIe 2.0 功耗数字（0.25-0.6 pJ/bit）与 μbump pitch（36-55μm）的规范原文页码——标准文档非公开全文，标注引用 UCIe 2.0 Specification (2024)。
