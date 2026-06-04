# 代码风格与贡献指南

所有新代码必须遵循以下原则。Code review 以此清单为基准。

---

### 1. 文件粒度：一个模块一个文件

禁止将多个类或函数堆在同一个文件中。每个独立的抽象单元应有自己的文件：

```
✅ 正确                                ❌ 错误
topology/                             topology.py   # 所有拓扑塞在一起
├── base.py      # Topology ABC
├── mesh.py      # Mesh
├── torus.py     # Torus
├── kary_ncube.py
└── dragonfly.py

solver/
├── interface.py    # Solver ABC
├── algorithm/
│   ├── hungarian.py
│   └── derangement.py
└── fixed_route.py  # 一个具体求解器

packaging_model/checks/
├── base.py         # PackagingCheck ABC
├── die_area.py     # 一个 check 一个文件
├── power.py
├── external_io.py
└── internal_io.py
```

**原则**：每个文件应能用一句话描述其唯一职责。如果描述中出现了"和"或"以及"，考虑拆分。

### 2. 分层解耦：接口 > 算法 > 实现

代码必须按依赖方向分层，内层不依赖外层：

```
编排层 (model.py)
  ├── 知道接口层（ABC）
  └── 不知道具体实现

接口层 (interface.py / base.py)
  ├── 定义 ABC + 输出 dataclass
  └── 不知道任何具体实现

算法层 (algorithm/)
  ├── 纯函数/纯数学
  ├── 不 import 任何本项目模块
  └── 不感知拓扑、网络、封装等上层概念

实现层 (fixed_route.py / die_area.py 等)
  ├── 实现接口层的 ABC
  ├── 可以 import 算法层
  └── 可以 import 下层数据模型
```

### 3. 多态扩展：不要写 if-else 分支

当需要多种求解策略或检查单元时，使用 ABC + 注册表模式，而不是条件分支：

```python
# ✅ 正确：多态 + 注册表
class Solver(ABC):
    @abstractmethod
    def solve(self, topo, route, cap) -> SolverResult: ...

class FixedRouteSolver(Solver): ...
class AdaptiveLPSolver(Solver): ...    # 未来扩展

def create_solver(route: str) -> Solver:
    for cls in _SOLVER_CLASSES:
        instance = cls()
        if route in instance.supported_routes:
            return instance
    raise ValueError(...)

# ❌ 错误：硬编码分支
def solve(topo, route, cap):
    if route in ("det", "val"):
        return _fixed_route_solve(...)
    elif route == "opt":
        return _adaptive_solve(...)
```

检查单元同理：

```python
# ✅ 正确：注册表
ALL_CHECKS: list[PackagingCheck] = [
    DieAreaCheck(),
    PowerCheck(),
    ExternalIOCheck(),
    InternalIOCheck(),
]
for check in ALL_CHECKS:
    result = check.run(cfg, req, net, lanes, ports)

# ❌ 错误：硬编码函数调用
area_ok = check_area(...)
power_ok = check_power(...)
```

### 4. 编排层是薄 facade

`model.py` 只做编排（构建对象 → 委托执行 → 聚合结果），不包含算法细节或业务逻辑：

```python
# ✅ 正确：薄编排
class ArchitectureModel:
    def evaluate(self, req, spec):
        topo = self._build_topology(spec)
        solver = create_solver(spec.route)    # 工厂选择
        result = solver.solve(topo, ...)       # 委托
        return NetworkPotential(...)           # 聚合

# ❌ 错误：编排层包含算法细节
class ArchitectureModel:
    def evaluate(self, req, spec):
        # 直接写 Hungarian / link weight / ...   ← 不允许
        ...
```

### 5. 数据契约用 frozen dataclass

跨模块传递的数据必须用 `frozen=True` 的 dataclass 定义在 `models.py`（或模块内的 `interface.py`）：

```python
@dataclass(frozen=True)
class SolverResult:
    worst_load: float
    nonblocking_gbps_per_port: float
    ...
```

- 不可变，保证模块间不会互相意外修改
- 字段类型明确，自文档化
- 禁止用裸 dict 作为模块间接口

### 6. 求解器与拓扑的解耦

求解器只依赖 `Topology` ABC 的公开方法（`terminals()`, `det()`, `valiant()`），不依赖具体拓扑实现：

```python
# ✅ 正确
class FixedRouteSolver(Solver):
    def solve(self, topo: Topology, route: str, cap: float) -> SolverResult:
        terminals = topo.terminals()       # ABC 方法
        paths = topo.det(src, dst)         # ABC 方法
        ...

# ❌ 错误
class FixedRouteSolver(Solver):
    def solve(self, topo: Mesh, ...):       # 依赖具体类型
        if topo.size == 4: ...              # 依赖具体属性
```

新拓扑只需实现 `Topology` 接口，所有现有求解器自动兼容。

### 7. 算法纯函数化

`algorithm/` 中的函数必须是纯数学函数：
- 不访问文件系统
- 不访问网络
- 不 import 本项目其他模块
- 相同输入永远产生相同输出

```python
# ✅ 正确
def hungarian_min_cost(cost: list[list[float]]) -> tuple[float, list[int]]:
    """输入方阵，输出最小成本匹配。"""

# ❌ 错误
def hungarian_min_cost(topo: Topology):    # 不应依赖拓扑
    cost = build_cost_from_topo(topo)       # 不应在算法中构建输入
```

### 8. 测试要求

每个模块必须有对应的单元测试文件：

| 被测模块 | 测试文件 | 最低要求 |
|---|---|---|
| 纯算法 (`algorithm/`) | `test_<name>.py` | 穷举验证（小 N 枚举所有解）+ 数学性质不变式 |
| 拓扑 (`topology/`) | `test_topology_<name>.py` | 全节点坐标往返 + 全对路由收敛 + 结构性约束 |
| 求解器 (`solver/`) | `test_solver_*.py` | 已知基准值回归 + witness 自洽性 |
| 检查单元 (`checks/`) | `test_packaging_checks.py` | 手工验算公式 + 通过/失败/边界 |

- **穷举验证**：对 N 足够小的纯数学函数，枚举所有可能的输出确认最优
- **已知基准值**：对 solver 输出固定 ground truth，任何改动必须保持这些值不变
- **自洽性**：输出中包含的 witness / 中间值必须可以反推验证

### 9. 命名与 docstring

- 类名用 `PascalCase`，函数/变量用 `snake_case`
- `_private` 前缀表示模块内部实现
- 每个公开类和方法必须有 docstring（中文），包含一句话概述 + 关键公式/算法引用
- 禁止无意义的注释（如 `# 初始化变量`），注释应解释"为什么"而非"是什么"

### 10. 禁止事项

- **禁止循环导入**：如果出现，说明分层方向错误
- **禁止 `*` 导入**：`__all__` 用于文档，实际导入必须显式
- **禁止裸 dict 跨模块**：跨模块数据用 dataclass
- **禁止硬编码配置值**：所有工艺参数从 YAML 配置读取
- **禁止 `type: ignore`**：类型问题应修正而非抑制
