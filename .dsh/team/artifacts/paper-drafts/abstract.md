# Abstract —— 草稿（Phase 3, v0.1）

> WritingPolisher 草稿，2026-08-21。目标 ~200 词单段（ISCA 双栏）。结构：问题 → gap → 设计 → 主张 → 结果预览 → 边界。
> 结果预览数字全部来自 DataSteward 报告（可复现）：E5 包络不变性（4 参数组 0 差异）、E1 排序稳健（Spearman ρ=1.000, n=11）、E3B v2 耦合分歧（10/72 构型 rel_diff>0.01，max 0.80，Mesh(3) sep=1075 vs joint=5363）。
> 术语按 terminology-ledger（two-level DSE / rated ingress/egress bandwidth with a QoS guarantee / expansion-ratio envelope / topological invariant）。
> "E3B v2" 是实验内部代号，Abstract 不出现，只出现其结论数字。

---

## Draft（English）

Wafer-scale switching is emerging as a core component of wafer-scale systems, yet the design space of a wafer-scale switch—topology, layout, packaging, and interconnect, coupled across thermal, electrical, geometric, and performance constraints—is too large and too tightly coupled for factor-by-factor decisions, and no design-space exploration (DSE) framework exists for it. We present a two-level DSE centered on the design of a single interposer. The outer level enumerates discrete configurations, reusing established chiplet DSE flows; the inner level evaluates each configuration with a single feasibility model that couples the four constraint families through an expansion-ratio envelope—a topological invariant that decouples performance from physics—and a three-layer die/interposer/substrate hierarchy with cross-layer coupling. The model outputs the optimal rated ingress/egress bandwidth $B^*$ with a QoS guarantee, which quantifies design quality and ranks configurations. Although the overall problem is nonconvex, it admits a polynomial-time global optimum without heuristics. In evaluation, the envelope is identical across physical parameter sets; rankings by $B^*$ are stable across parameter sets (Spearman $\rho = 1.0$); and separated single-factor decision-making diverges from the joint model on 10 of 72 configurations, by up to 80\% in $B^*$. We evaluate in model-based simulation with UCIe/OIF-CEI-aligned parameters; the specification's C2–C4 constraints are outside the experimental coverage.

---

## 字数统计

~200 词（正文段，不含公式标记）。若需压缩：删边界句或 "Spearman ρ=1.0" 从句（保留包络不变性与 10/72 分歧两个承重数字）。

## 中文说明（结构选择）

1. **主主张单一化**：一句话主 claim = "两层 DSE 产出有 QoS 保证的额定出入口带宽 B*，整体非凸但可多项式时间全局最优、不需启发式"；其余均作支撑从句。
2. **三个数字各有职责**：包络不变性（insight 6 主承重，最干净）、ρ=1.0（B* 排序稳定性，支撑 insight 2/5 的"量化指标可排序"）、10/72 分歧（insight 4 耦合价值，max 0.80 为反例最强的数字）。三个数字 = CCF 摘要上限（2-3 个）。
3. **术语纪律**：首用全称 "rated ingress/egress bandwidth with a QoS guarantee"（DomainExpert 定案）；"nonconvex yet polynomial-time global optimum without heuristics" 为 insight 7 定稿句式；不出现 "LP" 字样。
4. **边界句保留**：CCF 摘要纪律要求边界（模型仿真 + C2-C4 覆盖边界），提升可信度。
5. **E3B v2 处理**：10/72 分歧即 E3B v2 的结论；摘要不写实验代号，实验代号只在 §5.4 出现。

## Claim–Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| 包络与物理参数无关（拓扑不变量） | E5：5 拓扑 × 4 参数组逐链路 max\|ΔL\*\|=0 | supported（构造性成立 + 实证 0 差异） |
| B* 排序可作为质量排序 | E1：跨 3 参数组 Spearman ρ=1.000（n=11）；C2 判定 PASS | supported（热约束下排序，正文须标注绑定约束族） |
| 分离决策在布线/面积下与联合模型分歧 | E3B v2：10/72 构型 rel_diff>0.01，GM 0.264 / max 0.80；机制=固定路径拥塞 vs 联合绕行（Mesh(3) 1075→5363） | supported（C3' 终判通过；拓扑域：多路径拓扑；Dragonfly 类为 C4' 布线饱和机制） |
| 整体非凸但多项式时间全局最优、不需启发式 | 结构论证（MODEL_PROPERTIES.md）：固定 B 线性可判 + 对数次外迭代；E6 规模-时间多项式轮廓（迭代 ≈ log₂(249.5)） | supported（论证 + 规模数据） |

## 待办/缺口

- [ ] 数字口径复核（DataSteward 确认摘要数字与 §5 表一致——CCF 纪律：摘要数字须与实验表可复现对齐）
- [ ] 标题候选 T1 用 "Two-Layer" 而术语账本定 "two-level"——标题定稿时对齐（提请 master）
- [ ] 终校（ccf-polishing）
