# Interposer 布局

## 问题

正方形 die（边长 $d$）+ 正方形 interposer（边长 $L$）→ 正方形网格。

$n = \lfloor L / d \rfloor$，网格 $n \times n$，最多放 $n^2$ 个 die。放 $k$ 个 die，每个 die 占一个格子。

## 输入

- $d$：die 边长
- $L$：interposer 边长
- $k$：要放的 die 数量
- $\mathcal{E}$：逻辑拓扑的边集（预留给拓扑感知求解器，当前不用）

## 输出

- 每个 die 的网格坐标 $[r_i, c_i]$
- 物理坐标 $(x_i, y_i) = (c_i \cdot d,\; r_i \cdot d)$
- 网格尺寸 $n \times n$

## 网格

均匀正方形网格。每格一个 die。格间边界就是布线通道。

```
  L = 80mm,  d = 12mm  →  n = 6

  [0,0] [0,1] [0,2] [0,3] [0,4] [0,5]
  [1,0] [1,1] ...
  ...
  [5,0] ...                     [5,5]
```

## 求解

当前：**逐行填充**。不关心拓扑，只给一个可行布局。

未来：拓扑感知。使用 $\mathcal{E}$ 信息，让链路多的 die 对放在相邻位置，减少 SerDes 使用。本质上是最小化 $\sum_{(i,j)\in\mathcal{E}} \text{Manhattan}(i,j)$ 的离散布局问题。

## 与下游关系

```
布局 → die 坐标 → 链路距离 → UCIe / SerDes 分类
                 → 热 G 矩阵（谁和谁相邻）
                 → 布线网格（通道在哪）
```
