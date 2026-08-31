# §1 Introduction —— 草稿（Phase 3, v0.1）

> WritingPolisher 草稿，2026-08-21。素材：paper-skeleton §1、contributions C1-C4、abstract、gap-evidence-chain、benchmark-matrix（Gate② 定稿措辞）。
> 段落前 `[insight n]` = Gate④ 检查用。术语按 terminology-ledger。引文键 = paper.bib（核验版）。
> 目标：Intro ≤ 1 页（双栏）。贡献 4 条按 contributions.md C1-C4 定稿口径。

---

## 1. Introduction

### 1.1 Background

**[insight 4]** Wafer-scale integration has moved from research concept to deployed systems: Tesla's Dojo trains exascale-scale workloads on a wafer-scale carrier \cite{dojo2022hc,dojo2023micro}, and Cerebras ships wafer-scale engines with an on-wafer mesh fabric \cite{lie2023hcs}. Networking is now following. Recent work shows a wafer-scale network switch can support up to $32\times$ higher radix than state-of-the-art switches when only area is considered, but that the real limit is a combination of internal bandwidth, external bandwidth, and power density \cite{chen2024waferscale}; other work proposes switch-less wafer-scale interconnect architectures \cite{feng2024switchless_sc}. A switch is the connectivity backbone of such systems, and its design space—topology, layout, packaging, and interconnect—is large: chiplet design-space exploration (DSE) tools routinely enumerate hundreds of thousands of design points \cite{rapidchiplet2025}, and the wafer-scale switch adds coupling on top.

### 1.2 Problem: Coupled Decisions, No Joint Tool

**[insight 4]** Designing such a switch is not a matter of optimizing one factor. Topology, routing, power, area, signal integrity, packaging, and die placement interact: more bandwidth means more lanes, more area, more power, and more heat; power/ground traces share the wiring budget with signal traces; die size is capped. Existing tools cover only parts of this chain. Chiplet DSE tools focus on performance, cost, or layout dimensions, with thermal analysis either external (RapidChiplet delegates it to HotSpot \cite{rapidchiplet2025,rapidchiplet2023arxiv}) or absent \cite{firelink2025,chariot2026,fpia2024}; standalone thermal models \cite{hotspot2006,3dice2010,mfit2025} and thermal-aware placement engines \cite{atplace2p5d2024,tdpnavigator2025} are not coupled to network-performance DSE; and wafer-scale network studies analyze specific dimensions—radix limits \cite{chen2024waferscale}, architecture alternatives \cite{feng2024switchless_sc,wan2025architectural}, or physical/logical co-design \cite{yang2025ticktock}. None decides thermal, electrical, geometric, and performance constraints jointly and outputs a quantified, QoS-guaranteed metric.

### 1.3 The Gap

**[insight 1, 4]** Wafer-scale switch design currently lacks an early-stage DSE tool that does this. The gap is not a missing knob but a missing structure: a wafer-scale switch spans three physical layers—dies, the interposer that aggregates them, and the substrate that interconnects interposers—whose constraints couple across layers (I2I SerDes links leave the die through interposer bumps; interposer power feeds the substrate's heat). A separated decision process cannot see these couplings: it fixes each factor in turn and never revisits it. As we show in \S5, such separated decision-making diverges from a joint model on real design points (\S5.3), and the coupling runs through the wiring budget itself (\S5.4). To the best of our knowledge (检索, 2026-08), no DSE tool for wafer-scale switches jointly decides thermal, electrical, geometric, and performance feasibility.

### 1.4 Our Approach

**[insight 1, 6, 7]** We present a two-level DSE centered on the design of a single interposer. The outer level enumerates discrete configurations—topology family, layout, packaging process, and interconnect standard—reusing the established chiplet DSE flow \cite{rapidchiplet2025,firelink2025,fpia2024}. The inner level evaluates each configuration with a single feasibility model that couples the four constraint families through an expansion-ratio envelope—a topological invariant that decouples performance from physics—and a three-layer die/interposer/substrate hierarchy with cross-layer coupling. The model's output is the optimal rated ingress/egress bandwidth $B^*$ with a QoS guarantee, which quantifies a configuration's design quality and ranks configurations. The split is deliberate: the inner subproblem admits a polynomial-time global optimum without heuristics, while the outer enumeration stays with the mature chiplet flow.

### 1.5 Contributions

**[insight 1-7]** (C1) A two-level DSE framework for wafer-scale switches, centered on the design of a single interposer, whose inner layer jointly couples thermal, electrical, geometric, and performance constraints in one model—where existing tools cover single dimensions or external/absent thermal analysis (insight 1, 4). (C2) Rated bandwidth $B^*$ as a design-quality metric: the DSE output is upgraded from a binary feasible/infeasible verdict to a continuous, QoS-guaranteed scalar, with an explicit requirement $\times$ constraint trade-off framework (insight 2, 3). (C3) The expansion-ratio envelope as a performance–physics decoupling bridge: a topological invariant that lets the performance model be solved once, independent of $B$ and of physical parameters (insight 6). (C4) A polynomial-time global optimum without heuristics: the overall problem is nonconvex, yet the fixed-$B$ subproblem is exactly decidable and the optimum is found without heuristics (insight 7).

### 1.6 Results Preview and Organization

**[insight 2, 4, 6]** In evaluation, rankings by $B^*$ are stable across parameter sets; and separated single-factor decision-making diverges from the joint model on 10 of 72 configurations, by up to 80\% in $B^*$. Sensitivity analysis further shows the analysis can locate the bottleneck knob per design point—at a wiring-saturation point, improving cooling releases nothing, while reducing the power-wiring demand unlocks $+40\%$ of $B^*$; a Pareto-front DSE cannot provide such unlocking directions. \S2 backgrounds wafer-scale switches and the coupling; \S3 discusses related work; \S4 presents the model; \S5 evaluates; \S6 discusses boundaries and future work; \S7 concludes.

---

## 中文结构说明

- 1.1 以"晶圆级系统已落地 → 网络/交换机跟进 → 设计空间大"三句进题（insight 4 引子）。
- 1.2 用 xxx vs xxx 框架（Gate② 定稿）：不说"前人多分离决策"，列具体工具覆盖面 + 晶圆级工作做特定维度。
- 1.3 gap 用"缺的不是旋钮是结构"（三层实体跨层耦合），并预告 §5.3/§5.4 的证据（写作闭环）。
- 1.5 贡献 4 条与 contributions.md C1-C4 逐条对应，每条挂 insight。
- 1.6 结果预览与 Abstract 数字一致（ρ=1.0 / 10-72 分歧 max 80% / 灵敏度 +40%）。

## 待办/缺口

- [ ] DomainExpert 复核（内容归属）：1.2 工具覆盖面陈述、1.3 gap 表述强度（"检索未见"限定）
- [ ] 图 1 引用位：§1.4 未放图（骨架 §4.0 有图 1）；Intro 通常不放图，保持
- [ ] 数字终校：§1.6 与 §5 表回填后对齐（CCF 纪律：摘要/Intro 数字与实验表可复现）
