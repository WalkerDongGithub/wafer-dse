# 布线模型：Mesh 网格上的并发流 LP

## 问题

给定 die 摆放位置后，任意两点间的走线如何在 interposer 的布线网格上分配？

## 核心洞察

在以下假设下，布线问题**完完全全是一个 mesh 上的并发流问题——线性的**：

1. **只允许水平和竖直走线**（Manhattan，无斜线）
2. **最多拐一个直角弯**（L 形路径）——每个连接最多 2 条候选路径
3. **mesh 每条边的容量由金属层数决定**——C_g = 层数 × 每层 lane 数
4. **die 位置已固定**——来自 floorplan

## 数学形式

- 网格图 G = (V_grid, E_grid)，顶点是交叉点，边是布线通道
- 每个 die-to-die 链路 e（有物理 lane 需求 ℓ_e）映射为网格上的一对端点
- 对每个 e，有至多 2 条 L 形候选路径
- 分流变量：x_{e,k} = 链路 e 在第 k 条候选路径上分配的 lane 数
- 约束：Σ_k x_{e,k} = ℓ_e（需求必须满足）
- 容量约束：Σ_{e,k: g∈path} x_{e,k} ≤ C_g ∀g ∈ E_grid

**与性能约束的相似性：**

| 性能约束 | 布线约束 |
|---------|---------|
| 拓扑链路 e | 网格边 g |
| 排列模式 r | die-to-die 链路 e |
| 候选路径（Valiant） | 候选路径（L 形，至多 2 条） |
| 分流变量 f^(r) | 分流变量 x_e |
| 包络 L_e | 网格边负载 |

**和性能约束完全同构——都是多商品流。**

## 输入

| 输入 | 来源 |
|------|------|
| die 位置 (x, y) | Floorplan |
| die-to-die lane 需求 ℓ_e | LP 解出的 L → ℓ = B/λ · L |
| 网格边容量 C_g | 工艺参数（金属层数 × lanes/mm） |

## 实现

放在 `lp/models/phys/` 下，作为新的 `RoutingModel`：

```
lp/models/phys/
  bumps/      BumpModel
  therm/      NetworkModel
  routing/    RoutingModel（新增）
```

`RoutingModel.build(ctx)` 做的事：
1. 接收 die 位置 + ℓ_e（从 ctx["ell"] 拿）
2. 对每个 die-to-die 链路生成 L 形候选路径
3. 声明分流变量 x_{e,k}
4. 添加容量约束 Σ x ≤ C_g

## 与现有 LP 的关系

布线约束可以直接进入同一个 LP——不增加新的变量类（仍然是分流变量 + 容量不等式）。只是多了 |E_grid| 条不等式 + Σ_e 2 个分流变量。

## 待定

- L 形路径是否足够？（1 个弯 vs 多弯）
- 是否需要考虑电源走线占用布线资源？（现有公式里 κ·I_g 的项）
- 网格粒度——是否与 die 尺寸对齐？
