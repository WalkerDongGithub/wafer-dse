# 性能约束：严格定义与求解路径

## 1. 非阻塞的严格含义

$N$ 端口交换机。排列 $\pi$ 是一种"谁发给谁"的配对：$\pi(i) \neq i$，一一映射。共 $(N-1)!$ 种可能排列。

**非阻塞**：对任意排列 $\pi$，存在一种路由方案，使所有内部链路的流量不超过链路物理速率。

归一化后：设每端口发出 1 单位流量。链路 $e$ 的归一化负载 $L_e \le 1$ 对所有 $e$ 成立 $\iff$ 无阻塞。

---

## 2. 数学模型：Convex Maximization

给定流量矩阵 $\mathbf{D}$，定义**最优分流下的瓶颈负载**：

$$V(\mathbf{D}) = \min_{\mathbf{f}} \; \max_{e} \; L_e(\mathbf{f}) \quad \text{s.t.} \quad \sum_k f_{ij}^k = D_{ij}$$

这是一个 LP：$\min t$ s.t. $\sum_k f_{ij}^k = D_{ij}$，$\sum_{(i,j,k): e \in \text{path}} f_{ij}^k \le t$。

**数学事实**：$V(\mathbf{D})$ 是 $\mathbf{D}$ 的凸函数。LP 的值函数对其右手边参数是凸的。

非阻塞判据为：

$$\boxed{\max_{\mathbf{D} \in \mathcal{D}} \; V(\mathbf{D}) \;\le\; 1}$$

其中 $\mathcal{D} = \{\mathbf{D} \ge 0 : \sum_j D_{ij}=1,\; \sum_i D_{ij}=1,\; D_{ii}=0\}$ 是双随机矩阵多面体，顶点为排列矩阵。

**问题类型**：**凸函数在凸多面体上求最大**。不是 LP，不是 QP。全局最大值必在极点（排列）取到，但不需要穷举——下面是四条可用路径。

---

## 3. 路径一：均匀 D 近似

**核心观察**：对 Dragonfly 等对称拓扑，Valiant 分流的对称性使均匀流量成为最坏情况。

$$V(\mathbf{D}_{\text{uniform}}) \ge V(\mathbf{D}) \quad \forall \mathbf{D} \in \mathcal{D}$$

其中 $\mathbf{D}_{\text{uniform}} = \frac{1}{N-1}(\mathbf{1}\mathbf{1}^T - \mathbf{I})$——每个端口对发送等量流量。

此时非阻塞判据退化为单个 LP：

$$\boxed{\min_{t, \mathbf{f}} \; t \quad \text{s.t.} \quad \sum_k f_{ij}^k = D_{ij}^{\text{uniform}}, \quad \sum_{(i,j,k): e \in \text{path}} f_{ij}^k \le t \;\; \forall e}$$

$$\text{若 } t^* \le 1 \text{，则无阻塞}$$

**适用范围**：对称拓扑（Dragonfly, Mesh, Torus）。非对称拓扑需实验验证均匀假设是否成立。

**优点**：1 个 LP，$O(N^2 \cdot g)$，秒解。

---

## 4. 路径二：迭代对抗

Convex maximization 的标准解法是 cutting plane 或 Frank-Wolfe 类方法。这里用对策论的迭代对抗：

```
初始化：D^(0) = D_uniform
重复：
  第1步（防守方）：给定 D^(k)，解内层 LP
    min t s.t. Σf = D^(k), Σf ≤ t ∀e
    得到最优值 t^(k)，以及对偶变量 β_e（每条链路的紧张程度）
  
  第2步（进攻方）：利用 β_e 构造新的流量矩阵 D^(k+1)
    对每个(i,j)，定义路径成本 c_{ij} = min_k Σ_{e∈path(i,j,k)} β_e
    解分配问题：max Σ D_{ij} · c_{ij} s.t. D ∈ 𝒟
    → D^(k+1) = 排列矩阵（分配问题的解是排列）
  
直到 t^(k) 不再上升
```

**收敛性**：$t^{(k)}$ 单调不减，上界为 $\le N$（最坏情况所有流量走一条链路）。有限步收敛到全局最优 $V^*$。

**每次迭代**：1 个 LP（O(N²·g)）+ 1 个分配问题（O(N³)，匈牙利算法）。

**优点**：通用，不依赖对称性假设。N ≤ 30 时通常 ≤ 10 步收敛。

---

## 5. 路径三：枚举排列

N 较小时（N ≤ 8），直接穷举所有排列。每个排列算一次内层 LP，取最大值。

$$t^* = \max_{\pi \in \Pi_N} V(\mathbf{D}_\pi)$$

复杂度 O((N-1)! × LP)。N=8 时约 5040 个 LP，并行可行。

**用途**：小规模下的 ground truth，用于验证均匀假设和迭代对抗的精度。

---

## 6. 路径四：分边 max LP（上界）

对每条边 $e^*$，求解：

$$\max_{\mathbf{D}, \mathbf{f}} \; L_{e^*} \quad \text{s.t.} \quad \mathbf{D} \in \mathcal{D},\; \sum_k f_{ij}^k = D_{ij}$$

取 $t^{\text{ub}} = \max_{e^*} L_{e^*}^*$。这给出的是非阻塞条件的**充分条件**（上界偏悲观）。

**问题**：$\mathbf{f}$ 帮进攻方把流量往 $e^*$ 上灌，不是防守方的最优路由。$t^{\text{ub}}$ 可能高于真实最坏值。适合快速淘汰——若 $t^{\text{ub}} \le 1$，则一定无阻塞。

---

## 7. 四条路径对比

| | 均匀 D | 迭代对抗 | 枚举排列 | 分边 max |
|---|---|---|---|---|
| 类型 | 近似 | 精确 | 精确 | 上界 |
| LP 数量 | 1 | O(K)，K≈迭代次数 | O((N-1)!) | O($\vert\mathcal{E}\vert$) |
| N≤30 可行性 | ✅ | ✅ | N≤8 | ✅ |
| 拓扑依赖 | 需对称性 | 无 | 无 | 无 |
| 论文中的角色 | 主力工具 | 验证工具 | Ground truth | 快速筛选 |

---

## 8. 理论基础：Towles & Dally (SPAA 2002)

### 核心结论

对任意**固定**的 oblivious routing 函数 $\mathbf{f}$，链路负载是 $\mathbf{D}$ 的线性函数。定义链路 $e$ 对 $(i,j)$ 对的负载贡献 $\gamma_e^{ij}$——即 $(i,j)$ 对的一单位流量在路由 $\mathbf{f}$ 下对 $L_e$ 的贡献。则：

$$L_e(\mathbf{D}) = \sum_{i,j} \gamma_e^{ij} \cdot D_{ij}$$

对固定 $\mathbf{f}$，求 $\max_{\mathbf{D} \in \mathcal{D}} L_e(\mathbf{D})$ 是在双随机多面体上最大化线性函数。Birkhoff 定理保证极点在排列矩阵上。因此：

$$\boxed{\max_{\mathbf{D} \in \mathcal{D}} L_e(\mathbf{D}) = \max_{\text{排列 } \pi} \sum_i \gamma_e^{i,\pi(i)}}$$

这是一个**二分图最大权完美匹配**问题——匈牙利算法，$O(N^3)$。不需要穷举。

### 与 Valiant 最优分流的区别

Towles & Dally 假设路由 $\mathbf{f}$ 固定。我们的问题是：$\mathbf{f}$ 可随 $\mathbf{D}$ 优化（Valiant 分流比例自适应）。引入 $V(\mathbf{D}) = \min_{\mathbf{f}} \max_e L_e$ 后，$V(\mathbf{D})$ 不再是 $\mathbf{D}$ 的线性函数（是凸函数），Towles 的匹配归约不再直接适用。

但二者的关系为：
- **固定路由**（如 Valiant 均匀分流）：最坏 $\mathbf{D}$ = 排列，匈牙利 $O(N^3)$
- **最优分流** $V(\mathbf{D})$：一个 LP → 带这个 LP 做内层的 $\max_{\mathbf{D}}$ = convex maximization

---

## 9. 推荐的使用策略

1. **L0（二分带宽）**：O(1)，淘汰明显不可行的拓扑
2. **L1 主流程（均匀 D + 最优分流 LP）**：对通过 L0 的大多数设计点，固定均匀 D，解单个 min t LP。$t^* \le 1$ → 可行
3. **验证（匈牙利 + LP 迭代）**：固定 Valiant 均匀分流比例，用匈牙利算法 $O(N^3)$ 精确求最坏排列 $\mathbf{D}_{\text{worst}}$。在 $\mathbf{D}_{\text{worst}}$ 下跑最优分流 LP。若 $t^*_{\text{worst}} \le 1$，无阻塞成立
4. **上界（分边 max LP）**：若 L1 判定可行且验证通过，不必进入此步。若存疑，跑分边 max 给出上界（偏悲观）
