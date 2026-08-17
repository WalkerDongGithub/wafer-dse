# Do 报告 — 代码工程师（01）

日期：2026-08-17
任务：UCIe BER 分档修正 + 诊断原语 binding 判定（margin≈0 优先）

## 一、UCIe BER 硬错误修正

文件：`src/physical/interconnect/ucie.py`

按代码审查员给的 UCIe 2.0 分档，把六个实例的 `ber` 从统一 `1e-27` 改为分档：

| 实例 | 原值 | 新值 |
|------|------|------|
| UCIe-12G-Advanced | 1e-27 | 1e-27（保留） |
| UCIe-16G-Advanced | 1e-27 | **1e-15** |
| UCIe-24G-Advanced | 1e-27 | **1e-15** |
| UCIe-32G-Advanced | 1e-27 | **1e-15** |
| UCIe-8G-Standard  | 1e-27 | 1e-27（保留） |
| UCIe-16G-Standard | 1e-27 | **1e-15** |

无 ber 相关测试断言需要修改（tests/ 中无对 ucie.py ber 的断言）。

## 二、诊断原语 binding 判定改进

文件：`src/diagnostics.py`

- 新增模块常量 `_MARGIN_EPS = 1e-6`：margin ≈ 0 的绝对容差。
- `solve_diagnostic` 的 binding 判定改为：
  - **margin ≈ 0 优先**：物理约束（bump/therm/route/c4）只要 `|rhs−lhs| <= 1e-6` 就判 binding，即使 dual=0。
  - **duals 非零辅助**：保留原 duals 键集合（含 perf 侧如 `dem0` 等），并补齐数值噪声项。
  - 绑定条目按 `|dual|` 降序；margin-only（dual=0）条目排在末尾，dual 字段为 0.0。
- 保留 `constraint_family()` 前缀归类；infeasible 时 binding 仍强制为空（不改）。
- 模块 docstring 同步更新（binding 描述改为 margin≈0 优先 + duals 辅助）。

## 三、测试

- `tests/diagnostics/test12_diagnostic.md`：
  - 契约清单新增第 4 条「margin ≈ 0 优先」。
  - 新增「## 4. 退化点：物理约束取等但 dual=0 也判 binding」：toy 场景 L0≥2 与物理上界 L0≤2 同点取等，monkeypatch `CvxSolver.solve` 返回 duals 为空的确定性退化解，断言 `bump_d0` 经 margin≈0 判入 binding 且 dual=0。
  - 结论段同步更新。
- 验收命令 `cd tests && PYTHONPATH=../src python3 run_all.py`：**14 files, 14 passed, 0 failed**（全绿）。

## 四、待核实 / 备注

1. `_MARGIN_EPS=1e-6` 为绝对容差，未做相对容差归一。物理约束 rhs 量级差异大（bump 9900 vs therm ~100），若后续有接近量级边界但确实 slack 的约束，需按家族归一；当前 toy 与小拓扑无此风险。
2. 退化点测试用 monkeypatch 隔离求解器 dual 行为（CLARABEL 内点法对退化点不一定给 dual=0），未改生产求解器。
3. 未跑大实验（内存约束）：仅 toy 参数 + 小拓扑验证；BER 只进报告字段，不影响 B* 数值。
