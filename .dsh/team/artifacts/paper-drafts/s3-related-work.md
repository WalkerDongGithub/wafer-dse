# §3 Related Work —— 草稿（Phase 3, v0.1）

> WritingPolisher 草稿，2026-08-21。素材：related-work-draft（LiteratureSearcher Phase 1）+ paper-skeleton §3 + benchmark-matrix 定位段（Gate② 定稿）。
> 引文键已校正（birkhoff1946 → birkhoff1946tres；cerebras-wse2 → cerebras_wse2）。
> 纪律：先例 = 验证而非防先例；xxx vs xxx 框架；热只引不展开。

---

## 3. Related Work

### 3.1 Wafer-Scale Systems and Switches

Wafer-scale integration has moved from research concept to industrial deployment. Tesla's Dojo trains exascale-scale workloads on a wafer-scale training system built from 25 D1 dies on a TSMC InFO-SoW carrier \cite{dojo2022hc,dojo2023micro}; Cerebras has shipped wafer-scale engines integrating up to $\sim$850K cores and 2.6T transistors on a single wafer, interconnected by an on-wafer mesh fabric \cite{lie2023hcs,cerebras_wse2}. These systems establish wafer-scale integration as a viable substrate for high-bandwidth, tightly coupled computation.

More recently, wafer-scale networking has emerged as a research direction. Chen, Pal, and Kumar analyze the radix potential of wafer-scale network switches and show up to $32\times$ higher radix than state-of-the-art switches when only area is considered, with the actual radix "limited by a combination of internal bandwidth, external bandwidth, and power density" \cite{chen2024waferscale}—an early, quantitative statement of the physical–performance coupling we formalize. Feng and Ma propose a switch-less wafer-scale interconnection architecture \cite{feng2024switchless_sc}; Wan et al.\ explore waferscale switching architectures and quantify design trade-offs \cite{wan2025architectural}; Yang et al.\ co-design physical-design constraints and logical topology for network-on-wafer \cite{yang2025ticktock}; Yu et al.\ co-explore computing and hardware architecture of a waferscale chip \cite{yu2025cramming}.

These works analyze specific dimensions—radix limits \cite{chen2024waferscale}, architecture alternatives \cite{feng2024switchless_sc,wan2025architectural}, or co-design \cite{yang2025ticktock,yu2025cramming}—for one or a few design points. None provides a DSE tool that jointly evaluates thermal, electrical, geometric, and performance constraints across the design space and outputs a quantified, QoS-guaranteed metric; they are single-point analyses or architecture studies rather than early-stage DSE.

### 3.2 Chiplet DSE Tools: The Outer-Loop Baseline

Chiplet-based design has produced mature DSE tools that we adopt as the outer-loop baseline rather than reinventing. RapidChiplet provides high-level inter-chiplet interconnect latency/throughput proxies, trading 0.25\%--30.15\% accuracy for $427\times$--$137{,}682\times$ speedup and enabling DSE over hundreds of thousands of design points \cite{rapidchiplet2025,rapidchiplet2023arxiv}. FireLink evaluates chiplet designs across power, performance, area, and cost with pruning \cite{firelink2025}. CHARIOT explores 2.5D/3D interposer designs via roofline analysis and multi-objective Bayesian optimization over performance and energy \cite{chariot2026}. FPIA performs communication-aware multi-chiplet placement and routing \cite{fpia2024}.

These tools cover subsets of the coupling chain: RapidChiplet focuses on interconnect latency/throughput, delegates thermal simulation to an external tool (HotSpot), and provides only "very high-level power, area, and cost estimates" \cite{rapidchiplet2023arxiv}; CHARIOT optimizes performance and energy without thermal \cite{chariot2026}; FireLink evaluates PPAC without thermal \cite{firelink2025}; FPIA is a physical-design engine for placement/routing \cite{fpia2024}. Standalone thermal tools \cite{hotspot2006,3dice2010,mfit2025} and thermal-aware placement engines \cite{atplace2p5d2024,tdpnavigator2025} exist but are not coupled to network-performance DSE. We treat these tools as the discrete outer layer and supply the missing inner layer: a single-model feasibility check over thermal, electrical, geometric, and performance constraints.

### 3.2b Layout Algorithms: A Mature Outer-Loop Solver Domain

Chiplet/interposer placement is a classic NP-hard combinatorial problem with a mature EDA toolbox that we reuse rather than re-implement. The sequence-pair representation enables polynomial-time feasibility checks for rectangle packing \cite{murata1996seqpair}. For 2.5D chiplet placement, thermally aware solvers dominate: TAP-2.5D \cite{tap2p5d2021}, ATPlace2.5D (analytical, large-scale) \cite{atplace2p5d2024}, sequence-pair placement with thermal consideration \cite{chiou2023chiplet}, and learning-based MARL placers \cite{tdpnavigator2025}; cost-aware partitioning has also been explored \cite{chiplettpart2025}. At the interposer level, floorplanning with signal assignment jointly handles placement and wiring resources \cite{liu2014interposerfloorplan}, architecture--chip--package co-design flows exist for 2.5D heterogeneous integration \cite{kim2019codesign}, and the EDA perspective on 2.5D integration is surveyed comprehensively \cite{chen2025survey2p5d}.

These layout solvers optimize physical objectives (temperature, wirelength, cost) individually or in pairs; none is coupled to network-performance DSE or to a QoS-guaranteed bandwidth metric. We keep the outer layout layer NP-hard and delegate it to this mature toolbox, while the inner layer jointly decides thermal, electrical, geometric, and performance feasibility—precisely the coupling these separated solvers cannot express.

### 3.3 The Expansion-Ratio Envelope: Precedents in Oblivious Routing

The expansion-ratio envelope—per-link minimum overprovisioning under worst-case traffic, independent of the rated bandwidth $B$ and of physical parameters—builds on a well-established lineage in oblivious routing. Valiant and Brebner introduced randomized two-phase load balancing \cite{valiant1981universal}. Räcke showed that for any network there is an oblivious routing strategy whose congestion is within $O(\log^3 n)$ of optimal \cite{racke2002focs}, later improved to $O(\log n)$ via hierarchical decompositions \cite{racke2008stoc}. Azar et al.\ proved that the optimal oblivious routing can be computed in polynomial time by linear programming \cite{azar2004jcss}. In switching, Birkhoff--von Neumann input-buffered crossbar switches show that under admissible traffic, worst-case traffic collapses to permutation matrices, enabling guaranteed-rate services \cite{chang2000infocom,chang2001tcom} and 100\% throughput \cite{mckeown1999tcom,mckeown1999islip}; in dragonfly-class networks, Valiant-mode routing has been analyzed and improved \cite{kim2008dragonfly,benito2018valiant,navaridas2025proxy}.

We treat these as verification, not competition. Our contribution is not a new competitive-ratio bound; it is to specialize the per-link worst-case-load analysis into a topology-only expansion-ratio envelope (computed by per-link linear programs whose vertices are permutation matrices, per Birkhoff--von Neumann \cite{birkhoff1946tres,vonneumann1953}) and to use it as the performance--physics decoupling bridge in a wafer-scale switch DSE: the envelope is precomputed independent of $B$ and physics, and the physical layer consumes $B\cdot\mathbf{L}^*$ as fixed per-link lower bounds. Unlike global competitive-ratio bounds \cite{racke2002focs,racke2008stoc}, our envelope is a per-link vector used for physical feasibility, not an approximation-guarantee scalar.

### 3.4 Thermal Modeling

For steady-state thermal feasibility we use the linear thermal-network formulation $\mathbf{G}\mathbf{T}=\mathbf{P}+\mathbf{b}$ (with $\mathbf{G}$ an $M$-matrix, $\mathbf{G}^{-1}\ge 0$), following MFIT's multi-fidelity thermal modeling of 2.5D/3D multi-chiplet architectures \cite{mfit2025}; standalone thermal tools such as HotSpot \cite{hotspot2006} and 3D-ICE \cite{3dice2010} serve the same modeling role in their respective scopes. We do not contribute to heat-transfer modeling itself; thermal enters our model only as a linear constraint layer, and heat-transfer details stay in the appendix.

### 3.5 Positioning

Wafer-scale switch design lacks an early-stage DSE tool that jointly decides thermal, electrical, geometric, and performance feasibility and quantifies design quality via a QoS-guaranteed rated bandwidth $B^*$. Chiplet DSE tools cover performance/cost/layout subsets with thermal external or absent \cite{rapidchiplet2025,chariot2026,firelink2025,fpia2024}; wafer-scale network studies analyze specific dimensions without a full DSE \cite{chen2024waferscale,feng2024switchless_sc,wan2025architectural,yang2025ticktock}; and the envelope concept has verified precedents in oblivious routing \cite{valiant1981universal,racke2002focs,racke2008stoc,azar2004jcss} that we extend into a performance--physics decoupling bridge. This paper fills that gap (据检索, 2026-08; to the best of our knowledge).

---

## 中文结构说明

- 3.1-3.5 直接整合 related-work-draft（LiteratureSearcher 已核验），修正两处引文键（birkhoff1946tres / cerebras_wse2）；3.2b 布局算法保留（round 21+ 指令【4】成果）。
- 每小节"xxx vs xxx"对比段保留（Gate② 定稿框架）。
- 3.3 先例 = 验证 + 区分点（逐链路向量 vs Räcke 全局竞争比；Azar 求最优路由 vs 我们固定路由求扩展比下界）。
- 3.4 热只引不展开（纪律）。

## 待办/缺口

- [ ] DomainExpert/LiteratureSearcher 复核：3.2b 布局引用键（新 +10 条）与 paper.bib 逐一核对
- [ ] 3.1 yu2025cramming 覆盖维度待核实（related-work-draft 注）
- [ ] 3.5 "据检索 2026-08"限定保留
