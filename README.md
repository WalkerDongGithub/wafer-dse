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
                                           (JSON / CSV / Markdown)
```

### 模块结构

```
src/wafer_dse/
├── architecture_model/      体系结构级初筛
│   ├── topology/            拓扑定义
│   │   ├── base.py          Topology ABC
│   │   ├── mesh.py          Mesh
│   │   ├── torus.py         Torus
│   │   ├── kary_ncube.py    k-ary n-cube（n 维泛化）
│   │   └── dragonfly.py     Dragonfly / DragonflyPlus
│   ├── solver/              求解器
│   │   ├── interface.py     Solver ABC + SolverResult
│   │   ├── algorithm/       纯数学工具
│   │   │   ├── hungarian.py     Hungarian 算法
│   │   │   └── derangement.py   max-weight derangement
│   │   └── fixed_route.py   FixedRouteSolver
│   └── model.py             编排层
├── packaging_model/         封装级初筛（面积 / 功耗 / IO 预算）
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
# 无外部依赖（标准库即可运行）
pip install .        # 可选，或直接 PYTHONPATH=src 使用
```

### 运行

```bash
# 使用示例配置运行
python -m wafer_dse --config configs/example_user_request.yaml

# 或使用自己的配置
python -m wafer_dse --config path/to/your_request.yaml
```

### 配置文件示例

```yaml
# configs/example_user_request.yaml
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

output:
  directory: outputs/my_run
```

### Python API

```python
from wafer_dse.architecture_model import (
    ArchitectureModel, FixedRouteSolver, KaryNCube
)
from wafer_dse.models import Requirement, Strictness, TopologySpec

# 编排层（自动选择求解器）
req = Requirement(800, 200, Strictness("full"), "unused")
spec = TopologySpec(kind="torus", size=4, route="det")
net = ArchitectureModel().evaluate(req, spec)
print(f"nonblocking = {net.nonblocking_gbps_per_port:.1f} Gbps")

# 直接使用求解器
topo = KaryNCube(k=4, n=3, wrap=True)
result = FixedRouteSolver().solve(topo, "det", 800)
print(f"worst_load = {result.worst_load}")
```

## 测试

```bash
# 运行全部测试
make test

# 或手动
PYTHONPATH=src python -m pytest tests/ -v

# 单个文件
PYTHONPATH=src python -m pytest tests/test_hungarian.py -v
```

测试覆盖：
- **Hungarian / Derangement**：N≤8 穷举验证（枚举全部排列确认全局最优）
- **拓扑**：坐标往返一致、维序路由、邻接性、无环、收敛
- **求解器**：已知基准值回归 + witness 自洽性重放
- **编排层**：全部拓扑类型 + solver 注入

## 依赖

- Python 3.9+
- 零外部依赖（核心求解器仅使用标准库）
- 测试依赖：`pytest`

## 许可

MIT
