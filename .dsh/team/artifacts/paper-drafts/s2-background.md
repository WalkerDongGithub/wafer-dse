# §2 Background & Motivation —— 草稿（Phase 3, v0.1）

> WritingPolisher 草稿，2026-08-21。素材：paper-skeleton §2、gap-evidence-chain、INSIGHT_READING（insight 1-3）、coupling case（round 21+ 指令【1】）。
> 段落前 `[insight n]` = Gate④ 检查用。术语按 terminology-ledger。

---

## 2. Background and Motivation

### 2.1 Wafer-Scale Switches and the Three-Layer Hierarchy

A wafer-scale switch is built on the same packaging hierarchy as other wafer-scale systems (Fig.~\ref{fig:hierarchy}): dies sit on an interposer, and interposers sit on a substrate. Links come in two kinds. Within an interposer, dies connect through die-to-die (D2D) links—UCIe or on-die wires with essentially no physical cost per link. Across interposers, links are inter-interposer (I2I) SerDes links that leave the interposer through C4 bumps and cross the substrate. This hierarchy is where the coupling lives: the two link kinds share the same die, the same bump budget, the same power delivery, and the same heat path. A bandwidth decision on either kind ripples through all of them.

**[insight 4]** Prior wafer-scale network work already hints at this coupling. Chen et al.\ find the radix of a wafer-scale switch is "limited by a combination of internal bandwidth, external bandwidth, and power density" \cite{chen2024waferscale}—an early quantitative statement that performance and physics cannot be separated. Our model makes that statement structural: performance, thermal, electrical, and geometric constraints are decided in one feasibility model (\S4.2).

### 2.2 Why Existing DSE Is Not Enough

Chiplet DSE tools are mature, but they cover the outer layers of the coupling chain, not the chain itself. RapidChiplet explores interconnect latency/throughput with high-level proxies and explicitly delegates thermal simulation to an external tool (HotSpot) \cite{rapidchiplet2025,rapidchiplet2023arxiv}; CHARIOT optimizes performance and energy without thermal \cite{chariot2026}; FireLink evaluates power/performance/area/cost without thermal \cite{firelink2025}; FPIA is a communication-aware placement and routing engine \cite{fpia2024}. Thermal modeling itself is served by standalone tools \cite{hotspot2006,3dice2010,mfit2025} and thermal-aware placement \cite{atplace2p5d2024,tdpnavigator2025}, none coupled to network-performance DSE. Wafer-scale network studies analyze specific dimensions—radix limits \cite{chen2024waferscale}, architecture alternatives \cite{feng2024switchless_sc,wan2025architectural}, or PD-aware topology co-design \cite{yang2025ticktock}—for one or a few design points, not across the design space.

**[insight 4]** What is missing is not any single tool but the joint decision. Three things make the wafer-scale switch harder than the chiplet case. First, there are three physical layers whose constraints cross layer boundaries (I2I links consume die-side bumps and interposer C4; interposer power feeds the substrate's heat). Second, the physical and performance sides are entangled through the wiring budget: power/ground traces share the interposer's redistribution layer with signal traces, so power demand directly consumes routing capacity. Third, the quantities that bind—wiring saturation and die area—only appear when the factors are decided together; a factor-by-factor flow never sees them. We formalize the first two in \S4 and demonstrate the third in \S5.3--\S5.4.

### 2.3 Key Observations

**[insight 1]** Screening, not optimizing. The purpose of a DSE at this stage is not to find a Pareto surface of trade-offs but to screen for configurations that satisfy hard, basic conditions—non-blocking under the QoS guarantee and physically feasible. Screening is cheaper and more decisive than optimizing: it removes the configurations that cannot work before anyone invests in them.

**[insight 2]** Bandwidth as a quality measure. A binary feasible/infeasible verdict cannot express how much design margin a configuration has; between feasible and infeasible lies a gray zone where a configuration fails under strict settings but succeeds once a constraint is relaxed. We quantify this margin with the rated bandwidth $B^*$: under the same settings and port count, a configuration with a larger $B^*$ is strictly more capable. Screening then becomes ranking.

**[insight 3]** $B$ is a function of requirements and constraints. The rated bandwidth a design point can sustain depends on how strict the performance requirement is (full QoS guarantee vs.\ per-port peak) and how pessimistic the physical constraints are (peak-power vs.\ rated-power operating conditions). Stricter or more pessimistic choices lower $B$; looser choices raise it. This requirement $\times$ constraint structure gives the designer explicit knobs and motivates the sensitivity analysis of \S5.4.

### 2.4 Motivation Example (Brief)

**[insight 2]** Consider two configurations that are both "feasible" under a binary check at a target bandwidth, but one sustains $B^* = 685$\,Gbps while the other sustains $295$\,Gbps under the same settings and port count (real values from \S5.4). A binary verdict treats them as equal; $B^*$ ranks them. Conversely, a configuration rejected at a strict target may be viable once the requirement is relaxed—the ranking tells the designer which points to argue through next.

---

## 中文结构说明

- 2.1 三层实体（die/interposer/substrate + D2D/I2I 两链路族）为 §4.2.2 铺垫；图 2 引用位。
- 2.2 沿用 xxx vs xxx 框架（不写"前人多分离决策"），gap 证据链（gap-evidence-chain §6 一句话素材）展开为三段式：工具单维 / 热独立 / 晶圆级特定维度。
- 2.3 三条关键观察 = insight 1/2/3 的口语化落地（筛选、量化、双旋钮）。
- 2.4 动机示例用 §5.4 实测数字（685 vs 295 Gbps）——二元判断的灰色地带，一个实例说清 insight 2。

## 待办/缺口

- [ ] DomainExpert 复核：2.1 三层实体描述、2.2 难点拆解三点的强度
- [ ] 图 2 引用位已放（fig:hierarchy）；与 figure-intents v0.2 一致
- [ ] 2.4 示例数字与 §5.4 一致（685/295 来自 E7）
