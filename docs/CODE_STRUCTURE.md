# 新 DSE 代码结构说明

## 目标

本目录是一个独立完整的晶圆级交换机 DSE 小项目，不依赖旧 Titan 命名，也不依赖外部 NormNet 目录。它按职责拆成三层：

```text
wafer_dse/
  src/wafer_dse/
    user_interface/       用户指令级模块
    architecture_model/   体系结构级初筛模块
    packaging_model/      封装级初筛模块
    die_model/            单 die 物理模型（面积/功耗/预算）
    group_dse/            Group 级 DSE（die 分割枚举）
    wafer_dse/            晶圆级 DSE（多 group + 组间互连）
    reporting/            运行结果报告模块
  rust-solvers/           Rust 加速后端（可选）
```

## 1. 用户指令级模块

路径：

```text
src/wafer_dse/user_interface/
```

输入：

- 目标无阻塞带宽；
- 峰值功耗上限；
- 严格程度；
- 封装工艺配置文件；
- 待考查拓扑结构。

输出：

- 每个 topology 的 `FeasibilityReport`。

职责：

```text
读用户需求 -> 调 architecture model -> 调 packaging model -> 做耦合判断 -> 写报告
```

## 2. 体系结构级初筛模块

路径：

```text
src/wafer_dse/architecture_model/
```

输入：

- Requirement；
- TopologySpec，例如 mesh/torus/dragonfly。

说明：拓扑结构由用户指令级模块传入；进入 architecture model 后，它只是纯体系结构输入。

输出：

- NetworkPotential。

职责：

```text
拓扑 + route -> 独立 worst-case 求解器 -> nonblocking bandwidth -> required internal speedup
```

## 3. 封装级初筛模块

路径：

```text
src/wafer_dse/packaging_model/
```

输入：

- Requirement；
- NetworkPotential；
- packaging config。

输出：

- PackagingEstimate。

职责：

```text
网络需求 -> lane 数/面积/功耗估计 -> external/internal budget 判断
```

## 4. 报告模块

路径：

```text
src/wafer_dse/reporting/
```

输出：

```text
results.json
results.csv
report.md
```

`report.md` 包含 Mermaid 可视化图和候选结果表。

## 5. 单 die 物理模型

路径：

```text
src/wafer_dse/die_model/
```

输入：

- 封装工艺配置；
- crossbar 端口数、外部端口数、D2D 链路数。

输出：

- `DieEstimate`：面积/功耗账单 + 可行性检查。

职责：

```text
crossbar O(N²) + buffer O(N) + SerDes 线性 + D2D PHY 线性
→ 单 die 总 area / power
→ 检查 reticle limit 和 D2D 边沿密度
```

此模块只做物理账单，不感知网络拓扑。

## 6. Group 级 DSE

路径：

```text
src/wafer_dse/group_dse/
```

输入：

- Dragonfly 参数 (a, p, h)；
- Requirement + 封装配置。

输出：

- `GroupPlan`：网络性能 + K 分割方案的完整枚举。

职责：

```text
ArchitectureModel 评估组内网络
→ 枚举 K=1..a die 分割方案
→ 对每个方案调用 DieEstimator
→ 选出 die 数最少（面积最优）的可行方案
```

## 7. 晶圆级 DSE

路径：

```text
src/wafer_dse/wafer_dse/
```

输入：

- 晶圆总端口数；
- Requirement + 封装配置。

输出：

- `WaferPlan` 列表：所有可行的 (a, p, h, g) 组合。

职责：

```text
枚举 (a,p,h,g) 使 a×p×g = total_ports
→ 对每个 group 调用 GroupExplorer
→ 检查组间互连是否在 package 基板预算内
→ 按 total_dies 升序排列候选方案
```

## 8. Rust 加速后端（可选）

路径：

```text
rust-solvers/                          # Rust workspace
  ├── wafer-core/       类型定义 + I/O
  ├── wafer-hungarian/  Hungarian 算法（Rust）
  ├── wafer-derangement/ Derangement 算法（Rust）
  └── wafer-solve/      求解器 CLI（JSON 输入/输出）
```

Python 通过 `rust_backend.py` 调用 `wafer-solve` 二进制，签名完全兼容纯 Python 版本。不可用时自动回退。
