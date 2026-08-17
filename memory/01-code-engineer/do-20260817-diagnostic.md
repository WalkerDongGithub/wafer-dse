# Do 报告 — 代码工程师（01）

日期：2026-08-17
任务：固化诊断原语（min ΣL → L\* + margin + binding）

## 改动清单

| 文件 | 改动 | 对应 |
|------|------|------|
| src/diagnostics.py | `solve_diagnostic` 由返回 `(ctx, sol, L)` 固化为返回 `DiagnosticResult`；新增 `DiagnosticResult` / `BindingInfo`（frozen dataclass）与 `constraint_family()`（约束名前缀 → 模型家族）；内部固定解 min ΣL（`objective=sum(L), maximize=False`）；删除孤儿 `solve_min_L` 与 `binding_with_meaning`（功能被 `binding` 列表取代） | design_query §定案 + test08 三个坑 |
| src/main.py | `ctx, sol, L = solve_diagnostic(...)` → `diag = solve_diagnostic(...)` + `diag.L_star` | 依赖修复 |
| exp/run_ledger.py | 同步新签名；`binding_with_meaning(ctx, sol.duals)` → 遍历 `diag.binding`（含 family） | 依赖修复 |
| tests/diagnostics/test12_diagnostic.md | 新增测试：手算 toy 场景的 margin/binding、infeasible 时 binding 为空、前缀归类 | 验收 |

## 诊断原语契约（固化后）

```
solve_diagnostic(models, B) -> DiagnosticResult
  .B, .feasible
  .L_star   : {link_idx: load}                       # min ΣL 的真实包络
  .margins  : {constraint_name: rhs - lhs}           # 仅物理约束（bump/therm/c4/route）
  .binding  : (BindingInfo(name, family, dual, meaning), ...)  # |dual| 降序
```

三个坑的处理（与 test08 对应）：

1. 绑定诊断固定用 min ΣL 解，不用无目标可行性解（duals 不可靠）。
2. infeasible 时 duals 是 Farkas 证书 → `binding` 强制返回空，`margins`/`L_star` 也为空。
3. binding 每条带 `family`（`bump_/therm_/c4/route_` 前缀归类，`route` 判断在 `c4` 之前，避免 `route_c4pad_*` 被误归 C4；其余 `other`）。

## 测试

新增 tests/diagnostics/test12_diagnostic.md（3 节：手算 L\*=(2,0)、margin 4/3/98 与 binding={dem0, dual≈1}；infeasible → binding/margins/L_star 全空；前缀归类含 `route_c4pad_p0 → route` 边界）。

run_all.py：`14 files, 14 passed, 0 failed`（全绿）。

## 待核实

1. binding 判定沿用「duals 非零」机制（与 FeasibilityQuery 一致）。退化点（物理约束恰好取等但 dual=0，如 B\* 处）会被漏——design_sensitivity §2 的 λ 用闭式 1/(A_j·L\*)，不依赖 dual，但「谁在 B\* 处 binding」可能需要改用 `margin ≈ 0` 判定。本次未改判定机制，仅按任务字面补家族归类，留待 sensitivity 实验层确认。
2. 兜底家族用 `"other"`（perf 侧需求约束 `r*_env` 等也归 `other`），未细分 perf——任务只要求四物理家族归类，如需区分 perf 需另议。
3. 未跑大实验（内存约束）：仅 toy 参数 + 小拓扑验证；main.py / exp/run_ledger.py 只做了语法/签名同步，未端到端运行。
