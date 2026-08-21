# §4 Model —— 方法章草稿（Phase 3, v0.1）

> WritingPolisher 草稿，2026-08-21。依据：paper-skeleton §4.0-4.4、V5（经书，唯一权威模型文档）、contributions C1-C4、insight-orchestration 落点表、DomainExpert q-faeb99a1 术语/框架定案、paper.bib（LiteratureSearcher 核验版）。
> 行文风格：参考 Shouyi Yin 团队——平实克制、证据贴近主张、模块三要素（motivation → mechanism → role）清晰。
> 段落前 `[insight n]` 标注 = Gate④ 纪律检查用（成稿时删除或转注释）。
> 技术细节按道术分层：LP 完整表述 → 附录 A；二分+复杂度 → 附录 B；Birkhoff–von Neumann 顶点论证 → 附录 C。
> 待办（不阻塞）：C2-C4/sub 热为规范级约束，§4.2.2 末尾已按 DomainExpert 定案句式标注诚实边界。
> 2026-08-21 更新：**DomainExpert 技术复核通过**（与 V5（经书）严格一致，无技术修改要求）；§4.2.2 耦合案例**正式措辞已定稿替换**（占位段移除）；图 2 引用位补齐（figure-intents v0.2 对齐）。
> 2026-08-21 更新：**作者 round 21+ B 风格自查**——移除 §4.0 一处错位引用（Pareto 句不引 Chen）；§4.2.3 去除 RNB 重复（术语克制，§4.2.1 已定义）；全文朴素优先、矩阵表示清晰（V5 §2 标杆）。
> 2026-08-21 更新：**V5 经书/释经拆分对齐**——模型内容引用改指 V5（经书，锚点 §1 符号表/§2 (2d)(2f)/§7.3 包络未变）；模型性质（非凸/多项式全局最优）论证见 MODEL_PROPERTIES.md；版本历史见 V5_CHANGELOG.md。

---

## 4. Model

### 4.0 Two-Level DSE Overview

**[insight 1, 4, 6]** We frame the design of a wafer-scale switch as a two-level design-space exploration (DSE) centered on a single interposer: the object of study is one interposer's design—its dies, their interconnects, and its thermal/electrical boundary to the substrate. The outer level enumerates the discrete configuration axes—topology family, layout, packaging process, and interconnect standard—reusing the established chiplet DSE flow \cite{rapidchiplet2025,firelink2025,fpia2024}. The inner level tests each enumerated configuration with a single feasibility model that couples performance, thermal, electrical, and geometric constraints, and returns, for every feasible configuration, its optimal rated bandwidth $B^*$ (Fig.~\ref{fig:overview}). The two levels communicate through a physical-parameter interface and are otherwise independent: the outer level supplies candidate configurations; the inner level returns a scalar quality measure per candidate.

The split is deliberate. The outer level inherits the combinatorial hardness of layout, wiring, and topology selection; chiplet DSE tools already manage this enumeration, and we reuse rather than reinvent it. The inner level is where the coupling lives: for a fixed configuration, thermal, electrical, geometric, and performance decisions must be made jointly, and this subproblem admits a polynomial-time global optimum (\S4.3). Screening, not optimizing, is the purpose of the whole pipeline: the DSE outputs a ranked set of feasible configurations, not a Pareto surface. The performance envelope of each configuration is computed independently of the physics (dashed box in Fig.~\ref{fig:overview}), reflecting its topological invariance (\S4.2.1).

### 4.1 Outer Level: Discrete Enumeration

**[insight 1]** The outer level enumerates the discrete design space: topology family (mesh, torus, $k$-ary $n$-cube, dragonfly \cite{kim2008dragonfly}), the layout of dies and interposers, the packaging process, and the interconnect standard (UCIe for die-to-die links, SerDes/OIF-CEI for inter-interposer links). Each enumerated point is a concrete configuration: a set of dies and interposers, a typed link set, and a routing strategy. Because this is a standard enumeration over mature chiplet DSE flows \cite{rapidchiplet2025,firelink2025,fpia2024}, we make no claim about the complexity of the discrete layer itself; its job is to feed candidates to the inner screen.

### 4.2 Inner Level: Feasibility Model for a Given Configuration

The inner level answers two questions for one configuration: is it feasible, and what is the largest rated bandwidth it can sustain? Both answers come from a single model that couples four constraint families—performance, thermal, electrical, and geometric.

#### 4.2.1 The Expansion-Ratio Envelope: Decoupling Performance from Physics

**[insight 6]** The central difficulty in coupling performance and physics is that link bandwidth is simultaneously a performance quantity and a physical quantity: more bandwidth means more lanes, more area, more power, and more heat. Naively, this entangles the traffic model with every physical parameter. Our key move is to strip the rated bandwidth out of the per-link bandwidth: link $e$'s bandwidth is modeled as $B \cdot L_e$, where $L_e$ is the link's \emph{expansion ratio}—the factor by which link $e$ must be overprovisioned relative to the rated bandwidth. The \emph{expansion-ratio envelope} $\mathbf{L}^* = (L^*_1, \dots, L^*_{|\mathcal{E}|})$ is the minimum per-link expansion ratio a topology must provision for a given performance requirement.

Under a static oblivious routing strategy with uniform splitting \cite{valiant1981universal}, the load on link $e$ is a linear function of the traffic matrix $\mathbf{D}$: $L_e(\mathbf{D}) = \sum_{(i,j)} c^e_{ij} D_{ij}$, where $c^e_{ij}$ is the fraction of OD-pair $(i,j)$ traffic that crosses $e$. The envelope entry $L^*_e$ is the worst-case load over all admissible traffic—the maximum of $L_e(\mathbf{D})$ over the Birkhoff polytope of doubly stochastic matrices. By the Birkhoff–von Neumann theorem \cite{birkhoff1946tres,vonneumann1953}, the vertices of this polytope are permutation matrices, so the worst case is a permutation of sources to destinations—exactly the worst case behind a QoS guarantee (rearrangeably non-blocking, RNB) \cite{chang2000infocom,mckeown1999tcom}. Each $L^*_e$ therefore has a clean combinatorial reading: the maximum, over permutation matrices, of the traffic that crosses $e$ (Appendix~C).

Crucially, the envelope depends only on the topology, the routing strategy, and the performance requirement—not on $B$, and not on any physical parameter. The performance model is solved once, offline, and the physical layer consumes the envelope as fixed per-link lower bounds $B \cdot L^*_e$. This is the performance–physics decoupling bridge: the expansion-ratio envelope is a topological invariant—it depends only on the topology, routing, and performance requirement, independent of $B$ and of physical parameters. The worst-case-load analysis follows the lineage of oblivious routing \cite{valiant1981universal,racke2002focs,azar2004jcss}, which we treat as verification rather than competition (\S3.3).

#### 4.2.2 Three-Layer Physical Model with Cross-Layer Coupling

**[insight 4]** The physical side mirrors the wafer-scale packaging hierarchy with three entities (Fig.~\ref{fig:hierarchy}): dies, the interposer(s) that aggregate them, and the substrate that interconnects interposers. Dies within an interposer connect through die-to-die (D2D) links (UCIe or on-die); interposers connect across the substrate through inter-interposer (I2I) SerDes links that leave the interposer through C4 bumps. The model tracks, per entity, the quantities that jointly bound feasibility: power $\mathbf{P}$, temperature $\mathbf{T}$, area, and interconnect resources.

All four constraint families are decided in a single feasibility model rather than factor by factor. The model is organized in three segments. The \emph{die segment} couples D2D lane counts to die power, interposer wiring, and a coupled die/interposer thermal field; the \emph{I2I segment} couples I2I lane counts to the C4 budget and the substrate thermal field; and four \emph{cross-layer coupling constraints} $\mathrm{C}_1$–$\mathrm{C}_4$ close the model by defining the shared variables: $\mathrm{C}_1$ allocates the die-side $\mu$bump budget between D2D lanes, I2I lanes, and power bumps; $\mathrm{C}_2$ derives the power-C4 count from the interposer's total power; $\mathrm{C}_3$ aggregates die power into interposer power; and $\mathrm{C}_4$ feeds the substrate temperature back as the interposer's ambient boundary condition. The thermal relation is linear—$\mathbf{G}\mathbf{T} = \mathbf{P} + \mathbf{b}$, with $\mathbf{G}$ a diagonally dominant $M$-matrix—so temperature is a linear function of power \cite{mfit2025}, a fact that keeps the whole constraint set linear in the decision variables for any fixed $B$.

Two constraints deserve emphasis because they are the ones that bind in practice. First, \emph{interposer wiring} is a first-class constraint: power/ground and signal traces share the interposer's redistribution-layer (RDL) resources, and wiring saturation typically binds before the bump budget does. Second, the \emph{die area} has a hard upper bound $A_{\max}$; since die area grows with $B$ as $A_{\text{die}}(B) = (d_0 + \alpha_d B)^2$, the area bound directly caps the rated bandwidth whenever $\alpha_d > 0$. Under these two constraints the coupling between factors is real: a separated decision process that fixes routing paths factor by factor saturates a link's first path, whereas the joint model reroutes around it (\S5.4).

A canonical instance of this coupling runs through power delivery. Power/ground (P/G) traces occupy the same redistribution-layer (RDL) capacity as signal traces; when a die's power demand grows, its P/G routing demand grows with it and can saturate the wiring budget. The designer is then left with two moves: raise the cooling capability, which increases the P/G traces' carrying capacity, or lower the performance target—reduce the rated bandwidth, shrinking the power demand—until the wiring fits. Power, cooling, and wiring/performance thus constrain one another in a closed loop: the cleanest counterexample to the assumption that a DSE can judge power, thermal, and wiring factors independently.

The model specification includes the full constraint set—die-side (power, routing, thermal, area), I2I (C4, substrate thermal), and cross-layer coupling C1–C4. Our implementation and experiments cover the main-model subset (C1, thermal, expansion-ratio envelope, die scaling, routing, area); constraints C2–C4 and the substrate thermal equation are part of the specification whose experimental coverage is future work.

#### 4.2.3 Determining $B^*$: Rated Bandwidth as a Quality Metric

**[insight 2, 3, 5]** $B$ is the decision scalar of the inner model: the rated ingress/egress bandwidth with a QoS guarantee. As long as every port's load stays at or below $B$, the switch delivers non-blocking switching under the envelope (\S4.2.1). The optimal rated bandwidth $B^*$—the largest $B$ a configuration can sustain—is the configuration's quality measure. Unlike a binary feasible/infeasible verdict, $B^*$ quantifies how much design margin a configuration has: under the same DSE settings and the same port count, a configuration with a larger $B^*$ is strictly more capable. Screening thereby becomes a ranking of configurations by a single scalar.

The attainable $B^*$ is a monotone function of two families of choices—the strictness of the performance requirement (e.g., a full QoS guarantee vs.\ per-port peak load) and the pessimism of the physical constraints (e.g., peak-power vs.\ rated-power operating conditions). Stricter requirements or more pessimistic constraints lower the attainable $B$; loosening either raises it. This requirement $\times$ constraint framework gives the designer explicit knobs: a configuration rejected under the strictest setting may become feasible once a requirement is relaxed, and the ordering of configurations by $B^*$ tells the designer which points to argue through next.

For a fixed $B$, feasibility is exactly decidable in polynomial time: the die-scaling terms become constants and every remaining constraint is linear in the decision variables (lane counts, powers, temperatures). $B^*$ is the maximum feasible $B$, located by a logarithmic number of outer iterations (\S4.3; Appendix~B). The complete fixed-$B$ formulation is given in Appendix~A.

### 4.3 Model Properties: Nonconvex, Yet Polynomial-Time Globally Optimal

**[insight 7]** The overall problem—with $B$ itself as a decision variable—is nonconvex: because die area grows quadratically with $B$ ($A_{\text{die}}(B) = (d_0 + \alpha_d B)^2$), the feasible region is not convex in $B$. Yet the problem does not need heuristics. For a fixed $B$, the die-scaling terms become constants and every remaining constraint is linear, so feasibility is exactly decidable in polynomial time; the maximum feasible $B^*$ is then located by a logarithmic number of outer iterations, which the monotonicity of feasibility in $B$ supports (at low $B$ the area bound is slack and the remaining constraints scale linearly). The overall problem therefore admits a polynomial-time global optimum without heuristics. This is the screening philosophy of the framework: rather than assuming NP-hardness and defaulting to heuristics, we keep the inner model in a regime—strict but not over-constrained—where a provably optimal answer is computable (Appendix~B). The outer discrete layer, by contrast, inherits the hardness of layout and topology selection and is handled by the established enumeration flow (\S4.1); we make no complexity claim for it.

### 4.4 Solving and Implementation

**[insight 7, 4]** Solving the model for one configuration reduces to a bounded number of exact feasibility checks. Implementation and experiments cover the main-model subset—C1 (die-side $\mu$bump allocation), die-level thermal, the expansion-ratio envelope, die scaling, interposer wiring, and die-area bounds—evaluated with a standard convex-optimization solver \cite{diamond2016cvxpy} on parameters aligned with UCIe and OIF-CEI specifications \cite{ucie2.0-2024,oif-cei}. The remaining specification-level constraints (C2–C4, substrate thermal equation) are outside the current experimental coverage; we discuss the roadmap in \S6.3. All experiments are deterministic and reproducible from the released repository.

---

## 附录：insight 纪律检查表（Gate④ 用）

| 段落 | 体现的 insight | 检查 |
|---|---|---|
| §4.0 P1/P2 | 1（筛选定位）、4（耦合在单模型）、6（包络独立预解） | ✅ 无技术流水账；二分/LP 不上台面 |
| §4.1 | 1（外层枚举=筛选管道入口）、4（复用成熟流程） | ✅ 声明不 claim 离散层复杂度 |
| §4.2.1 P1-P3 | 6（扩展比联系一切；包络=拓扑不变量） | ✅ 机制简述 + 顶点论证转附录 C；先例=验证一句话 |
| §4.2.2 P1-P3 | 4（多因素耦合单模型联立）、6（包络为输入） | ✅ 布线/面积一级约束（经书 (2d)/(2f)；定案见 V5_CHANGELOG v5.21）为"真正会绑定"的耦合要素 |
| §4.2.3 P1-P3 | 2（B* 量化解质量）、3（B=f(要求,约束)）、5（排序=精调基石） | ✅ 无阻塞仅 QoS 语义；二分细节不上台面 |
| §4.3 | 7（非凸但多项式全局最优、不需启发式） | ✅ 不写"是 LP"；外层 NP-hard 边界声明 |
| §4.4 | 7、4 | ✅ 实现覆盖诚实标注；求解细节转附录 |

## 待办/缺口

- [x] DomainExpert 技术复核（2026-08-21：与 V5（经书）严格一致，无技术修改要求）；§4.2.2 耦合案例正式措辞已按定稿替换（round 21+ 指令【1】闭环）
- [x] 定位聚焦核对：全文对象 = 一个 interposer 的设计（round 21+ 指令【3】），§4.0 已更新；标题已统一 Two-Level（title-candidates.md 2026-08-21）
- [x] FigureArtist 图 1/图 2 语义对齐（figure-intents v0.2：图 1 单 interposer 聚焦 + 包络虚线框 + 筛选定位；图 2 三层实体 + C1-C4 + 三方牵制环）——本稿引用位已按 v0.2
- [ ] EvalDesigner 复核 §4.2.2 末尾"布线/面积绑定"与 §5.4 叙述的一致性；round 21+ 指令【2】"展现耦合影响"实验轴（散热增强释放带宽 / 降性能缓解布线饱和）落 §5 后回填本稿引用
- [ ] 布局算法调研（round 21+ 指令【4】）为 LiteratureSearcher 工作项——调研结论回填 §4.1/§4.2.2 引文后，本稿补 \cite
- [ ] 英文措辞终校（ccf-polishing 第二轮；当前为结构草稿）
