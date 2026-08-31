# 实验设计文档（experiment-design）

> Phase 2 产出（EvalDesigner，2026-08-20）
> 用途：针对 insight 1-7 设计演示实验（变量 / 基线 / 预期 / 判定标准）；评测报告规范；可行性评估（Gate③ 素材）；artifact/数据可用性声明素材。
> 落点编号对应 `paper-skeleton.md` §5.1-5.6 与 `insight-orchestration.md`；执行归 DataSteward；缺口上报 DomainExpert（Gate③ 定夺是否建 CodeEngineer）。
> 权威依据：`notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md`（唯一权威模型文档——**经书，只答"模型是什么"**）、`insight.md`（7 条，字节级不变）、`notes/INSIGHT_READING.md`（解读）、`notes/PAPER_TEAM_WORKFLOW.md`（总纲）、`paper-skeleton.md` / `contributions.md` / `insight-orchestration.md`（Phase 0 三件套）。
> 经书/释经拆分（2026-08-21）：V5 只答"模型是什么"；实现/推导/性质/历史内容改引 `notes/IMPLEMENTATION_MAP.md` / `notes/MODEL_PROPERTIES.md` / `notes/V5_CHANGELOG.md`（待定案在 `.dsh/team/decisions.md`）。本文档中的 V5 模型节号锚点（§7.3/§2.8/§7.3b/2a-2f/C1-C4）不变；v5.x 版本号出现处为协作历史溯源，详史见 `V5_CHANGELOG.md`。
> 定案约束（DomainExpert 2026-08-20 答复 q-26a5f11e）：覆盖 insight 1-7 全部，分两级（论文 §5 主实验 + 内部良心检查不上台面）；insight 1 不设独立实验；分离/无 DSE 基线形态定案；insight 7 正文只做规模-时间，MILP/启发式对比默认不做（可选附录）；缺口按"描述+影响+是否阻塞正文+建议"上报。
> Gate 对齐（2026-08-20）：Gate① 已放行（ISCA、贡献 4 条 C1-C4、标题暂定 T1——见 `.dsh/team/decisions.md`）；本文档为**草稿**，Gate② 对标矩阵回来后可随 C1 措辞等微调（`gate2-review-template.md` 逐条审查）。

---

## 0. 设计原则与全局口径

1. **insight 1（筛选而非优化）不设独立实验（DomainExpert 定案）**：insight 1 是定位性主张——DSE 输出是"B\* 标量 + 排序"而非多目标 Pareto 面，实验形态本身体现该主张；§5.3 排序实验（E1）即 insight 1+2+5 的联合载体。文档层面只声明一条**设计原则**：*本 DSE 不产出 Pareto 面，输出为按 B\* 排序的可行构型集合*（§5.3 图注与 §6.2 引用）。
2. **两级实验**：论文 §5 主实验（正文，E1-E6）+ 内部良心检查（EC，不上论文台面，结果只进内部报告给 master）。
3. **比较前提（insight 2 定案）**：一切"解质量比较"在同端口数、同 DSE 设置下进行。拓扑按端口数分组（见 §2 E1 端口数分组表）。
4. **归一化基准**：B\* = 联合模型解出的额定出入口带宽（有 QoS 保证，RNB）。比率类指标（衰减比/上推比/严格度比）以各自基线为分母（baseline = 1.0）。
5. **双面评估（L1 Progressive + Conservative）**：每个主实验除"提升/区分度"证据外，必须报告 Conservative 侧（无退化、开销诚实、非绑定构型如实列出）。
6. **独立实验单位 n**：n = (拓扑, 参数组, 场景) 组合，每个组合一次确定性 LP 求解（当前求解链无随机源）。若引入随机化组件（如启发式基线），n 变为 组合 × seed 数，seed 固定并报告。
7. **判定标准风格**：一律可测、可复现（数值阈值 + 计数），不写"应该更好"这类含糊表述。
8. **术语**：B = 有服务质量保证的额定出入口带宽；"无阻塞"仅作 QoS 语义（RNB）；性能语言用"包络/预期"。
9. **验证阶段执行策略（PAPER_TEAM_WORKFLOW 新章节，2026-08-21，Phase 2-4 生效）**：本文档已按"先验证想法、不铺大规模"执行——拓扑子集 7 个（每组 1-2 代表）、参数组 2-3、判据均为**方向级**（单调性/分歧计数/等价性/绑定族，非精度网格）；大实验（确需量化时）走 ssh walker 远机；可选探索（KaryNCube(4,3) 加固案例）已按此策略暂缓、条件触发。
10. **定位澄清（作者 2026-08-21）**：立项称 wafer DSE，但研究重心始终在"**一个 interposer 的设计**"——术语与实验对象保持此聚焦（build_scenario 场景均为单 interposer：die 在 interposer 内 + I2I 出 interposer）；外层布局不自研（NP-hard，引用成熟 chiplet DSE 流程——**LiteratureSearcher 已交付 `layout-algorithms-note.md`**：布局表示 sequence-pair（murata1996seqpair）、热感知布局（tap2p5d2021/atplace2p5d2024/chiou2023chiplet/tdpnavigator2025）、interposer 布局+信号分配（liu2014interposerfloorplan）、2.5D EDA 综述（chen2025survey2p5d）、co-design（kim2019codesign）、多核拆解（kannan2015interposer）；RapidChiplet 自身不做布局求解（布局=设计空间自由度，需借用成熟布局器）、FPIA 为外层布局+布线求解器候选/对标——E7/E3B 引用键已备）。
11. **耦合核心轴（作者 2026-08-21 定案，INSIGHT_READING §4）**：**功耗/电源走线（Power/GND）占用布线（RDL）容量**——power 走线需求过大顶满布线容量 → 必须 (a) 提高散热能力或 (b) 降低性能（减小带宽）换布线布得下——"**功耗—散热—布线/性能**"三向牵制，是反驳"分离决策能解 DSE"的**经典反例/靶子**（作者授权 diss）。实验设计核心轴 = 展现该耦合的可量化影响（E7）。

## 1. 实验总表

| # | insight | 实验 | 论文落点 | 现状 | 缺口 | 执行 |
|---|---|---|---|---|---|---|
| E1 | 2（载体 1+5） | 拓扑 × 约束场景矩阵 → B\* 排序与可行域 | §5.3（图 4） | ✅ run_matrix 已有雏形 | 无 | DataSteward |
| E2 | 3 | 要求旋钮 × 约束旋钮 → B\* 单调性（灵敏度） | §5.5（图 6） | ❌ 旋钮无模型 | 模型缺口（§4 G2） | Gate③ 定 |
| E3 | 4 | 消融阶梯 + 耦合 vs 分离决策 | §5.4（图 5） | 阶梯 ✅ / 分离基线 ❌ | 分离基线脚本（§4 G3） | DataSteward（阶梯）/ 缺口 |
| E4 | 5 | 严格 vs 放宽约束 → B\* 上推 + 排序保序 | §5.3 + §6.1 | 条件 ✅（依赖 E2 或场景近似） | 同 G2（若补则共用） | DataSteward |
| E6 | 7 | 规模 vs 求解时间 + 二分迭代 | §5.6 | ✅ BmaxQuery 可跑 | 规模扫描脚本（exp 层） | DataSteward |
| EC | 内部 | die 缩放（α_d, β_P ≠ 0）可行性单调性验证 | **不上论文** | ✅ 接口齐（test11 锚点） | 单调性扫描脚本 | DataSteward → master |
| E7 | 4（作者核心轴） | 功耗—散热—布线/性能 三向耦合演示 | §5.4（耦合牵制面板） | ❌ 模型缺口（power-trace 项未入 WiringModel） | **G7** | 待 G7（DomainExpert 拍板 + CodeEngineer 实现） |
| E8 | 2/3/4/5 深化（杀手锏） | 灵敏度验证：KKT/包络定理解锁排名 | §5.5（图 6 扩展 + 表 X） | ✅ duals 现有（min-ΣL 诊断） | SensitivityQuery 暂不建（已裁决） | 终跑待 power_trace 稳定提交 |

## 2. 各实验详细设计

### E1 — B\* 排序与可行域（insight 2，联合载体 insight 1+5）

- **动机**：insight 2——DSE 不只要"可行/不可行"，要"多大程度可行"；同设置同端口数下 B\* 更高的设计点质量更优。insight 1 的"筛选"形态（输出排序集合，非 Pareto 面）由此体现。
- **变量**：
  - 拓扑集（11 种，按端口数分组，同组内可比）：

    | 端口数 | 拓扑 |
    |---|---|
    | 4 | Mesh(2)、Torus(2)、KaryNCube(2,2) |
    | 8 | KaryNCube(2,3) |
    | 9 | Mesh(3)、Torus(3) |
    | 2/3/6/12/16 | FullMesh(2)、FullMesh(3)、Dragonfly(2,1,1)、Dragonfly(2,2,1)、Mesh(4)（单成员组，仅跨组参考） |

  - 约束场景：`perf+bump`、`perf+bump+therm`（`perf` 场景 B 无界——纯性能模型 B 不约束，作为"无物理约束上限"参考列，不参与排名）。
  - 参数组：`ucie-32g` 主跑；`ucie-16g`、`ucie-24g` 做排序稳健性复跑。
- **基线**：无 DSE 基线（DomainExpert 定案形态）= 固定 B_target 二元筛选——对所有构型只判"B ≥ B_target 可行/不可行"，无连续量化；对比 DSE 的 B\* 连续排序能力。
- **步骤**：`PYTHONPATH=src python3 exp/run_matrix.py <params>`（每参数组输出 `exp/output/matrix_<params>.csv`：topo/scenario/B_star/iterations/binding 约束/求解时间）；按端口数分组排序；绑定约束族诊断（`bump_*`/`therm_*` 前缀）。
- **规模控制（DataSteward 确认）**：全量 run_matrix = 88 次 BmaxQuery（perf 跳过）；小拓扑 <1s/组合，Mesh(4)（16 dies）可达数分钟-十分钟级/组合——**正文优先小拓扑**（Mesh(2/3)、Torus(2/3)、FullMesh(2/3)）× ucie 谱系，Mesh(4) 单列排队。
- **预期**：B\* 在同端口数组内有区分度；加约束后 B\* 单调不增；绑定约束随场景层级从 bump 迁移到 therm。
- **判定标准（可测）**：
  - C1 区分度：每个含 ≥2 个**非同构**拓扑的端口数组内，B\* 至少 2 个不同值且 max/min 比值 > 1.1。**端口数 4 组例外（已修订，DataSteward 实测确认）**：Mesh(2)、Torus(2)、KaryNCube(2,2) 为图同构（2×2 网格 = 2×2 环 = 2-ary 2-cube，同度数同边数），B\* 逐位相同属必然（3 参数组实测逐位一致：11211/14914/17838）——该**同构一致性本身是有效性检验**（B\* 是拓扑的良定义函数），该组 C1 判"不适用（同构）"而非失败。
  - C2 排序稳健：跨参数组（16g/24g/32g）同端口数组 B\* 秩的 Spearman ρ ≥ 0.9。
  - C3 场景单调：∀ 拓扑，B\*(perf+bump) ≥ B\*(perf+bump+therm)（约束加严 B\* 不增）。
  - C4 Conservative：报告热约束显著压制 B\* 的构型（衰减比 < 0.5 者）及其绑定约束，不回避。
- **归一化/聚合**：B\* 绝对值（Gbps）逐构型报告；排序用秩；场景衰减比跨拓扑用几何均值。
- **论文落点**：§5.3（图 4：按端口数分组的 B\* 排序条形图 + 绑定约束标注）。**图 4 语义标注（DataSteward 实测警示）**：ucie-32g 下 therm 档 B\* 仅为 bump 档的 ~4%（热衰减 24×，per-die T≤358.15K/R_vert=1.5 全面主导，绑定约束几乎全为 `therm_*`）——图 4 排序实为"热约束下的排序"，须标注绑定约束族 + 同时展示 bump 档排序结构差异（双面），避免读者误读为纯拓扑排序。
- **可行性**：✅ 现有 `run_matrix.py` + `BmaxQuery` + 三场景可完成；无缺口。
- **输出物**：`matrix_<params>.csv`（×3 参数组）；排序表 + 秩相关表；图 4 源数据。

### E2 — B = f(要求, 约束) 双旋钮单调性（insight 3）

- **动机**：insight 3——B 是要求与约束的单调函数；双旋钮（要求严格度 × 约束悲观度）得到不同的 DSE 模型，帮助设计者灵活决策（C2 的权衡框架）。
- **变量（2×2 档位，场景字符串定稿 2026-08-20）**：
  - 要求旋钮 R：`R_qos`（QoS 保证：端口负载 ≤ B 时无阻塞交换，当前 oblivious Valiant 包络语义）vs `R_peak`（**逐链路单对流量包络**：L ≥ L\*_peak，有逐链路包络但比 R_qos 松——只保证任意单对流量可达 B，不承诺多对并发无阻塞；**非"无逐链路包络"**——后者 L 无正下界、B 不可判；也**非次随机放宽**——次随机与双随机包络数学恒等已证，V5 §7.3b 附论证）。**R_peak 包络精确式（V5 §7.3b，v5.22 落盘）**：L\*_e(R_peak) = max_{(i,j)} c_ij^e（**单对流量包络**，闭式解 O(|E|N²)，≤1 通常=1）。
  - 约束旋钮 C：`C_peak`（峰值工况：P_peak(B) 计入，当前档）vs `C_rated`（额定功耗工况：不计峰值项或取额定值）。
  - 参考档 =（R_qos, C_peak）= V5 §0.1 当前固定档（最严苛一档，B\* 为保守下界）。
  - **4 档 build_scenario 字符串（CodeEngineer 已交付，git 5008ed0，2026-08-20）**：`perf+bump+therm`（参考档，向后兼容=回归锚点）／`perf+bump+therm+rated`（C 放宽）／`perf+egress_peak+bump+therm`（R 放宽）／`perf+egress_peak+bump+therm+rated`（双放宽）。命名约定：qos/peak 默认省略，egress_peak/rated 显式后缀。结构性断言进 test18（tests/perf/test18_dual_knobs.md：L\*_peak ≤ L\*_qos 逐链路 + rated rhs ≥ peak rhs（β_P>0），不依赖 solver）。
  - **预研实证（EvalDesigner 复跑确认，Mesh(2)/ucie-32g）**：β_P=0.05 档 ref 490 → C_rated 11211（22.9×）→ R_peak 490 → dual 33627（68.6×）；β_P=0 档 R_peak 11211→33627（3×）。M1 单调全过（允许相等）。**补充观察**：β_P>0 且 C_peak 时 R 旋钮效果被峰值功耗预算掩盖（热 rhs 绝对上限 B\*≈(P_max−P0)/β_P，与 L 无关）——M1 允许相等覆盖，如实报告。
- **基线**：参考档（R_qos, C_peak）；其余档与之比。
- **步骤**：对 4 档 × 拓扑子集 × 参数组分别求 B\*。**拓扑子集（7 个，每组端口数 1-2 代表）**：FullMesh(2)〔2 口〕、Mesh(2)〔4 口；Torus(2)/KaryNCube(2,2) 同构取一〕、KaryNCube(2,3)〔8 口〕、Mesh(3)+Torus(3)〔9 口，非同构取 2〕、Dragonfly(2,1,1)〔6 口〕、Dragonfly(2,2,1)〔12 口〕；Mesh(4)〔16 口〕可选（重拓扑控时长）。**参数组**：ucie-32g 主跑；ucie-16g/24g 稳健性复跑（M3 跨参数组）。⚠️ **约束旋钮可测效果依赖 β_P>0**（默认 β_P=0 时 P_peak(B)=P0 恒定，C_peak≡C_rated 退化）——E2 建议启用 die 缩放档位（β_P>0，程序化覆盖或专用参数档）；默认参数下的退化档如实报告（边界）。
- **预期**：要求越严/约束越悲观 → B\* 越低（单调）；放宽单旋钮 B\* 上推。
- **判定标准（可测）**：
  - M1 单调性：固定 C，B\*(R_qos) ≤ B\*(R_peak)；固定 R，B\*(C_peak) ≤ B\*(C_rated)（逐构型成立，允许相等）。**M1 方向正确性依据**：单对流量包络（R_peak，V5 §7.3b）≤ 双随机包络（R_qos，§7.3）⟹ B\*(R_qos) ≤ B\*(R_peak)，逐构型成立（实现口径：R_peak 包络按 V5 §7.3b 单对流量包络 max c_ij^e 实现）。
  - M2 可测效果：至少一个放宽方向 B\* 上推比 > 1.05（**数学依据**：单对包络 ≤1 vs 置换最坏 ≈2，故 R 放宽方向的上推有结构保证）。
  - M3 无交叉：同构型 4 档按"严格度偏序"排序无矛盾（无放宽档反而更低）。
- **缺口（§4 G2）**：要求旋钮（仅出入口峰值）与约束旋钮（额定功耗）**无对应模型/场景实现**——模型缺口，阻塞 §5.5 正文。已按流程上报 DomainExpert（倾向值得补，可能 CodeEngineer 做场景参数化或开关；Gate③ 定）。参数化建议：场景档位如 `perf+qos+bump+therm+peak` vs `perf+egress_peak+bump+therm+rated`，或 P_peak(B) 项开关。
- **约束旋钮的近似路径（DataSteward 确认，预研用）**：冷却方案变体可作约束悲观度的参数级近似——`ucie-32g-air`（R_vert=2.5 K/W，悲观）vs `ucie-32g-microfluidic`（R_vert=0.4，乐观）已有参数可直接跑。注意该轴是**散热能力**，与 insight 3 的"峰值 vs 额定功耗工况"（P_peak(B) 开关）**不是同一旋钮**——后者仍需 G2 模型补；近似路径仅作 G2 落地前的预研演示，不作正文替代。
- **归一化**：B\*_档 / B\*_参考档 比率，跨拓扑几何均值 + 逐构型值。
- **E2 实测（DataSteward 2026-08-20，git 5008ed0，附录 C；7 拓扑 × 4 档 × 3 参数组，56 行/组）**：M1 单调 ✅（逐构型；default 档 C 方向平凡相等如实报告退化）；M2 上推 ✅——default 档 R 上推 GM≈2.64×（三参数组一致 2.63-2.65，>1.05，与"单对包络 ≤1 vs 置换最坏 ≈2"结构预期一致）；β_P=0.05 档 C 上推 GM=17.9-28.6×（峰值功耗项 ∝ β_P·B 主导）；M3 无交叉 ✅（逐构型严格度偏序零矛盾，跨参数组稳健）。**2×2 正交结构诚实呈现**：β_P>0 且 C_peak 档内 R 上推被功耗压平（=1.000），R 区分度在 C_rated 档内体现（R-in-rated ≈2.64×）——"B=f(要求,约束)"单调权衡框架数据齐（图 6）。
- **论文落点**：§5.5（图 6：双旋钮热力图/单调曲线）。
- **输出物**：`knob_matrix_<params>.csv`（列规范：topo, n_terminals, scenario, B_star, B_star_ratio_vs_ref, iterations, solve_time_s；比率分母 = 参考档）。

### E3 — 多因素耦合：消融阶梯 + 耦合 vs 分离（insight 4）

- **动机**：insight 4——热、电、几何、性能多因素强耦合，前人多分离决策；本文在单一 LP 联立（C1-C4 跨层耦合）。实验须证明"耦合必要"。**V5 v5.21（作者推翻 G4）布线 (2d)/面积 (2f) 一级化**——布线 edge/vert/pad 三维容量共享 + A_die≤A_max 面积上界是"真正会绑定"的耦合要素，在此约束下联合 vs 分离的可行域/最优解可真正分歧。
- **实验 A（消融阶梯，✅ 可执行；`+wiring`/`+area` 级已接入）**：同一构型逐级加约束——`perf+bump` → `perf+bump+therm` → `+wiring`（2d edge/vert/pad 三维容量，WiringModel）→ `+area`（2f A_die≤A_max，DieAreaModel），看 B\* 衰减与绑定约束迁移（`run_matrix.py` 场景阶梯 + `run_ledger.py` B 轴账本：B\*/4、B\*/2、3B\*/4、B\* 处各约束族占用率/温度 margin）。**已接入（CodeEngineer git 459a6ed，2026-08-20）**：token 逐步追加可构造（实测模型列表：`+wiring`→+WiringModel、`+area`→+DieAreaModel、全=5 模型）；**绑定约束族命名**：`route_dem_l*` / `route_edge_e*` / `route_vert_v*`（布线族）+ `area_die`（面积族）；diagnostics 约束家族已含 route/area（DataSteward 账本/绑定迁移可直接用）。
- **实验 B（耦合 vs 分离，V5 v5.21 双阶段；分离基线口径与 v1 同口径）**：同一构型，(i) **联合模型**（单一 LP 联立：perf 包络 + bump(C1) + therm + **wiring(2d)** + **area(2f)**——lane 布线决策 x_D2D 与 lane 分配 ℓ 共享 edge/vert/pad 容量；die 面积在信号 lane/电源 bump 间竞争）vs (ii) **分离决策基线（布线/面积版，v1/v2 同口径可比）**：性能包络先定 L\* → 独立判 bump（N_sig 预算）→ 独立判热（T≤T_max）→ 独立判布线（固定候选路径下 edge/vert/pad 容量）→ 独立判面积（A_die≤A_max）→ 取各独立 B\* 的 min（简单交集）。对比可行判定、B\* 与绑定约束族。
- **G3 实测发现（DataSteward 2026-08-20，历史事实，保留为边界刻画）**：在**无布线/面积的旧子集**（C1+热+包络）下 11/11 拓扑 rel_diff=0——分离≡联合（B\*_joint=min(B\*_bump,B\*_therm) 解析成立：① 约束对 B 线性（∝B·L）；② 可行性边界处 L 钉在包络 L\*；③ α_d=β_P=0 下几何面积恒松）。该等价性是**线性可分离子集的数学事实**（`model-ruling-g3-sep-vs-joint.md` 结论仍有效），作为"耦合何时起作用"的边界刻画（进附录）。**V5 v5.21 布线/面积一级化后等价性前提被打破**——新 E3B 直接检验"耦合必要"假设（见预期）。
- **E3B 处理（DomainExpert 双阶段定案，V5 v5.21，2026-08-20）**：E3B 改**双阶段**——**v1（无布线/面积子集，已完成）**：等价性实证为诚实基线（rel_diff=0 ×11 + B\*_joint=min(B\*_bump,B\*_therm) 解析一致；`model-ruling-g3-sep-vs-joint.md` 仍有效，进附录作"模型条件刻画"）；**v2（布线/面积进主模型后，待 CodeEngineer 接入）**："分离决策在布线/面积下产生分歧"恢复为**实验主张**（预期 rel_diff ≠ 0，DataSteward 重跑）。§5.4 叙事 = 双阶段：v1 诚实基线 + v2 分歧主张（Progressive = 单一模型统一求解 + 全局最优 B\*（insight 7 载体）+ 真耦合要素（布线/面积/C4/ρ）单一数学载体；Conservative = v1 等价性边界 + v2 未分歧构型如实报告）。
- **分离链条的文献映射（LiteratureSearcher 核验，2026-08-20）**：分离决策基线对应成熟单维工具的链式判定——性能：BookSim 2.0（Jiang et al., ISPASS 2013, DOI 10.1109/ISPASS.2013.6557149）；热：HotSpot（Huang et al., IEEE TVLSI 2006, 14(5):501-513, DOI 10.1109/TVLSI.2006.876103）、3D-ICE（Sridhar et al., ICCAD 2010, DOI 10.1109/ICCAD.2010.5653749）、MFIT（Pfromm et al., ACM TODAES 2025/26, DOI 10.1145/3765905）；物理/布局：FPIA（Jiao et al., IEEE TCAS-I 2024, DOI 10.1109/TCSI.2024.3419579）、RapidChiplet（Iff et al., CF 2025, DOI 10.1145/3719276.3725170 / arXiv:2311.06081）、**liu2014interposerfloorplan（DAC'14，interposer 布局+信号分配）**、**chen2025survey2p5d（ASP-DAC'25，2.5D EDA 综述——布线容量基线的可引条目）**；电/PDN：RedHawk-SC（Synopsys 工业工具，白名单外）。**分离流水线基线 = BookSim(性能)→HotSpot/MFIT(热)→FPIA/RapidChiplet(布局)→RedHawk(电) 分步判定 vs 单一 LP 联立**（详见 `gap-evidence-chain.md` §2）。
- **RapidChiplet 直接铁证（原文 Related Work 引句）**："There exist numerous DSE-tools for other metrics, such as the Orion 2.0 power and area model, the ChipletActuary cost model, or the HotSpot thermal simulator. RapidChiplet focuses on the latency and throughput of the ICI and only provides very high-level power, area, and cost estimates"——工具自身把 thermal 划给外部 HotSpot，是 insight 4 gap 的最强引文。
- **部分覆盖警示（E3 对比必须处理，否则审稿人攻击点）**：TickTock（Yang et al., ISCA 2025, DOI 10.1145/3695053.3731045）已做 NoW 的 PD 约束感知物理/逻辑拓扑协同设计；Chen et al.（ISCA 2024, DOI 10.1109/ISCA59077.2024.00025）radix 受带宽+功率密度联合限制；"Cramming a Data Center into One Cabinet"（Yu et al., ISCA 2025, DOI 10.1145/3695053.3731016）做晶圆级计算+硬件架构协同探索——三者属"部分联合"，须以"xxx vs xxx"措辞纳入 §5.4 对比（我们的差异 = 内层单一模型联立（热-电-几何-性能）+ B\* 量化 + 包络解耦 + 全局最优），不得回避。
- **基线**：分离决策基线（实验 B 的 (ii)）；消融阶梯自身即 Progressive/Conservative 证据。
- **预期（布线/面积下真正分歧）**：逐级加约束 B\* 单调衰减；**联合 vs 分离的可行域/最优解真正分歧**——(a) **布线饱和先于 bump**：某些拓扑 lane 路由需求先耗尽 edge/vert/pad 容量（`route_*` 绑定）而 bump 预算仍有余，分离交集判 bump 可行但布线不可行；(b) **面积抢占**：A_die≤A_max 下 die 面积在信号 lane（N_total→N_sig）与电源 bump（N_pwr）间竞争，面积回挤 bump 可用预算，联合模型可重分配而分离基线（面积独立判定）不能；(c) **布线路径多样性**：联合模型经 x_D2D 在 L 形候选路径间分配（多商品流），瓶颈处可利用路径多样性，分离基线固定选路。→ 分歧构型数 ≥ 1（C3）。
- **判定标准（可测，双阶段）**：
  - **v1（已完成，等价性验证）**：分离 vs 联合 rel_diff = 0（11/11 拓扑，G3 实测）+ B\*_joint = min(B\*_bump, B\*_therm) 解析一致——无布线/面积子集的诚实基线（进附录）。
  - C1 消融单调（两阶段共用）：∀ 拓扑，B\*(perf+bump) ≥ B\*(perf+bump+therm)（接入后逐级 ≥，含 `+wiring`/`+area` 级）。
  - C2 衰减可量化（两阶段共用）：跨拓扑几何均值衰减比报告；至少一个拓扑绑定约束含 `therm_*` / `route_*` / `area_*`。
  - **v2（待接入，布线/面积分歧验证，判据按 model-ruling §六 定案）**：
    - C3' 主判据：**≥ 2 构型 rel_diff > 0.01**（1% 阈值）；报告 rel_diff 分布 + 分歧构型清单 + **v1→v2 对比**。
    - C4' 强化判据：**≥ 1 构型 B\*_joint 绑定族含 wiring/面积**（B\*_joint < min(B\*_bump, B\*_therm)）——验证"布线饱和先于 bump 绑定"。
    - C5' 机制归因（可选）：run_ledger 账本确认 RDL 共享/面积抢占来源，排除伪影。
    - 结果处理：**通过 → 主张成立（§5.4 双阶段定稿）**；**不通过 → 如实报告，主张限缩（数据说话）**。
    - **v2 实测（DataSteward 2026-08-20，git 5008ed0+459a6ed，附录 B）**：单调性抽查 ✅ PASS（6/6 无可行性带，§七 预期符合）；**C4' ✅ 通过**——Dragonfly(2,1,1)/(2,2,1) 默认参数 wiring(7897/3998) 先于 therm(8287/4193) 绑定（**"布线饱和先于 bump/therm"有数据支撑**），α=0.01 面积绑定（joint=area 上界 1464-4388）。
    - **C3' 终判 ✅ 通过（fixed_paths 重跑，缓存键修复 c5aa79f 后冷跑修正，2026-08-21）**：分离布线因素换 `WiringModel(fixed_paths=True)` 重跑（72 行 = 9 拓扑 × {default, lanes100} × α_d∈{0,0.001,0.01,0.05}）——**10/72 配置 rel_diff>0.01**（≥2 判据满足）。⚠️ **明细修正**：旧"Mesh(3) 默认域 rel=0.80"系缓存污染（真值：默认域无分歧，wiring_sep=5558、sep=5363=therm）；**真分歧 = 布线饱和域 lanes=100**（Mesh(3) 0.154、Torus(3) 0.190、KaryNCube 0.352/0.266）+ **默认域 KaryNCube(2,3) 0.087**（8 条两路径链路，固定首路径默认容量即拥塞）。**强分歧需布线饱和域（lanes=100）——与 E7 耦合显现域发现完全一致**（布线饱和域是耦合/分歧的共同显现域）。机制 = 规格预期 (c) 路径多样性（固定首路径拥塞 vs 联合 x_D2D 绕行）。**insight 4 双阶段主张成立（§5.4 定稿）**。
    - **v2 参数域扩展（DataSteward 2026-08-20，72 配置）**：α_d=0.05 + wiring_tight（lanes_per_mm 500→50）全 rel_diff=0（C3' 在扩域下仍不通过——等价性非参数调优伪影，跨域稳健）；C4' 44 行通过（Dragonfly 真实参数布线先于 bump/therm；α_d≥0.01 面积绑定）。**诚实边界：布线绑定域 = Dragonfly 类拓扑**——稀疏拓扑（Mesh/Torus）即使 lanes_per_mm 收紧 100×（5/mm）仍不绑定（余量充足）；绑定迁移账本 `ladder_migration_v2.csv`（bump→therm→route→area）。
    - **结构性张力（EvalDesigner 2026-08-20 预判，已被 decisive test 证伪）**：预判"布线绑定域=单路径拓扑重合、多路径拓扑不绑定"——基于 optimize-sep 数据（Mesh(3) B_wiring_sep=7117 非绑定）。**fixed_paths 重跑证伪该预判**（缓存键修复 c5aa79f 后冷跑修正）：固定首路径拥塞在**布线饱和域 lanes=100** 出现（Mesh(3)/Torus(3)/KaryNCube 分歧），默认域仅 KaryNCube(2,3)（8 条两路径链路）拥塞——**布线绑定与否取决于路径构造（fixed 首路径 vs optimize 分流）× 布线饱和域，而非仅拓扑族**（DataSteward 纠正，采纳）。
    - **双机制互补（DomainExpert §十）**：C3' 分歧机制（固定路径拥塞 vs 联合绕行）源于**优化自由度差异**，在多路径拓扑成立（Mesh(3)/KaryNCube(2,3)）；C4'（布线饱和先于 bump/therm）在 Dragonfly 单路径拓扑成立。**两种耦合机制互补，insight 4 主张双重证据**（分歧实证 + 真绑定识别）。
    - **机制补充（DomainExpert §九）**：布线饱和需两条件——① lane 需求接近布线容量（B 高）② 路径集中。ucie-32g 热约束主导（B\* 被压 ~4-5%）→ lane 需求低 → 布线永不饱和；Dragonfly 布线饱和恰因 B\* 相对高（热不主导）+ 路径集中——**稀缺是结构性的，非数据伪影**。
    - **限缩预案（model-ruling §九）**：**未触发**——C3' 终判通过（fixed_paths 重跑 10/72 分歧），§5.4 双阶段主张成立定稿：v1 等价性边界（附录）+ v2 分歧实证（正文：路径多样性机制 + 分歧幅度/构型）+ C4' 真绑定识别（正文含拓扑域界定：布线绑定域=Dragonfly 类、面积绑定 α_d≥0.01）+ 统一求解价值。可选翻案探索（KaryNCube(4,3)+microfluidic+wiring 收紧）不再需要。
    - **fixed_paths 重跑已完成**（规格完整 + 科学诚实执行；C3' 通过，见 v2 实测块）。
    - **可选探索（model-ruling §九，加固性质，暂缓）**：高 radix KaryNCube(4,3)（64 节点/288 链路/64 dies，大拓扑）+ microfluidic R_vert=0.4 + wiring 收紧——C3' 已通过后为"主张加固"（更干净的高 radix 路径多样性×布线饱和案例），非翻案必需。**DataSteward 决定暂缓**（资源纪律优先；C3' 通过、主张已成立；大拓扑走 ssh walker）。**条件触发**：Gate④ 内审若判 §5.4 需加固证据 → 经 ssh walker 跑小配置集（KaryNCube(4,3) × {default, lanes100} × α=0 × {optimize, fixed} ≈ 8 组合）。
    - 内部抽查（DataSteward 提议 + model-ruling §七 定案）：**v2 执行前置**——先在新模型（含 wiring/area）下做**二分前提单调性抽查**（沿用 run_monotonicity 模式，B 网格含低 B 段；理论预期低 B 恒可行、单调保持：B→0 时 lane→0 布线松、d_0²≤A_max 面积低 B 可行、α_d>0 面积只给上界）；实测出现真"可行性带"或全 B 不可行 → 上报 DomainExpert，不自行改判；α_d>0 时二分上界用面积闭式 (√A_max−d_0)/α_d。通过后再跑 C3'/C4'/C5'。
    - **v2 参数域（重要）**：默认参数（α_d=0）下 wiring/area 不绑定（实测联合 B*=11211 与三档相同，无分歧可测）——**v2 分歧验证需 α_d>0 档**（面积上界绑定；实测 α_d=0.05 → A_max=1600、闭式上界 560、B*≈529）+ 布线饱和参数域（如 lanes_per_mm 收紧使 route_* 绑定）。
- **归一化**：衰减比/分歧比跨拓扑几何均值；分歧用计数。
- **论文落点**：§5.4（图 5：阶梯衰减曲线 + 统一 vs 分离——v1 一致性 + v2 分歧点标注 + 绑定约束迁移图）。
- **可行性**：实验 A 现有三场景 + `+wiring`/`+area` 级 ✅（CodeEngineer 已接入，git 459a6ed；实测 5 模型联合可跑）；实验 B ❌ 需 DataSteward 扩展 `run_sep_vs_joint.py` 为布线/面积版分离基线（独立判 bump/热/布线/面积 + 交集，非新 query）。实验 B 阻塞 §5.4 对比正文（v2 待重跑；需 α_d>0 参数域，见 v2 判定标准）。
- **输出物**：`matrix_<params>.csv`（阶梯，接入后含 `+wiring`/`+area` 级）+ `ledger_<params>_<topo>.csv`（绑定迁移，含 `route_*`/`area_*` 族）+ `sep_vs_joint_<params>.csv`（重跑：分歧计数 + 分歧构型绑定族）。

### E4 — B 是精调基石：严格 vs 放宽 B\* 上推（insight 5）

- **动机**：insight 5——严格约束下的 B\* 排序是后续精调的量化基石："严格下接近目标 → 放宽后很可能可行"；设计师按 B\* 排序逐点论证。
- **变量**：约束严格度两档——严格档（`perf+bump+therm`，最严）vs 放宽档（优先用 E2 的约束旋钮放宽档 `C_rated`；E2 未落地前用场景阶梯近似：`perf+bump` 为放宽档）。
- **基线**：严格档 B\*。
- **预期**：放宽后 B\* 上推；严格档与放宽档排序保序（严格档排序可作为论证顺序）。
- **判定标准（可测）**：
  - C1 上推：∃ 构型 B\*(放宽)/B\*(严格) > 1.1（演示"接近目标→放宽可行"路径）。
  - C2 保序：严格档与放宽档 B\* 秩 Spearman ρ ≥ 0.85（排序可作精调论证顺序）。
  - C3 Conservative：放宽未上推的构型（约束本非绑定者）如实列出。
- **缺口**：依赖 E2 放宽档（G2，若补则共用）；场景近似方案不阻塞。
- **归一化**：上推比 B\*_relaxed/B\*_strict 跨拓扑几何均值。
- **论文落点**：§5.3（与 E1 联合叙述）+ §6.1 Discussion（限定"很可能/先验搜集"，不承诺真实物理必然可行——INSIGHT_READING insight 5）。
- **输出物**：复用 E1/E2 输出 + `pushup_<params>.csv`（上推比 + 保序秩）。

### E6 — 全局最优可多项式求解：规模 vs 时间（insight 7）

- **动机**：insight 7——整体问题非凸但存在可多项式时间求解的全局最优解（二分 + LP，不需启发式）。论文措辞按筛选哲学，不引复杂性战争（INSIGHT_READING 二.3）。
- **变量**：拓扑规模——Mesh(n)、Torus(n)，n = 2..6（节点/链路数递增）；每规模跑完整 `BmaxQuery`（lo/hi/step 固定相对区间）。
- **基线**：内部对照（单次 LP 时间 × 二分迭代次数）；**无外部 MILP/启发式基线**——DomainExpert 定案：默认不做（主张是数学性质，不靠实验竞赛；且环境无 MILP 求解器：cvxpy 1.9.2 已装 CLARABEL/HIGHS/OSQP/SCIPY/SCS，无 HIGHS_MIP/GLPK_MI，客观不支持）；LP vs MILP/启发式对比标注"**可选附录，默认不做**"。
- **可选附录的启发式基线对象（若做，LiteratureSearcher 核验）**：RapidChiplet（启发式剪枝+帕累托探索，Iff et al., CF 2025, DOI 10.1145/3719276.3725170）、FireLink（ID3 决策树剪枝，Li et al., JCRD 2025, 62(5):1108-1122, DOI 10.7544/issn1000-1239.202440082）、FPIA（物理设计启发式，Jiao et al., TCAS-I 2024）、CHARIOT（多目标 Bayesian 优化，ACM TODAES 2026, DOI 10.1145/3815192）——成熟 chiplet DSE 启发式流程；**对比维度 = 求解时间 + 解质量 vs 内层 LP+二分的多项式时间精确判定**（文献级立场：最优 oblivious 路由竞争比可多项式时间 LP 求解，Azar et al., JCSS 2004）。
- **指标**：总求解时间 vs 规模（n、n_links、LP 规模）；二分迭代次数。
- **预期**：时间-规模曲线呈多项式轮廓；迭代次数 ≈ O(log((hi−lo)/step))。
- **判定标准（可测）**：
  - C1：迭代次数与理论 O(log) 一致（实测迭代数 ≈ log2((hi−lo)/step)，±1）。
  - C2：时间-规模曲线单调，对数-对数坐标近似线性（多项式轮廓的实证形态；**不宣称复杂度结论**）。
  - C3 Conservative/开销诚实：报告最大规模的单次 LP 求解时间与总时间。
- **论文落点**：§5.6（规模-时间曲线图 + 迭代次数表）。
- **可行性**：✅ `BmaxQuery` 可跑；需规模扫描脚本（exp 层，DataSteward 写）。
- **输出物**：`scalability_<params>.csv`（n/n_links/单次 LP 时间/迭代数/总时间）。

### E7 — 功耗—散热—布线/性能 三向耦合演示（作者核心轴，insight 4 靶子案例）

- **动机（作者 2026-08-21 定案，INSIGHT_READING §4）**：Power/GND 走线占用 RDL 容量——power 走线需求（∝ P(B)）过大顶满布线容量 → 必须 (a) 提高散热能力或 (b) 降低性能（减小带宽）换布线布得下。"功耗—散热—布线/性能"三向牵制，是反驳"分离决策（bump/热/布线各判各的）就能解 DSE"的**经典反例/靶子**。实验展现该耦合的可量化影响。
- **可量化表现轴（DomainExpert 协作定，2026-08-21；验证阶段选 1-2 优先，小实验）**：
  - **轴 1 散热↔带宽（✅ 现状可跑，优先）**：固定布线容量，扫描 R_vert（`ucie-32g-air` 2.5 / 默认 1.5 / `ucie-32g-microfluidic` 0.4，参数已有）→ B\* 释放曲线——"散热能力每增强 X% 释放多少带宽"（热主导域已见 therm≈bump 4%，天然有数）。**不依赖 power-trace 项**。
  - **轴 2 降性能↔布线饱和（部分 ✅ 现状可跑 / 完整版需 G7）**：扫描目标 B（降性能）→ 布线容量余量/绑定变化——"降带宽多少可缓解布线饱和"。现状部分：信号 lane 占用 ∝ B·L，B 降 → 利用率降（可跑）；power 走线 ∝ P(B) 部分需 G7 后完整。
  - **轴 3 三方牵制相图（部分 ✅ / 完整需 G7）**：B × R_vert × 布线容量小网格 → 绑定相图（哪一维先顶到——therm/route/area 相界）——耦合靶子最直观呈现。完整版（power 走线项入布线 rhs）需 G7。**布线容量资源依据（LiteratureSearcher 2026-08-21）**：liu2014interposerfloorplan（DAC'14，interposer 布局+信号分配）+ chen2025survey2p5d（ASP-DAC'25，2.5D EDA 综述）。
- **变量（小规模、方向级）**：散热旋钮（R_vert 3 档，轴 1）；性能旋钮（B_target 2-3 档，轴 2）；网格（轴 3 可选小网格 3×3×3）。参数 **β_P 小/0 档**（耦合演示域，model-ruling §十三 定案；原 β_P 放大档 0.1-0.2 移作**边界观察**——"β_P 放大时 C_peak 先绑定、power 效应藏匿"作 D4 Conservative 证据，不进演示域）；单 interposer 场景；拓扑 2-3 个（Mesh(3)/Dragonfly(2,1,1) 等）。
- **布线饱和参数域（轴 2/3 完整版演示域，2026-08-21 数据复核修正）**：**lanes_per_mm 收紧（500 → 50-100）+ β_P 小/0**——DataSteward 复核（lanes∈{100,50} × β_P∈{0.1,0.2} × c_pwr∈{0,2}）：**β_P>0 时 C_peak 先把 B* 钉死（0.1→295、0.2→100），power 扣减零效应（B 低 → 布线余量充足）——β_P 放大反而藏匿 power 效应**；β=0 + lanes=50 时 wiring 先于 therm 绑定（685），power 项随 B 增长（经 P_dyn）显现（c_pwr 0→2→10 → 685→490→295）。**耦合演示域 = 布线饱和 + β_P 小/0**（这是 D4"耦合域如实界定"的又一证据）。轴 1 平台（7117/7897）在 power 项下降低——"散热释放被 power 走线顶住"曲线即耦合量化。
- **轴 1 部分实测（DataSteward 2026-08-21，coupling_axis1_ucie-32g.csv，零依赖部分 β_P=0 无 power 项）**：R_vert 扫描 2.5/1.5/0.4——Mesh(3): B\* 2829 → 5363 → **7117**（0.4 处 = wiring 独立 B\* 7117 → **散热释放被布线顶住，D2 迁移 therm→wiring 出现**）；Dragonfly(2,1,1): 4388 → 7897 → **7897**（1.5 以下零释放 = **C4-pad 布线硬顶**，与 E8 灵敏度发现一致）。D1 单调 ✅（R_vert↓ → B\* 不降）；D2 绑定迁移 ✅（平台 = 布线/C4-pad 上限）。
- **E7 完整版实测（DataSteward 2026-08-21，git 3ac0c50，coupling_ucie-32g.csv 11 行 + 报告附录 E；作者 round 21【1】耦合案例直接数据）**：Mesh(3)/lanes=50（布线饱和域）/c_pwr 试点/β=0——**c_pwr 0→2→10：B\* 685→490→295（-28%/-57%）**；**c_pwr 2→0.5：490→685（+40%）= 降功耗真解锁**；**R_vert 2.5→0.4：B\* 恒 490 = 散热增强零释放，被 power 布线顶住**（D2 迁移 therm→route/power）。D1 ✅ / D3 ✅（耦合可量化）/ D4 Conservative ✅（默认 lanes=500 power 项不绑定，耦合域 = 布线饱和域 lanes≤50 如实界定）。**"功耗—散热—布线/性能"三方牵制有直接数据：散热侧失效、功耗侧解锁**。c_pwr 物理取值待参数评审（0.5/2/10 试点映射耦合敏感度）；C4-pad 绑定域（Dragonfly）power 项（edge/vert 扣减）不直接作用（与 E8"绑定族→旋钮"一致）。
- **预期**：散热增强释放 B\*（直到 power-trace 布线成为新瓶颈——绑定迁移 therm_* → route_*）；B 降缓解布线饱和（power 走线需求 ∝ P(B) 线性降）；分离决策（把 power 走线当独立固定开销或忽略）与联合模型（power 走线与信号 lane 共享容量、可权衡）结论分歧。
- **判定标准（方向级）**：
  - D1 单调方向：R_vert 越低（散热越好）→ B\* 不降（monotone non-decreasing）；B_target 降 → 布线利用率不升。
  - D2 绑定迁移：随散热增强，绑定瓶颈从 `therm_*` 迁移到 `route_*`（power-trace 项绑定）——"散热释放的带宽被布线顶住"。
  - D3 耦合可量化（方向级数值即可）：报告 ≥1 个（冷却档, 设计点）的 ΔB\* 释放比例（散热增强释放 X% 带宽）+ 布线利用率对 B 的敏感度（B 降 X% → 利用率降 Y%）。
  - D4 Conservative：分离决策在该参数域下的结论差异如实报告（power-trace 项未绑定时分离≡联合，如实）。
- **模型式（§4 G7，DomainExpert 已拍板 model-ruling §十一 / V5 v5.25，2026-08-21）**：power/GND 走线占用 RDL——**edge/vert 容量 rhs 扣减项** `Σ_{路径经过 e} (B/lr)·L + c_pwr·P_die(B) ≤ cap_e`（P_die(B)=P0+β_P·B+P_dyn 与热方程同源；c_pwr = power 走线 lane 当量系数，W→RDL 占用，参数 YAML；固定 B 下 P_die(B) 常数 → LP 结构不变，insight 7 不受影响；C4 pad 同理，E7 小实验先做 edge/vert）。**E7 阻塞解除**——等 CodeEngineer 实现 → DataSteward 跑 coupling_<params>.csv（D1-D4）。我的 E7 设计（冷却 4 档 × B_target 2-3 档 × β_P>0 × 拓扑 2-3）与拍板模型式匹配，无需改。
- **论文落点**：§5.4 耦合（图 5 扩展或新增"耦合牵制"面板；散热释放 vs 布线饱和曲线）。
- **输出物**：`coupling_<params>.csv`（冷却档 × B_target 档 → B\*/布线利用率/绑定族）。

### E8 — 灵敏度验证：旋钮解锁排名（论文杀手锏）

- **动机（作者 2026-08-21）**：输出 **B\* + 绑定约束族 + 每旋钮解锁量排名**（别的 DSE 只给设计点/Pareto）。目标形态："根据灵敏度分析，改进散热/降功耗，一切就都解决了"。
- **数学框架（作者 A 修正：KKT/包络定理）**：模型**整体非线性**（die 缩放二次项），仅固定 B 子问题是 LP。灵敏度 = 固定 B 可行性 LP 在 B\* 处 **KKT 点**的**包络定理**（对偶乘子 λ 互补松弛定绑定集；B\* 对旋钮 θ 的一阶灵敏度 = 绑定约束方程全微分）：
  `ΔB* ≈ [∂r_i/∂θ − B*·∂(a_i L*+b_i)/∂θ] / (a_i L*+b_i) · Δθ`（= δ_i·[rhs 项 − 系数项]）
  即 δ_i = 1/(a_i L\*+b_i)，旋钮两类：rhs 旋钮（cap/R_vert/A_max）系数项=0；系数旋钮（ppl/lr）系数项主导。**成立条件**：非退化绑定下局部精确；退化/绑定集切换时一阶失效（如实报告）；**不得默认全局成立**。λ 仅作绑定识别（min-ΣL 对偶单位是 ΔΣL/Δrhs，非 ΔB\*/Δrhs）。
- **步骤（小规模、方向级）**：① 2 构型（Mesh(3) 热绑定 + Dragonfly(2,1,1) C4-pad 布线绑定），β 双档（0/0.05）；② B\* 处读 duals 定绑定集 → 闭式 δ_i → 旋钮解锁量 κ_j；③ 榜首旋钮小扰动（+5%）重解 vs 一阶预测。
- **判据（方向级）**：S1 绑定集一致+单调；S2 一阶方向正确、误差<20%；S3 排名工程合理（含反直觉：布线容量非首动）；S4 处方因点/因参数域而异；S5 Conservative（非绑定=0、离散旋钮设计点对比）。
- **数据路径**：有限差分（**step/B\*<1%**：β>0 档 B\*≈600 用 step=2）；max-B LP 精确对偶留附录。
- **结果（DataSteward 2026-08-21，sensitivity_ucie-32g.csv）**：热绑定一阶误差 **0.2%**（ppl -1%→+1.11%/-5%→+5.31%；β=0 时 ppl 榜首 +3.63%，β=0.05 时 R_vert +6.10% > beta_P +4.57%——**排名参数域相关**）；布线绑定 = **C4 布局结构旋钮**（c4_pitch 离散 -25%、lanes_per_mm 非解锁——设计点对比非边际扰动）；旋钮集按绑定族匹配（route_c4pad→C4 布局 / therm→R_vert·beta_P·ppl / edge·vert→lanes_per_mm）。
- **表 X / 图 6**：表 X = 设计点 × 旋钮解锁量（弹性 per 1%）+ 绑定族标注；图 6 = 解锁量条形图 + E2 实证双面板。**SensitivityQuery 暂不建**（现有 duals + 有限差分够）。
- **阻塞**：E7 完整版 + E8 终跑（step=2、双 β 档、校正旋钮清单）待 CodeEngineer power_trace 稳定提交。
- **输出物**：`sensitivity_<params>.csv`（旋钮/δ_i/κ_j/排名/一阶 vs 实测）。

### EC — 内部良心检查：die 缩放（α_d, β_P ≠ 0）可行性对 B 的单调性（**不上论文台面**）

- **目的**：V5 §5.3/§9 待定案——二分搜索的前提是"可行性对 B 单调"；默认 α_d = β_P = 0 时严格成立（低 B 面积约束为松上界，可加无逻辑硅）；启用 die 缩放后需验证。这是内部验证，不写进论文（INSIGHT_READING 二.4）。
- **变量**：α_d ∈ {0, 0.01, 0.1} mm/Gbps、β_P ∈ {0, 0.05, 0.2} W/Gbps 网格（9 组合）；B 轴网格（在 B\* 附近取点，覆盖低 B 到不可行区）；构型：Mesh(2)/Mesh(3) × ucie-32g。
- **步骤**：对每 (α_d, β_P)，沿 B 网格调 `FeasibilityQuery`（`DieParams` 已支持 alpha_d/beta_p，test11 有 rhs 锚点），记录 feasible(B)。
- **预期**：(0,0) 下严格单调（低 B 恒可行）；非零组合验证单调或记录反例。
- **判定标准（可测，内部）**：
  - V1：(0,0) 下 feasible(B) 单调降——不存在 feasible(B1)=false 且 feasible(B2>B1)=true 的反转。
  - V2：非零网格出现反转时，记录 (α_d, β_P, B1, B2) 组合上报 master（内部），不进论文。
  - V3：低 B 侧恒可行（B→0 可行），与"面积约束为松上界"叙事一致。
- **可行性**：✅ `FeasibilityQuery` + `DieParams` 接口齐（test11 锚定 rhs 缩放正确）；单调性扫描脚本已完成（DataSteward，`exp/run_monotonicity.py`）；α_d/β_P 档位由脚本 `dataclasses.replace` **程序化覆盖**（**未动共享 YAML**，扫描脚本自带档位值 → 可复现；无需独立 YAML 档位文件）。
- **输出物**：`monotonicity_scan.csv`（内部）；结论进内部报告给 master。

## 3. 评测报告规范（按 ccf-statistics）

| 项 | 规范 | 依据/理由 |
|---|---|---|
| 基准集 | 拓扑 11 种 × 参数组 4-6 组 × 场景 2-3；`n` = (拓扑, 参数组, 场景) 组合，逐组合报告，不选择性汇总 | L1：独立单位 = 构型组合；当前求解链无随机源 |
| 归一化 | B\* 绝对值（Gbps）逐构型报告；比率类（衰减比/上推比/严格度比）以基线为分母（baseline=1.0） | L1：baseline 在分母；insight 2 比较前提同端口数同设置 |
| 聚合 | 比率类跨拓扑用**几何均值**（Fleming & Wallace：归一化分数不取算术均值）；绝对量报每值 + 中位数/范围（算术均值须说明理由） | L1 强制 |
| 消融 | 每个核心设计点有消融证据：三层实体/跨层耦合（E3 阶梯）、约束严格度（E4）；组合效果有分项支撑 | L1/L4 |
| 公平性 | 基线不弱化：分离决策基线（E3B 定案形态）、无 DSE 基线（固定 B_target 二元筛选）；全部构型同参数/同求解器/同收敛容差 | L1：基线对等 |
| 双面评估 | Progressive（E1 区分度、E2 单调、E4 上推）+ Conservative（E1 C3/C4、E3 C4、E4 C3、E6 C3）缺一不可 | L1 Heiser "Need both!" |
| 异常值/排除 | 预定义排除：`perf` 场景 B 无界（作参考列不参与排名，注明原因）；求解失败/超时写入 error 列并说明；子集排除逐个解释 | L1 变体 2 |
| 方差/重复 | 当前 LP 确定性 → 单次求解即可，报告版本锁定替代重复运行；若引入随机化（启发式基线）→ 每配置 ≥ 3 seed，报 mean ± s.d. | L1：至少标准差 |
| 可复现 | 参数唯一源 `config/params/*.yaml`；记录 python/numpy/cvxpy 版本（实测 cvxpy 1.9.2，CLARABEL）与 git commit；输出命名规范（`matrix_<params>.csv` 等）；随机化组件固定 seed 并报告 | L1/L4 |
| 数据口径红线 | **`exp/output/` 2026-08-18 数据集不可引用**（Windows 机器生成、早于 V5 定稿与 Valiant 包络数值修正，同组合 B\* 差 350 倍）；论文所有数字按当前代码全量重跑（跑前清混合年代缓存）；正式输出附加 git 短 hash + params 名锁定口径（DataSteward 定案） | 可追溯原则 |
| 软件/版本 | Python ≥ 3.9（实测 3.13）、numpy、cvxpy 1.9.2、pyyaml；求解器 CLARABEL/HIGHS/OSQP/SCIPY/SCS | 如实报告 |

**审计表（每面板一行；E1/E6/EC 数据已产出，回填依据 `.dsh/team/artifacts/data-report-e1-e5-e6-ec.md`，git 46833c1）**：

| 面板 | 基准集与版本 | n（组合数） | 归一化基准 | 几何均值口径 | 误差/区间定义 | 重复次数 | 状态 |
|---|---|---|---|---|---|---|---|
| 图 3 包络（**概念图，非实验**——包络不变是构造保证，作者定案不设实验/判据；图位保留概念示意） | — | — | — | — | — | — | 不适用（概念图） |
| 图 4 排序 | 拓扑 11 × 参数 3 | 逐组合 | B\*（同端口数组内） | 比率类几何均值 | 不适用（确定性） | 1 | ✅ 数据齐（C2 ρ=1.000、C3 单调 PASS；C1 已修订——4 端口组同构例外；图 4 须标注热主导语义） |
| 图 5 耦合 | 拓扑 9 × 场景 5+（`+wiring`/`+area`）+ E7 耦合面板 | 逐组合 | B\*_bump 档 | 衰减比几何均值 | 不适用 | 1 | **E3B 双阶段定稿**（v1 等价性 ✅ 附录 + v2 C3' ✅ 10/72 分歧 + C4' ✅ 39 行）+ **E7 耦合牵制面板 ✅**（power 走线 c_pwr 0→2→10：685→490→295；散热零释放 R_vert 恒 490——被 power 布线顶住；降功耗 +40% 解锁）——§5.4 数据齐 |
| 图 6 灵敏度（升级为解锁量条形图 + 表 X，DomainExpert sensitivity-design.md v0.3 KKT/包络定理） | 旋钮 × 解锁量（E8，2 构型）+ E2 knob_matrix 实证面板 | 逐旋钮 / 逐组合 | 弹性 ΔB\*/B\* per 1% 旋钮（κ_j；λ 绑定确认） | 不适用（条形排名） | 不适用 | 1 | ✅ **E8 定稿**（step=2 一阶误差 ≤0.7%；热绑定→ppl/R_vert 榜首、布线饱和域→c_pwr 榜首——per-point prescription；表 X D1-D4 回填；E2 实证面板） |
| 规模曲线 | Mesh/Torus n=2..6 | 每规模 1 | 内部对照 | 不适用 | 不适用 | 1 | ✅ 数据齐（迭代 8≈log2(249.5)；Mesh 0.05→2.29s / Torus 0.04→7.07s 多项式轮廓） |
| 耦合牵制（E7） | 拓扑 2-3 × 冷却 4 档 × B_target 2-3 + c_pwr 试点 | 逐组合 | 无（ΔB\* 释放比例） | 不适用（方向级） | 不适用 | 1 | ✅ **数据齐**（轴 1 零依赖 + 轴 2/3 power 耦合完整版，附录 E）：c_pwr 0→2→10 → B\* 685→490→295；降功耗 +40% 解锁；散热增强零释放（被 power 布线顶住）；D1/D3 ✅、D4 Conservative ✅（耦合域=布线饱和域）——§5.4 耦合牵制面板数据齐；c_pwr 物理取值待参数评审 |
| 灵敏度（E8） | 2 构型（therm 绑定 + wiring 绑定） | 逐旋钮 | 无（κ_j 解锁量/一阶 vs 实测） | 不适用（方向级） | 不适用 | 1 | 🚧 **待 SensitivityQuery 决策**（duals 现有；数学/定位见 sensitivity-design.md；run_sensitivity.py 待 DataSteward） |

## 4. 可行性评估与缺口上报（Gate③ 素材）

> 缺口格式（DomainExpert 定案）：描述 + 影响实验/insight + 是否阻塞正文 + 建议。Gate③ 例会逐条定夺是否建 CodeEngineer。
> **Gate③ 裁决回执（DomainExpert 主持，master 暂定可推翻，2026-08-20）**：G1 执行中（DataSteward 已接令）；G3 ✅ DataSteward 实现分离基线（exp 层，**不需要 CodeEngineer 进场**）；G4 ~~暂定限缩论文 claim~~ **已被作者推翻（V5 v5.21，2026-08-20）：布线 (2d)/面积 (2f) 一级化、纳入主线，CodeEngineer 接入中**（§4 G4 行已更新；§5.4 由等价性验证改回"分歧计数 ≥ 1"）；G2 暂定**补**（master 放行 CodeEngineer 进场做双旋钮场景参数化或 P_peak(B) 开关，待 DataSteward 首批实验跑完、资源空闲时创建；E4 先用场景近似不阻塞；冷却变体仅预研演示、非同一旋钮）；G5 不阻塞；G6 定案不做（可选附录，环境无 MILP 求解器）。

| 编号 | 描述 | 影响实验/insight | 阻塞正文 | 建议 | 状态 |
|---|---|---|---|---|---|
| G1 | 无 | — | 否 | E1/E6/EC 直接由 DataSteward 执行 | **执行中**（DataSteward 已接令） |
| G2 | 要求旋钮（R_peak 仅出入口峰值）与约束旋钮（C_rated 额定功耗）无模型/场景实现（V5 §0.1 固定最严档） | E2（§5.5 灵敏度，正文）、E4 放宽档 | **是**（§5.5） | 模型缺口，**倾向补**（DomainExpert 预判）：CodeEngineer 场景参数化或 P_peak(B) 开关；实现成本 Gate③ 评估。**近似预研**：冷却变体 `ucie-32g-air`/`ucie-32g-microfluidic`（R_vert 2.5 vs 0.4）可作约束悲观度参数级演示（非同一旋钮，不作正文替代） | **✅ 实现完成（CodeEngineer git 5008ed0，EvalDesigner 验收 5/5，test18 全绿）**；DataSteward 出 knob_matrix 数据中；约束旋钮可测效果依赖 β_P>0（预研 490/11211/33627 确认）；§5.5 正文依赖数据回填 |
| G3 | 分离决策基线无实现（性能定 L → 独立判 bump/热/几何 → 可行域交集） | E3B（§5.4 耦合 vs 分离，正文） | **是**（§5.4 对比部分） | 优先 DataSteward exp 层实现（顺序解多次 LP，非新 query）；接口受限再上报 CodeEngineer | **Gate③ ✅（已回执）**：DataSteward 实现（exp 层，已接令）；**不需要 CodeEngineer 进场** |
| G4 | ~~C4/WiringGrid 未接入、限缩 claim~~ **V5 v5.21 作者推翻：布线 (2d) edge/vert/pad 三维容量 + 面积 (2f) A_die≤A_max 一级化，纳入主线**（CodeEngineer 接入 `build_scenario` 中；C4 电源 (3c)+sub 热 (3d) 仍为规范级） | E3 阶梯（`+wiring`/`+area` 级）+ E3B 分离基线（布线/面积独立判定）——**E3B 重设计核心** | **是**（§5.4，待接入完成） | CodeEngineer 接入 wiring/area 进 build_scenario（🚧 进行中）；DataSteward 扩展 run_sep_vs_joint 为布线/面积版并重跑 | **纳入主线（接入中）** |
| G5 | 分割比 ρ 旋钮（一个大 interposer vs 多个小 interposer）未引入（V5 §9） | 不涉及本期 7 实验；属模型演进 | 否 | 按 V5 §9 待定案推进，另行上报 | 不阻塞 |
| G6 | MILP/启发式对比基线（LP vs MILP 解质量+时间） | E6 可选附录 | 否（DomainExpert 定案默认不做；环境无 MILP 求解器） | **默认不做**，标"可选附录"；如需则另议（建 CodeEngineer + 装求解器） | 定案不做 |
| G7 | **power/GND 走线占用 RDL 项**（V5 v5.21 声明语义，实现缺失） | E7（功耗—散热—布线/性能耦合演示，作者核心轴） | **是**（E7 前置，已解除） | **已拍板**（DomainExpert model-ruling §十一 / V5 v5.25）：edge/vert 容量 rhs 扣减 `Σ(B/lr)·L + c_pwr·P_die(B) ≤ cap_e`（c_pwr 参数 YAML；C4 pad 同理后补）→ CodeEngineer 实现 → DataSteward 跑 coupling | **已拍板，CodeEngineer 实现中** |

## 5. artifact / 数据可用性素材（按 ccf-data）

### 5.1 库存与 access route

| artifact | 内容 | access route |
|---|---|---|
| 代码 | `src/`（LP 引擎、queries、models、builder）、`topology/`、`physical/` | public repository |
| 参数/配置 | `config/params/*.yaml`、`config/problems/*.yaml`（唯一参数源） | public repository |
| 实验脚本 | `exp/run_matrix.py`、`run_ledger.py`、smoke、新增扫描脚本 | public repository |
| 结果数据 | `exp/output/*.csv/json`（matrix/ledger/envelope/scalability/knob 等） | public repository |
| figure source data | 图源数据表（图 3 包络为概念图、无实验数据） | public repository（与结果数据同 release 或 Supplementary） |
| 第三方受限数据 | **无**（物理参数来自公开标准 UCIe 1.1/2.0、OIF-CEI-112G-VSR——引用而非重分发） | 不适用 |

### 5.2 仓库与标识符计划

- GitHub 仓库（wafer-dse）→ **Zenodo DOI-backed release**（版本化 tag，如 `v0.1.0-experiments`）；投稿前完成 release 与 DOI。
- 结果数据 + figure source data 与代码 release 同 DOI 记录（README 内 file manifest 逐文件说明列名/单位/缺失值/生成脚本）。
- 复现说明：README 含依赖（python ≥ 3.9、numpy、cvxpy ≥ 1.9、pyyaml）、`make matrix/ledger/smoke/run` 命令、预期运行时间、配置矩阵与 Methodology 一致。
- **数据口径锁定（DataSteward 定案）**：正式输出附加 git 短 hash + params 名；重跑前清 `exp/output/.cache`（混合年代缓存）；2026-08-18 数据集不入库、不作复现依据。

### 5.3 声明草稿（ready-to-paste + 中文核对）

**Data Availability（英文，投稿前回填方括号字段）**：

```text
The datasets generated in this study are available as follows: experiment result tables
(B* rankings, ablation ladders, envelope invariance, sensitivity, and scalability sweeps)
and figure source data in [Zenodo] under [DOI]; the source code, parameter configuration
files (config/params/*.yaml), and experiment scripts are available at [GitHub repository]
under [DOI-backed release vX.Y]. Reproducibility instructions, software versions, and
expected runtimes are described in the repository README. No third-party restricted
datasets were used; physical parameters are taken from public interconnect standards
(UCIe 1.1/2.0, OIF-CEI-112G-VSR) and cited in the paper.
```

**中文核对**：生成的实验数据与图源数据 → Zenodo（DOI）；代码/参数/脚本 → GitHub 版本化 release（DOI）；README 写明复现步骤与版本；无第三方受限数据；物理参数来自公开标准并引用（不重分发）。待作者确认：最终仓库 URL、DOI、release tag、是否参加 ISCA AE。

**Code/Artifact Availability（AE 场景）**：

```text
The source code and configuration files for the proposed two-layer DSE are available at
[Repository] under [DOI], with a versioned release [TAG]. The artifact includes the LP
engine, topology/physical parameter files, experiment scripts (run_matrix, run_ledger,
envelope and scalability sweeps), and result tables, and was evaluated with Python
[version], NumPy [version], and CVXPY [version] (CLARABEL).
```

### 5.4 AE 描述素材（ISCA AE：Available/Functional/Reproduced 徽章）

- 环境：Python ≥ 3.9（实测 3.13）、numpy、cvxpy 1.9.2（CLARABEL）、pyyaml；纯 CPU，无 GPU。
- 命令：`make smoke`（~30s 冒烟）、`make matrix PARAMS=ucie-32g`（全量矩阵）、`make ledger`、`make run PROBLEM=config/problems/xxx.yaml`。
- 预期运行时间（DataSteward 确认）：单 BmaxQuery 秒级（Mesh(2) 8 次 LP、~0.02s/次）；全量 run_matrix = 88 次 BmaxQuery，小拓扑 <1s/组合，Mesh(4) 可达数分钟-十分钟级/组合（单独排队）；全量矩阵预计分钟级。
- 配置矩阵与 Methodology 一致（几何均值口径、归一化基准、同端口数分组——§3 表）。

### 5.5 未决字段（AUTHOR_INPUT_NEEDED）

- 最终仓库 URL / DOI / release tag（投稿前定，不编造）。
- 是否参加 ISCA AE 及徽章范围（master/用户决策）。
- 数据报告（DataSteward）产出后：审计表回填 n/数值。

### 5.6 协作提醒（非本职，转达用）

- **MFIT 引文已核验修正并闭环（2026-08-20）**：V5 §10 原引用 "MFIT（Zhang et al., ACM TACO 2025）"有误，正确为 **Pfromm et al., *MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures*, ACM TODAES（DOI 10.1145/3765905；arXiv:2410.09188），完整 9 位作者：Lukas Pfromm, Alish Kanani, Harsh Sharma, Parth Solanki, Eric Tervo, Jaehyun Park, Janardhan Rao Doppa, Partha Pratim Pande, Ümit Y. Ogras**（DBLP 第一源 + ccf-ref-verifier 三源核验）；另 Feng & Ma Switch-Less Dragonfly 应为 **SC 2024** 非 ATC 2024。**闭环状态（三处一致）**：V5 §10 由 DomainExpert 拍板（**V5 v5.20**，代码 docstring 同改）；bib 侧由 LiteratureSearcher 修正（`paper.bib`）；本文档 E3B 已按修正后引文撰写。无遗留。

## 6. consult-team 记录（Phase 2 开工前）

- 咨询：DomainExpert（5 条，**已收齐验收**）；DataSteward（其 3 问已答 + 我的 5 问/追问 (a)-(e) 已由其 `data-inventory.md` 覆盖，**已收齐**）；LiteratureSearcher（4 条，**已回 + Phase 1 交付已落盘**——`benchmark-matrix.md` / `gap-evidence-chain.md` / `related-work-draft.md` / `paper.bib` / `bib-verification-report.md`；基线引文、RapidChiplet 铁证、部分覆盖警示已并入本文档 E3B/E6/E7）。
- 边界确认：实验设计文档归 EvalDesigner；执行归 DataSteward；缺口上报 DomainExpert（Gate③）；正文归 DomainExpert+WritingPolisher——无冲突（DomainExpert 确认）。
- 关键采纳（DataSteward 数据侧）：legacy 08-18 数据不可引用（350× gap）；LP 确定性无需 seed、git hash 锁定口径；包络 `envelope_L` 无需新 query；run_matrix 全量 88 次 BmaxQuery、Mesh(4) 重拓扑单独排队；**11 组 YAML 已接线**（run_matrix 改 `load_yaml_params` 全量 16 组，每组合 try/except 落 error 列不中断）；α_d/β_P 由 EC 脚本程序化覆盖（未动共享 YAML）。
- 关键采纳（LiteratureSearcher 引文侧）：分离链条 = BookSim→HotSpot/MFIT→FPIA/RapidChiplet→RedHawk 链式判定；RapidChiplet 原文铁证（thermal 外挂 HotSpot）；TickTock/Chen/Yu 部分覆盖须 "xxx vs xxx" 措辞；MFIT 引文修正为 Pfromm TODAES（bib 侧已改，V5 §10 文本侧归 DomainExpert 拍板）。
- 未获得：无（Gate② 材料 `benchmark-matrix.md` 已落盘，待 master 按 `gate2-review-template.md` 审查）。
- 结论：信息已齐（DomainExpert 全绿 + DataSteward 盘点 + 代码自查），文档已产出。

## 7. 待定项

> 定稿声明（2026-08-21，作者纪律广播）：本文档**即定稿**——不再新增实验/判据/调研；只做 Evaluation 章判据通过/失败陈述（见附录），审稿发现问题再补。可做可不做的不做。

- [x] DataSteward (a)-(e)：已由其 `data-inventory.md` 覆盖（矩阵时长/确定性/ledger 可跑/包络接口/planned 场景）。
- [x] **E1/E6/EC 数据已产出**（DataSteward，git 46833c1，`.dsh/team/artifacts/data-report-e1-e5-e6-ec.md`）：E1 C2 ρ=1.000/C3 单调 PASS、C4 热主导如实报告（therm≈bump 4%）；E6 迭代 8≈log2(249.5)、规模-时间多项式轮廓；EC 18 组合零反转（内部，二分前提稳健）。E1 C1 已修订（4 端口组图同构例外 + 同构一致性为有效性检验）；图 4 热主导语义标注已加。
- [x] G2/G3/G6 Gate③ 裁决回执（DomainExpert 主持，master 暂定可推翻，2026-08-20）：G1 执行中 / G3 DataSteward 实现（无需 CodeEngineer）/ G2 补（master 放行 CodeEngineer，创建条件已满足）/ G6 定案不做——落盘 §4。
- [x] **G4 裁决被作者推翻（V5 v5.21，2026-08-20）**：布线 (2d)/面积 (2f) 一级化、纳入主线，CodeEngineer 接入 `build_scenario` 中（🚧）——限缩 claim 撤销，§4 G4 行已更新。
- [x] **E3B v2 C3' 终判 ✅ 通过**（fixed_paths 重跑，缓存键修复 c5aa79f 后冷跑修正，2026-08-21）：10/72 分歧（真分歧 = 布线饱和域 lanes=100：Mesh(3) 0.154/Torus(3) 0.190/KaryNCube 0.352·0.266 + 默认域 KaryNCube(2,3) 0.087；旧"Mesh(3) 默认域 0.80"系缓存污染已废）；机制=路径多样性（固定首路径拥塞 vs 联合绕行）；C4' ✅ 39 行 route/area 绑定；单调性抽查 PASS。**insight 4 双阶段主张成立，§5.4 定稿**（v1 等价性边界附录 + v2 分歧实证正文 + C4' 真绑定识别）；§九 限缩预案未触发。
- [x] 11 组 YAML 接线（run_matrix 全量 `load_yaml_params` 16 组，已实测 ucie-12g 可跑、trad-air-ucie-std 错误正确落 error 行）；α_d/β_P 档位由 EC 脚本程序化覆盖（未动共享 YAML，无需独立档位文件）。
- [x] **CodeEngineer（G2 双旋钮）交付完成**（git 5008ed0，run_all 19/19 全绿，test18 双旋钮断言；EvalDesigner 验收 5/5 通过；预研 490/11211/33627 复跑一致）。knob_matrix_<params>.csv 已产出（附录 C）。
- [ ] **E7（作者核心轴，2026-08-21）**：功耗—散热—布线/性能三向耦合演示（设计已落盘 §2 E7，方向级判据 D1-D4，小规模；三轴：散热↔带宽✅可跑 / 降性能↔布线饱和 / 三方牵制相图）——**G7 已拍板解除**（DomainExpert model-ruling §十一/V5 v5.25：edge/vert rhs 扣减 c_pwr·P_die(B)）→ CodeEngineer 实现 → DataSteward 跑 coupling_<params>.csv。
- [x] **E8（作者补充指令，灵敏度杀手锏）**：验证完成闭环（SensitivityQuery 暂不建；细步长有限差分 step=20-50）——热绑定一阶误差 0.2%（ppl -1%→+1.11%/-5%→+5.31%）、布线绑定结构旋钮例外（c4_pitch 离散、lanes_per_mm 非解锁）；S1-S5/D1-D4 全回填、表 X 数据齐（sensitivity-design.md §3.2 含离散旋钮例外）；图 6 解锁量条形图 + E2 实证双面板数据齐。
- [x] **布局算法支撑（作者【4】，LiteratureSearcher 交付 2026-08-21）**：layout-algorithms-note.md + paper.bib +10 条布局引用（seqpair/TAP2.5D/ATPlace2.5D/TDPNavigator/ChipletPart/interposer floorplan/2.5D EDA 综述等），related-work §3.2b 已并入；布线资源引用（liu2014interposerfloorplan、chen2025survey2p5d）已并入 E3B/E7。
- [x] **E3B 旧判据修订（q-aa6aa76c 等价性验证）**：已被 E3B 重设计（V5 v5.21）取代——旧等价性结论保留为"无布线/面积子集"边界刻画（附录素材），C3 已恢复"分歧计数 ≥ 1"。
- [x] LiteratureSearcher 对标矩阵全文已落盘并核对（`benchmark-matrix.md` / `gap-evidence-chain.md` / `related-work-draft.md` / `paper.bib` / `bib-verification-report.md`，2026-08-20）：矩阵结论与本文档一致（insight 4 部分覆盖需限定 / insight 6 先例=验证 / insight 7 部分覆盖不引复杂性战争）；基线引文、RapidChiplet 铁证、CHARIOT/FireLink/FPIA 启发式对象已并入 E3B/E6/E7；Gate② 材料就绪，待 master 审查。
- [ ] 投稿前回填 §5.3 方括号字段（仓库/DOI/tag/AE 范围）。

---

## 附录：判据通过/失败陈述（供 WritingPolisher 写 Evaluation 章）

> 2026-08-21 定稿版。每实验：判据 → 通过/失败 → 一句话证据。审稿发现问题再补。

| 实验（论文节） | 判据结果 | 一句话证据 |
|---|---|---|
| E1 排序（§5.3） | C1 ✅（4 端口组图同构例外，同构一致性作有效性检验）；C2 ✅ ρ=1.000；C3 ✅ 场景单调；C4 ✅ 热主导如实 | 同端口数组 B\* 有区分度；跨参数组排序秩相关 1.0；加约束 B\* 不增；therm 档≈bump 档 4% |
| E2 双旋钮（§5.5） | M1 ✅ / M2 ✅ / M3 ✅ | 单调逐构型成立；要求放宽上推 GM≈2.64×、约束放宽（β_P>0）17.9-28.6×；4 档偏序无交叉 |
| E3 耦合（§5.4） | v1 ✅ 等价性（诚实基线）；v2 C3' ✅ 10/72 分歧（布线饱和域 lanes=100 + KaryNCube 默认域）；C4' ✅ 39 行真绑定；C5' ✅ 归因 | 无布线/面积子集分离≡联合（附录）；固定首路径拥塞 vs 联合绕行（强分歧在布线饱和域）；Dragonfly 布线先于 therm |
| E6 规模（§5.6） | C1 ✅ / C2 ✅ / C3 ✅ | 迭代 8≈log2(249.5)；Mesh 0.05→2.29s、Torus 0.04→7.07s 多项式轮廓；开销如实 |
| E7 耦合牵制（§5.4 面板） | D1 ✅ / D2 ✅ / D3 ✅ / D4 ✅ | power 走线 0→2→10 → B\* 685→490→295；降功耗 +40%；散热增强零释放（被布线顶住）；耦合域=布线饱和域如实界定 |
| E8 灵敏度（§5.5 表 X） | S1-S5 / D1-D4 全 ✅ | 一阶误差 ≤0.7%；热绑定→ppl/R_vert、布线饱和→c_pwr 榜首；"改走线非首动，降功耗/提散热真解锁" |
| EC（内部，不上论文） | V1-V3 ✅ | die 缩放 18 组合零反转，二分前提稳健 |
