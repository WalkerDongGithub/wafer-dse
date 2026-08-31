# §7 Conclusion —— 草稿（Phase 3, v0.1）

> WritingPolisher 草稿，2026-08-21。结构：问题 → 方法 → 主张 → 效果 → 一句展望（paper-skeleton §7）。
> 段落前 `[insight n]` = Gate④ 检查用。

---

## 7. Conclusion

**[insight 1, 4, 6, 7]** Wafer-scale switches face a design space too large and too coupled—across thermal, electrical, geometric, and performance constraints—for factor-by-factor decisions, and no DSE tool existed for them. We presented a two-level DSE centered on the design of a single interposer: an outer discrete enumeration reusing the mature chiplet flow, and an inner feasibility model that couples all four constraint families in one model through an expansion-ratio envelope—a topological invariant that decouples performance from physics—and a three-layer die/interposer/substrate hierarchy. The model outputs the optimal rated ingress/egress bandwidth $B^*$ with a QoS guarantee, upgrading screening from binary verdicts to a quantified ranking. Although the overall problem is nonconvex, it admits a polynomial-time global optimum without heuristics. In evaluation, rankings by $B^*$ are stable, separated decision-making diverges from the joint model under wiring and area constraints, and sensitivity analysis locates the bottleneck knob per design point—at a wiring-saturation point, improving cooling releases nothing while reducing the power-wiring demand unlocks $+40\%$ of $B^*$. We hope this turns wafer-scale switch design from trial-and-error into a screening process where the designer, not the heuristic, decides.

---

## 中文结构说明

- 复述问题 → 方法（两层 + 包络 + 三层实体）→ 主张（非凸但多项式全局最优、不需启发式）→ 效果（排序稳定 / 耦合分歧 / 灵敏度解锁）→ 一句展望（筛选哲学：决策权交给设计师，不是启发式）。
- 术语与 Abstract/Intro 一致（two-level DSE / rated ingress/egress bandwidth / expansion-ratio envelope / topological invariant）。

## 待办/缺口

- [ ] 与 Abstract/Intro 数字终校对齐（+40%、ρ=1.0、10/72）
- [ ] DomainExpert 复核
