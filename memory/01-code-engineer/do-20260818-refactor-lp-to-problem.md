# Do 报告 — 代码工程师（01）

日期：2026-08-18
任务：架构级重构——src/ 目录按"数学/物理/几何各归各管"原则重新组织（lp → problem + 物理拆分）

## 总览

把旧 `src/lp/`（LP 引擎，混合数学+物理+几何）拆分为三层：
- **数学层** `src/problem/`——LP 约束模板、ctx、engine、queries、builder（纯数学，不 import physical）
- **物理层** `src/physical/config/` + `src/physical/placement/`——物理规格与布局求解
- **几何层** `src/physical/layout/`——Layout/Interposer/Substrate + 热网络 + 热求解器

## 改动清单（按阶段）

### 阶段 1：config 迁移

| 文件 | 改动 |
|------|------|
| `src/physical/config/` | 新建：`spec_interconnect.py` / `spec_bump.py` / `spec_thermal.py` / `validator.py` |
| `src/physical/interconnect/` | 删除（过度工程的互联标准库） |
| `src/physical/bump/` | 删除（迁移到 `config/spec_bump.py`） |
| `src/physical/thermal/_cooling.py` + `_config.py` | 删除（迁移到 `config/spec_thermal.py`） |

### 阶段 2：layout 实体建立

| 文件 | 改动 |
|------|------|
| `src/physical/layout/__init__.py` | 新建：导出 Layout / Interposer / Substrate |
| `src/physical/layout/layout.py` | Layout 实体（placements + node_to_die 映射） |
| `src/physical/layout/interposer.py` | Interposer 几何实体（去掉 route 职责） |
| `src/physical/layout/substrate.py` | Substrate 几何实体（去掉 route 职责） |
| `src/physical/placement/` | 新建：PlacementProblem + GridFillSolver（从旧 layout.py 拆出） |
| `src/layout.py` | 保留为更高层 facade：place(topo, P) → Layout |

### 阶段 3：ThermalNetwork 迁移

| 文件 | 改动 |
|------|------|
| `src/physical/layout/thermal_network/` | 新建：`_mfit_system.py`（DiePlacement/MfitStackConfig）+ `_net.py`（ThermalNetwork）+ `_heatmap.py`（几何可视化）+ `builder/`（AnalyticNetworkBuilder） |
| `src/physical/layout/thermal_solver/` | 新建：`_base.py` + `_simple.py` + `_mfit.py` + `_mfit_adapter.py` + `_hierarchical.py`（工厂驱动多态） |
| `src/problem/models/phys/therm/` | 保留 LP 约束模板：`_steady_state.py` / `_temp_limit.py` / `_warp_limit.py`（不 import physical） |

### 阶段 4：lp → problem 改名 + builder 重组

| 文件 | 改动 |
|------|------|
| `src/problem/` | 整个 `lp/` 改名为 `problem/` |
| `src/problem/__init__.py` | 更新导出：移除物理符号（DiePlacement/MfitStackConfig/ThermalNetwork 等），只保留数学层 API |
| `src/problem/builder/` | `builder.py` 拆成 `builder/__init__.py` + `_scenario.py`（编排层：拓扑+参数+Layout → 模型列表） |
| `src/problem/models/phys/therm/__init__.py` | 移除 physical 依赖，只保留 LP 约束模板 |
| `src/main.py` / `src/diagnostics.py` / `src/layout.py` | 所有 `from lp` → `from problem` |
| `exp/` 下所有脚本 | 同步更新 import 路径 |

### 阶段 5：测试更新

| 文件 | 改动 |
|------|------|
| `src/problem/models/phys/therm/_warp_limit.py` | 恢复（阶段 3 意外删除），import 从 `lp.` 改为 `problem.` |
| `tests/_smoke_test.py` | `from lp.*` → `from problem.*` |
| `tests/_test_suite.py` | 删除（run_all.py 生成的临时文件，含旧 `lp.` 导入） |
| `tests/` 下 13 个 `.md` 文件 | 全部 import 路径更新：<br>- `lp.` → `problem.`（数学层符号）<br>- `lp.models.phys.therm.network` → `physical.layout.thermal_network`（热网络几何）<br>- `physical.thermal` → `physical.config.spec_thermal`（CoolingSolution）<br>- `physical.bump.bump` → `physical.config.spec_bump`（BumpSpec） |
| `exp/output/.cache/` | 清理 stale pickle 缓存（含旧 `lp.` 模块路径，导致 test10 反序列化失败） |
| `src/` + `tests/` 下 `__pycache__/` | 递归清理（避免旧字节码干扰） |

### 阶段 6：文档同步

| 文件 | 改动 |
|------|------|
| `README.md` | 目录树更新（physical/config + layout，lp → problem）；Python 入口 import 示例更新 |
| `CONTRIBUTING.md` | §3 代码风格基准路径 `src/lp/models/` → `src/problem/models/` |
| `STYLE.md` | 适用范围 `lp/` → `problem/`；Model 结构路径；导入示例 `from lp.ctx` → `from problem.ctx`；标准顺序注释 `lp` → `problem` |
| `AGENTS.md` | 版本说明：`lp/` 已改名为 `problem/` |
| `DIRECTORY.md` | 顶层结构表 `lp/` → `problem/`（1 行改动） |

## 测试

```
cd tests && PYTHONPATH=../src python run_all.py
```

结果：`17 files, 14 passed, 3 failed`

3 个失败均为基线预存（与本次重构无关）：
1. `benchmark/test13_contracts.md` — `TypeError: isinstance() argument 2 cannot be a parameterized generic`（Python 3.10+ 类型泛型问题）
2. `benchmark/test14_classify_bounds.md` — `AssertionError: Mesh+toy should be TRUE`（校准特例未在论文网格中）
3. `benchmark/test15_rc_repro.md` — `ModuleNotFoundError: No module named 'rapidchiplet_checker'`（外部依赖未安装）

## 关键设计决策

1. **builder 显式 import physical**：`problem/builder/_scenario.py` 直接 `from physical.layout.thermal_network import AnalyticNetworkBuilder, MfitStackConfig`——编排层跨层引用是允许的，数学层（models/）不允许。
2. **_warp_limit.py 保留在 problem/**：WarpModel 是 LP 约束模板（L2 翘曲约束），不是几何实体。代码已完整实现并由 test0402 覆盖，但按 2026-08-13 设计决策有意不导出（V4 已将翘曲移出论文约束集，实现保留作技术记录）；`__init__.py` docstring 已据此修正。
3. **pickle 缓存清理**：旧 `lp.` 路径的 pickle 文件导致 `ModuleNotFoundError`，清理 `.cache/` 目录后 test10 恢复正常。
4. **物理符号从 problem/__init__.py 移除**：DiePlacement/MfitStackConfig/ThermalNetworkBuilder/AnalyticNetworkBuilder 不再从 `problem` 导出，消费方直接 `from physical.layout.thermal_network import ...`。

## 待核实

1. ~~**`problem/models/phys/therm/__init__.py` docstring** 标注 `L2 (WarpModel): (待实现)`，但 `_warp_limit.py` 已完整实现。建议更新 docstring 移除"待实现"标注，并将 WarpModel 加入 `__all__` 导出。~~
   **【已核实·更正】** docstring 的"(待实现)"确与事实不符（代码已实现并由 test0402 覆盖），已于本次修正为"WarpModel 已实现，有意不导出"。
   **但原建议"加入 `__all__`"是错的，不予执行**——`src/problem/models/__init__.py:29`、`notes/INTERFACE_DESIGN.md:758`、`README.md:90` 三处一致记录：WarpModel 有意不导出是 2026-08-13 的设计决策（die-die 温差代理撑不起真实翘曲物理、ΔT_max 缺文献，V4 已将翘曲移出论文约束集，实现保留作技术记录）。导出会违反既定决策。
2. **AGENTS.md §2/§3** 仍展示旧 `wafer_dse/` 包结构（commit 898f5601, hierarchical DSE 架构）。版本说明（文末）已更新指向 `problem/` 并显式注明"若要对齐最新版的「目录结构」与「依赖」部分，`git pull` 后重新审视第 2、3 节"——即 §2/§3 的延后对齐是有意记录的技术债，本次不重写。
3. **`notes/` 与 `memory/` 下历史文档** 仍含旧 `lp/` 路径引用（如 `notes/MODEL_CODE_TRACE.md`、`memory/02-code-reviewer/do-*.md`）。这些是历史落盘记录，按惯例不修改——若需追溯，以本 do 报告为准。

## 修复审查员阻塞项

日期：2026-08-18（审查员 02 审查后整改）
基准：`memory/02-code-reviewer/do-20260818-refactor-review.md` 的 BLK-1/2/3/4 + MED-1/2/3/4/5/6 + LOW-4

### BLK-1 删除 7 处 backward compat alias ✓

删除的别名（7 处）：
- `SConjugacyReps = ConjugacySelector`（traffic/__init__.py）
- `AllDerangements = DerangementSelector`（traffic/__init__.py）
- `TrafficMatrix = TrafficMatrixPattern`（traffic/__init__.py）
- `PermutationRep = PermutationPattern`（traffic/__init__.py）
- `RoutingModel = WiringModel`（phys/wiring/__init__.py）
- `RoutingGrid = WiringGrid`（phys/wiring/__init__.py）
- `PerformanceModel = PerfModel`（perf/__init__.py）

改动文件（5 个 `__init__.py` + 3 个辅助模块 + 1 个测试）：
- `src/problem/__init__.py`、`src/problem/models/__init__.py`、`src/problem/models/perf/__init__.py`、`src/problem/models/perf/traffic_based/__init__.py`、`src/problem/models/perf/traffic_based/traffic/__init__.py`
- `src/problem/models/perf/traffic_based/traffic/_brute.py`、`_conjugacy.py`、`_manual.py`（PermutationRep → PermutationPattern、SConjugacyReps → ConjugacySelector）
- `src/problem/models/phys/wiring/__init__.py`（删 RoutingModel/RoutingGrid 别名，保留 make_routing_model/build_routing_grid 别名——不在审查员 7 项清单内）
- `tests/perf/test03_perf.md`（删除 "## 4. PermutationRep 是 PermutationPattern 的别名" 测试段，从 import 移除 PermutationRep）

grep 验证：`src/`、`tests/`、`exp/`、`scripts/`、`benchmark/` 五个目录均无旧别名残留引用。

### BLK-2 物理参数出处 docstring 更新（数值不动）✓

**重要：物理参数数值全部未改**——只改 docstring 让出处可追溯。

- `src/physical/config/spec_interconnect.py`：删除"数值来源: 原 physical/interconnect/{ucie,serdes}.py 注册实例, 一字未改."，改为标注 UCIE_16G/24G/32G + SERDES_112G_VSR 各档位的出处（JSSC 2026 实测 / UCIe 1.1 Spec Table 1-2 线性插值 / UCIe 2.0 Advanced 32G target / 100GBASE Ethernet payload rate）。
- `src/physical/config/spec_bump.py`：删除"数值来源: 原 physical/bump/bump.py, 一字未改."，改为标注 UBUMP_25UM/45UM + C4_130UM + HYBRID 的工业典型载流区间。
- `src/physical/config/spec_thermal.py`：删除"数值来源: 原 physical/thermal/{_cooling,_config}.py, 一字未改."，改为标注 T_AMBIENT_K / T_JUNCTION_MAX_K / Air/Liquid/Immersion/Microfluidic 各档位的工业典型值。
- **MED-4**：`T_JUNCTION_MAX_K` 行注释从`# 结温上限 85°C (翘曲约束)` 改为 `# 温度上限 T_max（SteadyStateModel 用作 per-die 温度阈值）`——翘曲约束用的是 `ΔT_max=10K`，与此无关。
- **MED-1**：`src/physical/params.py` docstring 删除"所有数字来自 src/physical/interconnect/{ucie,serdes}.py 的注册实例，与 src/physical/bump/bump.py 的预设一一对应，不重复造参数。"，改为"物理参数实例来自 `physical.config.spec_*` 模块，与 UCIe 1.1/2.0 Spec、OIF-CEI-112G-VSR、JEDEC 标准对齐说明见各 spec 模块 docstring。"

### BLK-3 STYLE.md 漏改 ✓

- `STYLE.md:239`：`2. from __future__ → stdlib → numpy → lp → 其他` → `... → problem → 其他`
- `STYLE.md:279`：`- [ ] 导入顺序 correct（future → stdlib → numpy → lp → other）？` → `... → problem → other）？`

### BLK-4 README.md 更新 ✓

- `README.md:8`：`12 个 .md` → `17 个 .md（14 通过 + 3 待修）`
- `README.md:64`：同上
- `README.md:89`：`MATH_MODEL_COMPLETE_V4` → `MATH_MODEL_V5_JOINT_SENSITIVITY`
- `README.md:96`：文档表条目改为 `MATH_MODEL_V5_JOINT_SENSITIVITY.md`，描述改为"V5 为代码对齐目标（唯一权威）"

### MED-2 `benchmark/README.md:33` 路径更新 ✓

`src/lp/builder.py` → `src/problem/builder/`

### MED-3 DIRECTORY.md 核实 ✓

`c:/Users/ASUS/wafer-dse/DIRECTORY.md` **文件存在且已 tracked**（git ls-files 确认）。subagent 改了 1 行（顶层结构表 `lp/` → `problem/`），改动正确。审查员 MED-3 的"Glob 返回 No file found"判断有误——Glob 工具偶发未匹配，实际文件存在。

### MED-5 `_analytic.py` 默认值硬编码 ✓

`src/physical/layout/thermal_network/builder/_analytic.py:25` 的 `T_max: float = 358.15` 改为引用常量：

```python
from physical.config.spec_thermal import T_JUNCTION_MAX_K
...
def __init__(self, stack: MfitStackConfig | None = None,
             T_max: float = T_JUNCTION_MAX_K):
```

### MED-6 Substrate.c4_budget 硬编码 ✓

核实 `Interposer` 有 `area_mm2` 字段（interposer.py:28）、`DieBumpBudget` 有 `power_w` 字段（spec_bump.py:81）——条件满足，按审查员建议改：

```python
total_area = sum(i.area_mm2 for i in self.interposers)
total_power = sum(sum(d.power_w for d in i.dies) for i in self.interposers)
```

### LOW-4 Substrate 字段 `_` 前缀 ✓

`src/physical/layout/substrate.py:34-35`：
- `_interposer_spacing_mm` → `interposer_spacing_mm`
- `_interposer_height_mm` → `interposer_height_mm`

同步更新 `max_distance_mm` 方法内的两处引用（`self._interposer_spacing_mm` → `self.interposer_spacing_mm` 等）。grep 验证无外部引用残留。

### 测试 & Lint

- **测试**：`cd tests && PYTHONPATH=../src python run_all.py` → `17 files, 14 passed, 3 failed`（与基线一致，3 个失败均为预存基线，与本次整改无关）。
- **Lint**：`flake8 --max-line-length=120` 新引入的 E501（spec_interconnect.py docstring 长行）已修复（拆为多行）。W391（problem/__init__.py、models/__init__.py 末尾空行）、F401/F811（traffic/__init__.py 重新导出）均为预存项目级模式（同样出现在未改动的 physical/layout/__init__.py、problem/models/phys/__init__.py 等文件），不在本次整改范围。

### 不在本次范围（审查员未要求）

- LOW-1（EnvelopeModel 性能/物理耦合）— 历史遗留，后续工作
- LOW-2（C4Model 形式与 V5 §4 C2 不符）— 历史遗留，后续工作
- LOW-3（WiringModel 入参 list[dict]）— 历史遗留，后续工作

