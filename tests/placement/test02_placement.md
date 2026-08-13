# test02 — die 布局

## 这个模块做什么

给定正方形 die 和正方形 interposer，把 die 放在网格格点上。
这是整个 pipeline 的第一个物理步骤——布局一确定，die 间距、热邻接关系、布线网格就全确定了。

**核心公式**: $n = \lfloor L / d \rfloor$，$n\times n$ 网格，逐行填充。

```python
import sys; sys.path.insert(0, '../src')
from physical.placement import PlacementProblem, solve_grid_placement
```

---

## 案例 1: 一个具体的例子

假设我们有一颗 12×12mm 的交换 die，贴在 80×80mm 的 interposer 上。

**首先问一个最简单的问题**: 这个 interposer 能放多少个 die？

$$n = \lfloor 80 / 12 \rfloor = 6 \quad\rightarrow\quad 6\times 6 = 36 \text{ 个格子}$$

```python
sol = solve_grid_placement(PlacementProblem(
    die_side_mm=12.0, interposer_side_mm=80.0, die_count=6))
print(f"grid_n = {sol.grid_n},  max_dies = {sol.max_dies}")
assert sol.grid_n == 6 and sol.max_dies == 36
```

现在只放 6 个 die。它们会被放在哪？策略极简——从 `[0,0]` 开始逐行填充。

```python
for i in range(6):
    p = sol.positions[i]
    print(f"  die {i}: [{p.row},{p.col}] @ ({p.x:.0f}, {p.y:.0f})")
assert sol.positions[0].row == 0 and sol.positions[0].col == 0
assert sol.positions[5].row == 0 and sol.positions[5].col == 5
```

**物理含义**: d0 和 d1 边缘刚好接触（间隙=0），中心距 12mm。
如果 UCIe 可达距离是 25mm（Standard Package），d0↔d1 可以走 UCIe。
布线通道容量 = 12mm × 4 layers × 10 lanes/mm/layer = **480 lanes**。

---

## 案例 2: 换一个尺寸

把 die 换成 10×10mm，interposer 还是 80×80mm。

$$n = \lfloor 80/10 \rfloor = 8 \quad\rightarrow\quad 8\times 8 = 64 \text{ 个格子}$$

更密的排布 → 更短的 UCIe 链路 → 更低的功耗。

```python
sol2 = solve_grid_placement(PlacementProblem(
    die_side_mm=10.0, interposer_side_mm=80.0, die_count=6))
print(f"grid_n = {sol2.grid_n},  max_dies = {sol2.max_dies}")
print(f"d1 @ ({sol2.positions[1].x:.0f}, {sol2.positions[1].y:.0f})")
assert sol2.grid_n == 8 and sol2.positions[1].x == 10.0
```

---

## 案例 3: 放满一行后换行

3×3 网格（36mm interposer, 12mm die），放 5 个。
第 0 行放满后，第 4 个 die 自动进入 `[1,0]`。

```python
sol3 = solve_grid_placement(PlacementProblem(
    die_side_mm=12.0, interposer_side_mm=36.0, die_count=5))
for i in range(5):
    p = sol3.positions[i]
    print(f"  die {i}: [{p.row},{p.col}]")
assert sol3.positions[3].row == 1 and sol3.positions[3].col == 0
assert sol3.positions[4].row == 1 and sol3.positions[4].col == 1
```

现在 die 分布在两行——引出二维热耦合和垂直布线通道。

---

## 案例 4: 面积硬约束

interposer 24mm 宽，die 12mm → $n=2$，最多 $2\times 2 = 4$ 个 die。
放 5 个直接报错——这是物理硬极限。

```python
try:
    solve_grid_placement(PlacementProblem(
        die_side_mm=12.0, interposer_side_mm=24.0, die_count=5))
except ValueError as e:
    print(f"ValueError: {e}")
```

---

## 案例 5: 网格坐标 → 物理坐标

$(x, y) = (c \cdot d,\; r \cdot d)$——完全由网格位置决定，不存在"自由浮动"坐标。

```python
sol5 = solve_grid_placement(PlacementProblem(
    die_side_mm=12.0, interposer_side_mm=80.0, die_count=4))
for i in range(4):
    p = sol5.positions[i]
    print(f"  [{p.row},{p.col}] → ({p.x:.0f}, {p.y:.0f})")
    assert p.x == i * 12.0
```

---

## 小结

布局层做的事情极其简单——正方形网格、逐行填充。但它是后续所有物理模型的基础：

- **die 坐标** → 链路距离 → UCIe / SerDes 分类
- **die 邻接关系** → 热 G 矩阵（谁挨着谁）
- **网格结构** → 布线网格（顶点、边、容量）

布局一变，这三个全变。这就是它作为 pipeline 第一个环节的原因。

---

## 求解器接口

`solve_grid_placement(problem)` 是函数接口，但它只是 `GridFillSolver`（逐行填充）的薄封装。求解器本体是抽象接口 + 子类：

- `PlacementSolver(ABC)`：`solve(problem) -> PlacementSolution`
- `GridFillSolver`：逐行填充（feasible-only，当前唯一实现）
- 未来拓扑感知求解器（链路多的 die 对放相邻）是第二个子类，调用方不用改

```python
from physical.placement import PlacementSolver, GridFillSolver

solver = GridFillSolver()
sol = solver.solve(PlacementProblem(
    die_side_mm=12.0, interposer_side_mm=80.0, die_count=4))
sol_fn = solve_grid_placement(PlacementProblem(
    die_side_mm=12.0, interposer_side_mm=80.0, die_count=4))

# 函数接口与求解器实例必须产出完全一致的解
assert [(p.row, p.col) for p in sol.positions] == \
       [(p.row, p.col) for p in sol_fn.positions]
assert sol.grid_n == sol_fn.grid_n

# ABC 不能实例化
try:
    PlacementSolver()
    assert False, "抽象类应抛 TypeError"
except TypeError:
    pass

print(f"✓ {solver.name} 求解器接口: 函数 = 实例, ABC 不可实例化")
```
