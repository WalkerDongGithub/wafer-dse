# Wafer DSE

晶圆级交换机（Wafer-Scale Switch）设计空间探索工具。

在架构设计早期，快速判断某种**网络拓扑 + 路由策略 + 封装工艺**的组合是否具备达到目标无阻塞带宽和功耗要求的潜力。

## 架构

```
用户需求 (YAML)
     │
     ▼
┌─────────────────────────┐
│  ArchitectureModel       │  编排层
│  1. 构建拓扑              │
│  2. 按 route 选择求解器   │
│  3. 计算 nonblocking     │
└──────────┬──────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌──────────┐
│ Topology │ │  Solver   │
│ 子包     │ │  子包      │
└─────────┘ └──────────┘
     │           │
     ▼           ▼
  NetworkPotential ──► PackagingModel ──► FeasibilityReport
     │                      │                    (JSON / CSV / Markdown)
     │                      ▼
     │                 checks/ (4 个独立检查单元)
     │
     ▼
┌──────────────────────────────────────────┐
│  层次化 DSE (die → group → wafer)         │
│                                          │
│  DieEstimator  ──► GroupExplorer         │
│  (单 die 物理)     (K 分割枚举)            │
│                          │               │
│                          ▼               │
│                     WaferAssembler       │
│                     (多 group + 组间互连) │
└──────────────────────────────────────────┘
```

### 模块结构

```
src/wafer_dse/
├── architecture_model/      体系结构级初筛
│   ├── topology/            拓扑定义（按拓扑族分文件）
│   │   ├── base.py          Topology ABC
│   │   ├── mesh.py          Mesh
│   │   ├── torus.py         Torus
│   │   ├── kary_ncube.py    k-ary n-cube（n 维泛化）
│   │   └── dragonfly.py     Dragonfly / DragonflyPlus
│   ├── solver/              求解器（接口 + 算法 + 实现三层分离）
│   │   ├── interface.py     Solver ABC + SolverResult
│   │   ├── algorithm/       纯数学工具（不感知拓扑）
│   │   │   ├── hungarian.py     Hungarian 算法
│   │   │   └── derangement.py   max-weight derangement
│   │   ├── fixed_route.py   FixedRouteSolver (纯 Python)
│   │   └── rust_backend.py  Rust 加速后端（透明回退）
│   └── model.py             编排层（薄 facade）
├── packaging_model/         封装级初筛
│   ├── checks/              独立检查单元（一个文件一个 check）
│   │   ├── base.py          PackagingCheck ABC + CheckResult
│   │   ├── die_area.py      DieAreaCheck
│   │   ├── power.py         PowerCheck
│   │   ├── external_io.py   ExternalIOCheck
│   │   └── internal_io.py   InternalIOCheck
│   └── model.py             编排层（薄 facade）
├── die_model/               单 die 物理模型
│   └── estimator.py         DieEstimator（crossbar O(N²)+ buffer O(N)）
├── group_dse/               Group 级 DSE
│   └── explorer.py          GroupExplorer（K 分割枚举 + 选最优）
├── wafer_dse/               晶圆级 DSE
│   └── assembler.py         WaferAssembler（多 group + 组间互连）
├── user_interface/          用户指令解析 + 驱动
├── reporting/               报告生成（JSON / CSV / Markdown）
├── models.py                跨模块数据契约（dataclass）
└── config.py                配置读取器
```

### 支持的拓扑

| 拓扑 | 说明 |
|---|---|
| `Mesh(size)` | 二维 mesh（无边环绕） |
| `Torus(size)` | 二维 torus（有边环绕） |
| `KaryNCube(k, n, wrap)` | n 维 k-ary n-cube，泛化 Mesh/Torus |
| `Dragonfly(a, p, h)` | 标准 Dragonfly（Cray Cascade 风格） |
| `DragonflyPlus(a, p, h, t)` | Dragonfly+ 骨架（待完整实现） |

### 支持的求解策略

| 求解器 | 路由 | 算法 |
|---|---|---|
| `FixedRouteSolver` | `det`, `val` | Hungarian exact worst-case (O(N³)) |
| `FixedRouteSolver` (Rust) | `det`, `val` | 同上，Rust 加速版（通过 `rust_backend.py` 透明调用） |

### 层次化 DSE（die → group → wafer）

为 Dragonfly 拓扑提供递进式物理方案探索：

| 层级 | 模块 | 职责 |
|---|---|---|
| **Die** | `DieEstimator` | 单 die 面积/功耗/可行性：crossbar O(N²) + buffer O(N) + SerDes + D2D PHY |
| **Group** | `GroupExplorer` | 枚举 K=1..a die 分割方案，选可行的最小 die 数 |
| **Wafer** | `WaferAssembler` | 多 group 枚举 (a,p,h,g) + 组间全互联互连预算检查 |

### Rust 加速后端（可选）

`rust-solvers/` 包含 Hungarian、derangement 和 FixedRouteSolver 的 Rust 实现，通过 `wafer-solve` 二进制提供约 10–50× 的加速：

```bash
make rust-build           # 编译优化版本
make test-rust-backend    # 验证 Rust ↔ Python 等价性
make test-all             # 完整测试（含 Rust 后端）
```

Python 端在 [rust_backend.py](src/wafer_dse/architecture_model/solver/rust_backend.py) 中自动探测二进制，不可用时静默回退纯 Python。

## 快速开始

### 安装

```bash
# 克隆项目（含子模块）
git clone --recurse-submodules https://github.com/WalkerDongGithub/wafer-dse.git
cd wafer-dse

# 开发模式安装
pip install -e .

# 编译 Rust 加速后端（可选）
make rust-build

# 编译拥塞仿真器（可选）
cd vendor/congestion && cargo build --release
```

核心求解器仅使用 Python 标准库，零外部依赖。测试依赖 `pytest`。

### 命令行

```bash
# 使用示例配置运行
python -m wafer_dse --config configs/example_user_request.yaml

# 或指定自己的配置
python -m wafer_dse --config path/to/my_request.yaml
```

### 配置文件示例

```yaml
# my_request.yaml
requirement:
  target_nonblocking_gbps_per_port: 800
  max_power_w: 200
  port_count: 16
  max_die_area_mm2: 800
  packaging_config: example_packaging.yaml
  strictness:
    mode: full

topologies:
  mesh4:
    kind: mesh
    size: 4
    routes: [det, val]
  torus4:
    kind: torus
    size: 4
    routes: [det, val]
  dragonfly_small:
    kind: dragonfly
    a: 2
    p: 2
    h: 1
    routes: [det, val]
  kary_3d:
    kind: kary_ncube
    size: 4
    n: 3
    wrap: true
    routes: [det]

output:
  directory: outputs/my_run
```

### Python API

```python
from wafer_dse.architecture_model import (
    ArchitectureModel, FixedRouteSolver, KaryNCube
)
from wafer_dse.models import Requirement, Strictness, TopologySpec
from wafer_dse.packaging_model import PackagingModel

# —— 编排层（自动选择求解器） ——
req = Requirement(800, 200, Strictness("full"), "unused")
spec = TopologySpec(kind="torus", size=4, route="det")
net = ArchitectureModel().evaluate(req, spec)
print(f"nonblocking = {net.nonblocking_gbps_per_port:.1f} Gbps")

# —— 直接使用求解器 ——
topo = KaryNCube(k=4, n=3, wrap=True)
result = FixedRouteSolver().solve(topo, "det", 800)
print(f"worst_load = {result.worst_load}")

# —— 封装级检查 ——
est = PackagingModel("configs/example_packaging.yaml").estimate(req, net)
print(f"area={est.die_area_mm2:.1f} mm², power={est.power_w:.1f} W")
```

## 测试

```bash
make test               # 全部 223 个测试
make test-hungarian     # 纯算法测试
make test-topology      # 拓扑测试
make test-solver        # 求解器测试
make test-quiet         # 安静模式
make test-slow          # 显示最慢的 10 个测试
make test-rust-backend  # Rust 后端等价性测试
make test-all           # 完整测试（含 Rust）
make ci                 # CI 流水线（构建 + 测试）
```

测试策略：

| 策略 | 应用模块 |
|---|---|
| **穷举验证**（枚举全部可能解） | Hungarian (N≤8, 40320 排列), Derangement (N≤8, 14833 derangements) |
| **已知基准值回归** | FixedRouteSolver 对各种拓扑的 nonblocking / worst_load |
| **数学性质不变式** | Hungarian 行列常数性质, Derangement 无自环约束 |
| **往返一致性** | 所有拓扑的 to_loc / to_node |
| **路径结构性约束** | 起终点、维序、邻接、无环、收敛 |
| **Witness 自洽性** | 重放 witness traffic 验证 solver 内部计算 |
| **手工验算公式** | 每个 packaging check 的面积/功耗/budget 公式，die estimator crossbar/buffer 公式 |
| **边界与失败路径** | 每个 check 的超限/边界/零输入场景 |
| **枚举完整性** | Group DSE 的 partition 枚举和 crossbar 端口公式 |
| **缩放单调性** | Group/Wafer DSE 的 die 数-面积-功耗单调关系 |
| **等价性** | Rust 后端 vs 纯 Python 在 Hungarian/derangement/solver 上的精确一致性 |

## 贡献

请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解代码规范。

## 依赖

| 层 | 依赖 | 说明 |
|---|---|---|
| **Python** | 标准库（零外部依赖） | Python 3.9+ |
| **Python 测试** | `pytest` ≥7 | `pip install -e ".[test]"` |
| **Rust 加速（可选）** | [rust-solvers/](rust-solvers/) | Cargo workspace，编译后约 10–50× 加速 |
| **拥塞仿真（可选）** | [vendor/congestion](vendor/congestion) | Git submodule，网络拥塞仿真器 |

```bash
# 首次克隆
git clone --recurse-submodules https://github.com/WalkerDongGithub/wafer-dse.git

# 如果已克隆，拉取子模块
git submodule update --init --recursive
```

## 许可

MIT
