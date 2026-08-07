# Wafer DSE

晶圆级交换机设计空间探索——用线性规划判定"这个拓扑 + 这些物理参数能撑多大带宽？"

## 架构

```
topology/       全局顶层——拓扑定义（Mesh / Dragonfly / Torus / k-ary n-cube）
physical/       辅助模块——bump 规格、热参数、互连标准（纯数据，被调用）
lp/             核心引擎
  ctx/           变量声明 + 约束收集（模型之间的"语言"）
  models/        约束模型（性能 / bump / 热）
    topo/          拓扑结构分析（一次性提取）
    perf/          性能约束（多排列包络）
    phys/          物理约束（bump 预算 + 热网络）
  engine/        求解器 + 缓存 + 持久化
  queries/       数学问题定义（feasibility / bmax / ...）
```

## 快速开始

```python
import numpy as np
from lp import Ctx, CvxSolver, Runner, FeasibilityQuery, BmaxQuery
from lp import analyze_topo, EnvelopeModel, SConjugacyReps
from lp import BumpModel, NetworkModel, build_thermal_network
from topology import Mesh
from physical.bump.bump import DieBumpBudget, UBUMP_45UM

# 1. 拓扑 → 结构数据
cs = analyze_topo(Mesh(2))

# 2. 装配模型
perf = EnvelopeModel(cs, SConjugacyReps(True).select(4))
budgets = [DieBumpBudget(f'd{i}', UBUMP_45UM, 12, 12, 50, 0.8, 0.7) for i in range(4)]
bump = BumpModel(cs, budgets)
G = np.eye(4) * 0.9 - np.eye(4, k=1) * 0.1 - np.eye(4, k=-1) * 0.1
net = build_thermal_network(G, np.full(4, 240.0), 358.15, cs.die_to_links, cs.n_links)
therm = NetworkModel(net)

# 3. 求解
engine = CvxSolver()
runner = Runner(engine)
q = FeasibilityQuery()
sol = runner.solve(q.query_id, 800.0, Ctx(), [perf, bump, therm])
r = q.interpret(sol, Ctx(), 800.0)
print(f"B=800: feasible={r.feasible}")

# 4. 找最大带宽
bq = BmaxQuery()
result = bq.solve(runner, lambda b: (Ctx(), [perf, bump, therm]))
print(f"B* = {result.B_star:.0f} Gbps")
```

## 安装

```bash
pip install numpy pyyaml cvxpy
```

## 测试

```bash
PYTHONPATH=src python3 tests/test_ctx.py
PYTHONPATH=src python3 tests/test_traffic.py
PYTHONPATH=src python3 tests/test_engine.py
PYTHONPATH=src python3 tests/test_queries.py
```

## 许可

MIT
