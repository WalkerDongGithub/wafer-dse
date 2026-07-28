# 无阻塞性能模型的 LP 推导：从排列到线性规划

> 本文是对 [MATH_MODEL.md](MATH_MODEL.md) §1 的详细展开，面向第一次接触这个推导的读者。

---

## 1. 前提假设

- 交换机有 $N$ 个端口，编号 $1,2,\ldots,N$
- 每个端口以**同样的速率** $B$ 收发（如 800 Gbps）
- 归一化：设每个端口发出 **1 单位**流量，每单位 = $B$
- 每个端口恰好发给另一个端口：不闲置，不广播，不发给自己
- 内部每条链路的物理速率 = $B_{\text{link}}$（在归一化下也等于 1 单位）

---

## 2. $\pi$ 是什么

$\pi$ 是一个**排列（permutation）**——一种"谁发给谁"的配对方案。

$\pi: \{1,\ldots,N\} \to \{1,\ldots,N\}$，$\pi(i) \neq i$（不发给自己），且 $\pi$ 是一一映射。

$N=4$ 的例子：

$$\pi(1)=3,\; \pi(2)=4,\; \pi(3)=1,\; \pi(4)=2$$

翻译：1→3, 2→4, 3→1, 4→2。

$N$ 个端口的合法排列数 = $(N-1)!$（每个源 $N-1$ 个选择，依次递减）。

$N=64$ 时 = $63! \approx 2 \times 10^{87}$。**不可能穷举。**

---

## 3. 排列矩阵：把 $\pi$ 写成矩阵

排列 $\pi$ 等价于一个 0-1 矩阵 $\mathbf{P}$：

$$P_{ij} = \begin{cases} 1 & \text{若 } \pi(i) = j \\ 0 & \text{否则} \end{cases}$$

上面 $\pi = \{1\to3, 2\to4, 3\to1, 4\to2\}$ 对应的矩阵：

$$\mathbf{P} = \begin{bmatrix} 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \\ 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \end{bmatrix}$$

三个性质：
- **每行恰好一个 1**：$\sum_j P_{ij} = 1$，每个源恰好发给一个人
- **每列恰好一个 1**：$\sum_i P_{ij} = 1$，每个目的恰好被一个人发给
- **对角线全 0**：$P_{ii} = 0$，不给自己发

---

## 4. 链路负载的物理定义

### 4.1 物理量纲

- 每个端口以速率 **$B$ Gbps** 发送（目标带宽，如 800 Gbps）
- 交换机内部每条物理链路 $\ell$ 的线速率 = **$B_{\text{link}}$ Gbps**
- 归一化：设 $B = B_{\text{link}} = 1$（单位 = "一份端口带宽"），后续所有量都是这个单位的倍数

### 4.2 确定路由下的链路负载

网络内部有若干条物理链路，每条链路记作 $\ell$。

**确定性路由（det）**：对任意 $(i,j)$ 对，从 $i$ 到 $j$ 的路径是唯一的、预先确定的（由拓扑和路由协议决定）。

因此，对每条链路 $\ell$，可以**预先**算出哪些 $(i,j)$ 对的流量会经过它：

$$\mathcal{P}_\ell = \{(i,j) : \text{从 }i\text{ 到 }j\text{ 的 det 路径经过了 }\ell\}$$

$\mathcal{P}_\ell$ 是一个**常数集合**，与流量无关，只取决于拓扑和路由规则。

### 4.3 排列 $\pi$ 下的链路负载

给定一个具体的排列 $\pi$（即一个具体的"谁发给谁"方案），从 $i$ 到 $\pi(i)$ 有一条流量为 1 单位的流。

链路 $\ell$ 的负载：**所有经过 $\ell$ 的流的流量之和**。

$$\boxed{\text{load}_\ell(\pi) = \sum_{(i,j) \in \mathcal{P}_\ell} P_{ij}^\pi}$$

因为 $P_{ij}^\pi \in \{0,1\}$，这个和就是**整数**。它的物理含义：

> **链路 $\ell$ 上承载的总流量，以"端口带宽"为单位。**

- $\text{load}_\ell = 1$：链路上恰好有 1 条流 → 总带宽 = $1 \times B = B_{\text{link}}$ → **链路恰好满载**
- $\text{load}_\ell = 2$：链路上挤了 2 条流 → 总带宽需求 = $2 \times B = 2 B_{\text{link}}$ → **链路过载，每条流只能分到一半带宽**
- $\text{load}_\ell = 3$：3 条流共享 → 每条流只能分到 $B_{\text{link}}/3$

### 4.4 无阻塞条件

这条链路要不成为瓶颈，必须有：

$$\text{load}_\ell(\pi) \le 1$$

即链路上承载的总流量不超过链路本身的线速率。如果所有链路在所有排列下都满足 $\text{load}_\ell(\pi) \le 1$，则交换机是**严格无阻塞**的（每条流在任何情况下都能以满速率 $B$ 通过）。

### 4.5 举例

设 N=4，2×2 Mesh：

```
[0]──[1]
 │    │
[2]──[3]
```

路由规则：先走 x 方向，再走 y 方向。

- 从 0→3：路径 = 0→1→3（经过链路 (0,1) 和 (1,3)）
- 从 0→1：路径 = 0→1（只经过 (0,1)）
- 从 0→2：路径 = 0→2（只经过 (0,2)）
- 从 2→3：路径 = 2→3（不经过 (0,1)）

各条流的路径是**固定的、预先可算的**。$\mathcal{P}_{(0,1)}$（经过链路 (0,1) 的 (src,dst) 对）包括所有"源在左侧、目的在右侧"的对，以及部分需要穿过的对。这个集合在路由协议确定后就固定了。

给定排列 $\pi = \{0\to3, 1\to0, 2\to1, 3\to2\}$：

- 0→3 经过 (0,1) → 贡献 1
- 1→0 不经过 (0,1)（反方向走 1→0）→ 贡献 0
- 2→1：路径 2→0→1，经过 (0,1) → 贡献 1
- 3→2：不经过 (0,1)

$\text{load}_{(0,1)}(\pi) = 2$。这条链路被 2 条流共享 → 每条流最多分到 $B_{\text{link}}/2$ → 达不到 $B$ 的目标 → 这个排列下链路 (0,1) 是瓶颈。

---

## 5. 要找最坏排列 → 组合爆炸

**最坏情况负载**：在所有可能的排列中，某条链路 $\ell$ 上可能出现的最大负载。

$$\boxed{L_\ell^* = \max_{\pi} \; \text{load}_\ell(\pi) = \max_{\pi} \sum_{(i,j) \in \mathcal{P}_\ell} P_{ij}^\pi}$$

如果 $L_\ell^* \le 1$：即使最坏的排列，链路 $\ell$ 也不会过载。
如果 $L_\ell^* = 3$：存在某个排列，使 3 条流同时挤在链路 $\ell$ 上。

排列有 $(N-1)!$ 个。$N=64$ 时 $\approx 10^{87}$。**枚举不可行。**

---

## 6. Birkhoff–von Neumann 定理

**定理**（Birkhoff 1946, von Neumann 1953）：

> 排列矩阵集合 $\mathcal{P}$ 的凸包 = 双随机矩阵集合 $\mathcal{D}$。

**双随机矩阵**：

$$\mathcal{D} = \left\{ \mathbf{D} \in \mathbb{R}^{N\times N} \;\middle|\;
\begin{aligned}
& D_{ij} \ge 0 && \forall i,j \\
& \sum_{j=1}^N D_{ij} = 1 && \forall i \quad \text{(行和=1)} \\
& \sum_{i=1}^N D_{ij} = 1 && \forall j \quad \text{(列和=1)} \\
& D_{ii} = 0 && \forall i \quad \text{(对角线=0)}
\end{aligned}
\right\}$$

**几何含义**：

- $\mathcal{P}$（排列矩阵）是 $\mathcal{D}$ 这个多面体的**顶点**
- $\mathcal{D}$ 中的任何一个点都可以写成若干个排列矩阵的凸组合：

$$\mathbf{D} = \lambda_1 \mathbf{P}_1 + \lambda_2 \mathbf{P}_2 + \cdots + \lambda_k \mathbf{P}_k, \quad \lambda_i \ge 0, \quad \sum \lambda_i = 1$$

- 比如 N=3 时，两个排列矩阵的平均：

$$\mathbf{D} = 0.5\begin{bmatrix}0&1&0\\0&0&1\\1&0&0\end{bmatrix} + 0.5\begin{bmatrix}0&0&1\\1&0&0\\0&1&0\end{bmatrix} = \begin{bmatrix}0&0.5&0.5\\0.5&0&0.5\\0.5&0.5&0\end{bmatrix}$$

这个 $\mathbf{D}$ 是双随机的（行和=1, 列和=1），但它不是排列矩阵（有分数值）。在几何上，它在**多面体内部**，不在顶点。

---

## 7. 松弛：从 0/1 到 $[0,1]$，不损失精度

原来的离散问题（在排列矩阵上搜索）：

$$\max_{\mathbf{P} \in \mathcal{P}} \sum_{(i,j) \in \mathcal{P}_\ell} P_{ij}$$

松弛到在双随机矩阵上搜索：

$$\max_{\mathbf{D} \in \mathcal{D}} \sum_{(i,j) \in \mathcal{P}_\ell} D_{ij}$$

**松弛不改变最优值**，论证分两步：

### 步骤 1：目标函数是线性的

$$f(\mathbf{D}) = \sum_{(i,j) \in \mathcal{P}_\ell} D_{ij}$$

这是 $\mathbf{D}$ 各元素的加权和（权重要么是 1——在 $\mathcal{P}_\ell$ 里，要么是 0——不在）。**纯线性函数。**

### 步骤 2：线性函数在凸多面体上的最大值一定在顶点取到

这是线性规划的基本定理。可行集 $\mathcal{D}$ 是一个多面体（有界、凸、由线性不等式定义），线性目标函数 $f$ 的最大值**必然在多面体的某个顶点上取到**。

而 Birkhoff–von Neumann 告诉我们：$\mathcal{D}$ 的顶点恰好是排列矩阵 $\mathcal{P}$。

**因此**：虽然 LP 求解器在连续空间 $\mathcal{D}$ 里搜，允许 $D_{ij}$ 取 $[0,1]$ 中任意值，但**最优解自动就是 0 或 1**——因为它一定落在顶点上，而顶点就是排列矩阵。

这就是"松弛是免费的"的完整逻辑。

---

## 8. 完整的 LP

把 §5 的离散最大化换成双随机矩阵 $\mathbf{D}$ 上的连续最大化：

$$
\boxed{
\begin{aligned}
\max_{\mathbf{D} \in \mathbb{R}^{N\times N}} \quad & \sum_{(i,j) \in \mathcal{P}_\ell} D_{ij} && \text{① 目标：链路 }\ell\text{ 上的总流量} \\[8pt]
\text{s.t.} \quad & \sum_{j=1}^N D_{ij} = 1 \quad \forall i && \text{② 每个源发出 1 单位} \\[4pt]
& \sum_{i=1}^N D_{ij} = 1 \quad \forall j && \text{③ 每个目的收到 1 单位} \\[4pt]
& D_{ii} = 0 \quad \forall i && \text{④ 不给自己发} \\[4pt]
& D_{ij} \ge 0 \quad \forall i,j && \text{⑤ 流量非负}
\end{aligned}
}
$$

### 逐行解释

**① 目标函数**：$\mathcal{P}_\ell$ 是**预先算好的常数集合**——哪些 $(i,j)$ 对的 det 路由经过了链路 $\ell$。这一步在 LP 之外完成，只和拓扑 + 路由规则有关。目标 $\sum_{(i,j)\in\mathcal{P}_\ell} D_{ij}$ 就是**链路 $\ell$ 上汇聚的总流量**（以"端口带宽"为单位）。LP 的任务是在所有合法流量矩阵中，找一个使这个和最大的。

**② 行和=1**：每个源 $i$ 把它的 1 单位流量分配出去。$\sum_j D_{ij} = 1$ 就是"源 $i$ 满速率发送"。

**③ 列和=1**：每个目的 $j$ 收到恰好 1 单位。$\sum_i D_{ij} = 1$ 就是"目的 $j$ 满速率接收"。

**④ 对角线=0**：$D_{ii}=0$，端口不给自己发包。

**⑤ 非负**：$D_{ij} \ge 0$，物理上流量不能是负的。

### 为什么松弛不改变最优值

目标函数 $\sum_{(i,j)\in\mathcal{P}_\ell} D_{ij}$ 是 $\mathbf{D}$ 各元素的**线性组合**（系数要么是 1 要么是 0）。可行集 $\mathcal{D}$（双随机矩阵）是凸多面体，其顶点恰好是排列矩阵（Birkhoff-von Neumann）。**线性函数在凸多面体上的最大值一定在顶点取到** → LP 的最优解自动是一个排列矩阵 → $D_{ij}$ 自动全是 0 或 1。松弛不损失精度。

---

## 9. LP 解出之后：从 $L^*$ 到无阻塞判据

### 9.1 每条链路的瓶颈分析

对**每条**内部链路 $\ell$，求解 §8 的 LP，得到该链路在最坏排列下的最大负载：

$$L_\ell^* = \max_{\mathbf{D}\in\mathcal{D}} \sum_{(i,j)\in\mathcal{P}_\ell} D_{ij}$$

$L_\ell^*$ 的单位是"端口带宽的倍数"。它的物理含义：

> **在最坏的排列下，链路 $\ell$ 上汇聚了 $L_\ell^*$ 条端口满速率流。**
>
> 链路 $\ell$ 自身的线速率 = $B_{\text{link}}$ = 1 单位（归一化）。
>
> 因此每条经过 $\ell$ 的流最多只能分到 $B_{\text{link}} / L_\ell^*$ 的带宽。

- $L_\ell^* = 1$：链路 $\ell$ 在任何排列下都不会过载
- $L_\ell^* = 2$：存在某个排列，使 $\ell$ 上挤了 2 条流，每条流最多只能以 $B_{\text{link}}/2$ 的速率通过
- $L_\ell^* = 3$：最坏情况 3 条流共享，每条 $B_{\text{link}}/3$

### 9.2 全网瓶颈

取所有链路中最坏的那个：

$$\boxed{L^* = \max_{\ell} L_\ell^*}$$

$L^*$ 就是**全网的瓶颈链路在最坏排列下的负载**。

### 9.3 无阻塞带宽

每条流端到端经过多条链路。只要**最坏的那条链路**不把流降速太多，整条流的速率就是由它决定的（木桶原理）。

$$\boxed{B_{\text{nonblocking}} = \frac{B_{\text{link}}}{L^*}}$$

### 9.4 可行性判定

目标带宽 $B_{\text{target}}$（如 800 Gbps）能否达到：

$$\boxed{B_{\text{nonblocking}} \ge B_{\text{target}} \quad \Longleftrightarrow \quad L^* \le \frac{B_{\text{link}}}{B_{\text{target}}}}$$

在 $B_{\text{link}} = B_{\text{target}}$ 的特殊情况（内部链路速率 = 端口速率，常见假设）：

$$B_{\text{nonblocking}} \ge B_{\text{target}} \quad \Longleftrightarrow \quad L^* \le 1$$

### 9.5 三种情况总结

| $L^*$ | $B_{\text{nonblocking}}$ | 含义 |
|---|---|---|
| $=1$ | $= B_{\text{link}}$ | **真无阻塞**：不管谁发给谁，每条链路最多承载 1 条流，所有流满速通过 |
| $>1$ 但 $\le B_{\text{link}}/B_{\text{target}}$ | $\ge B_{\text{target}}$ | **广义无阻塞**：最坏情况下有链路被多条流共享，但降速后仍 $\ge$ 目标速率 |
| $> B_{\text{link}}/B_{\text{target}}$ | $< B_{\text{target}}$ | **不可行**：存在某个排列，使瓶颈链路降速到目标以下 |

---

## 10. 和 Dragonfly 拓扑的关系

Dragonfly 拓扑 $(a,p,h,g)$ 决定了：

| 决定因素 | 含义 |
|---|---|
| 终端集合 | $\{1,\ldots,N\}$，$N = a \cdot p \cdot g$ |
| det 路由 | 对每对 $(i,j)$，路径由 Dragonfly 的分层结构预先确定 |
| 链路集合 $\{\ell\}$ | 哪些是有向链路（intra-group 链路 + global 链路） |
| $\mathcal{P}_\ell$ | 对每条链路 $\ell$，哪些 $(i,j)$ 的路径经过了它 |

改变拓扑参数 $(a,p,h)$ → $N$ 变 → 路由变 → $\mathcal{P}_\ell$ 变 → $L^*$ 变 → $B_{\text{nonblocking}}$ 变。

整个 LP 的其他部分——双随机矩阵的定义、行和=1、列和=1——**与拓扑无关**。拓扑只通过 $\mathcal{P}_\ell$ 进入 LP。

---

## 11. 和代码的对应关系

对应 `src/wafer_dse/architecture_model/solver/_potential/_adversarial.py` 中的 `_AdversarialLp.compute()`：

| 数学 | 代码 |
|---|---|
| 双随机矩阵 $\mathbf{D}$ | `D_param = cvx.Variable((n, n), nonneg=True)` |
| 行和=1 | `cvx.sum(D_param[i, :]) == 1` |
| 列和=1 | `cvx.sum(D_param[:, i]) == 1` |
| 对角线=0 | `D_param[i, i] == 0` |
| $\mathcal{P}_\ell$ | `link_pairs[link] = [(si, di), ...]` 预计算 |
| LP 求解 | `cvx.Problem(cvx.Maximize(...), constraints).solve()` |
| 全网 $L^*$ | 所有链路取 `max` |

---

## 12. 广义无阻塞：从"一条路径"到"多条路径"

### 12.1 det 的局限

前面 §4-§9 讲的是**确定性路由（det）**：每个 $(i,j)$ 对只有一条固定的路径。$D_{ij}$ 的全部流量只能走这条路。

链路 $\ell$ 的负载 = $\sum_{(i,j) \in \mathcal{P}_\ell} D_{ij}$——就是那些"唯一路径经过 $\ell$"的 $(i,j)$ 对的流量之和。

这个模型的自由度很低：我们只能选 $D_{ij}$（谁发给谁），但不能选路由。路由是死的。

### 12.2 Valiant 路由：一个 $(i,j)$ 有多条候选路径

Dragonfly 的 Valiant 路由：从 $i$ 到 $j$，先走 global link 到一个**随机中间 group**，再走 intra-group link 到 $j$。

因为中间 group 有多种选择（$g$ 种），$(i,j)$ 对就有**多条候选路径**。记 $\Pi(i,j)$ 为所有候选路径的集合。

### 12.3 两种不同的变量

现在我们需要区分**两个层次**的变量：

| 变量 | 含义 | 层次 |
|---|---|---|
| $D_{ij}$ | 源 $i$ 到目的 $j$ 的总流量 | 流量矩阵（端到端） |
| $f_{ij}^k$ | $D_{ij}$ 分配给第 $k$ 条候选路径的**分量** | 路径流量（更细粒度） |

关系：

$$\boxed{\sum_{k=1}^{|\Pi(i,j)|} f_{ij}^k = D_{ij}}$$

即 $D_{ij}$ 被拆成若干份，分别走不同的候选路径。

### 12.4 链路负载：统一形式

和 det 情况一样，定义**指示集**：

$$\mathcal{P}_\ell = \{(i,j,k) : \text{第 }k\text{ 条候选路径经过了 }\ell\}$$

链路负载就是在这个指示集上求和：

$$\boxed{\text{load}_\ell = \sum_{(i,j,k) \in \mathcal{P}_\ell} f_{ij}^k}$$

**det 是 Valiant 在 $|\Pi(i,j)|=1$ 时的特例**：每个 $(i,j)$ 只有一条路径，$f_{ij}^1 = D_{ij}$，指示集退化为 $\mathcal{P}_\ell = \{(i,j,1) : \text{唯一路径经过了 }\ell\}$。于是：

$$\text{load}_\ell = \sum_{(i,j,1) \in \mathcal{P}_\ell} f_{ij}^1 = \sum_{(i,j) \in \mathcal{P}_\ell} D_{ij}$$

**两种情况的负载定义完全统一**：指示集 $\mathcal{P}_\ell$ 标记了哪些"分量"经过这条链路，链路负载就是这些分量的和。唯一区别是索引维度——det 是 $(i,j)$，Valiant 是 $(i,j,k)$。

### 12.5 统一的 LP

$$
\boxed{
\begin{aligned}
\min_{t,\;\mathbf{D},\;\mathbf{f}} \quad & t \\[6pt]
\text{s.t.} \quad & \mathbf{D} \in \mathcal{D} && \text{$\mathbf{D}$ 双随机} \\[4pt]
& \sum_{k} f_{ij}^k = D_{ij} \quad \forall(i,j) && \text{端到端流量 = 各分量之和} \\[4pt]
& \sum_{(i,j,k) \in \mathcal{P}_\ell} f_{ij}^k \le t \quad \forall\ell && \text{链路负载} \le t \\[4pt]
& f_{ij}^k \ge 0 \quad \forall i,j,k
\end{aligned}
}
$$

和 det LP（§8）对比——结构一模一样，只是多了一层路径索引：

| | det LP | Valiant LP |
|---|---|---|
| 变量 | $\mathbf{D}$ | $\mathbf{D} + \mathbf{f}$ |
| $\mathcal{P}_\ell$ 索引 | $(i,j)$ | $(i,j,k)$ |
| 链路负载 | $\sum_{(i,j)\in\mathcal{P}_\ell} D_{ij}$ | $\sum_{(i,j,k)\in\mathcal{P}_\ell} f_{ij}^k$ |
| 优化 | $\max$ 负载（被动算） | $\min$ 最大负载（主动优化） |

### 12.6 为什么这叫"广义无阻塞"

det LP（§8）：$L^*$ 是**被动承受**的——路由是死的，只能接受流量集中。

Valiant LP（本节）：$t^*$ 是**主动优化**的——同时选谁发给谁 + 每条流走哪条路径，最小化瓶颈。

因为 Valiant 的自由度更大（det 的路由是 Valiant 候选路径的一个特例——只选一条、不分流），$t^* \le L^*$ 总是成立。

**广义无阻塞** = 虽然单条固定路径可能阻塞（$L^* > 1$），但通过主动分流可以把瓶颈压到 $t^* \le 1$。

---

## 总结

1. **排列** $\pi$ = 一种谁发给谁的方案（$N!$ 种可能）
2. **排列矩阵** $\mathbf{P}$ = $\pi$ 的 0-1 矩阵表示
3. **Birkhoff–von Neumann**：排列矩阵的凸包 = 双随机矩阵多面体
4. **松弛**：把离散搜索 $(\max_{\mathbf{P} \in \mathcal{P}})$ 变成连续 LP $(\max_{\mathbf{D} \in \mathcal{D}})$
5. **松弛不损失精度**：因为目标函数是线性的，极值在顶点 = 排列矩阵 = 0/1
6. **链路负载**：$\text{load}_\ell = \sum_{x \in \mathcal{P}_\ell} (\text{变量}_x)$——det 下 $x=(i,j)$，Valiant 下 $x=(i,j,k)$，结构统一
7. **LP 输出**：det 下取 $L^* = \max_\ell\,\text{load}_\ell$；Valiant 下求 $\min t = t^*$ 使所有 $\text{load}_\ell \le t$
8. **无阻塞带宽**：$B_{\text{nonblocking}} = B_{\text{link}} / L^*$（det）或 $B_{\text{link}} / t^*$（Valiant）
9. **解的严格性**：这是 LP 最优值，不是近似，是拓扑在给定路由策略下的**理论上限**
10. **在 DSE 中的角色**：作为**早筛**——$L^* > B_{\text{link}}/B_{\text{target}}$ 则拓扑不可能达标，后面的 bump/热/布线等物理约束不必再看
11. **拓扑的角色**：仅通过 $\mathcal{P}_\ell$（指示集）进入 LP，LP 结构本身与拓扑无关
