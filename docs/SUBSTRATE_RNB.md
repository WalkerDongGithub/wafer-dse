# Substrate 层可重排无阻塞（RNB）的数学表述

> 问题：$N$ 个完全相同的 interposer，通过 substrate 层互联（度约束 $K$），
> 每个 interposer 有 $M$ 个外部端口、每端口速率 $B$。
> substrate 在什么条件下是**可重排无阻塞**的？这个条件的精确数学形式是什么？

---

## 0. 问题设定

### 0.1 物理对象

```
┌─────────────────────────────────────────────────────────┐
│                    Substrate Graph                       │
│  G = (V, E),  |V| = N,  deg(v) = K ∀v                  │
│                                                         │
│  每条边 e = (v,w) ∈ E 的物理容量:                        │
│    ℓ_e 条 lane, 每 lane 速率 R_e                        │
│    总带宽: C_e = ℓ_e · R_e  (Gbps)                      │
│                                                         │
│  每个顶点 v ∈ V 关联:                                    │
│    M 个外部端口（每端口 B Gbps）                          │
│    K 条 substrate 链路（度数 K）                          │
└─────────────────────────────────────────────────────────┘
```

### 0.2 两层流量结构

一个**外部排列** $\pi$ 是 $N \cdot M$ 个外部端口到自身的双射（$\pi(i) \neq i$）。

排列 $\pi$ 在 substrate 层诱导出**interposer 间流量矩阵** $\mathbf{T}^\pi \in \mathbb{Z}_{\ge 0}^{N \times N}$：

$$T_{vw}^\pi = \left|\left\{ \text{端口 } p \in \text{interposer } v : \pi(p) \in \text{interposer } w \right\}\right|$$

$\mathbf{T}^\pi$ 的性质：
- 行和：$\sum_w T_{vw}^\pi = M$（$v$ 的所有端口都发出去）
- 列和：$\sum_v T_{vw}^\pi = M$（$w$ 的所有端口都收到）
- 对角：$T_{vv}^\pi = 0$（不发给自己，可放宽）

所有可能的流量矩阵构成**运输多面体**：

$$\mathcal{T} = \left\{ \mathbf{T} \in \mathbb{R}_{\ge 0}^{N \times N} \;\middle|\;
\sum_w T_{vw} = M,\; \sum_v T_{vw} = M,\; T_{vv} = 0 \right\}$$

$\mathcal{T}$ 的顶点是整数矩阵（全单模），BvN 定理在此处的一个推广保证极值在整数顶点取到。

---

## 1. RNB 的定义

### 1.1 单次排列的路由问题

给定一个具体的 $\mathbf{T} \in \mathcal{T}$，substrate 路由问题为：

> 在 $G$ 中为每对 $(v,w)$ 找到 $T_{vw}$ 个单位（每单位 $=B$ Gbps）的流，
> 使得每条边 $e$ 上的总流量不超过其物理容量 $C_e$。

这是一个**多商品流（multicommodity flow）**问题：

$$\boxed{
\begin{aligned}
\text{find} \quad & \mathbf{f}^{(v,w)} \in \mathbb{R}_{\ge 0}^{|E|} \quad \forall (v,w) \in V \times V,\; v \neq w \\[4pt]
\text{s.t.} \quad & \sum_{p \in \mathcal{P}(v,w)} f_p^{(v,w)} = T_{vw} \quad \forall v \neq w && \text{(需求满足)} \\[4pt]
& \sum_{(v,w)} \sum_{p \ni e} f_p^{(v,w)} \le \ell_e \quad \forall e \in E && \text{(边容量)} \\[4pt]
& f_p^{(v,w)} \ge 0
\end{aligned}
}
$$

其中 $\mathcal{P}(v,w)$ 是 $(v,w)$ 在 $G$ 中的所有候选路径（通常是所有简单路径，或限制跳数）。

### 1.2 可重排无阻塞（RNB）

> **定义**：Substrate $G$ 是**可重排无阻塞**的，当且仅当对**所有** $\mathbf{T} \in \mathcal{T}$，
> 上述多商品流问题都有可行解。

"可重排"的含义：从一个排列切换到下一个排列时，允许拆除全部已有路径并重新建立。
每次排列变更是"从零开始路由"——不需要考虑历史状态和路径连续性。
这对应经典交换理论中 RNB 的定义（Slepian-Duguid 1959）。

### 1.3 与严格无阻塞（SNB）和广义无阻塞的关系

| | SNB (substrate) | RNB (substrate) |
|---|---|---|
| 定义 | 新连接到达时不改变已有路径即可路由 | 允许重排全部路径 |
| 数学 | 在线约束（路径历史依赖） | 离线约束（每次从零开始） |
| 难度 | 极难（需考虑所有中间状态） | 可解（多商品流可行性） |
| 条件 | $K \ge 2M-1$（Clos） | $K \ge M$（Slepian-Duguid） |

**本文选择 RNB 作为分析层级。** 理由：substrate 层的路由重排是批量操作（全交换矩阵更新），
不涉及逐个连接的在线到达。RNB 是正确且更经济的抽象。

---

## 2. 必要条件：割条件（Cut Condition）

### 2.1 推导

对任意子集 $S \subset V$，割 $\delta(S)$ 将图分为 $S$ 和 $V \setminus S$。

在最坏情况下，$S$ 中的所有 $M \cdot |S|$ 个端口全部发往 $V \setminus S$ 中的端口。
这个最坏配置是否合法？
- $V \setminus S$ 共有 $M \cdot (N - |S|)$ 个接收端口
- 合法当且仅当 $M \cdot |S| \le M \cdot (N - |S|)$，即 $|S| \le N/2$

对称地，$V \setminus S$ 发往 $S$ 的最大流量为 $M \cdot (N - |S|)$（当 $|S| \ge N/2$ 时受限）。

**因此**：穿越割 $\delta(S)$ 的总流量需求在最坏情况下为：

$$\boxed{D(S) = M \cdot \min(|S|,\; N - |S|)}$$

单位：端口带宽 $B$。

### 2.2 割条件（Cut Condition）

如果 substrate 是 RNB 的，则对任意 $S \subset V$，割的总容量必须 ≥ 最坏需求：

$$\boxed{\sum_{e \in \delta(S)} C_e \ge M \cdot \min(|S|,\; N - |S|) \cdot B \qquad \forall S \subset V}$$

等价 lane 数形式（令 $C_e = \ell_e \cdot R_e$）：

$$\boxed{\sum_{e \in \delta(S)} \ell_e \cdot \frac{R_e}{B} \ge M \cdot \min(|S|,\; N - |S|) \qquad \forall S \subset V}$$

### 2.3 特殊情况：$K$-正则图 + 均匀容量

如果 $G$ 是 $K$-正则的，且每条边有相同的 lane 数 $\ell$ 和速率 $R$：

$$|\delta(S)| \cdot \ell \cdot \frac{R}{B} \ge M \cdot \min(|S|,\; N - |S|)$$

最紧的割出现在 $|S| = \lfloor N/2 \rfloor$：

$$\boxed{\min_{S: |S| = \lfloor N/2 \rfloor} |\delta(S)| \cdot \ell \cdot \frac{R}{B} \ge M \cdot \left\lfloor \frac{N}{2} \right\rfloor}$$

左边是图的**等周剖面（isoperimetric profile）**——给定顶点数的最小割边数。

### 2.4 割条件的地位

割条件是 RNB 的**必要条件**（割容量不够 → 一定阻塞），但不是充分条件（即使所有割都够，
仍可能因多商品流的复杂性而不可路由）。

对于特定图族（树、环、完全图），割条件也是充分的。对于一般图，两者之间的 gap 由
**流-割间隙（flow-cut gap）**刻画——对于无向图，多商品流的 flow-cut gap 上界为 $O(\log N)$
（Linial, London & Rabinovich 1995）。

---

## 3. 图族分类与 RNB 条件

### 3.1 完全图 $K_N$（全互联 substrate）

每条边 $(v,w)$ 容量 $\ell \cdot R$。从 $v$ 到 $w$ 的直连边直接承载 $T_{vw}$ 的流量（无需中转）。

最坏情况：$T_{vw} = M$（$v$ 的所有端口指向 $w$）。
要求：$\ell \cdot R \ge M \cdot B$，即 $\ell \ge M \cdot B / R$。

每个顶点的总 lane 消耗：$(N-1) \cdot M \cdot B/R$。

**RNB 条件**：
$$\boxed{K \ge N-1 \quad \text{且} \quad \ell \ge M \cdot \frac{B}{R}}$$

当 $K = N-1$ 且每条边 $\ell = M \cdot B/R$ 时可达。

代价：总 lane 数 = $N(N-1)/2 \cdot M \cdot B/R$，随 $N^2$ 增长。仅 $N$ 小时可行。

### 3.2 Clos 折叠网络（分布式中间级）

$N$ 个 interposer 通过 $K$ 个中间节点互联。每个 interposer 有 $K$ 条上联链路
（连到 $K$ 个不同的中间节点），每个中间节点有 $N$ 条链路（连到全部 $N$ 个 interposer）。

每条 substrate 链路容量：$\ell \cdot R$（设为均匀）。

**Slepian-Duguid 定理**：折叠 Clos 是 RNB 当且仅当：

$$\boxed{K \ge M}$$

此时每条 interposer→中间节点 链路的容量需求为 $\ell = B/R$（因为每条链路在重排后恰好承载一个端口的流量）。

代价：每个 interposer 的 substrate lane 总数 = $K \cdot B/R \le$ bump 预算。

**这是本文的主力构造。** $K = M$ 即可保证 RNB，中间节点分布式实现在 $N$ 个 interposer 上。

### 3.3 Benes 网络（递归 Clos，$\log N$ 级）

当 $N$ 更大时（如 $N=32$），用递归 Clos（Benes 网络）：

- 每级二分：$N \to N/2 \to N/4 \to \cdots \to 1$
- 每级度 = 2，共 $2\log_2 N - 1$ 级
- RNB 条件：每级满足 Slepian-Duguid（$m \ge n$），递归构造自动满足

**RNB 条件**：递归构造保证。总交叉点数 = $O(N \log N)$。
每条链路的容量需求仍为 $\ell = B/R$。

### 3.4 $K$-正则 expander 图

如果 $G$ 是一个 $K$-正则 expander（如 Ramanujan 图），具有性质：
对于任意 $S \subset V$ 且 $|S| \le N/2$：
$$|\delta(S)| \ge c \cdot K \cdot |S|$$
其中 $c > 0$ 是 expansion 常数。

割条件给出：
$$c \cdot K \cdot |S| \cdot \ell \cdot R \ge M \cdot |S| \cdot B$$

$$\boxed{K \cdot \ell \ge \frac{M \cdot B}{c \cdot R}}$$

对于最优 expander（$c \approx 1/2$），$K \cdot \ell \ge 2M \cdot B/R$。

Expander 路由是可能的（有分布式路由算法）但比 Clos 复杂。主要用于理论下界。
实际晶圆级系统中，Clos 的规整结构更适合物理布局。

### 3.5 Dragonfly（$a,p,h$）

Dragonfly 作为 substrate 时，RNB 条件需要更精细的分析。

将 $N$ 个 interposer 分为 $g$ 个 group，每个 group 有 $a$ 个 interposer。
Group 内全互联（$a-1$ 条链路/interposer），group 间通过 $h$ 条 global link 连接。

在 Valiant 路由（非最小路由，通过随机中间 group 中转）下，负载在 global link 上被分摊。
但 Valiant 不是 RNB——它是通过牺牲 50% 吞吐（每条流走两次 global link）来换取负载均衡，
而不是通过重排。

**Dragonfly 的 RNB 条件是一个开放问题**（至少没有 Clos 那样的简洁充要条件）。

---

## 4. 统一 RNB 条件：多面体表述

### 4.1 路由多面体

固定 $G$ 和路径集 $\mathcal{P} = \bigcup_{v,w} \mathcal{P}(v,w)$。

对每条路径 $p$，定义变量 $f_p \ge 0$（承载的流量）。对每条边 $e$，定义矩阵 $\mathbf{A}$：

$$A_{e,p} = \begin{cases} 1 & \text{若路径 } p \text{ 经过边 } e \\ 0 & \text{否则} \end{cases}$$

对每个 $(v,w)$ 对，定义需求矩阵 $\mathbf{H}$：

$$H_{(v,w),p} = \begin{cases} 1 & \text{若路径 } p \text{ 连接 } v \to w \\ 0 & \text{否则} \end{cases}$$

多商品流可行性问题：

$$\boxed{
\begin{aligned}
\exists \mathbf{f} \ge 0 \quad \text{s.t.} \quad & \mathbf{H} \cdot \mathbf{f} = \mathbf{T} && \text{(需求满足)} \\
& \mathbf{A} \cdot \mathbf{f} \le \boldsymbol{\ell} && \text{(边容量)} \\
& \mathbf{f} \ge 0
\end{aligned}
}
$$

### 4.2 RNB 作为鲁棒可行性

Substrate 是 RNB 当且仅当：

$$\boxed{\forall \mathbf{T} \in \mathcal{T}, \quad (\mathbf{H} \cdot \mathbf{f} = \mathbf{T},\; \mathbf{A} \cdot \mathbf{f} \le \boldsymbol{\ell}) \text{ 有可行解 } \mathbf{f} \ge 0}$$

由 Farkas 引理，这等价于以下命题对所有 $\mathbf{T} \in \mathcal{T}$ 成立：

$$\forall \mathbf{y} \ge 0 : \mathbf{A}^T \mathbf{y} \ge \mathbf{H}^T \mathbf{z} \;\Longrightarrow\; \mathbf{z}^T \mathbf{T} \le \boldsymbol{\ell}^T \mathbf{y}$$

但这涉及 $\forall \mathbf{T} \in \mathcal{T}$ 的全称量词。

### 4.3 利用 $\mathcal{T}$ 的多面体结构

$\mathcal{T}$ 的顶点有限（全单模多面体）。RNB 等价于：对 $\mathcal{T}$ 的**所有顶点** $\mathbf{T}^k$，路由问题有可行解。

$$\boxed{\forall \mathbf{T}^k \in \text{vert}(\mathcal{T}), \quad \exists \mathbf{f} \ge 0 : \mathbf{H} \cdot \mathbf{f} = \mathbf{T}^k,\; \mathbf{A} \cdot \mathbf{f} \le \boldsymbol{\ell}}$$

$\mathcal{T}$ 的顶点数 = 整数运输矩阵的数量。对于 $N$ 较小（≤ 8），顶点数可控，可以直接枚举验证。

对于 $N$ 更大时：利用对偶性将鲁棒可行性转化为线性规划。

### 4.4 对偶形式：鲁棒可行性 → LP

$\forall \mathbf{T} \in \mathcal{T}$ 的路由可行性等价于以下 LP 的最优值 ≤ 0：

$$\boxed{
\max_{\mathbf{T} \in \mathcal{T}} \; \min_{\mathbf{f} \ge 0} \; \max_{e \in E} \; \left( \frac{(\mathbf{A} \cdot \mathbf{f})_e}{\ell_e} - 1 \right) \quad \text{s.t.} \quad \mathbf{H} \cdot \mathbf{f} = \mathbf{T}
}$$

内层 min-max（固定 $\mathbf{T}$ 下的最优路由）不存在超过容量的边 → 最大值 ≤ 0。
外层 max（对手选最坏 $\mathbf{T}$）使超过容量最大化。
若 max ≤ 0，所有 $\mathbf{T}$ 皆可行 → RNB。

**这是对流-割间隙的 LP 表述。** 对于一般图，此问题至少和最大流问题一样难。
但对于特定图族（Clos、Benes），经典结果直接给出了充要条件（$K \ge M$），无需求解此 LP。

---

## 5. 与 DSE 框架的衔接

### 5.1 RNB 条件作为常数下界

选定 substrate 图族后（如 Clos $K=M$），RNB 条件退化为：

$$K \ge M$$

每条 substrate 链路负载（归一化）为常数 $L_e = 1$（平衡重排下每条链路恰好承载一个端口流量）。
$L_e$ 不再是对手可操纵的变量——RNB 构造已消解了对抗性。

### 5.2 物理约束检查

$L_e = 1$ 作为常数进入统一 LP：

$$\boxed{
\begin{aligned}
\max_{B} \quad & B \\[4pt]
\text{s.t.} \quad & K \ge M && \text{(RNB 条件：离散参数检查)} \\[4pt]
& \ell_e = L_e \cdot \frac{B}{R_e} = 1 \cdot \frac{B}{R_e} && \text{(每条 substrate 链路的 lane 需求)} \\[4pt]
& \sum_{e \in \delta(v)} \ell_e \le N_v^{\text{sig}} \quad \forall v && \text{(bump 预算)} \\[4pt]
& \text{热约束、翘曲约束} \ldots
\end{aligned}
}
$$

**结果**：给定 $N, M, K$ 和图族选择，$B^*$ 由最紧的物理约束决定。
RNB 条件保证：只要物理约束撑得住，任何排列都能被路由。

### 5.3 当 $K < M$ 时

如果 bump 预算不够支撑 $K \ge M$：

- 系统是 oversubscribed 的
- 最大无阻塞带宽按比例缩放：$B_{\text{eff}} = \frac{K}{M} \cdot B_{\text{link}}$
- 此时 $L_e = M/K > 1$（链路被多条流共享，每条流降速到 $B_{\text{link}} / (M/K)$）

---

## 6. 总结

| 层级 | RNB 条件 | 数学形式 | 求解难度 |
|------|---------|---------|---------|
| 完全图 $K_N$ | $\ell \ge M \cdot B/R$（每条边） | 常数检查 | O(1) |
| Clos 折叠 | $K \ge M$ | 参数比较 | O(1) |
| Benes 递归 | 递归构造保证 | 构造 | O(1) |
| $K$-正则 expander | $K \cdot \ell \ge M \cdot B / (c \cdot R)$ | 割条件检查 | O(1) |
| Dragonfly | 未完全解决 | 多商品流 + 对抗性 $\mathbf{T}$ | 开放 |
| 一般图 | $\forall \mathbf{T} \in \mathcal{T}$，多商品流可行 | max-min LP（§4.4） | 难（需要验证全部顶点或利用对偶） |

**推荐路径**：对 substrate 采用 Clos 构造（$K \ge M$），
RNB 由 Slepian-Duguid 定理保证。DSE 框架只需检查物理约束是否支撑 $K \ge M$ 所需的 lane 数。
这不失一般性——如果未来有更好的 substrate 构造（如新型 expander），
只需替换 RNB 条件，框架其他部分（$L_e \to \ell_e \to$ bump + 热约束）不变。

---

## 参考文献

1. C. Clos, "A Study of Non-Blocking Switching Networks," *Bell System Technical Journal*, 1953.
2. D. Slepian, "Two Theorems on a Particular Crossbar Switching Network," 1952.
3. A.M. Duguid, "Structural Properties of Switching Networks," Brown University, 1959.
4. V.E. Benes, *Mathematical Theory of Connecting Networks and Telephone Traffic*, 1965.
5. F.K. Hwang, *The Mathematical Theory of Nonblocking Switching Networks*, 1998.
6. N. Linial, E. London, Y. Rabinovich, "The Geometry of Graphs and Some of Its Algorithmic Applications," *Combinatorica*, 1995. (flow-cut gap)
7. S. Hoory, N. Linial, A. Wigderson, "Expander Graphs and Their Applications," *Bull. AMS*, 2006.
