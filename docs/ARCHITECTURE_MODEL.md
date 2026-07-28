# Wafer DSE 架构说明

## 一句话

> 外层枚举离散架构选择，内层求解一个多约束耦合的线性规划。

## 两层 DSE 架构

```
═══════════════════════════════════════════════════════════════
外层（离散枚举）
  ├── 拓扑选择: 谁和谁连 → G = (V, E)
  ├── 芯粒选型: 从库中选 die（面积、功耗、bump pitch 固定）
  ├── Placement: 哪个 die 放哪个 grid 位置
  └── 每个离散组合 → 所有常数矩阵固定 → 进入内层

───────────────────────────────────────────────────────────────
内层（统一 LP）
  find  L = (L_e)_{e∈E}     — 链路负载向量，唯一变量

  s.t.  L ∈ L_perf          — 性能多面体：双随机流量 + 路径分流
        M·L ≤ b             — 几何约束：bump 预算 per die
        C·L ≤ d             — 热约束：功率密度上限
        A·L ≤ c             — 布线约束：grid 容量 (v2)

  输出: feasible? 哪个约束是瓶颈? 对偶变量?
═══════════════════════════════════════════════════════════════
```

关键点：四个约束组在同一个变量 **L** 上联立。每个物理模块不再是独立做布尔判断，而是向 LP 贡献一组线性不等式。

## 模块结构

```
src/wafer_dse/
│
├── lp/                          ★ 统一 LP 引擎（核心新增）
│   ├── engine.py                UnifiedLp: 构建 + 求解
│   ├── performance.py           性能约束：链路权重 + Hungarian / LP
│   ├── geometry.py              几何约束：bump 预算 per die
│   ├── thermal.py               热约束：功率密度上限
│   └── report.py                LpResult: 可行性 + 灵敏度报告
│
├── architecture_model/
│   ├── topology/                ★ Topology ABC + 4 种实现
│   │   ├── base.py              Topology ABC (to_loc, to_node, next, …)
│   │   ├── mesh.py              Mesh 2D (无边环绕)
│   │   ├── torus.py             Torus 2D (有边环绕)
│   │   ├── kary_ncube.py        k-ary n-cube (n 维泛化)
│   │   └── dragonfly.py         Dragonfly / DragonflyPlus (骨架)
│   └── solver/
│       ├── interface.py         Solver ABC + SolverResult
│       ├── algorithm/
│       │   ├── hungarian.py     Hungarian 最小成本完美匹配 O(N³)
│       │   └── derangement.py   max-weight derangement (无自环)
│       ├── fixed_route.py       FixedRouteSolver (det/val + Hungarian)
│       └── rust_backend.py      Rust 批量加速，不可用时静默回退
│
├── physical/
│   ├── bump/                    BumpSpec, DieBumpBudget, C4Budget
│   ├── interconnect/            17 种互连标准 + 全局注册表
│   │   ├── base.py              InterconnectProfile ABC + LinkBudget
│   │   ├── ucie.py / serdes.py / ethernet.py / optical.py / tsv.py
│   │   └── tsmc_profiles.py     TSMC 工艺参数
│   ├── thermal/                 热求解器 (simple / hierarchical / MFIT)
│   ├── interposer.py            Interposer 模型
│   └── substrate.py             Substrate 级互联模型
│
├── models.py                    数据契约 (Requirement, TopologySpec)
├── config.py                    PyYAML + JSON 配置读取
├── pareto.py                    Pareto 前沿计算 + 品质因数
├── trace/                       结构化日志 (console / report / summary)
├── reporting/                   文件输出 (JSON / CSV / Markdown)
└── __main__.py                  CLI 入口
```

## 数据流

```
用户配置 (YAML)
    │
    ▼
Requirement + [TopologySpec, …]
    │
    ▼
┌──────────────────────────────────────────┐
│  UnifiedLp(topo, route, target_gbps)      │
│                                           │
│  lp.add_geometry(die_configs, bump_spec)  │  ← 约束构建
│  lp.add_thermal(thermal_cfg)              │  ← 约束构建
│                                           │
│  lp.solve()                               │  ← 求解
│    ├─ det 路径: Hungarian + 独立检查       │
│    └─ valiant 路径: cvxpy 联立 LP         │
│                                           │
│  → LpResult                               │
│    ├── feasible                           │
│    ├── per_link_load (L 向量)              │
│    ├── constraints[] (每个约束组的状态)     │
│    │    ├── satisfied / max_violation      │
│    │    ├── binding_constraints            │
│    │    └── dual_values (灵敏度)            │
│    └── report() → 人类可读报告             │
└──────────────────────────────────────────┘
    │
    ▼
Pareto 前沿 + 灵敏度分析 → 报告输出
```

## 经典用法

### 命令行

```bash
# 单点评估
python -m wafer_dse --topology dragonfly --a 4 --p 4 --h 2

# 配置文件（批量枚举）
python -m wafer_dse --config configs/example_lp.yaml

# Valiant LP 路径（需要 pip install ".[lp]"）
python -m wafer_dse --topology dragonfly --a 4 --p 4 --h 2 --route valiant
```

### Python API

```python
from wafer_dse.architecture_model.topology import Dragonfly
from wafer_dse.lp import UnifiedLp
from wafer_dse.lp.geometry import DieConfig
from wafer_dse.lp.thermal import ThermalConfig
from wafer_dse.physical.bump.bump import UBUMP_45UM
from wafer_dse.physical.thermal._cooling import LIQUID_COOLING

# 1. 拓扑
topo = Dragonfly(a=4, p=4, h=2)

# 2. 构建 LP
lp = UnifiedLp(topo, route="det", target_gbps=800)

# 3. 添加物理约束
dies = [DieConfig(label=f"die_{i}") for i in range(topo.g)]
lp.add_geometry(dies, UBUMP_45UM)

thermal = ThermalConfig(cooling=LIQUID_COOLING)
lp.add_thermal(thermal)

# 4. 求解
result = lp.solve()

# 5. 报告
print(result.report())
if result.feasible:
    print(f"无阻塞带宽: {result.nonblocking_gbps:.0f} Gbps/port")
else:
    for cs in result.constraints:
        if not cs.satisfied:
            print(f"瓶颈: {cs.name}, violation={cs.max_violation}")
```

## 一般用例

### 用例 1: 快速早筛

场景：有 20 个 Dragonfly 参数组合，快速淘汰明显不可行的。

```python
for a, p, h in combinations:
    topo = Dragonfly(a=a, p=p, h=h)
    result = UnifiedLp(topo, route="det").solve()
    if result.worst_load > 2.0:
        skip(f"L*={result.worst_load:.1f}, bottleneck={result.bottleneck_link}")
    else:
        keep(topo)
```

### 用例 2: 完整物理可行性

场景：对通过早筛的拓扑，加入 bump/热约束，确认物理可实现。

```python
lp = UnifiedLp(topo, route="det", target_gbps=800)
lp.add_geometry(die_configs, UBUMP_45UM)
lp.add_thermal(ThermalConfig(cooling=LIQUID_COOLING))
result = lp.solve()

# 灵敏度: 如果不可行，是 bump 不够还是散热不行？
for cs in result.constraints:
    if cs.binding_constraints:
        print(f"{cs.name} 在边界上: {cs.binding_constraints}")
```

### 用例 3: Valiant 最优路由

场景：确定路由有瓶颈，想评估 Valiant 路由是否能通过自适应分流解决问题。

```bash
pip install ".[lp]"  # 安装 cvxpy
python -m wafer_dse --topology dragonfly --a 4 --p 4 --h 2 --route valiant
```

### 用例 4: Pareto 前沿

场景：枚举一组设计点，画 Pareto 前沿 (BW vs Area vs Power)。

```python
from wafer_dse.pareto import Metrics, compute_foms

results = []
for group_size, die_cfg in enumerate_configs():
    topo = Dragonfly(a=group_size, p=4, h=2)
    lp = UnifiedLp(topo, route="det", target_gbps=800)
    lp.add_geometry(die_cfg, UBUMP_45UM)
    result = lp.solve()
    if result.feasible:
        results.append(Metrics(
            perf=result.nonblocking_gbps,
            cost=sum(d.area_mm2 for d in die_cfg),
            power=sum(d.power_w for d in die_cfg),
            plan=None, label=f"a{group_size}"
        ))

foms = compute_foms(results)
frontier = [f for f in foms if f.on_frontier]
```

## 与旧架构的区别

| | 旧架构 (已删除) | 新架构 |
|---|---|---|
| 编排层 | ArchitectureModel + PackagingModel + couple() | UnifiedLp |
| 物理模块角色 | 独立做布尔判断 | 向 LP 贡献约束矩阵 |
| 约束耦合 | 串行 AND | 联立 LP |
| 灵敏度 | 无 | dual values + binding constraints |
| 求解路径 | 仅 det (Hungarian) | det + valiant LP |
| DSE 层次 | 三条并行路径 | 一条统一路径 |
