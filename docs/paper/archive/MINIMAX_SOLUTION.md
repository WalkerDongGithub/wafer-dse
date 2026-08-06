# 非阻塞判据的数学结构与求解

## 1. 问题定义

**非阻塞**：对任意排列 $\pi$，存在路由方案使所有链路不过载。

用 Valiant 分流表达：给定流量矩阵 $\mathbf{D}$，防守方最优分流的瓶颈负载为内层 LP 的值函数：

$$V(\mathbf{D}) = \min_{\mathbf{f}} \; \max_{e} \; L_e(\mathbf{f}) \quad \text{s.t.} \quad \sum_k f_{ij}^k = D_{ij}$$

非阻塞 $\iff$ $\displaystyle\max_{\mathbf{D} \in \mathcal{D}} V(\mathbf{D}) \le 1$。

$\mathcal{D} = \{\mathbf{D} \ge 0 : \sum_j D_{ij}=1, \sum_i D_{ij}=1, D_{ii}=0\}$ 是双随机多面体，顶点为排列矩阵。

---

## 2. $V(\mathbf{D})$ 的结构

内层 LP 的对偶为：

$$\max_{\alpha, \beta} \; \sum_{i,j} D_{ij} \cdot \alpha_{ij} \quad \text{s.t.} \quad \alpha_{ij} \le \sum_{e \in \text{path}(i,j,k)} \beta_e \;\; \forall k, \quad \sum_e \beta_e = 1, \quad \beta_e \ge 0$$

记对偶可行域为 $\mathcal{F}_{\text{dual}}$。由 LP 强对偶：

$$V(\mathbf{D}) = \max_{(\alpha,\beta) \in \mathcal{F}_{\text{dual}}} \sum_{i,j} D_{ij} \cdot \alpha_{ij}$$

**结构**：$V(\mathbf{D})$ 是 $\mathcal{F}_{\text{dual}}$ 上一族线性函数的上包络——**分段线性凸函数**。$\mathcal{F}_{\text{dual}}$ 有限个极点，所以 $V(\mathbf{D})$ 是有限个线性函数的逐点最大。

---

## 3. 外层问题的等价形式

$$\max_{\mathbf{D} \in \mathcal{D}} V(\mathbf{D}) = \max_{\mathbf{D} \in \mathcal{D}} \; \max_{(\alpha,\beta) \in \mathcal{F}_{\text{dual}}} \; \sum_{i,j} D_{ij} \cdot \alpha_{ij}$$

两个 max 可以交换：

$$= \max_{(\alpha,\beta) \in \mathcal{F}_{\text{dual}}} \; \max_{\mathbf{D} \in \mathcal{D}} \; \sum_{i,j} D_{ij} \cdot \alpha_{ij}$$

**内层（对固定 $\alpha$）**：$\max_{\mathbf{D} \in \mathcal{D}} \sum_{i,j} D_{ij} \cdot \alpha_{ij}$ 是线性函数在双随机多面体上的最大化。Birkhoff：极点在排列矩阵上。等价于：

$$\max_{\text{排列 } \pi} \sum_i \alpha_{i,\pi(i)}$$

这是 **二分图最大权完美匹配**——匈牙利算法，$O(N^3)$。

---

## 4. 求解路径

### 路径 A：交替上升（启发式，但实践中接近精确）

交替优化两个 max，每次严格上升：

```
初始化：D^(0) = D_uniform

循环：
  步骤1（解内层LP）：给定 D^(k)，解 min_f max_e L_e → 得 V(D^(k)) 和对偶 (α^(k), β^(k))
  
  步骤2（匈牙利）：用 α^(k) 作为边权，解 max_D Σ D_{ij} α_{ij} → 得 D^(k+1)（一个排列矩阵）
  
  步骤3（停止判断）：若 V(D^(k+1)) ≤ V(D^(k)) + ε，停止
```

**性质**：
- $V(\mathbf{D}^{(k)})$ 严格单调上升（除非已在局部极大）
- 有限步收敛（$\mathcal{D}$ 的极点有限）
- 不保证全局最优，但 $V(\mathbf{D})$ 的分段线性结构使局部极大多为全局极大
- N ≤ 30 时通常 ≤ 10 步收敛

### 路径 B：MILP（保证全局最优）

把"选排列"直接写进约束：

$$\boxed{
\begin{aligned}
\max_{t,\; \mathbf{D},\; \mathbf{f}} \quad & t \\
\text{s.t.} \quad & D_{ij} \in \{0,1\} \;\; \forall(i,j) \\
& \mathbf{D} \in \mathcal{D} \\
& \sum_k f_{ij}^k = D_{ij}, \quad \sum_{(i,j,k): e \in \text{path}} f_{ij}^k \le t \\
& t \ge 0,\; \mathbf{f} \ge 0
\end{aligned}
}$$

$N^2$ 个 0-1 变量，排列约束。N ≤ 30 时商用求解器（Gurobi/CPLEX）可求解。

### 路径 C：均匀 D 近似（最快，用于 DSE 扫描）

固定 $\mathbf{D} = \frac{1}{N-1}(\mathbf{1}\mathbf{1}^T - \mathbf{I})$，解单个内层 LP。

若 $t^*_{\text{uniform}} \le 1$ 且交替上升验证最坏排列的 $t^*$ 不显著更大 → 均匀 D 在 DSE 扫描中是安全的。

---

## 5. 路径对比

| | 均匀 D | 交替上升 | MILP |
|---|---|---|---|
| 类型 | 近似（下界） | 启发式 | 精确 |
| 保证全局最优 | ✗ | ✗ | ✓ |
| 每次迭代 | 1 LP | 1 LP + 1 匈牙利 | — |
| N=30 可行 | ✓ | ✓ | ✓ |
| 论文中角色 | DSE 主力 | 验证 | Ground truth (N≤30) |

---

## 6. 与 Towles & Dally (SPAA 2002) 的关系

Towles & Dally 针对**固定路由**（$\mathbf{f}$ 不随 $\mathbf{D}$ 变），证明了最坏排列 = 匈牙利。

我们的是**自适应路由**（$\mathbf{f}$ 随 $\mathbf{D}$ 优化）。$V(\mathbf{D})$ 是对偶域上一族线性函数的上包络，不再是单条线性函数。但外层的 max-max 结构使我们仍能用匈牙利作为交替优化的子程序——匈牙利解步骤 2 的 max_D 问题（固定 α），正是 Towles 结论的推广：不是固定路由，而是固定**对偶变量 α**（路由的"影子成本"）。

---

## 7. 推荐流程

1. **L0（二分带宽）**：O(1)，淘汰明显不可行拓扑
2. **L1 扫描（均匀 D + LP）**：对通过 L0 的设计点，在设计中点密度下用均匀 D 判据。$O(N^2 \cdot g)$ 秒级
3. **L1 验证（交替上升）**：选少数关键设计点，跑交替上升确认均匀 D 未低估。约 10×(1 LP + 1 匈牙利)
4. **L1 Ground truth（MILP）**：N ≤ 30 时用 MILP 精确求解 2-3 个设计点，与交替上升结果对比，建立信心
