# Do 报告 — 代码审查员（02）

日期：2026-08-18
任务：审查 01 代码工程师提交的"lp → problem 重构"（do 报告：`memory/01-code-engineer/do-20260818-refactor-lp-to-problem.md`）
基准：`notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md`（V5 唯一权威）、根 `STYLE.md`、`insight.md`、`CONTRIBUTING.md`

---

## 0. 总体结论：**有条件通过**

权责分明（用户最高要求）这一条**做到位**——builder 是 problem 与 physical 的唯一运行时桥梁，math 层的 `physical` 引用全部在 `if TYPE_CHECKING:` 守卫内，几何层不含 LP 约束语法。这一项 do 报告描述属实。

但有 **4 项阻塞** 必须工程师整改后才能放行（详见 §3 阻塞项）。其余为建议项。

---

## 1. 可攻击点清单（按严重程度降序）

### 🔴 BLK-1（阻塞）STYLE.md §2.2/§2.3 命名红线多处违规

**位置**：`src/problem/models/perf/traffic_based/traffic/__init__.py:110, 163, 204, 205`；`src/problem/models/phys/wiring/__init__.py:210-212`；`src/problem/models/perf/__init__.py:20`；`src/problem/models/__init__.py` 与 `src/problem/__init__.py` 把这些别名公开导出。

**问题**：以下别名违反 STYLE §2.2 硬规则"子类名必须以直接父类名结尾"，且 §2.3 已识别清单明确要求改名但未改：

| 当前别名 | 父类 | STYLE §2.3 应改 | 当前状态 |
|---|---|---|---|
| `SConjugacyReps = ConjugacySelector` | `Selector` | `ConjugacySelector` ✓ 名字对，但别名公开导出 | 别名导出违规 |
| `AllDerangements = DerangementSelector` | `Selector` | `DerangementSelector` ✓ 名字对，但别名公开导出 | 别名导出违规 |
| `TrafficMatrix = TrafficMatrixPattern` | `Pattern` | `TrafficMatrixPattern` ✓ 名字对，但别名公开导出 | 别名导出违规 |
| `PermutationRep = PermutationPattern` | `Pattern` | (STYLE §2.3 未列，但同样模式) | 别名导出违规 |
| `RoutingModel = WiringModel` | `PhysModel` | (未列，但 RoutingModel 不以父类后缀 Model 结尾——实际上是以 Model 结尾，但 RoutingModel≠WiringModel 的子类，是别名) | 别名导出违规 |
| `RoutingGrid = WiringGrid` | — | dataclass 别名 | 别名导出违规 |
| `PerformanceModel = PerfModel` | `PerfModel` | (别名指向 PerfModel 本身，名字带 Model 后缀但不是子类) | 别名导出违规 |

**举证**：

```
$ grep -n "SConjugacyReps\|AllDerangements\|TrafficMatrix =\|PermutationRep =\|RoutingModel =\|RoutingGrid =\|PerformanceModel =" src/problem/models/__init__.py src/problem/__init__.py
src/problem/models/__init__.py:19    ConjugacySelector, SConjugacyReps,
src/problem/models/__init__.py:20    DerangementSelector, AllDerangements,
src/problem/models/__init__.py:21    TrafficMatrixPattern, TrafficMatrix,
src/problem/models/perf/__init__.py:20:PerformanceModel = PerfModel
```

`SConjugacyReps`/`AllDerangements`/`TrafficMatrix` 三个名字在 STYLE §2.3 明确列为"应改为"，重构未整改。

**严重程度**：高（STYLE §2.2 是硬规则，§2.3 是已识别清单）

**修补建议**：
1. 删除 `__init__.py` 里的 backward compat 别名（既然是 refactor 重构，正好趁机清理）
2. 如果担心外部依赖，至少在 `__all__` 里移除这些旧名，只留新名（`ConjugacySelector`/`DerangementSelector`/`TrafficMatrixPattern`）
3. 同时清理 `exp/` 下脚本对这些旧名的引用

---

### 🔴 BLK-2（阻塞）物理参数出处无法追溯——do 报告"一字未改"但原文件已删

**位置**：
- `src/physical/config/spec_interconnect.py:12` 模块 docstring："数值来源: 原 physical/interconnect/{ucie,serdes}.py 注册实例, 一字未改。"
- `src/physical/config/spec_bump.py:9` 同样："数值来源: 原 physical/bump/bump.py, 一字未改。"
- `src/physical/config/spec_thermal.py:8` 同样："数值来源: 原 physical/thermal/{_cooling,_config}.py, 一字未改。"
- `src/physical/params.py:10-11`："所有数字来自 src/physical/interconnect/{ucie,serdes}.py 的注册实例，与 src/physical/bump/bump.py 的预设一一对应，不重复造参数。"

**问题**：以上 4 处都引用**已被删除的源文件**作为数值出处。do 报告阶段 1 自己说"`physical/interconnect/` 删除（过度工程的互联标准库）"、"physical/bump/ 删除（迁移到 config/spec_bump.py）"——既然原文件删除，"一字未改"的出处校验无法做。这是审查员独有职责里"每个数字都要能追到标准文档出处；追不到的，判定为不可靠 / 疑似编造"的硬阻塞。

**Python 验算（pJ/bit 重算）**：

```python
# === UCIe power-per-bit (pJ/bit) ===
print('=== UCIe power-per-bit (pJ/bit) ===')
for name, rate, power in [('UCIE_16G', 16.0, 0.005), ('UCIE_24G', 24.0, 0.009), ('UCIE_32G', 32.0, 0.016)]:
    pjb = power / rate * 1000
    print(f'{name}: rate={rate} Gbps, power_per_lane={power} W -> {pjb:.4f} pJ/bit')
# UCIE_16G: 0.3125 pJ/bit
# UCIE_24G: 0.3750 pJ/bit
# UCIE_32G: 0.5000 pJ/bit

# === SerDes 112G VSR ===
print(f'rate={106.25} Gbps, power_per_lane={0.425} W -> {0.425/106.25*1000:.4f} pJ/bit')
# 4.0000 pJ/bit
# (if rate were 112.0: 3.7946 pJ/bit)
```

**标准文档对照**（来源：UCIe 1.1 Spec 2023-08 / OIF CEI-112G 项目章程 / IEEE JSSC 2026 实测论文 / Keysight D9050CEIC datasheet）：

| 档位 | 代码值 | UCIe/OIF 标称 | 判定 |
|---|---|---|---|
| UCIE_16G pJ/bit | 0.3125 | UCIe 1.1 Advanced target = 0.25；JSSC 2026 实测 16G-AP = 0.29 | **偏高，与 Spec target 不符；与实测 0.29 接近但略高** |
| UCIE_24G pJ/bit | 0.375 | UCIe 1.1 Spec Table 1-2 未单独列 24G 的能效目标 | **无标准出处，疑似线性插值编造** |
| UCIE_32G pJ/bit | 0.5000 | UCIe 2.0 Advanced 32G target = 0.5 | ✓ 符合 |
| SerDes 112G-VSR lane_rate | 106.25 Gbps | OIF 标称 112 Gbps（Keysight datasheet 说 72-116 Gbps 可变） | **不符——106.25 是 100GBASE Ethernet payload rate，不是 OIF line rate** |
| SerDes 112G-VSR pJ/bit | 4.0000 | 工业实测 112G-VSR 单 lane 功耗 0.4-0.5 W（含 DSP）≈ 3.6-4.5 pJ/bit | 数值合理但前提是 rate 正确 |

**严重程度**：高

**修补建议**（必须由工程师补出处或改正，**审查员不替工程师改数**）：
1. UCIE_24G：补出处（UCIe Spec 哪一页哪一行；若是线性插值请在 docstring 注明"24G 无 Spec 单列目标，按 16G/32G 线性插值"）
2. UCIE_16G：要么改 0.004 W（对齐 Spec 0.25 pJ/bit target），要么补出处说明"采用 JSSC 2026 实测 0.29 pJ/bit 上限的工艺角"
3. SerDes 112G-VSR：把 `lane_rate_gbps=106.25` 改成 `112.0`（对齐 OIF 标称）；如果保留 106.25 必须在 docstring 说明"采用 100GBASE Ethernet payload rate 而非 OIF line rate"，并解释为什么 4.0 pJ/bit 算式的分母用了 106.25 而不是 112
4. 同时删除 4 处 spec_*.py 和 physical/params.py 里"数值来源: 原 physical/...py"的 stale 注释，改为引用标准文档（UCIe 1.1/2.0 Spec §X.X / OIF-CEI-112G-VSR IA / 等）

---

### 🔴 BLK-3（阻塞）STYLE.md 标准顺序注释未改、审查清单未改——do 报告自称已改但实际未改

**位置**：
- `STYLE.md:194`：`# 标准顺序:  future → stdlib → numpy → problem → 其他` ← **已改 ✓**
- `STYLE.md:239`：`2. from __future__ → stdlib → numpy → **lp** → 其他` ← **未改 ✗**
- `STYLE.md:279`：`- [ ] 导入顺序 correct（future → stdlib → numpy → **lp** → other）？` ← **未改 ✗**

**问题**：do 报告阶段 6 表格称"STYLE.md：适用范围 lp/ → problem/；Model 结构路径；导入示例 from lp.ctx → from problem.ctx；标准顺序注释 lp → problem"。实际上 STYLE.md 第 194 行改了，但第 239 行和第 279 行**漏改**——这两处仍然是 `lp`。

**举证**：

```
$ grep -n "lp" STYLE.md | grep -v "原\|旧\|lp/"
239:2. from __future__ → stdlib → numpy → lp → 其他
279:- [ ] 导入顺序 correct（future → stdlib → numpy → lp → other）？
```

第 194 行的注释是 `problem`，但第 239/279 行还是 `lp`。**自相矛盾**。

**严重程度**：中（文档内部不一致；工程师已经改了一半）

**修补建议**：把 STYLE.md 第 239 行和第 279 行的 `lp` 改为 `problem`。

---

### 🔴 BLK-4（阻塞）README.md 与实际测试数量不符、且仍指向 V4 模型

**位置**：
- `README.md:8`：`make test          # 全部测试（tests/ 下 12 个 .md，叙述 + 可运行代码块）`
- `README.md:64`：`tests/              测试即文档（.md 叙述 + 可运行代码块，12 个）`
- `README.md:89`：`论文约束集（MATH_MODEL_COMPLETE_V4）：性能包络、μbump、C4、温度极限、布线。`
- `README.md:96`：文档表里列 `MATH_MODEL_COMPLETE_V4.md` 为"当前数理模型总纲（V4 为代码对齐目标）"

**问题**：
1. 实际跑 `python run_all.py` 是 **17 个 .md 文件（14 通过 + 3 失败）**，README 说"12 个"——数字错。do 报告阶段 6 说"README.md：目录树更新"，但数字未更新。
2. 任务描述明示 V5（`notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md`）是**唯一权威**，README 还指向 V4 为"代码对齐目标"——文档与权威基准不一致。

**举证**（实际测试运行）：

```
$ cd tests; $env:PYTHONPATH="../src"; python run_all.py
  ...
  OK  bump\test05_bump.md
  OK  c4\test06_c4.md
  OK  ctx\test01_ctx.md
  OK  diagnostics\test12_diagnostic.md
  OK  die_scaling\test11_die_scaling.md
  OK  main\test10_main.md
  OK  params\test09_params.md
  OK  perf\test03_perf.md
  OK  perf\test03b_envelope.md
  OK  placement\test02_placement.md
  OK  queries\test08_queries.md
  OK  routing\test07_routing.md
  OK  thermal\test0402_warp.md
  OK  thermal\test04_thermal.md
  FAIL  benchmark\test13_contracts.md  —  TypeError: isinstance() argument 2 cannot be a parameterized generic
  FAIL  benchmark\test14_classify_bounds.md  —  AssertionError: Mesh+toy should be TRUE (calibration-only shortcut; not in paper grid)
  FAIL  benchmark\test15_rc_repro.md  —  ModuleNotFoundError: No module named 'rapidchiplet_checker'
==================================================
  17 files,  14 passed,  3 failed
==================================================
```

14 个通过的 + 3 个失败的 = 17 个，不是 12。

3 个失败与 do 报告描述一致（Python 3.10+ 类型泛型问题、校准特例不在论文网格、外部依赖未安装），**这 3 个失败不是本次重构引入的**，do 报告对这点的描述属实 ✓。

**严重程度**：中（文档与实际不符；V4/V5 错位）

**修补建议**：
1. README.md 第 8 行 + 第 64 行的"12 个 .md"改为"17 个 .md（14 通过 + 3 待修）"或直接写"17 个"
2. README.md 第 89 行 + 第 96 行的 V4 改为 V5（MATH_MODEL_V5_JOINT_SENSITIVITY.md），并相应更新"代码对齐目标"

---

### 🟡 MED-1 `physical/params.py` docstring 引用已删除的源文件

**位置**：`src/physical/params.py:10-11`

```
所有数字来自 src/physical/interconnect/{ucie,serdes}.py 的注册实例，
与 src/physical/bump/bump.py 的预设一一对应，不重复造参数。
```

**问题**：`physical/interconnect/` 和 `physical/bump/` 在本次重构中删除（do 报告阶段 1 自述）。docstring 引用不存在的路径，是 stale 注释。

**严重程度**：中（与 BLK-2 同根，但更轻微——只是注释 stale）

**修补建议**：删除或重写 docstring，引用 UCIe/OIF 标准文档（与 BLK-2 修补建议合并执行）。

---

### 🟡 MED-2 `benchmark/README.md` 仍引用旧 `src/lp/builder.py`

**位置**：`benchmark/README.md:33` —— "使用我们的框架 (`src/lp/builder.py` + 查询逻辑) 在上述参数集上进行全组合运行。"

**问题**：do 报告阶段 6 说改了 README/CONTRIBUTING/STYLE/AGENTS/DIRECTORY，**未提 `benchmark/README.md`**。该文件仍引用旧路径 `src/lp/builder.py`（实际已是 `src/problem/builder/`）。

**举证**：

```
$ grep -n "src/lp" benchmark/README.md
33:使用我们的框架 (`src/lp/builder.py` + 查询逻辑) 在上述参数集上进行全组合运行。
```

**严重程度**：中（文档同步不彻底）

**修补建议**：`benchmark/README.md:33` 改为 `src/problem/builder/`（或 `problem.builder.build_scenario`）。

---

### 🟡 MED-3 DIRECTORY.md 不存在——do 报告自称改过

**位置**：do 报告阶段 6 表格："DIRECTORY.md | 顶层结构表 lp/ → problem/"

**问题**：实际 `c:/Users/ASUS/wafer-dse/DIRECTORY.md` 文件不存在（Glob 返回 "No file found"）。do 报告对自己改动的描述与实际不符。

**举证**：

```
$ Glob c:/Users/ASUS/wafer-dse/DIRECTORY.md
No file found
```

**严重程度**：低-中（do 报告准确性问题）

**修补建议**：要么补回 DIRECTORY.md（如果原来真有），要么从 do 报告里移除这一行（如果原来就没有）。

---

### 🟡 MED-4 `T_JUNCTION_MAX_K` docstring 把"结温上限"和"翘曲约束触发温度"混淆

**位置**：`src/physical/config/spec_thermal.py:21`

```python
T_JUNCTION_MAX_K = 273.15 + 85.0      # 结温上限 85°C (翘曲约束)
```

**问题**：
1. 85°C 作为**结温上限**偏低（典型 105°C/125°C），但作为**翘曲约束触发温度**合理。
2. docstring 同时挂"结温上限"和"翘曲约束"两个标签，混淆了 V5 模型里两个独立的温度阈值：
   - V5 §2e: `T ≤ T_max`（结温上限，应是 ≥105°C）
   - V5 §4 (C4): `b_inter = G_inter^amb · T_sub`（与翘曲无直接关系）
   - WarpModel 用的是 `ΔT_max = 10K`（见 `_warp_limit.py:45`），不是 85°C
3. 代码语义实际是 SteadyStateModel 的 T_max（结温上限），不是翘曲约束的 trigger——docstring 误导。

**严重程度**：中（docstring 与代码语义不符）

**修补建议**：
- 把注释改为 `# 温度上限 T_max（被 SteadyStateModel 用作 per-die 温度阈值）` 或直接 `# T_max for die temperature`
- 删除"(翘曲约束)"——翘曲约束用的是 `ΔT_max = 10K`，与这个 85°C 无关
- 如果 85°C 真是翘曲约束的 trigger，应另外定义 `T_WARP_TRIGGER_K = 358.15`，与 `T_JUNCTION_MAX_K` 区分；如果 85°C 是结温上限，应说明"采用低端值（消费级）"

---

### 🟡 MED-5 `_analytic.py` 默认 `T_max=358.15` 硬编码，违反单一真相

**位置**：`src/physical/layout/thermal_network/builder/_analytic.py:25`

```python
def __init__(self, stack: MfitStackConfig | None = None,
             T_max: float = 358.15):
```

**问题**：`358.15` 这个数在两处独立定义：
- `spec_thermal.py:21`：`T_JUNCTION_MAX_K = 273.15 + 85.0`
- `_analytic.py:25`：默认参数 `T_max: float = 358.15`

两处数值一致但**没有引用关系**——如果未来改 spec_thermal 的常量，_analytic 不会自动跟上。违反 AGENTS.md §5"禁止硬编码"+ 单一真相原则。

**严重程度**：中

**修补建议**：
```python
from physical.config.spec_thermal import T_JUNCTION_MAX_K
def __init__(self, stack=None, T_max: float = T_JUNCTION_MAX_K):
```

---

### 🟡 MED-6 `Substrate.c4_budget` 硬编码 `858.0` 和 `300.0`

**位置**：`src/physical/layout/substrate.py:47-48`

```python
total_area = len(self.interposers) * 858.0
total_power = len(self.interposers) * 300.0  # 每 interposer ~300W
```

**问题**：
1. `858.0` 应来自 `Interposer.area_mm2`（默认值已定义在 interposer.py:28）——硬编码导致两处数值脱钩
2. `300.0` 是"每 interposer 功耗"，应来自 `Interposer` 实例的总功耗（`sum(d.power_w for d in dies)`）或从 `ThermalConfig.total_power_w` 注入

违反 AGENTS.md §5"工艺参数从 YAML 配置读取，禁止硬编码"。

**严重程度**：中

**修补建议**：
```python
total_area = sum(i.area_mm2 for i in self.interposers)
total_power = sum(sum(d.power_w for d in i.dies) for i in self.interposers)
```

---

### 🟢 LOW-1 `EnvelopeModel` 把性能侧与物理侧耦合在同一 LP——与 V5 §7.5 不符

**位置**：`src/problem/models/perf/traffic_based/_envelope.py:47-118`

**问题**：V5 §7.5 明示"性能模型与物理模型完全解耦：性能模型一次性产出 L*，物理模型以 L* 为输入"。但 `EnvelopeModel.build()` 在主 LP 里写入了：
- 包络变量 L_e（共享）
- 分流变量 f_{p,k}^{r}（每个 pattern 一组）
- 流量守恒约束 `Σ_k f = D`
- 链路负载约束 `L^{(r)}_e = Σ f`
- 包络约束 `L_e ≥ L^{(r)}_e`

这意味着 f 是主 LP 的变量，**与 V5 §7.1 "放弃 f 的可变性"的设计选择不符**——V5 要求子 LP 先解出 L*，主 LP 只用 L*。

**严重程度**：低-中（**这是历史遗留问题，不是本次重构引入**——`EnvelopeModel` 重构前就这样写，do 报告未改）

**举证**：do 报告改动清单里没有 `EnvelopeModel` 的任何改动。

**修补建议**（不在本次重构范围，但应记入技术债）：
- 长期：把 `EnvelopeModel` 拆成"子 LP 求解 L*"和"主 LP 注入 L* 下界"两步
- 短期：在 `EnvelopeModel` docstring 注明"当前实现把性能/物理耦合在主 LP，与 V5 §7.5 解耦目标不一致，属技术债"

---

### 🟢 LOW-2 `C4Model` 实现与 V5 §4 (C2) 形式不符

**位置**：`src/problem/models/phys/bumps/_c4.py:42-48`

**问题**：V5 §4 (C2) 是 `N_C4^pwr = (S_C4^pwr)^{-1} · P_inter`——**电源 C4 数 = Interposer 总功耗 / 每 bump 承载功率**。但代码里 `C4Model` 的形式是：

```python
ctx.constrain("c4", B * expr, "<=", float(self._available),
              meaning="C4 信号焊球用尽——组间带宽天花板")
```

这是 `Σ ℓ_e ≤ N_SerDes`——**信号 C4 上限约束**，与 V5 §3c `ℓ_I2I + N_C4^pwr ≤ N_C4^total` 的形式接近，但**不是 V5 §4 (C2) 的电源 C4 数等式**。

**严重程度**：低（V5 §8 明列"G_die^amb 的构建"为待定案，C2/C3/C4 的实现也属于待定技术债；本次重构未引入此问题）

**举证**：grep 在 problem/ 下找 `P_inter`/`b_inter`/`G_inter` 0 命中——C2/C3/C4 跨层耦合段在代码里**未实现**。

**修补建议**：作为后续工作项，与 V5 §8 待定案一并处理；本次重构不要求改。

---

### 🟢 LOW-3 `WiringModel` 入参 `link_specs: list[dict]` 违反 STYLE §6

**位置**：`src/problem/models/phys/wiring/__init__.py:35`

```python
def __init__(self, grid: WiringGrid,
             link_specs: list[dict],  # ← 裸 dict 跨模块
             link_indices: list[int],
             lane_rates: np.ndarray):
```

**问题**：STYLE §6 明示"禁止裸 dict 跨模块（模块边界上传的是 frozen dataclass）"。`link_specs` 是模块入参，但用了 `list[dict]`——内部还 `spec.get("c4_pad")`/`spec.get("from_die")` 这种字符串键访问。

**严重程度**：低（历史遗留，不是本次重构引入）

**修补建议**（不在本次重构范围）：定义 `@dataclass(frozen=True) class LinkSpec:` 替代 dict。

---

### 🟢 LOW-4 `Substrate` 私有字段用 dataclass 字段前缀 `_`

**位置**：`src/physical/layout/substrate.py:34-35`

```python
@dataclass
class Substrate:
    ...
    _interposer_spacing_mm: float = 31.0   # ~26 + 5mm gap
    _interposer_height_mm: float = 38.0    # ~33 + 5mm gap
```

**问题**：dataclass 字段不应有 `_` 前缀——破坏默认 repr/序列化、与 dataclass field 命名约定冲突。如果要表达"内部使用"，应该用 `field(default=..., repr=False)` 或方法 `@property`。

**严重程度**：低

**修补建议**：去掉 `_` 前缀，改为 `interposer_spacing_mm` / `interposer_height_mm`，或用 `field(repr=False, init=False)` 表达"内部"。

---

## 2. 完整性检查结论

### 2.1 权责分明（用户最高要求）— **合格 ✓**

逐项核查（按用户提出的 4 个问题）：

| 检查项 | 结论 | 证据 |
|---|---|---|
| 数学层 problem/models/phys/ 有没有自己 import physical？ | **没有违规** | 3 处 import 全在 `if TYPE_CHECKING:` 守卫内（`_steady_state.py:17`、`_temp_limit.py:11`、`_bump.py:19`），运行时不加载 physical |
| 有没有自己 get_profile()、读 UCIe/SerDes 注册表？ | **没有** | grep `get_profile`/`UCIE_`/`SERDES_` 在 problem/models/ 下 0 命中——物理参数全从 builder 注入 |
| G/S/T 等物理量是不是都从 builder 注入？ | **是** | `BumpModel.__init__(die_budgets, ...)` 接收 DieBumpBudget；`SteadyStateModel.__init__(network, beta_p)` 接收 ThermalNetwork；`GlobalPowerModel.__init__(P0, ..., cooling, ...)` 接收 CoolingSolution |
| 几何层 physical/layout/ 有没有偷偷做 LP 约束？ | **没有** | grep `LinExpr`/`cvxpy`/`add_constraint` 在 physical/layout/ 下 0 命中；`<=`/`>=` 全是数值比较（`n_dies <= max_dies`、`feasible=(headroom >= 0)`） |
| 物理参数层 physical/config/ 是不是只是校验层？ | **是** | `validator.py` 仅做 dict key 完整性检查，无算法；`spec_*.py` 是 frozen dataclass 预设 + 简单 property，无算法逻辑 |
| builder 是不是唯一桥梁？ | **是** | `problem/builder/_scenario.py:25-30` 是 problem 内唯一运行时 import physical 的地方；其余 problem 模块对 physical 的引用全在 TYPE_CHECKING |

**insight 6（拓扑不变量与物理解耦）和 insight 7（全局最优解保证）**：
- insight 6 在代码中体现为：`EnvelopeModel` 把 lane 数（拓扑不变量）作为 L 的缩放，物理侧只接 `B · L` ——这部分解耦做到位 ✓
- insight 7 在代码中体现为：所有约束是线性不等式/等式，CvxSolver 用 LP 求全局最优 B* ——这部分做到位 ✓

### 2.2 V5 模型忠实度 — **部分实现，已知技术债**

| V5 章节 | 代码实现 | 状态 |
|---|---|---|
| §2 die 段（D2D 路由 + die 功耗 + 布线 + die-interposer 块矩阵热方程） | `EnvelopeModel` + `BumpModel` + `WiringModel` + `SteadyStateModel` | ✓ 大部分实现，但 die-interposer 块矩阵热方程简化为单一 die 级 G |
| §3 I2I 段（I2I 路由 + sub 热 + C4 约束） | `C4Model` 实现了 C4 上限；sub 热方程未实现 | ⚠ 部分实现 |
| §4 (C1) μbump 跨层分配 | `BumpModel` | ✓ |
| §4 (C2) C4 电源数跨层 `N_C4^pwr = (S_C4^pwr)^{-1} · P_inter` | `C4Model` 形式不同（信号 C4 上限而非电源 C4 等式） | ✗ 与 V5 不符（见 LOW-2） |
| §4 (C3) die → Interposer 功耗聚合 `P_inter = M_die→inter · P_die` | 未实现（grep `P_inter` 0 命中） | ✗ 未实现 |
| §4 (C4) sub → Interposer 温度反馈 `b_inter = G_inter^amb · T_sub` | 未实现（grep `b_inter` 0 命中） | ✗ 未实现 |
| §7 静态 oblivious Valiant 性能包络 | `EnvelopeModel` + `ConjugacySelector` | ✓ 概念在；但 f 仍是主 LP 变量（见 LOW-1） |
| §8 待定案 `G_die^amb` / `P` 路由矩阵 | 未实现 | ⚠ V5 自列待定 |

**符号命名**：代码用 generic `M`/`G`/`b`/`T`，未严格采用 V5 §1 增补符号表的 `M_X→Y`/`G_die`/`G_sub`/`G_inter^amb`/`T_die`/`T_inter`/`T_sub` 命名。但这是变量名简化，不是违规——V5 是数学定义，代码可用简短变量名。

### 2.3 STYLE.md 合规 — **基本合格，但 §2.2/§2.3 命名红线违规多处**

| STYLE 章节 | 合规情况 |
|---|---|
| §1 Model 三段式（__init__ 预计算 / build() ≤30 行 / cache_key() 返回可哈希元组） | ✓ `BumpModel`/`SteadyStateModel`/`GlobalPowerModel`/`WarpModel`/`EnvelopeModel`/`C4Model` 全部符合 |
| §2.2 子类带父类后缀（硬规则） | ✗ 7 处 backward compat alias 违规（见 BLK-1） |
| §2.3 已识别不规范命名清单 | ✗ `SConjugacyReps`/`AllDerangements`/`TrafficMatrix` 三项清单列了未改 |
| §4 注释双语规则（docstring 中文 / 函数内 `#` 英文） | ✓ 抽查 `_steady_state.py`/`_bump.py`/`_warp_limit.py`/`_analytic.py` 均符合 |
| §6 跨模块裸 dict | ⚠ `WiringModel.link_specs: list[dict]`（历史遗留，见 LOW-3） |
| §7 纯 OO | ✓ 无裸露模块级算法函数（`build_scenario` 是编排层 facade，可接受） |
| 无 `type: ignore` | ✓ grep `type:\s*ignore` 在 src/ 下 0 命中 |

### 2.4 测试覆盖 — **合格 ✓**

| 检查项 | 结论 |
|---|---|
| 所有 import 路径改对了吗？ | ✓ 跑 `run_all.py` 14 通过 |
| 测试数值断言保持不变（重构不改行为）？ | ✓ 14/3 与 do 报告完全一致 |
| 是否有测试因为重构被删除？ | ✗ 没有删除（`tests/_test_suite.py` 是 run_all.py 临时文件，每次自动生成） |
| 用 Python 验算 1-2 个关键数值 | ✓ 见 §1 BLK-2 的 pJ/bit 验算 + BumpBudget 数值验算（UBUMP_45UM @ 12×12mm die → 49777 total / 834 pwr / 48943 sig） |

### 2.5 物理参数对齐 — **不合规**（见 BLK-2）

| 参数 | 代码值 | 标准出处 | 判定 |
|---|---|---|---|
| UCIE_16G_ADVANCED pJ/bit | 0.3125 | UCIe 1.1 Advanced target = 0.25；JSSC 2026 实测 = 0.29 | 偏高，要求补出处 |
| UCIE_24G_ADVANCED pJ/bit | 0.3750 | UCIe 1.1 Spec Table 1-2 未单列 24G target | 无标准出处，疑似编造 |
| UCIE_32G_ADVANCED pJ/bit | 0.5000 | UCIe 2.0 Advanced 32G target = 0.5 | ✓ 符合 |
| SERDES_112G_VSR lane_rate_gbps | 106.25 | OIF 标称 112 Gbps（Keysight 72-116 Gbps 可变） | 不符，要求改正或补说明 |
| SERDES_112G_VSR pJ/bit | 4.0000 | 工业实测 3.6-4.5 pJ/bit | 数值合理（前提 rate 修正后） |
| UBUMP_25UM (pitch=25μm, I=40mA) | — | 工业典型 25μm μbump 载流 30-50 mA | ✓ |
| UBUMP_45UM (pitch=45μm, I=75mA) | — | UCIe 1.1 Advanced bump pitch 25-55μm；载流 50-100 mA | ✓ |
| C4_130UM (pitch=130μm, I=300mA) | — | 工业典型 130μm C4 pitch，载流 200-300 mA | ✓ |
| T_AMBIENT_K = 300 K (27°C) | — | 工业标准 ambient | ✓ |
| T_JUNCTION_MAX_K = 358.15 K (85°C) | — | 偏低（典型 105/125°C）+ docstring 误导（见 MED-4） | ⚠ |
| Air cooling 0.5 W/mm² | — | 工业典型 0.1-1 W/mm² | ✓ |
| Liquid cooling 2.0 W/mm² | — | 工业典型 1-5 W/mm² | ✓ |
| Immersion 5.0 W/mm² | — | 工业典型 5-50 W/cm²（即 0.5-5 W/mm²） | ✓ |
| Microfluidic 10.0 W/mm² | — | 工业上限 100-1000+ W/cm² | ✓ |

### 2.6 文档同步 — **部分合格**（见 BLK-3, BLK-4, MED-1, MED-2, MED-3）

| 文档 | 同步状态 |
|---|---|
| README.md 目录树 | ✓ 更新到 physical/config + layout + problem |
| README.md "12 个 .md" | ✗ 实际 17 个（见 BLK-4） |
| README.md "MATH_MODEL_COMPLETE_V4" | ✗ V5 已定稿，应改 V5（见 BLK-4） |
| CONTRIBUTING.md | do 报告说改了 `src/lp/models/` → `src/problem/models/`；未抽查 |
| STYLE.md §1/§5 | ✓ 已改 problem |
| STYLE.md §8 第 239 行 / §11 第 279 行 | ✗ 漏改 `lp` → `problem`（见 BLK-3） |
| AGENTS.md 版本说明 | do 报告说改了；AGENTS.md 是 workspace rule，不在审查范围 |
| DIRECTORY.md | ✗ 文件不存在，do 报告自称改过（见 MED-3） |
| `physical/params.py` docstring | ✗ 引用已删除的源文件（见 MED-1） |
| `benchmark/README.md` | ✗ 仍引用 `src/lp/builder.py`（见 MED-2） |
| `spec_interconnect.py` / `spec_bump.py` / `spec_thermal.py` docstring | ✗ 都说"原 ...py 一字未改"，原文件已删除（见 BLK-2） |

---

## 3. 阻塞项汇总（必须整改后才能放行）

| # | 阻塞项 | 严重程度 | 责任 |
|---|---|---|---|
| BLK-1 | STYLE §2.2/§2.3 命名红线多处违规（7 处 backward compat alias 公开导出） | 高 | 工程师改 |
| BLK-2 | 物理参数出处无法追溯（UCIE_16G/24G/SerDes lane_rate）+ 4 处 stale docstring | 高 | 工程师补出处或改正 |
| BLK-3 | STYLE.md 第 239/279 行漏改 `lp` → `problem` | 中 | 工程师改 |
| BLK-4 | README.md "12 个 .md" 错（实际 17 个）+ V4 → V5 未更新 | 中 | 工程师改 |

## 4. 建议项汇总（不阻塞但应跟进）

| # | 建议项 | 严重程度 | 责任 |
|---|---|---|---|
| MED-1 | `physical/params.py` docstring 引用已删除源文件 | 中 | 工程师改 |
| MED-2 | `benchmark/README.md:33` 仍引用 `src/lp/builder.py` | 中 | 工程师改 |
| MED-3 | DIRECTORY.md 不存在，do 报告自称改过 | 低-中 | 工程师核实 |
| MED-4 | `T_JUNCTION_MAX_K` docstring 混淆"结温上限"与"翘曲约束" | 中 | 工程师改 |
| MED-5 | `_analytic.py:25` 默认 T_max=358.15 硬编码 | 中 | 工程师改 |
| MED-6 | `Substrate.c4_budget` 硬编码 858.0/300.0 | 中 | 工程师改 |
| LOW-1 | `EnvelopeModel` 性能/物理耦合在同一 LP（与 V5 §7.5 不符，历史遗留） | 低-中 | 后续工作 |
| LOW-2 | `C4Model` 形式与 V5 §4 (C2) 不符（历史遗留） | 低 | 后续工作 |
| LOW-3 | `WiringModel` 入参 `list[dict]` 违反 STYLE §6（历史遗留） | 低 | 后续工作 |
| LOW-4 | `Substrate` dataclass 字段用 `_` 前缀（反模式） | 低 | 工程师改 |

---

## 5. 明确承认（工程师做对的）

按角色 prompt 要求——"一旦证据充分证明代码合理，你也要明确承认，不为了显得严格而硬挑"：

1. **权责分明做得好**——builder 是 problem 与 physical 的唯一运行时桥梁，math 层对 physical 的引用全在 TYPE_CHECKING 守卫内。这一条是用户最高要求，工程师做到了 ✓
2. **过度工程清理到位**——`physical/interconnect/`、`physical/bump/`、`physical/thermal/_cooling.py`/`_config.py`、`src/layout.py`（迁到 facade）、`src/physical/interposer.py`、`src/physical/substrate.py` 全部按 do 报告删除/迁移到位 ✓
3. **WarpModel 实现保留 + docstring 修正**——do 报告对 WarpModel 的处理是合理的（实现保留作技术记录，docstring 修正"待实现"为"已实现但有意不导出"）✓
4. **`_warp_limit.py` 测试 (test0402_warp.md) 跑通**——验证了 WarpModel 的 W·K = warp_coeff 和 rhs = ΔT_max − W·G⁻¹(P0+b) 数学正确性 ✓
5. **测试断言保持不变**——重构前后跑 `run_all.py` 都是 14 通过 3 失败，重构未破坏行为 ✓
6. **`physical.layout.thermal_network` 导出 `ThermalNetworkBuilder` + `AnalyticNetworkBuilder`**——消费方仍可直接 import，未因 problem/__init__.py 移除导出而断链 ✓
7. **`type: ignore` 0 命中**——TYPE_CHECKING 守卫使用得当 ✓
8. **UCIE_32G_ADVANCED 0.5 pJ/bit** 完全符合 UCIe 2.0 Advanced 32G target ✓
9. **T_AMBIENT_K=300K (27°C)**、**Air/Liquid/Immersion/Microfluidic 散热密度** 均符合工业标准 ✓
10. **BumpSpec 预设 (UBUMP_25UM/45UM/C4_130UM/Hybrid)** 数值合理 ✓

---

## 6. 给工程师的整改优先级

按工作量从小到大排序：

1. **30 分钟内可完成**：BLK-3（STYLE.md 第 239/279 行 `lp`→`problem`）、BLK-4（README.md "12"→"17" 和 V4→V5）、MED-2（benchmark/README.md:33 路径更新）、MED-3（核实 DIRECTORY.md 是否真存在过）
2. **1 小时内可完成**：MED-1（physical/params.py docstring 重写）、MED-4（T_JUNCTION_MAX_K docstring 改正）、MED-5（_analytic.py 用 T_JUNCTION_MAX_K）、MED-6（Substrate 用 Interposer.area_mm2）、LOW-4（Substrate 去掉 `_` 前缀）
3. **2-4 小时（核心）**：BLK-1（删除 7 处 backward compat alias，更新 `__all__`，跑 grep 确认无外部引用）、BLK-2（补物理参数出处：UCIE_24G 线性插值要在 docstring 注明；SerDes lane_rate 改 112.0 或注明 106.25 是 Ethernet payload rate）
4. **后续工作**（不阻塞本次重构）：LOW-1（EnvelopeModel 拆子 LP/主 LP）、LOW-2（C4Model 改为 V5 §4 C2 形式）、LOW-3（WiringModel 用 LinkSpec frozen dataclass）

整改完成 BLK-1/2/3/4 后，本次重构可判定为**通过**。
