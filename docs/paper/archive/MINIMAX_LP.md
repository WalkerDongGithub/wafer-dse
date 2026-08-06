# Minimax 非阻塞判据：通用形式

## 问题结构

两个对抗方：

- **防守方**选路由策略 $\mathbf{f}$（对每个 $(i,j)$ 决定如何在候选路径间分配流量）
- **进攻方**选流量矩阵 $\mathbf{D} \in \mathcal{D}$（排列的凸组合，BvN 保证覆盖所有排列）

防守方先选 $\mathbf{f}$，进攻方看到 $\mathbf{f}$ 后选 $\mathbf{D}$ 最大化瓶颈链路负载。防守方的目标是让这个最坏情况的瓶颈负载尽可能小：

$$\min_{\mathbf{f}} \; \max_{\mathbf{D} \in \mathcal{D}} \; \max_{e \in \mathcal{E}} \; L_e(\mathbf{f}, \mathbf{D})$$

其中 $L_e(\mathbf{f}, \mathbf{D}) = \sum_{(i,j,k): e \in \text{path}(i,j,k)} f_{ij}^k$，且 $\sum_k f_{ij}^k = D_{ij}$。

若此 minimax 值 $\le 1$，则任何排列下都存在路由方案使所有链路不过载——无阻塞。

---

## 转化：从 minimax 到单层 LP

**第一步：内层路由 LP（固定 $\mathbf{D}$，优化 $\mathbf{f}$）**

$$\min_{t, \mathbf{f}} \; t \quad \text{s.t.} \quad \sum_k f_{ij}^k = D_{ij}, \quad \sum_{(i,j,k): e \in \text{path}} f_{ij}^k \le t \;\; \forall e$$

**第二步：对偶**

引入对偶变量 $\alpha_{ij}$（每个 $(i,j)$ 对）和 $\beta_e \ge 0$（每条链路，$\sum_e \beta_e = 1$）。内层 LP 的对偶为：

$$\max_{\alpha, \beta} \; \sum_{i,j} D_{ij} \cdot \alpha_{ij} \quad \text{s.t.} \quad \alpha_{ij} \le \sum_{e \in \text{path}(i,j,k)} \beta_e \;\; \forall (i,j,k)$$

**第三步：进攻方选 $\mathbf{D}$**

进攻方在 $\mathcal{D}$ 上最大化 $\sum D_{ij} \alpha_{ij}$。对于固定的 $\alpha$，线性函数在双随机多面体上的最大值等于其在排列顶点上的最大值（BvN），等价于一个分配问题：

$$\max_{\mathbf{D} \in \mathcal{D}} \sum_{i,j} D_{ij} \alpha_{ij} = \max_{\text{排列 } \pi} \sum_i \alpha_{i, \pi(i)}$$

分配问题写为 LP 并取对偶（变量 $u_i, v_j$）：

$$\min_{u, v} \; \sum_i u_i + \sum_j v_j \quad \text{s.t.} \quad u_i + v_j \ge \alpha_{ij} \;\; \forall (i,j)$$

**第四步：合并**

将第三步的对偶代入第二步的目标，消去 $\alpha_{ij}$（在最优解处 $u_i + v_j = \alpha_{ij}$）：

$$\boxed{
\begin{aligned}
\min_{\beta,\; u,\; v} \quad & \sum_{i=1}^N u_i + \sum_{j=1}^N v_j \\
\text{s.t.} \quad & \sum_{e \in \mathcal{E}} \beta_e = 1, \quad \beta_e \ge 0 \;\; \forall e \\
& u_i + v_j \le \sum_{e \in \text{path}(i,j,k)} \beta_e \quad \forall (i,j,k)
\end{aligned}
}$$

一条约束将链路权重 $\beta_e$ 与节点势 $u_i, v_j$ 连接：对每个 $(i,j)$ 的每条候选路径，$u_i + v_j$ 不超过该路径上所有链路的权重之和。

---

## 物理直觉

- $\beta_e$ 是给每条链路分配的"容量价格"（总和为 1，瓶颈链路获得高权重）
- $u_i + v_j$ 是进攻方给 $(i,j)$ 对估算的"收益"——如果在某条路径上 $\sum_{e \in \text{path}} \beta_e$ 很大（路径重），进攻方会把流量往这对上集中
- 防守方选 $\beta$ 让进攻方无利可图——任何 $(i,j)$ 的收益都不超过其路径成本
- 最优值 $t^* = \sum_i u_i^* + \sum_j v_j^*$，若 $\le 1$ 则无阻塞

---

## 与 $|\mathcal{E}|$ 个分边 LP 的比较

| | 分边 max LP | Minimax LP |
|---|---|---|
| 变量数 | $|\mathcal{E}|$ 个独立 LP，每个 $O(N^2 \cdot g)$ | 1 个 LP，$O(|\mathcal{E}| + N)$ |
| $\mathbf{f}$ 的角色 | 帮进攻方灌流量（错误） | 帮防守方分流（正确） |
| $\mathbf{D}$ 的角色 | 进攻方自由选（正确） | 进攻方自由选（正确） |
| 拓扑依赖 | 无 | 无 |
| 对偶分析 | 分散在 $|\mathcal{E}|$ 个 LP | 集中在一个 LP |
