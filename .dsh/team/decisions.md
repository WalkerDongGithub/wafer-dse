# 团队决策日志（master 维护）

> 记录 master 代表用户/团队的决策与待决项；**所有条目可被用户随时推翻**。
> 用户主会话 = master = 唯一决策通道（session-13e74b58-8ae9-4cd0-8af2-07a4ab4f6f2f）。

## Gate① 立项决策（2026-08-20，暂定默认，可推翻）

| # | 决策点 | 暂定结论 | 状态 |
|---|---|---|---|
| 1 | 目标会议 | **ISCA**（用户已定） | ✅ 定案 |
| 2 | 贡献声明 | 默认 **4 条**（C1-C4，见 `contributions.md`）；合并 3 条为备选 | 暂定，Gate② 前可改 |
| 3 | 标题 | 候选见 `title-candidates.md`：**候选 1**《Bandwidth Envelopes as Topological Invariants: Two-Layer DSE for Wafer-Scale Network Switches》（DomainExpert 推荐，主打 insight 6）/ 候选 2《Rated Bandwidth as a Design Metric...》（insight 2/3）/ 候选 3《Two-Layer DSE...without Heuristics》（insight 7，T1 精简替代）。暂定 T1 路线，待用户拍板 | 暂定，可改 |
| 4 | C1"首个/填补空缺"措辞 | 去掉"首个"；"填补空缺"等 LiteratureSearcher 对标矩阵（Gate②）回来定稿 | 待 Gate② |
| 5 | 放行 Phase 2 | ✅ 已放行：EvalDesigner 出实验设计文档（草稿，随 Gate② 调整）；DataSteward 数据盘点 | 已执行 |

## 待决项

- Gate① #2/#3：用户最终确认（无异议即按暂定走；用户可随时推翻）
- Gate②：对标矩阵回来后逐条审结论分档，被削弱的 insight 提前降级/限定（决策单呈用户）
- 用户终裁（Phase 5 投稿决定）

## Gate③ 实验缺口裁决（2026-08-20，暂定，可推翻）

| 缺口 | 暂定裁决 | 执行 |
|---|---|---|
| G1 | 无缺口，直接执行 | DataSteward（已接令：E1/E3A/E5/E6/EC） |
| G2 | **补**（CodeEngineer 双旋钮场景参数化），待 DataSteward 首批实验后资源空闲时建；E4 先用场景近似 | 待建 CodeEngineer |
| G3 | 分离决策基线 exp 层实现（顺序解多次 LP，非新 query） | DataSteward |
| G4 | **限缩论文 claim**（§4.2.2 描述完整 V5 规范，实验覆盖实现子集 C1+热+包络；C2-C4/sub 热=模型规范与未来工作） | DomainExpert 措辞任务 |
| G5 | 不阻塞（V5 §9 待定案推进） | — |
| G6 | 定案不做（可选附录；环境无 MILP 求解器） | — |

## 引用核验修正（2026-08-20，已 web 确认 + LiteratureSearcher DBLP 交叉）

- MFIT：ACM TACO 2025（Zhang et al.）→ **Pfromm et al., ACM TODAES**（DOI 10.1145/3765905；arXiv:2410.09188）——V5 §10（v5.20）+ 代码 docstring 已同步
- Feng & Ma Switch-Less Dragonfly：USENIX ATC 2024 → **SC 2024**（DOI 10.1109/SC41406.2024.00102）——LITERATURE_MAP 已同步

## Gate② 对标矩阵裁决（2026-08-20，LiteratureSearcher benchmark-matrix.md 已过审）

| insight | 覆盖度 | 结论 | 处置 |
|---|---|---|---|
| 1 筛选而非优化 | 部分覆盖 | 成立（需限定） | §4.0 写与 Pareto DSE 差异（筛选+质量量化，非 Pareto 解集） |
| 2 B 量化指标 | 部分覆盖（BvN/guaranteed-rate 先例） | 成立（需限定） | §4.2.3 引 Chang INFOCOM'00 + McKeown ToN'99；贡献表述"DSE 语境质量标尺"，不写"首次" |
| 3 B=f(要求,约束) | 完全没有 | 成立（贡献点） | 双旋钮框架；二分/单调性不上台面 |
| 4 多因素耦合 | 部分覆盖（TickTock ISCA'25 / Chen ISCA'24 部分联合） | 成立（需限定） | **C1 措辞按矩阵 §4 建议限缩**（xxx vs xxx），禁全称"分离决策" |
| 5 B 精调基石 | 完全没有 | 成立（定位性） | 保持"很可能/先验搜集"限定 |
| 6 扩展比包络 | **已有先例=验证** | 成立 | §3.3 定位段采用矩阵 §6 英文表述 + 区分点（逐链路向量 vs Räcke 全局竞争比） |
| 7 全局最优 | 部分覆盖（LP 网络问题有先例；二分+LP DSE 框架无） | 成立（需限定） | 筛选哲学措辞；外层 NP-hard 边界声明 |

**写作纪律同步**：Räcke 2002 = FOCS 非 STOC；3D-ICE = ICCAD 2010；HotSpot = IEEE TVLSI 2006（Huang et al.）。
**引用库**：paper.bib 42 条（31 核验通过 / 9 待核实 / 2 数学经典）；bib-verification-report.md 逐条在档。

## Gate③ G3 实验发现与 insight 4 主张重构（2026-08-20，重要）

**发现（DataSteward G3 数据 + EvalDesigner 分析）**：当前实现子集（C1+热+包络）下，分离决策基线 vs 联合模型**数学等价**——B\*_joint = min(B\*_bump, B\*_therm) 解析成立（L 钉包络 + 约束对 B 线性 + α_d=β_P=0 几何恒松），rel_diff 全 0（11 拓扑）。E3B 原判据"分歧≥1"不可满足；真耦合要素（C2/C4/布线共享、ρ、L 自由分流）均属 G4/G5 未来工作。

**裁决（DomainExpert 认可，EvalDesigner 落盘）**：
- E3B 改为"**等价性实证 + 边界刻画**"（写进正文——insight 4 诚实边界）
- claim 限缩：**不声称"分离产生不同数字"**；承重转为"单一模型统一求解（一致性+全局最优）+ 耦合收益条件的精确边界刻画"
- G4/ρ 补为未来工作（§6.3）；§5.4 双线叙事；解析推导可选入附录
- 与 G4 限缩、C1 措辞自洽；benchmark-matrix 结论无需改

## ⛔ 作者推翻 G4 裁决：布线/面积一级化（2026-08-20，最高优先级）

**作者技术反馈**（总 agent 传达，推翻上述"G4/ρ 推 §6.3 未来工作"默认裁决）：
1. 仅 bump/功耗子集的等价性说服力不足——那不是约束最先顶到的地方。
2. **布线/路由饱和约束**（power/gnd+信号走线共享 RDL，布线饱和先于 bump 绑定）与**芯粒面积上界约束**（A_die ≤ A_max，粗上界 ≈ interposer 面积 ÷ 芯粒数）**拉回主模型主线，不是未来工作**。
3. 在此类真绑定约束下重跑耦合联合 vs 分离决策，重估 G3 等价性（预期真正分歧）。
4. **资源策略**：大规模实验/网格搜索/密集求解一律 `ssh walker` 远机（chenmz，257GB）跑；小规模本机。
5. 更新模型约束集、E3B 实验设计与 claim 重构后回报关键结论。

**已执行**：
- V5 **v5.21**：新增 §2 (2f) A_die ≤ A_max；布线 (2d) 明确一级约束；§8 实现对表更新
- **CodeEngineer 已创建**（session-team-code-engineer-ra74vh）：接入 WiringGrid + 面积上界到 build_scenario（测试先行）
- EvalDesigner：E3B 重设计（布线+面积下恢复"分歧≥1"判据）
- DomainExpert：insight 4 claim 重构 + §6.3 去留（G4/ρ 回主线）
- DataSteward：E3B v2 重跑准备（大规模走 ssh walker）
- **ssh walker 已验证可用**（远机 chenmz，257GB 总 / 248GB 可用）

**可选项（用户若想要更强的耦合演示）**：补实现 C2/C4/wiring + 分割比 ρ（CodeEngineer 大工作量），让耦合分歧真实出现——默认**不补**（限缩 claim，科学诚实）。
**待核实（不阻塞）**：Ngo INFOCOM'10 会议版存在性；ATPlace2.5D/TDPNavigator 元数据；Yu ISCA'25 维度；OIF-CEI 版本号。

## 🎯 作者 round 21+ 指令（2026-08-21，全队对齐，已广播 + 耦合案例入 INSIGHT_READING §4）

| # | 指令 | 分派 |
|---|---|---|
| 【0】 | **不再跑大实验**：想法验证/迭代期，小实验验证方向；大规模留到确需量化且后期 | DataSteward（明令）+ 全员 |
| 【1】 | **标准耦合案例**（作者核心洞察，全队吃透）：Power/GND 走线占用 RDL 容量 → 顶满布线容量 → (a) 提高散热 或 (b) 降性能（减带宽）换布线布得下——"功耗—散热—布线/性能"三者互相牵制；定位 = 反驳"分离决策能解 DSE"的经典靶子（授权可 diss） | 已写入 INSIGHT_READING §4；DomainExpert 纳入论证 |
| 【2】 | 实验围绕"展现该耦合的影响"：散热增强释放多少带宽 / 降性能缓解多少布线饱和 | EvalDesigner（实验核心轴）+ DomainExpert（挖掘） |
| 【3】 | 定位澄清：重心 = **一个 interposer 的设计**（术语与实验对象聚焦） | 全员 |
| 【4】 | **布局算法调研（新工作项）**：不自研（经典 NP-hard），调研组补齐 interposer/chiplet 布局算法已有模型/结论（调研+引用） | LiteratureSearcher（流水线 Phase 3 支撑） |

## ✅ Phase 2 完成：E3B v2 分歧实证通过（2026-08-21，作者指令闭环）

**作者指令核心问题已回答：耦合在布线/面积下成立。**
- **E3B v2 C3' 终判通过**（fixed_paths 重跑，git f680fc5）：**10/72 分歧**（rel GM 0.264 / max 0.80：Mesh(3) 0.80、KaryNCube(2,3) 0.087）；**机制 = 路径多样性**（固定首路径拥塞 1075 vs 联合绕行 5363）；C4' 39 行 route/area 真绑定；单调性抽查 PASS。
- **insight 4 双阶段主张成立，§5.4 定稿**：v1 等价性边界（无布线/面积子集，附录素材）+ v2 分歧实证（正文）+ C4' 真绑定识别；原"限缩预案"未触发。
- **Phase 2 七实验数据全齐**：E1 排序（图 4）/ E2 灵敏度（图 6）/ E3 v1+v2（图 5）/ E5 包络不变性（图 3 首选）/ E6 规模 / EC 内部单调性（18 组合零反转）。experiment-design.md 定稿（~330 行），审计表全回填。
- **代码落地**：459a6ed（布线/面积）+ 5008ed0（双旋钮）+ f680fc5（fixed_paths）；run_all 19/19。

**Phase 3 写作激活**（2026-08-21）：WritingPolisher 起草 §4 方法章 + Abstract；DomainExpert 内容审阅/整合/图意图；FigureArtist 概念图 1-2（数据图 3-6 源数据齐，按用户"图优先级靠后"缓排）；LiteratureSearcher 引文支援待命。

## 🎯 作者补充指令：灵敏度分析 = 论文杀手锏（2026-08-21，全队深想中）

**要求（a/b/c 三满足）**：数学严谨（明确定义/可计算/有界或单调可证）+ 工程震撼（别的 DSE 做不到）+ 目标形态 = "改进走线，一切就都解决了"（定位瓶颈旋钮，改它全局解锁，而非泛泛报导数）。

**master 技术种子（供讨论，LP 对偶/影子价格机制）**：
- **机制**：在 B\*（二分求出的最大可行 B）处解固定 B 的可行性 LP，读**绑定约束的影子价格（dual）**——λ_i = 第 i 条约束 rhs 的单位边际可行性价值；一阶近似 ΔB\* ≈ λ_i·(∂rhs_i/∂θ)·Δθ。对每个物理旋钮 θ（布线容量 C、散热 R_vert、每 lane 功耗 p、面积 A_max）算 λ_i·∂rhs_i/∂θ，**最大者 = 解锁旋钮**。
- **严谨性**：固定 B 为 LP（dual 精确可解，Bertsekas 影子价格/insight 7 对偶）；可行性对 B 单调（低 B 恒可行）⇒ B\* 对任何约束放松单调不减（可证）；一阶近似在非退化绑定下局部精确，小扰动验证（小实验）。
- **震撼点**：别的 DSE 输出"设计点/Pareto 集"，我们输出"**B\* + 哪个约束族绑定 + 每个旋钮放松 1 单位能解锁多少 B\***"——量化瓶颈诊断（insight 5 量化基石的具体化）。
- **与耦合案例结合**：功耗-散热-布线三向牵制下，"改走线"可能因 power/gnd 走线随功耗缩放而收益有限 → 真正的解锁旋钮可能是"降功耗/提散热"——灵敏度排名揭示非线性真相，叙事 = 分析（耦合）→ 定位瓶颈（绑定族+影子价格排序）→ 可行动结论（改 X 收益最大，附数字）。
- **实现**：cvxpy（CLARABEL）dual_value 可读；小规模验证即可（验证阶段策略）。

**深想任务**：DomainExpert 主持整合（方法论 + 对象/变量选择 + 数学形式 + 工程可行动翻译 + 论文叙事），EvalDesigner（数学形式/实验设计/判据）、DataSteward（duals 数据侧可行性 + 小规模验证）、WritingPolisher（叙事形态）。产出落盘 `.dsh/team/artifacts/sensitivity-design.md`。

## Phase 3 写作进度（2026-08-21）

- **WritingPolisher 交付**：`paper-drafts/terminology-ledger.md`（术语账本：two-level DSE / rated bandwidth $B$ with a QoS guarantee / expansion-ratio envelope / inner feasibility model for a given configuration / cross-layer coupling constraints C1–C4 / screening not optimizing / insight 7 定稿句式）+ `s4-model.md`（§4 方法章草稿，insight 纪律标注）+ `abstract.md`（~200 词 + Claim–Evidence Map）。
- **标题对齐**：正文定案 "two-level DSE"，title-candidates.md 三候选 "Two-Layer" → **"Two-Level"**（DomainExpert 更新中，消除标题/正文不一致）。
- **复核链**：§4 → DomainExpert 技术复核 → 回 WritingPolisher；图 1 意图规格（DomainExpert）→ FigureArtist 绘制；Abstract 数字待 §5 表格定稿后终校（ccf-polishing）。
- **引文**：MFIT 按核验版 Pfromm et al., ACM TODAES（\cite{mfit2025}）；正文不点名 venue。

## 灵敏度杀手锏方法论进展（2026-08-21）

- `sensitivity-design.md`（DomainExpert v0.2 整合中）：松弛 LP 影子价格方案 + 旋钮表 + 系数旋钮完整式 s_θ = λᵀ(∂b/∂θ − ∂A/∂θ·z*) + 耦合案例叙事 + 线性化 max-B LP 附录强化。
- **E8 小规模验证规格已落盘**（experiment-design.md §2 E8）：1-2 构型读 duals + 闭式 δ_i/κ_j + 扰动验证一阶近似；判据 S1-S5 方向级。
- 目标形态落实：旋钮解锁排名揭示真解锁旋钮。
- **SensitivityQuery 决策（master 倾向）：暂不建**——E8 方向级验证用 cvxpy 直读 duals；论文需要正式查询再建。
- 待办链：DomainExpert 定稿 → 替换 §5.5 示范占位 → DataSteward 小验证。

## 灵敏度杀手锏·首个实测锚点（2026-08-21）

- **ppl 每 lane 功耗 −1% → B* +3.63%**（s5-sensitivity-sample.md v0.2 登记；主导解锁旋钮 = 系数旋钮，实证审阅 3.2 公式缺口判断）——与耦合案例"降功耗缓解布线/散热"方向一致。
- sensitivity-design.md 定稿（4 条审阅全采纳：max-B LP → 附录、系数旋钮通用式入 §3.2、取整边界入 §3.3、示例数字标注待回填）。
- 术语账本 v0.4 固化：unlocking rate / binding constraint family / shadow price。
- 待扩展：热/布线绑定点锚（DataSteward 小实验）→ §5.5 叙事合并。

## 🎯 作者 round 21+ 指令：A 灵敏度框架修正 + B 风格整顿（2026-08-21）

- **A 技术修正**：模型本质非线性（仅固定 B 子问题是 LP）。灵敏度框架改为 **KKT 乘子 / 包络定理**（KKT 点 (x*,λ*,μ*) 处 dV/dθ = ∂L/∂θ = λᵀ∂g/∂θ + μᵀ∂h/∂θ）；"固定 B 的 LP 影子价格"降级为退化情形，须写明成立条件与局限，不得默认全局成立。DomainExpert 已接修正任务。
- **B 风格整顿（长期红线）**：朴素优先 / 清晰矩阵表示 > 鬼画符（V5 §2 标杆）/ 几个符号说清不堆砌 / 文档越简洁越好（不做作者看不懂、不"费大劲懂后发现错了"）/ 术语克制（无此术语说不清才用）/ 交付前自查。已入 `PAPER_TEAM_WORKFLOW.md`《📐 文档质量红线》长期章节，全员开工前必读。
- **C 执行**：广播 7 成员；各角色按 B 自查已有产出（过度堆砌 → 简化）；DomainExpert 按 A 修 sensitivity-design.md。

## 🎯 E7 耦合案例数据闭环（2026-08-21，作者 round 21【1】直接实证）

- **Power 走线占 RDL**：c_pwr 0→2→10 → B* 685→490→295（edge/vert 容量 -28%/-57%）
- **降功耗 = 真解锁**：c_pwr 2→0.5 → B* **+40%**
- **散热增强 = 零释放**：R_vert 2.5→0.4 → B* 恒 490（被 power 布线顶住）——"散热侧失效、功耗侧解锁"反直觉核心，作者叙事数据闭环
- E8 终跑：step=2 一阶误差 ≤0.7%（灵敏度数据链完整）
- **Phase 2 全闭环**：E1/E2/E3 v1+v2/E5/E6/E7/E8/EC；D1/D3 ✅、D4 Conservative ✅（耦合域=布线饱和域 lanes≤50 如实界定）

## 📖 经书/释经拆分（2026-08-21，作者最高优先级指令，已执行）

**v5 定位净化**：v5 只保留 ① 唯一参考符号体系 ② 唯一参考模型标准 ③ 必要符号解释 ④ 必要约束项物理意义。一切可由 v5 派生的内容全部移出（不删除，各归其位）。

**拆了什么、放哪了**：
| 移出内容 | 去向 |
|---|---|
| 修正日志（v5.9-v5.27） | `notes/V5_CHANGELOG.md`（+v5.28 拆分记录） |
| 实现对应表（原 §8）+ 参考文献（原 §10）+ power 走线双分支推导/fixed_paths 细节 | `notes/IMPLEMENTATION_MAP.md` |
| 闭合性论证 + 模型类别（非凸但多项式全局最优）+ 单调性注意（原 §5.2/§5.3） | `notes/MODEL_PROPERTIES.md` |
| 待定案（原 §9：G_inter^amb、P 构造、sub 热/C4 接入、分割比 ρ、die 缩放单调性验证） | 本文件「待决项」 |
| insight 相关内容（落点引用、定案记录） | 从 v5 正文剥离；解读见 `notes/INSIGHT_READING.md` |

**v5 现在剩什么**（经书）：§0 模型对象与物理图像 / §1 符号表 / §2 die 段（2a-2f 约束 + 物理意义） / §3 I2I 段 / §4 跨层耦合 C1-C4 / §5.1 整体结构 / §6 关键假设 / §7 性能模型（7.1-7.5+7.3b）+ 释经指引。测试锚点节号保留（§7.3、§2.8、§7.3b、2a-2f、C1-C4）。
