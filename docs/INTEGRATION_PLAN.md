# 端到端 DSE 原型集成计划

## 目标

输入 Dragonfly (a,p,h) 参数 → 自动检查物理可行性 → 输出 Pareto 前沿。

## 模块清单

```
已有 ✓                      待建 ✦                      外部依赖
──────────────────────────────────────────────────────────────────
architecture_model/          physical/bump/              congestion (Rust)
  topology/                    bump.py                     (Phase 4, 后续)
  solver/                    physical/interposer.py
die_model/                   physical/substrate.py
group_dse/                   configs/wafer_scale.yaml
wafer_dse/                   
pareto.py                    
partition/
  grid.py
  assignment.py
physical/interconnect/
  17 standards
```

## 四步构建

### Step 1: Bump 模块 (`physical/bump/bump.py`)

职责：封装 μbump 和 C4 的纯几何约束。

```python
BumpSpec(pitch_um, utilization)  →  density_per_mm
DieBumpBudget(spec, width, height)  →  .available  (可用信号 bump 数)
C4Budget(spec, interposer_area_mm2)  →  .available
```

逻辑极简：`available = perimeter × density × utilization`。不依赖任何其他模块。

### Step 2: Interposer 抽象 (`physical/interposer.py`)

职责：将 die 集合 + bump 约束 + interposer 面积 + 互连标准组合为一个物理单元。

```python
Interposer(
    dies: list[DieBumpBudget],
    area_mm2: float,
    interposer_bump: BumpSpec,     # μbump 上界面
    c4_bump: BumpSpec,             # C4 下界面
)
    → can_fit(dragonfly_group) → bool        # 组内 die 放得下吗
    → can_route_intra(edges) → bool           # 组内 D2D 可达吗
    → can_route_global(edges) → bool          # C4 出 substrate 够吗
```

这是关键模块。输入 Dragonfly group 的边集，输出 yes/no + 使用的是哪种 UCIe 标准。

### Step 3: Substrate 抽象 (`physical/substrate.py`)

职责：多个 interposer 的互联。

```python
Substrate(
    interposers: list[Interposer],
    c4_budget_per_interposer: int,
    max_reach_mm: float = 250,     # 4×4, 最远对角
)
    → feasible_global_links(topology) → bool
```

逻辑：对于跨 interposer 的 global edge，自动选 SerDes-112G-MR（唯一覆盖 250mm 的标准），检查 C4 预算是否够。

### Step 4: 端到端流程 (`scripts/dse_demo.py`)

```python
# 1. 定义工艺
bump_ucie = BumpSpec(pitch=45, utilization=0.55)   # μbump
bump_c4   = BumpSpec(pitch=130, utilization=0.40)  # C4

# 2. 构建 16 个 interposer
interposers = [Interposer(...) for _ in range(16)]

# 3. 构建 substrate
sub = Substrate(interposers, ...)

# 4. 枚举 Dragonfly 参数
for a, p, h in enumerate_combinations():
    # 4a. 拓扑层: 非阻塞带宽
    net = ArchitectureModel().evaluate(req, spec)
    if net.nonblocking < target: continue
    
    # 4b. Bump 层: μbump 够吗
    for interposer in interposers:
        if not interposer.can_fit(group): continue
    
    # 4c. 布线层: interposer 内 + substrate 间
    if not interposer.can_route_intra(edges): continue
    if not sub.feasible_global_links(edges): continue
    
    # 4d. Pareto
    metrics = compute_metrics(net, interposer, sub)
    pareto_points.append(metrics)

# 5. 输出
print(frontier_summary(pareto_points))
```

## 数据流

```
User Input (YAML)
  ├── process: {bump_pitch_um: 45, c4_pitch_um: 130}
  ├── interposer: {count: 16, area_mm2: 858}
  ├── die: {width: 12, height: 12}
  ├── requirement: {target_gbps: 800, max_power_w: 500}
  └── topologies: [{kind: dragonfly, a: 4, p: 4, h: 2}, ...]
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  Phase 0: 物理初始化                         │
  │  BumpSpec → DieBumpBudget → Interposer      │
  │  输出: 每个 interposer 的可用资源             │
  └──────────────────┬──────────────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────────────┐
  │  Phase 1: 拓扑滤波 (已有)                     │
  │  ArchitectureModel.evaluate()                │
  │  输出: NetworkPotential (nonblocking BW)      │
  └──────────────────┬──────────────────────────┘
                     │ feasible
                     ▼
  ┌─────────────────────────────────────────────┐
  │  Phase 2: Bump 约束 (新增)                   │
  │  DieBumpBudget.can_support(edges)            │
  │  过滤: μbump 不够的直接淘汰                   │
  └──────────────────┬──────────────────────────┘
                     │ feasible
                     ▼
  ┌─────────────────────────────────────────────┐
  │  Phase 3: 布线约束                            │
  │  Interposer + Substrate + GreedyRouter       │
  │  过滤: 距离不可达的直接淘汰                    │
  └──────────────────┬──────────────────────────┘
                     │ feasible
                     ▼
  ┌─────────────────────────────────────────────┐
  │  Phase 4: Pareto (已有)                      │
  │  compute_foms() → pareto_frontier()          │
  │  输出: 排序列表 + Markdown 表格               │
  └─────────────────────────────────────────────┘
```

## 每个模块的依赖关系

```
BumpSpec          ← 零依赖
DieBumpBudget     ← BumpSpec
Interposer        ← DieBumpBudget + InterconnectStandard
Substrate         ← Interposer + InterconnectStandard
RoutingProblem    ← LogicalTopology + WaferGrid + InterconnectStandard
GreedyRouter      ← RoutingProblem
DSE Pipeline      ← 以上全部 + ArchitectureModel + Pareto
```

## 预计代码量

| 模块 | 预估行数 |
|---|---|
| bump.py | ~50 |
| interposer.py | ~80 |
| substrate.py | ~60 |
| dse_demo.py | ~100 |
| wafer_scale.yaml | ~40 |
