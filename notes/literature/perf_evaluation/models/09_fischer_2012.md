# 09 Fischer 2012 —— 基于 queueing 的 many-core NoC 灵活解析模型

> 出处：E. Fischer, A. Fehske, G. P. Fettweis, "A Flexible Analytic Model for the Design Space Exploration of Many-Core Network-on-Chips Based on Queueing Theory," SIMUL 2012, pp. 119–124。
> 问题：给任意拓扑、任意路由、任意流量模式的 NoC，用 queueing 给出**路由器稳态分布**（而非均值），从而导出任意 KPI（平均延迟、buffer 占用、阻塞概率）。

> **公式来源说明**：本文式 (1)–(6)（网络层）在 PDF 中为位图，无法逐字提取，按正文文字描述交叉确认；式 (7)–(13)（路由器层）正文逐字给出，可直接引用。

## 0. 符号表（本节所有符号在此定义）

| 符号 | 定义 |
|------|------|
| $M,\ Q,\ E$ | 模块数、路由器节点数、链路（边）数 |
| $P$ | 单个路由器的输入端口数 |
| $t_{sd}$ | 流量表征矩阵 $\mathbf{T}=(t_{sd})$（$M\times M$）：模块 $s$→$d$ 的发送概率 |
| $l_s$ | 外部到达率向量 $\mathbf{l}=[l_s]$：源模块 $s$ 的注入率（packets/cycle） |
| $\lambda_{sd}=l_s\,t_{sd}$ | $s$→$d$ 的流量强度（= 连续化的 $D_{sd}$） |
| $\Gamma=(\gamma_{sd})$ | 连通矩阵（$(M{+}Q)\times(M{+}Q)$）：$\gamma_{sd}>0$ 若有向连接 $s\to d$，其值为该连接（链路）的 ID |
| $r_{sd,i}$ | 路由矩阵 $\mathbf{R}=(r_{sd,i})$（$M\times M\times E$）：包从 $s$ 到 $d$ 占用链路 $i$ 的概率，$\sum_i r_{sd,i}=1$ |
| $\lambda_i$ | 链路 $i$（= 路由器输入队列 $i$）的局部到达率（packets/cycle） |
| $f_{i,j}$ | 转发概率：到达输入 $i$ 的包被转发到输出 $j$ 的概率，$\sum_j f_{i,j}=1$ |
| $\mathbf{F}=(f_{i,j})$ | 转发概率矩阵（$P\times P$） |
| $c_{i,j}$ | 输入 $i,j$ 的成对争用概率；$\mathbf{C}=(c_{i,j})$ 争用概率矩阵 |
| $\bar x$ | 基础（无争用）平均路由器服务时间（cycles），$\bar x=1/\mu$ |
| $\mathbf{x}=(x_1,\dots,x_P)$ | 路由器状态向量：$x_i\in\mathbb{Z}_{\ge0}$ 为输入队列 $i$ 的 fill level |
| $\mathbf{y}=\operatorname{sgn}(\mathbf{x})$ | 宏状态向量：$y_i=\mathbf{1}\{x_i>0\}$ |
| $x_i(\mathbf{y})$ | 宏状态 $\mathbf{y}$ 下输入 $i$ 的平均（含争用）服务时间 |
| $\mu_i(\mathbf{y})=1/x_i(\mathbf{y})$ | 宏状态 $\mathbf{y}$ 下输入 $i$ 的服务率 |
| $\rho_i(\mathbf{y})=\lambda_i/\mu_i(\mathbf{y})$ | 宏状态 $\mathbf{y}$ 下输入 $i$ 的利用率 |
| $N_1(\mathbf{y})=\{i:y_i=1\}$ | 非空输入队列下标集 |
| $\sigma(\mathbf{y})$ | 宏状态 $\mathbf{y}$ 的稳态概率 |
| $\tilde\pi(\mathbf{x})$ | 路由器稳态分布（近似） |
| $\bar W_i$ | 输入队列 $i$ 的平均排队延迟 |
| $e_i$ | 第 $i$ 维单位向量 |

## 1. 模型定位

分层结构（图 1）：**网络层**把 $(\mathbf{T},\mathbf{l},\Gamma,\mathbf{R})$ 折成每路由器的局部参数（$\lambda_i$、$f_{i,j}$）；**路由器层**解多维 Markov 链得稳态分布 $\tilde\pi(\mathbf{x})$；再回**网络层**聚合（路径延迟 = 各跳排队延迟 + 固定传播延迟之和）。输出是**分布**而非均值，故任意 KPI 均可导出。

## 2. 模型假设（显式）

- **A1 拓扑**：路由器任意拓扑；每路由器可连任意多个 core。
- **A2 交换**：wormhole（best-effort 的常见选择）。
- **A3 路由**：不限制（外生给定路由矩阵 $\mathbf{R}$）。
- **A4 仲裁**：FCFS（round-robin 等其他方案留作 future work）。
- **A5 缓冲**：**无限** buffer（输入缓冲路由器，输出端口无缓冲）。
- **A6 到达**：外部 PE 到达为 Poisson（指数到达间隔）。
- **A7 服务**：服务时间含仲裁 + 转发延迟，指数分布；所有路由器基础服务率 $\mu=1/\bar x$ 相同。
- **A8 时钟**：全局单时钟。

## 3. 核心方程

### 3.1 网络层：局部到达率与转发概率（式 (1)–(6)）

链路 $i$ 的到达率 = 所有经过它的流之和（正文逐字）：

$$
\lambda_i=\sum_{s=1}^{M}\sum_{d=1}^{M} l_s\,t_{sd}\,r_{sd,i},\qquad 1\le i\le E
\tag{1}
$$

正文注明式 (1) 可用 Frobenius 内积重写为矩阵方程（式 (2)，**位图，据正文交叉确认**，具体矩阵结构见原文）。

转发概率 $f_{i,j}$ 的语义定义（正文明确）：到达输入 $i$ 的包被转发到输出 $j$ 的比例；其求和/矩阵形式为式 (3)–(5)（**位图，据正文交叉确认**）。单路由器 $r$ 的转发概率集合（正文逐字）：

$$
F_r:=\big\{f_{i,j}\ \big|\ \exists s,d;\ 1\le s,d\le M{+}Q;\ \gamma_{s,r}=i\ \wedge\ \gamma_{r,d}=j\big\}
\tag{6}
$$

### 3.2 路由器层：争用折入服务时间（式 (7)–(10)）

核心思想（图 2）：把「FCFS 仲裁下与其它输入队列争用输出端口」的阻塞时间**折入服务时间**，得到逐端口服务率 $\mu_i(\mathbf{y})$，从而把路由器简化成「单输出 server + 多输入队列」的等价系统。

两输入 $i,j$ 的成对争用概率（正文逐字）：

$$
c_{i,j}=\sum_{k=1}^{P} f_{i,k}\,f_{j,k},\qquad i\ne j,\ 1\le i,j\le P
\tag{7}
$$

矩阵形式（$\mathbf{C}$ 主对角线置 1 以简化后续）：

$$
\mathbf{C}=\mathbf{F}\,\mathbf{F}^{T}
\tag{8}
$$

宏状态 $\mathbf{y}$ 下的平均服务时间（第一项 = 基础服务，第二项 = 争用延迟，$y_j=\mathbf{1}\{x_j>0\}$）：

$$
x_i(\mathbf{y}):=\bar x+\bar x\sum_{j=1,\,j\ne i}^{P} c_{i,j}\,y_j,\qquad 1\le i\le P
\tag{9}
$$

利用 $c_{ii}=1$ 可把式 (9) 凝成矩阵紧凑式（正文逐字，$\mathbf{C}_i$ 为 $\mathbf{C}$ 的第 $i$ 行）：

$$
\mu_i(\mathbf{y}):=\Big[\bar x\,\mathbf{C}_i^{T}\,\mathbf{y}\Big]^{-1}=\frac{1}{x_i(\mathbf{y})},\qquad 1\le i\le P
\tag{10}
$$

**推导依据（不跳步）**：$x_i(\mathbf{y})=\bar x\big(1+\sum_{j\ne i}c_{ij}y_j\big)=\bar x\sum_{j}c_{ij}y_j=\bar x\,\mathbf{C}_i^T\mathbf{y}$（因 $c_{ii}=1$、$y_i=1$ 当 $x_i>0$）。$\mu_i(\mathbf{y})=1/x_i(\mathbf{y})$。

### 3.3 稳态分布：变量聚合近似（式 (11)–(13)，核心贡献）

多维 Markov 链的状态转移率：$\mathbf{x}\to\mathbf{x}+e_i$ 强度 $\lambda_i$，$\mathbf{x}\to\mathbf{x}-e_i$ 强度 $\mu_i(\mathbf{y})$。但该链**不可逆**（边界区不满足 Kolmogorov 判据，正文给出反例 $(0,0)\to(1,0)\to(1,1)\to(0,1)\to(0,0)$ 与回路的转移率乘积不等），故不能靠局部平衡解。

**变量聚合**：按宏状态 $\mathbf{y}=\operatorname{sgn}(\mathbf{x})$ 把状态聚成 $S(\mathbf{y})=\{\mathbf{x}\in\mathbb{N}_0^P:\operatorname{sgn}(\mathbf{x})=\mathbf{y}\}$。同一宏状态内 $\mu_i(\mathbf{y})$ 齐次（争用只取决于「非空/空」，与 fill level 无关），故每个宏状态内是**可逆子链**，得乘积形式稳态（正文逐字）：

$$
\tilde\pi(\mathbf{x})=\begin{cases}
\displaystyle\prod_{i\in N_1(\mathbf{y})}\big(1-\rho_i(\mathbf{y})\big)\,\rho_i(\mathbf{y})^{x_i-1}\,\sigma(\mathbf{y}), & \mathbf{y}\ne 0\\[6pt]
\sigma(0), & \mathbf{y}=0
\end{cases}
\tag{11}
$$

$$
\rho_i(\mathbf{y})=\frac{\lambda_i}{\mu_i(\mathbf{y})}
$$

宏状态级转移率（正文逐字，来自 [15]）：

$$
p(\mathbf{y},\mathbf{y}')=\begin{cases}
\lambda_i, & \mathbf{y}'=\mathbf{y}+e_i\\[4pt]
\mu_i(\mathbf{y})-\lambda_i, & \mathbf{y}'=\mathbf{y}-e_i\\[4pt]
0, & \text{else}
\end{cases}
\tag{12}
$$

据此构转移率矩阵 $\mathbf{P}=(p_{ij})$，$p_{ii}:=-\sum_{j}p_{ij}$，解有限链得宏状态概率：

$$
\sigma\mathbf{P}=0,\qquad \sum_{\mathbf{y}}\sigma(\mathbf{y})=1
$$

**注意**：式 (11) 只是近似——它忽略了宏状态间的转移，仅通过 $\sigma(\mathbf{y})$ 条件化。

### 3.4 KPI 与饱和点修正（Little 定律 + 式 (13)）

平均队列长度与平均排队延迟（Little 定律）：

$$
\mathbb{E}[x_i]\approx\sum_{\mathbf{x}}\tilde\pi(\mathbf{x})\,x_i=\sum_{\mathbf{y}}\frac{\rho_i(\mathbf{y})}{1-\rho_i(\mathbf{y})}\,\sigma(\mathbf{y}),\qquad
\bar W_i=\frac{\mathbb{E}[x_i]}{\lambda_i}
$$

**问题**：直接聚合解的稳定性由「最坏（争用最强）宏状态」决定，导致饱和点被显著低估（正文实测 0.66 vs 仿真 0.8 pkt/cycle）。**修正**：对每输入取跨宏状态的平均服务时间 $\bar x_i$，再套单队列式（正文逐字）：

$$
\bar x_i=\sum_{\mathbf{y}\in\{0,1\}^P}x_i(\mathbf{y})\,\sigma(\mathbf{y})\,y_i
\tag{13}
$$

$$
\bar W_i=\frac{\bar x_i}{1-\lambda_i\,\bar x_i}
$$

其中因子 $y_i$ 把期望约束在「队列 $i$ 非空」的宏状态上。

## 4. 模型输出与精度

- 路由器稳态分布 $\tilde\pi$ → 任意 KPI：平均排队延迟 $\bar W_i$、buffer 占用分布、阻塞概率。
- 4×1 chain 争用场景与 4×4 mesh（多媒体应用流量）：平均误差 <3%（参考 mean value 模型 9%）；修正后饱和点亦准确（4×4 mesh 仍轻微低估约 2.5%）。
- 路径延迟 = 各跳 $\bar W_i$ + 固定传播延迟之和。

## 5. 无阻塞与放宽

**不答无阻塞**。稳态/平均模型；饱和点由稳定性判据近似给出（修正后与仿真接近，但仍是估计值，非「无阻塞带宽」保证）。它的分布信息可给出「阻塞概率」，但这是**给定 $\mathbf{D}$ 下的概率**，不是对所有 admissible $\mathbf{D}$ 的判定。明确不覆盖：round-robin 仲裁、有限 buffer、一般服务分布、多时钟域（均列在 future work）。

## 6. 功耗地位

**完全不建模**。输出「buffer 占用分布」可间接服务于 buffer 尺寸（面积/功耗）决策，但论文本身无功耗项。

## 7. 与我们的对照

| 维度 | 我们（00_ours） | Fischer 2012 |
|------|----------------|-------------|
| 输出 | 无阻塞 $B^*$ + $\mathbf{L}$ | 路由器稳态分布 $\tilde\pi$ → 任意 KPI |
| 信息量 | 一阶（最坏负载） | 分布（均值/占用/阻塞概率） |
| 需求结构体 | 排列 $\mathbf{P}$ | $\mathbf{T}$ + $\mathbf{l}$（合成 $\lambda_{sd}=l_st_{sd}$，即 $\mathbf{D}$） |
| 仲裁/交换 | 最优自适应路由 | FCFS + wormhole |
| 功耗 | 线性 + 静态 | 无 |

**可借鉴点**：$\mathbf{C}=\mathbf{F}\mathbf{F}^T$ 争用概率 + 变量聚合，是「把路由器内部争用抽象成单服务率」的干净办法；若要把我们的 $\mathbf{L}$ 映射到延迟，这个 router-level 抽象可作为中间层（负载 → 争用 → 服务率 → 延迟）。

**缺口**：不答无阻塞、不碰功耗、无 $\mathbf{L}$ 包络概念。
