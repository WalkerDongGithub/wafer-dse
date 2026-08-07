# 内层 LP 的原问题与对偶问题

## 原问题（Primal）

给定流量矩阵 $\mathbf{D}$，选择分流 $\mathbf{f}$ 使瓶颈负载 $t$ 最小：

$$\boxed{
\begin{aligned}
\min_{t,\; \mathbf{f}} \quad & t \\
\text{s.t.} \quad & \sum_{k} f_{ij}^k = D_{ij} && \forall (i,j) \quad (\text{自由变量 } \alpha_{ij}) \\
& \sum_{(i,j,k):\, e \in \text{path}(i,j,k)} f_{ij}^k \le t && \forall e \in \mathcal{E} \quad (\beta_e \ge 0) \\
& f_{ij}^k \ge 0 \quad \forall (i,j,k), \quad t \ge 0
\end{aligned}
}$$

- 变量数：$\sum_{(i,j)} |\Pi(i,j)| + 1 \sim O(N^2 \cdot g)$
- 约束数：$N^2 + |\mathcal{E}|$
- 第一个约束（$\alpha_{ij}$）是等式，对偶变量自由
- 第二个约束（$\beta_e$）是不等式，对偶变量 $\ge 0$

---

## 拉格朗日函数

$$L(t, \mathbf{f}, \alpha, \beta) = t + \sum_{i,j} \alpha_{ij} \left(D_{ij} - \sum_k f_{ij}^k\right) + \sum_e \beta_e \left(\sum_{(i,j,k): e \in \text{path}} f_{ij}^k - t\right)$$

展开：

$$L = \sum_{i,j} D_{ij} \alpha_{ij} + t\left(1 - \sum_e \beta_e\right) + \sum_{(i,j,k)} f_{ij}^k \left(\sum_{e \in \text{path}(i,j,k)} \beta_e - \alpha_{ij}\right)$$

对偶函数：$g(\alpha, \beta) = \min_{t \ge 0,\; \mathbf{f} \ge 0} L$

---

## 对偶约束的推导

$g$ 有界需要三个系数非正（否则可令对应变量 $\to \infty$ 使 $L \to -\infty$）：

| 项 | 系数 | 条件 |
|---|---|---|
| $t$ | $1 - \sum_e \beta_e$ | $= 0$ → $\displaystyle\sum_e \beta_e = 1$ |
| $f_{ij}^k$ | $\sum_{e \in \text{path}(i,j,k)} \beta_e - \alpha_{ij}$ | $\ge 0$ → $\displaystyle\alpha_{ij} \le \sum_{e \in \text{path}(i,j,k)} \beta_e$ |

当两个条件成立时，最小化时取 $t=0,\; f_{ij}^k=0$，得 $L = \sum D_{ij} \alpha_{ij}$。

---

## 对偶问题（Dual）

$$\boxed{
\begin{aligned}
\max_{\alpha,\; \beta} \quad & \sum_{i,j} D_{ij} \cdot \alpha_{ij} \\
\text{s.t.} \quad & \alpha_{ij} \le \sum_{e \in \text{path}(i,j,k)} \beta_e && \forall (i,j,k) \\
& \sum_{e \in \mathcal{E}} \beta_e = 1 \\
& \beta_e \ge 0 \quad \forall e \in \mathcal{E} \\
& \alpha_{ij} \text{ 自由}
\end{aligned}
}$$

- 变量数：$N^2 + |\mathcal{E}|$（$\alpha_{ij}$ 每个端口对，$\beta_e$ 每条链路）
- 约束数：$\sum_{(i,j)} |\Pi(i,j)| + 1$

---

## 物理含义

| 变量 | 含义 |
|------|------|
| $\beta_e$ | 链路 $e$ 的"容量价格"。$\sum_e \beta_e = 1$ 意味着总容量预算归一，瓶颈链路获得高权重 |
| $\sum_{e \in \text{path}} \beta_e$ | 路径 $(i,j,k)$ 的"成本"——途经所有链路的容量价格之和 |
| $\alpha_{ij}$ | $(i,j)$ 对的"影子收益"。对偶约束 $\alpha_{ij} \le \sum_{e \in \text{path}} \beta_e$（对所有 $k$）意味着：$\alpha_{ij}$ 不超过**最短**路径的链路成本之和 |

**在最优解处**：

$$\alpha_{ij}^* = \min_{k} \sum_{e \in \text{path}(i,j,k)} \beta_e^*$$

即每个 $(i,j)$ 对的收益恰好等于其最短路径的链路成本总和。

**对偶目标**：$\max \sum_{i,j} D_{ij} \cdot \alpha_{ij}$。进攻方已知 $\alpha_{ij}$ 受链路价格 $\beta_e$ 约束，选择 $\beta_e$ 来最大限度抬高 $\sum D_{ij} \alpha_{ij}$。

由 LP 强对偶：$\text{Primal opt} = \text{Dual opt} = V(\mathbf{D})$。

---

## 用于外层问题

外层问题是 $\max_{\mathbf{D} \in \mathcal{D}} V(\mathbf{D})$。用对偶表达：

$$V(\mathbf{D}) = \max_{(\alpha,\beta) \in \mathcal{F}_{\text{dual}}} \sum_{i,j} D_{ij} \cdot \alpha_{ij}$$

$$\max_{\mathbf{D} \in \mathcal{D}} V(\mathbf{D}) = \max_{(\alpha,\beta) \in \mathcal{F}_{\text{dual}}} \; \max_{\mathbf{D} \in \mathcal{D}} \; \sum_{i,j} D_{ij} \cdot \alpha_{ij}$$

其中 $\mathcal{F}_{\text{dual}} = \{(\alpha,\beta) : \alpha_{ij} \le \sum_{e \in \text{path}(i,j,k)} \beta_e,\; \sum_e \beta_e = 1,\; \beta_e \ge 0\}$。

内层 $\max_{\mathbf{D} \in \mathcal{D}} \sum D_{ij} \alpha_{ij}$（固定 $\alpha$）是线性函数在双随机多面体上的最大化 → Birkhoff → 等价于 $\max_{\text{排列 } \pi} \sum_i \alpha_{i,\pi(i)}$ → 匈牙利 $O(N^3)$。
