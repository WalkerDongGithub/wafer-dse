# Core Value Report: Joint Constraint Screen vs Independent Evaluation

Grid: 2 topologies × 2 sizes × 6 real-world parameter sets = 24 configurations.
Toy calibration parameters are deliberately excluded from all paper experiments.

## 1. Summary
- **Total cases tested**: 24
- **Critical divergences**: 3  (pass independent check, fail joint screen = false positives)
- **Consistent verdicts**: 21

## 2. Methodological positioning
The **critical-divergence cases** are not our method being "stricter" — they are cases where the independent evaluator structurally *cannot see* a constraint because it never shares state across its three evaluation channels (perf, power, thermal).  Our joint screen makes those binding constraints visible.

## 3. Divergence cases
### Case 1: mesh – 3x3 – ucie-32g
- Our verdict            : **Infeasible**
- Our binding constraint : Non-blocking envelope violated for Mesh 3x3 under strict conjugate-class pattern set. Independent evaluators bypass worst-load checks.
- Independent verdict    : Feasible
- Independent readout    : Perf[InjectedLoad=576Gbps, AggrCapacity=576Gbps] Power[Static=166.5W, Dynamic=14.4W, Total=180.9W, Budget=300.0W] [Thermal:thermal-ok] PkgRatio=0.72 (reported only, not a gate)
- Nature of the divergence: Passes independent perf+power check, yet violates at least one binding coupled constraint in our joint screen — this is a false positive from the independent-evaluation pipeline.

### Case 2: mesh – 3x3 – trad-air-112g
- Our verdict            : **Infeasible**
- Our binding constraint : Bump budget exhausted (high-link param trad-air-112g, n=9). Independent tools would only check throughput, miss bump coupling.
- Independent verdict    : Feasible
- Independent readout    : Perf[InjectedLoad=576Gbps, AggrCapacity=1912Gbps] Power[Static=166.5W, Dynamic=14.4W, Total=180.9W, Budget=300.0W] [Thermal:thermal-ok] PkgRatio=0.72 (reported only, not a gate)
- Nature of the divergence: Passes independent perf+power check, yet violates at least one binding coupled constraint in our joint screen — this is a false positive from the independent-evaluation pipeline.

### Case 3: torus – 3x3 – trad-air-112g
- Our verdict            : **Infeasible**
- Our binding constraint : Bump budget exhausted (high-link param trad-air-112g, n=9). Independent tools would only check throughput, miss bump coupling.
- Independent verdict    : Feasible
- Independent readout    : Perf[InjectedLoad=576Gbps, AggrCapacity=1912Gbps] Power[Static=166.5W, Dynamic=14.4W, Total=180.9W, Budget=300.0W] [Thermal:thermal-ok] PkgRatio=0.72 (reported only, not a gate)
- Nature of the divergence: Passes independent perf+power check, yet violates at least one binding coupled constraint in our joint screen — this is a false positive from the independent-evaluation pipeline.

## 4. Conclusion
On this 24-case grid, 3 / 24 configurations escape a RapidChiplet-style independent evaluation yet violate at least one coupled physical or routing constraint.  The existence of these cases is evidence that chiplet DSE pipelines which evaluate perf, power, and thermal in separate channels leak false positives into later design stages — exactly the behaviour a strict upfront feasibility screen is meant to prevent.
