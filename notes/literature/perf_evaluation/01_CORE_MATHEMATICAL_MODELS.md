# 01 各性能模型的核心数学模型（统一符号）

> 配套 `00_REVIEW_FRAMEWORK.md` 的定性审视。这里用**一套符号**重述每篇的核心数学模型，符号优先沿用 v4（`MATH_MODEL_COMPLETE_V4.md`），没有的才新引入。
> 分「带宽轴」与「延迟轴」两组——对应框架扫出的「性能两轴分裂」。

---

## 0. 统一符号表

| 符号 | 含义 | 与 v4 的关系 |
|------|------|-------------|
| $n$ | 端口 / 终端数 | = $\lvert\mathcal{V}\rvert$ |
| $\mathbf{D}=(D_{ij})$ | 流量需求矩阵，$D_{ij}$ = i→j 的流量**率** | v4 的 $\mathbf{D}^{(r)}$ 去掉模式下标、放宽到任意非负矩阵 |
| $\mathbf{P}$ | 排列矩阵（每行每列恰一个 1） | v4 排列需求的特例 |
| $\mathbf{L}$ | 链路负载（包络） | v4 同义 |
| $B,\ \boldsymbol{\ell}$ | 端口带宽、物理 lane 数 | v4 同义 |
| $\lambda_{ij},\ \mu$ | 到达率、单链路服务率（queueing） | $\lambda_{ij}$ 即连续化的 $D_{ij}$；$\mu$ 对应 $B\cdot S_{\text{bw}}$ |
| $\rho$ | 利用率 $\rho=\lambda/\mu$ | 新引入 |
| $\mathbf{R}(t)$ | 累计到达流量（时间函数） | 新引入（网络演算） |
| $\alpha(t),\ \beta(t)$ | arrival curve（需求上界）、service curve（供给下界） | 新引入（网络演算） |
| $h(\alpha,\beta),\ v(\alpha,\beta)$ | 延迟界、积压界 | 新引入（网络演算） |

> 核心对应：**别人的「流量矩阵」= 我们的 $\mathbf{D}$；别人的「服务率/链路容量」= 我们的 $B\cdot S_{\text{bw}}$；别人的「link load」= 我们的 $\mathbf{L}$**。这是统一符号的枢纽。

---

## 1. 带宽轴（输出：无阻塞 / 吞吐 / radix）

### 1.1 我们 —— Birkhoff 排列 + LP 包络

**问题**：给定拓扑，最大无阻塞带宽 $B^*$ 是多少？

**核心**：最坏流量 = 排列 $\mathbf{P}\in\mathcal{R}$（Birkhoff：任意 admissible $\mathbf{D}$ 是排列凸组合）。每个排列独立做最优分流，链路负载取包络：

$$
\forall \mathbf{P}\in\mathcal{R}:\quad
\sum_k f^k_{ij} = P_{ij},\qquad
\mathbf{L}^{(r)} = \mathcal{P}_r\,\mathbf{f}^{(r)},\qquad
\mathbf{L} = \max_r \mathbf{L}^{(r)}
$$

物理桥梁：$\boldsymbol{\ell} = B\,\mathbf{S}_{\text{bw}}^{-1}\,\mathbf{L}$，再进 bump/热约束。二分搜索 $B^*$。

**结论**：$B^*$ 是无阻塞带宽；$\mathbf{L}$ 是「所有排列下最坏负载」。

---

### 1.2 McKeown 1996 —— 100% throughput（输入排队）

**问题**：输入排队交换机（每输入 $n$ 个 VOQ）能达多少吞吐？

**核心**：admissible 流量 $\sum_j D_{ij}\le1,\ \sum_i D_{ij}\le1$；每时隙做**最大权重匹配**（权重 = 队列长度 $q_{ij}$），并证明二次 Lyapunov 函数漂移为负：

$$
V = \sum_{i,j} q_{ij}^2 \;\Rightarrow\; \mathbb{E}[\Delta V] < 0 \;\Rightarrow\; \text{稳定}
$$

**结论**：最大权重匹配 → **100% throughput**（任意 admissible、均匀或非均匀独立到达）。FIFO 只有 58.6%（HOL blocking 上界）。

---

### 1.3 Chang 1999 —— Birkhoff 分解 + service guarantee

**问题**：不做逐时隙匹配，怎么给确定性 service guarantee？

**核心**：von Neumann 把 doubly-substochastic $\mathbf{D}$ 补成双随机，Birkhoff 分解为排列凸组合：

$$
\mathbf{D} \;\le\; \tilde{\mathbf{D}} = \sum_{k=1}^{K} \phi_k \mathbf{P}_k,\qquad \sum_k \phi_k = 1,\qquad K \le n^2-2n+2
$$

调度 = 按权重 $\phi_k$ 轮转（weighted round-robin）用排列 $\mathbf{P}_k$。

**结论**：对**所有**非均匀流量统一给 service guarantee，即 100% throughput；offline 复杂度 $O(n^{4.5})$，online $O(\log n)$。

---

### 1.4 Yuan 2009 —— oblivious routing 性能比

**问题**：流量不确定（不给定 $\mathbf{D}$），路由能多差于最优？

**核心**：oblivious 路由（路径与流量无关）的性能比：

$$
\text{ratio} = \max_{\mathbf{D}} \frac{\lVert\mathbf{L}^{\text{obl}}(\mathbf{D})\rVert_{\infty}}{\lVert\mathbf{L}^{\text{opt}}(\mathbf{D})\rVert_{\infty}}
$$

**结论**：fat-tree 上单路径 ratio 有下界（且可达）；**多路径 ratio = 1**（对任意 $\mathbf{D}$ 与最优同优）。$\mathbf{L}$ 仍是链路负载，但不再靠枚举最坏 $\mathbf{D}$，而是直接给 ratio 保证。

---

### 1.5 Zhang-Shen & McKeown 2008 —— VLB（Valiant load-balancing）

**问题**：任意流量矩阵 + 容错，如何无拥塞？

**核心**：两跳中转 $i\to k\to j$，负载摊到全网格：

$$
\mathbf{L} = \underbrace{\mathbf{D}/\text{access}}_{一跳} + \underbrace{\text{中转流量}}_{两跳} \;\Rightarrow\; \text{需 } 2\times \text{ 容量}
$$

**结论**：VLB 支持**任意** $\mathbf{D}$ 无拥塞；容忍 $k$ 个故障仅需 $k/n$ 过配。这是「用 2× 带宽换流量无关性」的经典取舍。

---

## 2. 延迟轴（输出：延迟界 / 平均延迟）

### 2.1 Le Boudec & Thiran —— 网络演算（确定性延迟/积压界）

**问题**：最坏情况下延迟和 buffer 需要多大？（**确定性界，非平均**）

**核心**：三件套。

**(a) arrival curve $\alpha$**（需求上界）：
$$
\mathbf{R}(t)-\mathbf{R}(s) \le \alpha(t-s),\quad \forall s\le t
$$

**(b) service curve $\beta$**（供给下界，min-plus 卷积 $\otimes$）：
$$
\mathbf{R}^*(t) \ge (\mathbf{R}\otimes\beta)(t) = \inf_{0\le s\le t}\{\mathbf{R}(s)+\beta(t-s)\}
$$

**(c) 两个界**（最大水平/垂直距离）：
$$
h(\alpha,\beta)=\sup_t\inf\{d:\alpha(t)\le\beta(t+d)\},\qquad
v(\alpha,\beta)=\sup_t\{\alpha(t)-\beta(t)\}
$$

**结论**：$h$ = 端到端延迟上界，$v$ = buffer（积压）上界。给「延迟界」而非「无阻塞」，但二者同属 worst-case 确定性框架。

> 对应关系：$\alpha$ 是「需求结构体」的网络演算版（比 $\mathbf{D}$ 多时序），$\beta$ 是「供给」的时序版（对应 $B\cdot S_{\text{bw}}$ 的时序化）。

---

### 2.2 Harchol-Balter —— queueing theory（平均延迟）

**问题**：给定到达/服务分布，平均延迟、队列长度多少？

**核心**：三条定律（统一到 $\lambda,\mu,\rho$）。

**Little's law**（最普适）：
$$
\bar{N} = \lambda\,\bar{W}
$$

**M/M/1**（指数到达 + 指数服务）：
$$
\bar{W} = \frac{1}{\mu-\lambda},\qquad \bar{N} = \frac{\rho}{1-\rho},\qquad \rho=\frac{\lambda}{\mu}
$$

**M/G/1**（一般服务分布，Pollaczek–Khinchin）：
$$
\bar{W} = \frac{\lambda\,\mathbb{E}[S^2]}{2(1-\rho)}
$$

**结论**：平均指标，$\rho\to 1$ 时 $\bar{W}\to\infty$（饱和）。与网络演算的「最坏界」互补：一个给均值，一个给上界。

---

### 2.3 NoC queueing 三篇 —— 分析延迟模型（Kiasari / Fischer / Mandal）

统一为同一范式（三篇的差别只在细节）：

**Kiasari 2013**（G/G/1，wormhole，任意拓扑 + 确定性路由 + 任意流量）：
$$
\bar{W}_{ij} = \text{每跳等待之和},\quad \text{误差} <10\%, \text{快于仿真 } 10^4\times
$$

**Fischer 2012**（queueing，给路由器**稳态分布**而非均值）：
$$
\pi(\text{router state}) \Rightarrow \bar{W},\ \text{buffer usage},\ \text{blocking prob},\quad \text{误差}\sim 3\%
$$

**Mandal 2019**（**优先级**感知，工业 NoC）：
$$
\text{高优先级抢占低优先级} \Rightarrow \bar{W}_{ij}^{\text{class}},\quad \text{精度 } 97\%
$$

**结论**：都是「平均延迟」的快速解析估计，输入全是 $(\mathbf{D},\ \text{拓扑},\ \text{routing/mapping})$，输出 $\bar{W}$。**无一回答无阻塞，也无一碰功耗**。

---

## 3. 一张表收束

| 模型 | 需求结构体（统一符号） | 输出 | 确定性/平均 | 功耗 |
|------|----------------------|------|------------|------|
| 我们 | 排列 $\mathbf{P}\in\mathcal{R}$ | 无阻塞 $B^*$ + $\mathbf{L}$ | 确定性（worst-case） | 有（线性+静态） |
| McKeown / Chang | admissible $\mathbf{D}$ | 100% throughput | 确定性（稳定） | 无 |
| Yuan | 不确定 $\mathbf{D}$ | ratio（$\mathbf{L}$ 比值） | 确定性（worst-case） | 无 |
| Zhang-Shen | 任意 $\mathbf{D}$ | congestion-free | 确定性 | 无 |
| Le Boudec | arrival curve $\alpha$ | $h$（延迟界）+ $v$（积压） | 确定性（worst-case） | 无 |
| Harchol-Balter | $\lambda,\mu$ 分布 | $\bar{W},\bar{N}$ | 平均 | 无 |
| NoC queueing | $\mathbf{D}$ + 拓扑 + routing | $\bar{W}_{ij}$ | 平均 | 无 |

**唯一横跨「带宽 × 功耗」的格子是我们**；「带宽 × 延迟」的格子（$B^*$ 同时给延迟界）是空的——网络演算的 $h(\alpha,\beta)$ 是唯一现成入口。
