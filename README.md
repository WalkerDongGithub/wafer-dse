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
                         │                    (JSON / CSV / Markdown)
                         ▼
                    checks/ (4 个独立检查单元)
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
│   │   └── fixed_route.py   FixedRouteSolver
│   └── model.py             编排层（薄 facade）
├── packaging_model/         封装级初筛
│   ├── checks/              独立检查单元（一个文件一个 check）
│   │   ├── base.py          PackagingCheck ABC + CheckResult
│   │   ├── die_area.py      DieAreaCheck
│   │   ├── power.py         PowerCheck
│   │   ├── external_io.py   ExternalIOCheck
│   │   └── internal_io.py   InternalIOCheck
│   └── model.py             编排层（薄 facade）
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

## 快速开始

### 安装

```bash
pip install -e .        # 开发模式安装，或直接 PYTHONPATH=src 使用
```

无外部依赖，核心求解器仅使用 Python 标准库。测试依赖 `pytest`。

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
make test              # 全部 177 个测试
make test-hungarian    # 纯算法测试
make test-topology     # 拓扑测试
make test-solver       # 求解器测试
make test-quiet        # 安静模式
make test-slow         # 显示最慢的 10 个测试
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
| **手工验算公式** | 每个 packaging check 的面积/功耗/budget 公式 |
| **边界与失败路径** | 每个 check 的超限/边界/零输入场景 |

## 贡献

请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解代码规范。

## 依赖

- Python 3.9+
- 核心：零外部依赖（仅标准库）
- 测试：`pytest`

## 许可

MIT
