# test07 — 布线模型 (src/problem/models/phys/wiring/)

## 模块定位

die 之间的 lane 需要在 interposer 金属层上走线。布线模型把 interposer 离散化为网格图，每条链路生成 ≤2 条 L 形候选路径，用多商品流 LP 分配 lane，受边容量和点容量约束。

**核心模型**: 网格顶点 = die 中心 + C4 阵列位置 → 完整 2D 网格。边容量 = 通道宽度 × 金属层数 × 走线密度。

```python
import sys; sys.path.insert(0, '../src')
from problem.models.phys.wiring import build_wiring_grid, populate_paths
from physical.layout.thermal_network import DiePlacement
```

---

## 1. 网格有顶点和边

2 个 die，30×20mm interposer。每个 die 映射到不同顶点。C4 阵列在 5mm 间距下增加了额外顶点。

```python
p = [DiePlacement("d0", 0, 0, 12, 12),
     DiePlacement("d1", 13, 0, 12, 12)]
g = build_wiring_grid(p, 30, 20, 4, 10)
print(f"vertices = {g.n_vertices},  edges = {g.n_edges}")
print(f"die_vertex = {{0: {g.die_vertex[0]}, 1: {g.die_vertex[1]}}}")
assert g.n_vertices > 0 and g.n_edges > 0
assert g.die_vertex[0] != g.die_vertex[1]
```

---

## 2. L 形路径

die→die 至少有一条 L 形路径（由网格边索引序列组成）。每条链路最多 2 条候选路径——先横后纵、先纵后横，在拐角处分叉。

```python
g = populate_paths(g, [{"from_die": 0, "to_die": 1, "type": "UCIe"}])
paths = g.path_groups[0]
print(f"paths = {len(paths)} candidates")
print(f"first path: {len(paths[0])} edges")
assert len(paths) >= 1
assert len(paths[0]) > 0
```

---

## 3. 边容量为正

每条网格边的容量 = 相邻顶点间距 × 金属层数 × 走线密度。间距越大 → 通道越宽 → 容量越大。

```python
print(f"edge caps: min={g.edge_cap.min():.0f}, max={g.edge_cap.max():.0f}")
assert all(g.edge_cap > 0)
```
