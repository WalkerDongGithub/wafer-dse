# §6 Discussion —— 草稿（Phase 3, v0.1）

> WritingPolisher 草稿，2026-08-21。素材：paper-skeleton §6（6.3 定稿 2026-08-21）、sensitivity-design / s5-sensitivity-sample（灵敏度叙事整合）、INSIGHT_READING（insight 5 限定）。
> 段落前 `[insight n]` = Gate④ 检查用。

---

## 6. Discussion

### 6.1 $B^*$ as the Quantitative Foundation for Refinement

**[insight 5]** The DSE is a mathematical abstraction, not a guarantee about the real chip. Its value is that it collects strong prior evidence cheaply: a configuration that sits close to the target under strict settings is likely to become feasible once the settings are relaxed to realistic conditions. This is the quantified version of "probably feasible": the designer gets an ordering of design points and argues through them one by one, from the most capable to the least—instead of guessing where to start. Sensitivity analysis strengthens this: the same model that ranks design points also ranks the physical knobs that move each point (\S5.4). The decision right stays with the designer; the DSE supplies the ordering and the unlocking directions, not the verdict.

### 6.2 Screening Philosophy and Boundaries

**[insight 1, 7]** The framework is deliberately screening-oriented. The inner layer, for a fixed configuration, admits a polynomial-time global optimum without heuristics—the nonconvexity of the overall problem does not force an approximation. The outer discrete layer, by contrast, inherits the NP-hardness of layout and topology selection and is handled by the established chiplet enumeration flow; we make no complexity claim for it. This boundary is the honest statement of what the framework claims and what it delegates.

**[insight 1, 4]** Several boundaries deserve to be explicit. The model rests on stated assumptions (e.g., steady-state thermal linearity, signal integrity embedded in the interconnect standards, uniform substrate temperature); they are listed with the model (\S4, Appendix). The experiments cover the main-model constraint subset; constraints C2--C4 and the substrate thermal equation are part of the specification whose coverage is future work. The coupling results are demonstrated on the tested topologies and parameter domains—divergence on multi-path topologies, wiring-before-therm on dragonfly-class topologies—and are reported with their domains, not as universal facts. We do not promise that a feasible design point is physically buildable; we promise that the model's screening is exact for what it models.

### 6.3 Future Work

**[insight 4, 6]** Three directions follow directly from the boundaries above. (1) The D2D/I2I split ratio $\rho$—one large interposer vs.\ several small ones—is a core design knob whose mathematical vehicle (how the two envelope segments share load) is not yet in the model; introducing it makes the split a decision variable. (2) Full coverage of the specification's cross-layer constraints—C4 power delivery, die-to-interposer power aggregation, substrate temperature feedback, and the substrate thermal equation—for multi-interposer scenarios. (3) Real physical validation: simulation- or silicon-level comparison, which would turn the "likely feasible" prior of \S6.1 into measured evidence. Interposer wiring and die-area bounds are already first-class constraints in the model and are not part of this list.

---

## 中文结构说明

- 6.1：insight 5 价值主张（决策权交给设计师、排序逐点论证、"很可能/先验搜集"限定）+ 灵敏度强化的决策权叙事（§5.4 回链）。
- 6.2：筛选哲学（内层全局最优 vs 外层 NP-hard 边界）+ 诚实边界清单（假设、实现覆盖、拓扑域限定、不承诺真实物理可行）。
- 6.3：定稿三项未来工作（分割比 ρ / C2-C4/sub 热全接入 / 真实物理验证）；布线/面积已进主模型，明确不在未来工作之列。

## 待办/缺口

- [ ] DomainExpert 复核：6.2 边界清单与模型假设（A1-A8）对应；6.3 与 V5 §9 待定案一致
- [ ] 附录引用位（假设表、KKT 证明）待附录定稿后补 \ref
