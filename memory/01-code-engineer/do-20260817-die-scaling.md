# Do 报告 — 代码工程师（01）

日期：2026-08-17
任务：实现 V4 §2.8 die 缩放 + 接口完善

## 改动清单

| 文件 | 改动 | 对应 V4 |
|------|------|---------|
| src/physical/params.py | DieParams 增加 d0_mm/alpha_d/beta_p（默认 None/0.0/0.0 向后兼容），新增 base_side_mm、side_mm(B)、area_mm2_at(B)、peak_power_w(B) | §2.8 |
| src/physical/bump/bump.py | DieBumpBudget 增加同款缩放字段，新增 total_bumps_at(B)/power_bumps_at(B)/available_at(B)（N_total(B)=η·A_die(B)/p²，电源扣减用 P_peak(B)）；顺带把 `__import__('math')` 改为顶部 `import math` | §2.8 + §2.3 |
| src/lp/models/phys/bumps/_bump.py | BumpModel 不再存固定 _rhs，改存 _budgets，build() 按 B 调 budget.available_at(B) 算 rhs；cache_key() 编码 d0/α_d/β_d/P0/V/I/η/pitch 结构参数（不含具体 B） | §2.3 + §2.8 + §4 |
| src/lp/models/phys/therm/_steady_state.py | SteadyStateModel.__init__(network, beta_p=0.0) 预计算 _rhs0（β_P=0 基线）与 _peak_coeff=G⁻¹·1；build() 按 rhs = rhs0 − β_P·B·(G⁻¹·1)；cache_key 增加 _peak_coeff 与 _beta_p | §2.5 + §2.8 + §4 |
| src/lp/builder.py | build_scenario 把 P.die.d0_mm/alpha_d/beta_p 传进 DieBumpBudget，SteadyStateModel(net, beta_p=P.die.beta_p) | §2.8 接线 |
| src/diagnostics.py | bump_ledger/thermal_ledger 由读 _rhs/rhs_ambient 改为按 B 计算 rhs | 依赖修复 |
| src/lp/ctx/_model.py | Model.build ABC 改两参 build(self, ctx, B) | INTERFACE §8.1 |
| src/lp/models/phys/therm/_temp_limit.py | GlobalPowerModel 补 cache_key() | INTERFACE §8.2 |
| src/lp/models/perf/traffic_free/ | 删除 TrafficFreeModel（论文不需要）+ 清理 perf/__init__.py 引用 | INTERFACE §8.4 |
| src/topology/dragonfly.py | DragonflyPlus 保留，docstring 标「骨架占位，未接入」 | INTERFACE §8.4 |

## 测试

新增 tests/die_scaling/test11_die_scaling.md（§2.8 手算锚点 + 接口断言）。

run_all.py：`13 files, 13 passed, 0 failed`（全绿）。

## 待核实

1. V4 §4 μbump 手写式 rhs 用 P_0，§2.8 语义下 die 流量无关功耗是 P_peak(B)。实现按 §2.8 用 P_peak(B) 扣电源 bump。若审查认定电源只扣 P_0（β_P 只进热约束），需回退这一处。
2. 正方形假设：d0_mm=None 时退化为 width_mm，A_die(B)=d(B)² 隐含正方形 die；当前 TOY/UCIE 均为正方形，非正方形未覆盖。
3. 布局固定：placement 仍用固定 P.die.width_mm，α_d 只影响 bump/热 rhs，不改物理布局（对应 V4 §5「布局固定」假设）。
