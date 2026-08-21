# Related Work 中稿（related-work-draft）

> **产出**：LiteratureSearcher（Phase 1）
> **日期**：2026-08-20
> **用途**：paper-skeleton §3（Related Work）首稿素材；最终润色归 WritingPolisher，内容边界归 DomainExpert。
> **引用键**：对应 `.dsh/team/artifacts/paper.bib`（全部 DBLP/CrossRef/arXiv 核验；未核验项标"待核实"）。
> **写作纪律**：先例 = 验证而非防先例；"xxx vs xxx"措辞；不写方法章内容。

---

## §3.1 晶圆级系统与晶圆级交换机（Wafer-Scale Systems and Switches）

Wafer-scale integration has moved from a research concept to industrial deployment. Tesla's Dojo trains exascale-scale workloads on a wafer-scale training system built from 25 D1 dies integrated on a TSMC InFO-SoW carrier [dojo2022hc, dojo2023micro]. Cerebras has shipped wafer-scale engines integrating up to ~850K cores and 2.6T transistors on a single wafer, interconnected by an on-wafer mesh fabric [lie2023hcs, cerebras-wse2]. These systems establish that wafer-scale integration is a viable substrate for high-bandwidth, tightly coupled computation.

More recently, wafer-scale networking has emerged as a research direction. Chen, Pal, and Kumar analyze the radix potential of wafer-scale network switches and show that a waferscale switch can support up to 32x higher radix than state-of-the-art switches when only area is considered, but that the actual radix is "limited by a combination of internal bandwidth, external bandwidth, and power density" [chen2024waferscale]—an early, quantitative statement of the physical–performance coupling we formalize. Feng and Ma propose Switch-Less Dragonfly on Wafers, a wafer-scale interconnection architecture that removes switch dies and connects compute dies directly through the wafer-level fabric [feng2024switchless_sc]. Wan et al. explore waferscale switching system architectures and quantify design trade-offs [wan2025architectural]. Yang et al. co-design physical-design (PD) constraints and logical topology for network-on-wafer [yang2025ticktock], and Yu et al. co-explore computing and hardware architecture of a waferscale chip [yu2025cramming].

**xxx vs xxx.** These works analyze specific dimensions—radix limits [chen2024waferscale], architecture alternatives [feng2024switchless_sc, wan2025architectural], PD-aware topology co-design [yang2025ticktock], or computing/hardware co-exploration [yu2025cramming]—for one or a few design points. None provides a design-space exploration (DSE) tool that jointly evaluates thermal, electrical, geometric, and performance constraints across the design space and outputs a quantified, QoS-guaranteed metric; they are single-point analyses or architecture studies rather than early-stage DSE. (待核实: exact coverage dimensions of [yu2025cramming] to be confirmed on full text.)

## §3.2 Chiplet DSE 工具：外层流程的对标基线（Chiplet Design-Space Exploration Tools）

Chiplet-based design has produced a set of mature DSE tools that we adopt as the outer-loop baseline rather than re-inventing. RapidChiplet provides high-level inter-chiplet interconnect (ICI) latency/throughput proxies, trading 0.25%–30.15% accuracy for 427x–137,682x speedup, enabling DSE over "hundreds of thousands of design points" [rapidchiplet2025, rapidchiplet2023arxiv]. FireLink evaluates chiplet designs across power, performance, area, and cost (PPAC) with ID3-based pruning [firelink2025]. CHARIOT explores 2.5D/3D interposer designs via roofline analysis and multi-objective Bayesian optimization over performance and energy [chariot2026]. FPIA performs communication-aware multi-chiplet placement and routing [fpia2024].

**xxx vs xxx.** These tools cover subsets of the coupling chain: RapidChiplet focuses on ICI latency/throughput and states that thermal simulation is provided by external tools (HotSpot), while it "only provides very high-level power, area, and cost estimates" [rapidchiplet2023arxiv]; CHARIOT optimizes performance and energy without thermal in its objective [chariot2026]; FireLink evaluates PPAC without thermal [firelink2025]; FPIA is a physical-design engine for placement/routing [fpia2024]. Thermal modeling itself is served by standalone tools—HotSpot [hotspot2006], 3D-ICE [3dice2010], MFIT [mfit2025]—and thermal-aware placement engines such as ATPlace2.5D [atplace2p5d2024] and TDPNavigator-Placer [tdpnavigator2025] exist, but none is coupled to network-performance DSE. We therefore treat these tools as the discrete outer layer (topology × layout × packaging × interconnect enumeration) and supply the missing inner layer: a single-model feasibility check over thermal, electrical, geometric, and performance constraints.

## §3.2b 布局算法：外层的成熟工具域（Layout Algorithms as Mature Outer-Loop Solver Domain）

Chiplet/interposer placement is a classic NP-hard combinatorial problem with a mature EDA toolbox that we reuse rather than re-implement. The sequence-pair representation enables polynomial-time feasibility checks for rectangle packing [murata1996seqpair]. For 2.5D chiplet placement, thermally-aware solvers dominate: TAP-2.5D [tap2p5d2021], ATPlace2.5D (analytical, large-scale) [atplace2p5d2024], sequence-pair-based placement with thermal consideration [chiou2023chiplet], and learning-based MARL placers [tdpnavigator2025]; cost-aware partitioning has also been explored [chiplettpart2025]. At the interposer level, floorplanning with signal assignment jointly handles placement and wiring resources [liu2014interposerfloorplan], and architecture–chip–package co-design flows exist for 2.5D heterogeneous integration [kim2019codesign]; the EDA perspective on 2.5D integration is surveyed comprehensively in [chen2025survey2p5d]. Interposer-based disintegration of multi-core processors motivates chiplet integration itself [kannan2015interposer].

**xxx vs xxx.** These layout solvers optimize physical objectives (temperature, wirelength, cost) individually or in pairs; none is coupled to network-performance DSE or to a QoS-guaranteed bandwidth metric. We keep the outer layout layer NP-hard and delegate it to this mature toolbox, while the inner layer jointly decides thermal, electrical, geometric, and performance feasibility—precisely the coupling these separated solvers cannot express.

## §3.3 扩展比包络先例：oblivious routing 的负载因子与竞争比（Precedents: Load Factors and Competitive Ratios in Oblivious Routing）

The expansion-ratio envelope—per-link minimum overprovisioning under worst-case traffic, independent of the rated bandwidth B and of physical parameters—builds on a well-established lineage in oblivious routing. Valiant and Brebner introduced randomized two-phase load balancing for parallel communication [valiant1981universal]. Räcke showed that for any network there is an oblivious routing strategy whose congestion is within O(log³ n) of optimal [racke2002focs], later improved to O(log n) via hierarchical decompositions [racke2008stoc]. Azar, Cohen, Fiat, Kaplan, and Räcke proved that the optimal oblivious routing—the routing minimizing worst-case congestion—can be computed in polynomial time by linear programming [azar2004jcss]. In switching, Birkhoff–von Neumann input-buffered crossbar switches show that under admissible traffic (row/column sums ≤ 1, i.e., port loads within the rated bound), worst-case traffic collapses to permutation matrices, enabling guaranteed-rate services [chang2000infocom, chang2001tcom] and 100% throughput [mckeown1999tcom, mckeown1999islip]. In dragonfly-class networks, Valiant-mode routing and its variants have been analyzed and improved [kim2008dragonfly, benito2018valiant, navaridas2025proxy].

**We treat these as verification, not as competition.** Our contribution is not a new competitive-ratio bound; it is to specialize the per-link worst-case-load analysis into a topology-only expansion-ratio envelope (computed by per-link LPs whose vertices are permutation matrices, per Birkhoff–von Neumann [birkhoff1946, vonneumann1953]) and to use it as the performance–physics decoupling bridge in a wafer-scale switch DSE: the envelope is precomputed independent of B and physics, and the physical layer consumes B·L\* as linear constraints. Unlike global competitive-ratio bounds [racke2002focs, racke2008stoc], our envelope is a per-link vector used for physical feasibility, not an approximation-guarantee scalar.

## §3.4 热建模（Thermal Modeling）

For steady-state thermal feasibility we use the linear thermal-network formulation G·T = P + b (G an M-matrix with G⁻¹ ≥ 0), following MFIT's multi-fidelity thermal modeling of 2.5D/3D multi-chiplet architectures [mfit2025]; standalone thermal tools such as HotSpot [hotspot2006] and 3D-ICE [3dice2010] serve the same modeling role in their respective scopes. We do not contribute to heat-transfer modeling itself; thermal enters our model only as a linear constraint layer (per the G·T = P + b form), consistent with the "热只引 MFIT" discipline.

## §3.5 定位小结（Positioning）

Wafer-scale switch design currently lacks an early-stage DSE tool that jointly decides thermal, electrical, geometric, and performance feasibility and quantifies design quality via a QoS-guaranteed rated bandwidth B\*. Existing chiplet DSE tools cover performance/cost/layout subsets with thermal either external or absent [rapidchiplet2025, chariot2026, firelink2025, fpia2024]; wafer-scale network studies analyze specific dimensions without a full DSE [chen2024waferscale, feng2024switchless_sc, wan2025architectural, yang2025ticktock]; and the envelope concept has verified precedents in oblivious routing [valiant1981universal, racke2002focs, racke2008stoc, azar2004jcss] that we extend into a performance–physics decoupling bridge. This paper fills that gap (据检索, 2026-08; to the best of our knowledge).

---

## 引用键 ↔ 文献对照（详见 paper.bib 与 bib-verification-report.md）

| 键 | 文献 | 核验 |
|---|---|---|
| chen2024waferscale | Chen, Pal, Kumar, ISCA 2024, pp.215-229 | ✅ DBLP/CrossRef |
| feng2024switchless_sc | Feng, Ma, SC 2024 | ✅ DBLP（**venue 修正：SC 非 ATC**） |
| wan2025architectural | Wan et al., IEEE TVLSI 2025, pp.512-524 | ✅ DBLP |
| yang2025ticktock | Yang et al., ISCA 2025, pp.49-64 | ✅ DBLP |
| yu2025cramming | Yu et al., ISCA 2025, pp.631-645 | ✅ CrossRef（覆盖维度待核实） |
| dojo2022hc / dojo2023micro | Talpes et al., Hot Chips 34 2022 / IEEE Micro 2023 | ✅ CrossRef |
| lie2023hcs | Sean Lie, Hot Chips 35 2023 | ✅ CrossRef |
| cerebras-wse2 | Cerebras WSE-2（产品规格，白名单外） | 待核实规范引用 |
| rapidchiplet2025 / rapidchiplet2023arxiv | Iff et al., CF 2025 / arXiv:2311.06081 | ✅ DBLP/arXiv（**发表版标题为 Inter-Chiplet Interconnects**） |
| firelink2025 | Li et al., JCRD 2025, 62(5):1108-1122 | ✅ 期刊官网 DOI |
| chariot2026 | CHARIOT, ACM TODAES 2026 | ✅ CrossRef（DOI 10.1145/3815192） |
| fpia2024 | Jiao et al., IEEE TCAS-I 2024, 71:4156-4168 | ✅ DBLP |
| hotspot2006 | Huang et al., IEEE TVLSI 2006 | ✅ DBLP |
| 3dice2010 | Sridhar et al., ICCAD 2010 | ✅ DBLP |
| mfit2025 | Pfromm et al., ACM TODAES | ✅ DBLP/CrossRef/arXiv（**修正：非 Zhang/TACO**） |
| atplace2p5d / tdpnavigator | ATPlace2.5D / TDPNavigator-Placer | 待核实 |
| valiant1981universal | Valiant & Brebner, STOC 1981 | ✅ DBLP |
| racke2002focs | Räcke, FOCS 2002（**FOCS 非 STOC**） | ✅ DBLP |
| racke2008stoc | Räcke, STOC 2008 | ✅ DBLP |
| azar2004jcss | Azar et al., JCSS 2004 | ✅ DBLP |
| chang2000infocom / chang2001tcom | Chang, Chen, Huang, INFOCOM 2000 / IEEE ToN 2001 | ✅ DBLP |
| mckeown1999tcom / mckeown1999islip | McKeown et al., IEEE Trans. Commun. 1999 / iSLIP ToN 1999 | ✅ DBLP/CrossRef |
| kim2008dragonfly | Kim et al., ISCA 2008 | ✅ DBLP |
| benito2018valiant | Benito et al., HiPINEB@HPCA 2018 | ✅ DBLP |
| navaridas2025proxy | Navaridas & Pascual, Computer Networks 2025 | ✅ DBLP |
| birkhoff1946 / vonneumann1953 | Birkhoff 1946 / von Neumann 1953 | ✅ 标准（DBLP 未收录，数学经典） |
