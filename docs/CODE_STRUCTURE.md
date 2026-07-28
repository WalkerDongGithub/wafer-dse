# 代码结构

## 目录总览

```
wafer-dse/
├── src/wafer_dse/
│   ├── lp/                           ★ 统一 LP 引擎
│   ├── architecture_model/
│   │   ├── topology/                 拓扑定义 (ABC + 4 种)
│   │   └── solver/                   求解器 (Hungarian + Rust 后端)
│   ├── physical/
│   │   ├── bump/                     μbump / C4 / Hybrid bond
│   │   ├── interconnect/             17 种互连标准 + 注册表
│   │   ├── thermal/                  热求解器
│   │   ├── interposer.py             Interposer 模型
│   │   └── substrate.py             Substrate 互联模型
│   ├── models.py                     数据契约
│   ├── config.py                     PyYAML 配置读取
│   ├── pareto.py                     Pareto 前沿
│   ├── trace/                        结构化日志
│   ├── reporting/                    文件输出 (JSON/CSV/Markdown)
│   └── __main__.py                   CLI 入口
├── rust-solvers/                     Rust 加速 (可选)
├── configs/                          示例配置
├── tests/                            测试
└── docs/                             文档
```

## 各模块职责

### `lp/` — 统一 LP 引擎

DSE 的核心。将拓扑、bump 预算、热约束编码为**单一线性规划**，变量为链路负载向量 **L**。

| 文件 | 职责 |
|---|---|
| `engine.py` | `UnifiedLp`: 逐步添加约束，一次 solve。det 路径走 Hungarian，valiant 路径走 cvxpy LP |
| `performance.py` | 链路权重矩阵 + per-link 最坏负载 (Hungarian) + 路径-链路 incidence (供 LP) |
| `geometry.py` | 每 die 一个 bump 预算约束: Σ L_e·B/R_e ≤ N_signal |
| `thermal.py` | 功率密度约束: Σ p_e·L_e ≤ A·q_max |
| `report.py` | `LpResult`: feasible, constraints[], dual_values, 人类可读报告 |

### `architecture_model/topology/` — 拓扑定义

所有拓扑实现 `Topology` ABC (6 个方法: `to_loc`, `to_node`, `is_terminal`, `terminal_num`, `node_num`, `next`)。基类提供 `det()` 和 `valiant()` 的通用实现。

| 文件 | 拓扑 | 参数 |
|---|---|---|
| `mesh.py` | 2D Mesh | `size` |
| `torus.py` | 2D Torus | `size` |
| `kary_ncube.py` | k-ary n-cube | `k, n, wrap` |
| `dragonfly.py` | Dragonfly / DragonflyPlus | `a, p, h, t` |

### `architecture_model/solver/` — 求解器

| 文件 | 职责 |
|---|---|
| `interface.py` | `Solver` ABC + `SolverResult` dataclass |
| `algorithm/hungarian.py` | Hungarian 最小成本匹配 O(N³) |
| `algorithm/derangement.py` | max-weight derangement (无自环排列) |
| `fixed_route.py` | `FixedRouteSolver`: 固定路由 + Hungarian 精确最坏情况 |
| `rust_backend.py` | 批量 Hungarian/derangement 的 Rust 加速，不可用时静默回退 |

### `physical/` — 物理模型

作为 **LP 约束构建器的数据源**，不再独立做布尔判断。

| 模块 | 关键类 | 提供给 LP 的约束 |
|---|---|---|
| `bump/` | `BumpSpec`, `DieBumpBudget` | §2 几何: N_signal per die |
| `interconnect/` | `InterconnectProfile`, `LinkBudget` | R_e (lane 速率), p_e (per-lane 功耗) |
| `thermal/` | `CoolingSolution`, `ThermalSolver` | §3 热: q_max, G 矩阵 |
| `interposer.py` | `Interposer` | 多 die 到一个 interposer 的映射 |
| `substrate.py` | `Substrate` | interposer 间互联距离 + C4 预算 |

### 支撑模块

| 文件 | 职责 |
|---|---|
| `models.py` | 数据契约: `Requirement`, `TopologySpec`, `Strictness` |
| `config.py` | YAML/JSON 配置 → dict |
| `pareto.py` | Pareto 前沿 + 品质因数 (FOM) |
| `trace/` | 结构化日志: console / report / summary |
| `reporting/` | JSON / CSV / Markdown 文件输出 |
| `__main__.py` | CLI: 解析配置 → 枚举拓扑 → 求解 → 报告 |

## 为什么是这个结构

旧的 DSE 有三个并行的执行路径（ArchitectureModel+PackagingModel, dse_demo.py, GroupExplorer+WaferAssembler），物理模块各自做独立布尔判断，没有联立。

新架构遵循 MATH_MODEL.md 的数学框架：**外层枚举离散选择（拓扑、die、placement），内层解一个四组约束联立的统一 LP**。唯一变量 **L**（链路负载向量）是连接性能/几何/功耗/布线的桥梁。

`lp/` 是新核心。`physical/` 模块不再自己判断 feasible/infeasible，而是给 LP 引擎提供系数矩阵和常数向量。`topology/` 和 `solver/` 提供网络结构数据和快速求解子程序。
