# 晶圆级交换机统一 DSE 框架：完整数理模型

## 0. 符号表

| 符号 | 含义 | 来源 |
|------|------|------|
| $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ | 物理图：裸片为节点，链路为边 | 拓扑定义 |
| $N$ | 裸片/终端数量 | |
| $\delta(v)$ | 裸片 $v$ 上 incident 链路的集合 | 图论 |
| $\mathbf{L} = (L_e)_{e \in \mathcal{E}}$ | 每条链路的归一化负载（中间变量，由流量分配决定） | BvN 框架 |
| $B$ | 端口带宽（**优化变量**） | — |
| $R_e$ | 链路 $e$ 的每 lane 速率 | UCIe/OIF-CEI 标准 |
| $c_e$ | 链路 $e$ 的每单位负载功耗系数 $c_e = P_{\text{lane}} \cdot B/R_e$ （注：$B$ 进入 $c_e$ 后，约束为 $L_e$ 的线性函数） | UCIe 标准 |
| $\mathbf{D}$ | 双随机流量矩阵 $D_{ij} \in [0,1]$ | BvN 框架 |
| $\mathcal{D}$ | 双随机矩阵多面体 | Birkhoff 1946 |
| $\Pi(i,j)$ | $(i,j)$ 对的候选路径集合 | Valiant 路由 |
| $f_{ij}^k$ | $(i,j)$ 对第 $k$ 条路径上的分流变量 | LP 变量 |
| $N_v^{\text{total}}$ | 裸片 $v$ 的总 $\mu$bump 数 $= \eta A_v / p^2$ | 几何约束 |
| $N_v^{\text{sig}}$ | 裸片 $v$ 的信号 bump 预算 $= N_v^{\text{total}} - N_v^{\text{power}}$ | 几何约束 |
| $P_v$ | 裸片 $v$ 的总功耗 $= P_{0v} + \sum_{e \in \delta(v)} c_e L_e$ | 功耗约束 |
| $\mathbf{G}$ | 热导矩阵（M-矩阵，$\mathbf{G}^{-1} \ge 0$） | Berman & Plemmons 1994 |
| $T_{\max}$ | 裸片温度上限 | 工艺约束 |
| $\Delta T_{\max}$ | 相邻裸片允许的最大温差（翘曲约束） | 机械可靠性约束 |
| $q_{\max}$ | 冷却方案的散热能力 (W/mm$^2$) | 工程参数 |

---

## 1. 性能约束

### 1.1 物理问题

$N$ 端口交换机。最坏情况下，$N$ 个输入端口各自向 $N$ 个输出端口发送数据（排列流量模式），共 $(N-1)!$ 种可能排列。无阻塞意味着：在任何排列下，存在一种路由方案使内部所有链路的负载不超过链路物理速率。

### 1.2 流量模型

归一化：每个端口发出 1 单位流量。$\mathbf{D} \in \mathbb{R}^{N \times N}$ 为流量矩阵，$D_{ij}$ 为从 $i$ 到 $j$ 的归一化流量。$\mathbf{D}$ 为双随机矩阵：

$$\sum_j D_{ij} = 1,\quad \sum_i D_{ij} = 1,\quad D_{ii} = 0$$

Birkhoff--von Neumann 定理 [Birkhoff 1946]：双随机矩阵多面体 $\mathcal{D}$ 的顶点恰好为排列矩阵。将离散排列搜索松弛为连续 LP 不损失精度——线性函数在多面体上的最大值必在顶点（排列）上取到。

### 1.3 L0：二分带宽（最粗糙的下界）

将网络切成两半的任意割 $C$ 给出一条必要条件：

$$\sum_{e \in C} L_e \ge \frac{N}{4} \quad \forall\;\text{割}\; C$$

不需要路由信息，O(1) 条约束。适合快速淘汰明显不可行的候选拓扑，但忽略路由策略，过于松弛。

### 1.4 L1：Valiant 分流与无阻塞条件

自适应路由（Valiant）允许每个 $(i,j)$ 对在 $|\Pi(i,j)|$ 条候选路径间拆分流量。分流变量 $f_{ij}^k \ge 0$，满足 $\sum_k f_{ij}^k = D_{ij}$。

链路 $e$ 的总负载为所有经过 $e$ 的分流量之和：

$$L_e = \sum_{(i,j,k)\;:\; e \in \text{path}(i,j,k)} f_{ij}^k$$

**无阻塞条件**：所有链路的归一化负载不超过 1，即 $L_e \le 1 \; \forall e \in \mathcal{E}$。这是关于 $\mathbf{L}$ 的一组线性不等式。

**L0 与 L1 的关系**：二分带宽是 L1 在"候选路径仅包含割上链路"这一退化情形下的特例。精度升级只增加约束的紧度，不改变线性形式。

**变量规模**：对于 Dragonfly 拓扑（$g$ 个 group），$|\Pi(i,j)| = g-2$（Valiant 排除源和目的 group），总变量数 $\sim O(N^2 \cdot g)$。

---

## 2. 几何约束

### 2.1 物理问题

每条链路需要物理 lane 和信号 $\mu$bump。后者受裸片面积和电源竞争的严格限制。

### 2.2 L0：全局 lane 预算

$$\sum_{e \in \mathcal{E}} L_e \cdot \frac{B}{R_e} \le N_{\text{total}}$$

一条不等式，O(1)。忽略 bump 的 per-die 分配约束，几乎不会绑定。

### 2.3 L1：裸片级 bump 竞争

裸片 $v$ 的总 bump 数：$N_v^{\text{total}} = \eta A_v / p^2$。

信号 bump 与电源 bump 竞争同一物理面积。电源 bump 需求：$N_v^{\text{power}} = P_v / (V_{\text{dd}} \cdot I_{\text{bump}})$。

信号 bump 预算为差值：

$$N_v^{\text{sig}} = \frac{\eta A_v}{p^2} - \frac{P_v}{V_{\text{dd}} I_{\text{bump}}}$$

裸片 $v$ 上所有 incident 链路的 lane 需求之和不超过信号 bump 预算：

$$\sum_{e \in \delta(v)} L_e \cdot \frac{B}{R_e} \le N_v^{\text{sig}} \quad \forall v \in \mathcal{V}$$

矩阵形式：$\mathbf{M} \cdot \mathbf{L} \le \mathbf{b}$，其中 $M_{v,e} = B/R_e$（若 $e \in \delta(v)$），$b_v = N_v^{\text{sig}}$。

**耦合效应**：$P_v = P_{0v} + \sum_{e \in \delta(v)} P_{\text{lane}} \cdot L_e \cdot B/R_e$——$\mathbf{L}$ 同时出现在不等式左边（lane 需求）和右边（通过 $P_v$ 影响 $N_v^{\text{sig}}$）。实现中取 $P_v$ 的 TDP 值使右手边固定为常数，保持严格线性。

### 2.4 L2：布局感知布线容量

裸片布局 $p: \mathcal{V} \to \{0,\ldots,N-1\}^2$ 确定后，grid 边 $g$ 上的走线需求约束：

$$\sum_{e} a_{g,e}(p) \cdot L_e \cdot \frac{B}{R_e} \le C_{\text{total}} \quad \forall g$$

其中 $C_{\text{total}} = L_{\max} \cdot C_0$（层数 × 每层容量）。矩阵形式：$\mathbf{A}(p) \cdot \text{diag}(B/R_e) \cdot \mathbf{L} \le \mathbf{c}$，与 L1 同构。

---

## 3. 功耗约束

### 3.1 物理问题

每条链路消耗物理层功耗，转化为热。冷却方案有散热上限，且功耗的空间不均匀性导致温度梯度和翘曲风险。

### 3.2 单链路功耗

每条链路 $e$ 的物理层功耗：$P_e = P_{\text{lane}}(R_e) \cdot L_e \cdot B / R_e = c_e \cdot L_e$，其中 $c_e = P_{\text{lane}} \cdot B / R_e$ 为常数。$P_{\text{lane}}(R_e)$ 由互联标准决定（UCIe Advanced: 0.25--0.6 pJ/bit；SerDes VSR/MR/LR: 15--20 pJ/bit）。裸片 $v$ 总功耗：

$$P_v = P_{0v} + \sum_{e \in \delta(v)} c_e \cdot L_e$$

其中 $P_{0v}$ 为与链路负载无关的静态功耗。

### 3.3 L0：全局功率密度

$$\sum_{e \in \mathcal{E}} c_e \cdot L_e \le A_{\text{total}} \cdot q_{\max}$$

一条不等式，O(1)。$q_{\max}$ 取决于冷却方案。忽略热的空间分布。

### 3.4 L1：稳态热网络与温差约束

稳态热传导方程 $\nabla \cdot (k \nabla T) + \dot{q} = 0$ 是 Fourier 定律的直接结果——线性 PDE，温度对热源的依赖天然是线性的。离散化为热网络后：

$$\mathbf{T} = \mathbf{G}^{-1} (\mathbf{P}_0 + \mathbf{C} \cdot \mathbf{L} + \mathbf{b}_{\text{thermal}})$$

其中 $\mathbf{C}$ 的每一行为 $\sum_{e \in \delta(v)} c_e \cdot L_e$。

温度约束 $\mathbf{T} \le T_{\max} \cdot \mathbf{1}$ 等价于：

$$\mathbf{C} \cdot \mathbf{L} \le \mathbf{G} \cdot (T_{\max} \cdot \mathbf{1}) - \mathbf{b}_{\text{thermal}} - \mathbf{P}_0$$

翘曲（温差）约束 $\Delta T_{ij} \le \Delta T_{\max}$ 中，$\Delta T_{ij} = (\mathbf{G}^{-1}_i - \mathbf{G}^{-1}_j) \cdot (\mathbf{P}_0 + \mathbf{C} \cdot \mathbf{L} + \mathbf{b})$，是 $\mathbf{L}$ 的线性函数。

$\mathbf{G}$ 为 M-矩阵 [Berman & Plemmons 1994]，$\mathbf{G}^{-1} \ge 0$（所有元素非负）。物理含义：任何位置增加功耗，任何位置温度只升不降（正线性单调性）。因此取 TDP + 稳态为最坏情况——若通过，所有非峰值和非稳态场景自动通过。

精度可升级：无论离散化精度如何，约束形式始终为 $\mathbf{C} \cdot \mathbf{L} \le \mathbf{d}$。

---

## 4. 统一线性规划

### 4.1 约束族与精度级别

三族约束各自提供 L0（粗筛）和 L1（精判）两级精度。
表~\ref{tab:l0-l1} 汇总了每级精度的数学形式、物理内容和计算代价。

| | **L0（粗筛）** | **L1（精判）** |
|---|---|---|
| **性能** | $\sum_{e \in C} L_e \ge N/4 \quad \forall C$ | $L_e \le 1 \quad \forall e$，$\mathbf{D} \in \mathcal{D}$，Valiant 分流 |
| 物理内容 | 割上链路总容量 ≥ 穿越割的流量 | 在最优分流下，所有链路负载 ≤ 链路速率 |
| 计算代价 | O(1)，不需要路由信息 | O(N²·g)，需构建路径-链路 incidence |
| 漏判风险 | 可能高估可行性（忽略路由策略） | 无（BvN 定理保证精度） |
| **几何** | $\sum_{e \in \mathcal{E}} L_e \cdot B/R_e \le N_{\text{total}}$ | $\sum_{e \in \delta(v)} L_e \cdot B/R_e \le N_v^{\text{sig}} \quad \forall v$ |
| 物理内容 | 整晶圆总 bump 数够不够 | 每裸片的信号 bump 预算（信号和电源零和竞争） |
| 计算代价 | O(1)，一条不等式 | O(|𝒱|)，每裸片一条不等式 |
| 漏判风险 | 可能高估可行性（裸片间不可借调） | 保守取 TDP 保证安全性 |
| **功耗** | $\sum_e P_{\text{lane}} \cdot L_e \cdot B/R_e \le A \cdot q_{\max}$ | $\mathbf{G} \cdot \mathbf{T} = \mathbf{P}_0 + \mathbf{C} \cdot \mathbf{L} + \mathbf{b}$，$\mathbf{T} \le T_{\max}$，$\mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max}$ |
| 物理内容 | 总功耗 ≤ 冷却能力 | 稳态热传导 + 每裸片温度上限 + 相邻裸片温差上限（翘曲） |
| 计算代价 | O(1)，一条不等式 | O(|𝒱|²)（$\mathbf{G}^{-1}$ 预计算一次），$|\mathcal{V}| + |\mathcal{E}_{\text{adj}}|$ 条不等式 |
| 漏判风险 | 可能高估可行性（忽略横向热传导） | 取 TDP + 稳态为最坏情况（M-矩阵保序性保证安全性） |

其中 $\mathbf{C}_{v,e} = P_{\text{lane}} \cdot B/R_e$（$e \in \delta(v)$），$\mathbf{G}$ 为热导 M-矩阵，$\mathbf{W}$ 为相邻裸片对的差分化矩阵。

### 4.2 完整问题形式（L1 精度，max $B$）

$$\boxed{
\begin{aligned}
\max_{B,\; \mathbf{D},\; \mathbf{f},\; \mathbf{L},\; \mathbf{T}} \quad & B \\[8pt]
\text{s.t.} \quad
% ---- 流量模型 ----
& \mathbf{D} \in \mathcal{D}, \quad
\sum_k f_{ij}^k = D_{ij}, \quad
L_e = \sum_{(i,j,k):\, e \in \text{path}} f_{ij}^k \\[8pt]
% ---- 性能: 无阻塞 ----
& \boxed{L_e \le 1 \qquad \forall e \in \mathcal{E}} \\[8pt]
% ---- 几何: bump预算 ----
& \boxed{\sum_{e \in \delta(v)} L_e \cdot \frac{B}{R_e} \;\le\; N_v^{\text{sig}} \qquad \forall v \in \mathcal{V}} \\[8pt]
% ---- 功耗: 热网络 ----
& \boxed{\mathbf{G} \cdot \mathbf{T} = \mathbf{P}_0 + \mathbf{C} \cdot \mathbf{L} + \mathbf{b}} \\[8pt]
% ---- 功耗: 温度与翘曲 ----
& \boxed{\mathbf{T} \le T_{\max} \cdot \mathbf{1}} \\[4pt]
& \boxed{|T_i - T_j| \le \Delta T_{\max} \qquad \forall\; \text{相邻裸片对}\;(i,j)} \\[8pt]
% ---- 非负 ----
& \mathbf{D} \ge 0,\; \mathbf{f} \ge 0,\; \mathbf{L} \ge 0,\; B \ge 0
\end{aligned}
}$$

其中 $\mathbf{C}_{v,e} = P_{\text{lane}} \cdot B / R_e$（$e \in \delta(v)$），$\mathbf{G}$ 为热导 M-矩阵。

**关于线性规划**：上述形式含 $L_e \cdot B$ 项（bump 约束中 $B$ 乘 $L_e$，热网络中 $\mathbf{C}$ 含 $B$），不是标准 LP。
令 $\beta = 1/B$，则 $\max B \iff \min \beta$，所有含 $B$ 的项移项后变为 $(\beta, \mathbf{L}, \mathbf{T})$ 上的线性不等式（$\beta$ 在 RHS，$\mathbf{L}$ 在 LHS，$\mathbf{G} \cdot \mathbf{T}$ 方程用 $\mathbf{G}^{-1}$ 形式消去 $\mathbf{T}$ 与 $\beta$ 的耦合），等价为一个标准 LP。
正文中以 $\max B$ 形式呈现以保持物理直观，$\beta$ 变换为求解细节。

以上为 L1 精度（完整模型）。L0 精度将热网络与翘曲约束替换为全局散热不等式 $\sum_e P_{\text{lane}} \cdot L_e \cdot B / R_e \le A \cdot q_{\max}$，热网络与翘曲约束省略。

### 4.3 解的判据

$B^*$ 是给定设计点在全部约束下可支撑的**最大端口带宽**。

观察 $B^*$ 与各约束的绑定状态，可直接判定瓶颈位置：

| 绑定约束 | 诊断 | 改进方向 |
|---------|------|---------|
| $L_e = 1$ 绑定，物理约束松弛 | 拓扑能力不足 | 优化路由、增大 $a$ 或 $p$ |
| bump 约束绑定 | 信号bump预算不足 | 缩 pitch、增大裸片面积 |
| 散热/温度约束绑定 | 冷却能力不足 | 升级冷却方案 |
| 翘曲约束绑定 | 温度分布不均 | 调整裸片布局或功耗分布 |
| 全部松弛，$\beta^* \to 0$ | 物理资源充裕，$B$ 无上限 | 增加端口数 $N$ 以利用盈余 |

优化过程的物理直觉：推高 $B$（减小 $\beta$）收紧所有物理约束的 RHS，反逼 $\mathbf{L}$ 下降。
若物理资源充裕，$\beta$ 可一直减小到 $L_e = 1$（拓扑极限）；
若物理资源紧缺，$\beta$ 先被 bump 或散热约束卡住，此时 $L_e < 1$——说明即便最优分流，物理上也不可行。

### 4.4 梯度配置

三族约束各自支持独立的精度级别，精度升级仅替换系数矩阵，不改变线性结构：

| 约束族 | 可选精度 | 计算代价 |
|--------|---------|---------|
| 性能 | k=0: 二分带宽 / k=1: Valiant 无阻塞 | O(1) / O(N²·g) |
| 几何 | m=0: 全局bump / m=1: per-die / m=2: +布线 | 约束行数递增 |
| 功耗 | n=0: 全局散热 / n=1: +热网络+翘曲 | 约束行数递增 |

从 $(0,0,0)$（3 条不等式，O(1)）到 $(1,1,1)$（完整 LP，秒级求解）连续可选。

---

## 5. 两层 DSE 架构

### 5.1 外层：离散枚举与智能选型

外层决定离散架构选择，固定内层 LP 的所有系数矩阵：

| 外层参数 | 决定的内层系数 |
|---------|--------------|
| 拓扑 $(a,p,h)$ + 路由策略 | $\mathcal{E}$, $\Pi(i,j)$, 路径→链路 incidence |
| 互联标准（UCIe/SerDes 等级） | $R_e$, $P_{\text{lane}}(R_e)$ |
| 裸片面积 $A_v$, bump pitch $p$ | $N_v^{\text{total}}$, $N_v^{\text{sig}}$ |
| 冷却方案 | $q_{\max}$ |
| 裸片布局（若使用几何 L2） | $\mathbf{A}(p)$ |

外层策略可以是暴力枚举、启发式剪枝、或基于 agent 的智能选型。

### 5.2 内层：最大化端口带宽

内层求解 §4.2 中的统一问题，变量为 $\mathbf{L}$ 和 $B$。
内层不关心外层如何选定参数——只回答：
该技术选型下，最大可支撑带宽 $B^*$ 是多少？
若 $B^* < B_{\text{target}}$，绑定约束在哪里？

### 5.3 两层解耦

两层通过物理参数接口解耦。解耦的关键：
**一旦外层固定了物理参数，内层所有耦合都发生在 $\mathbf{L}$ 上，且都是线性的。**

---

## 6. 灵敏度分析

### 6.1 对偶变量：物理约束的影子价格

求解时令 $\beta = 1/B$，对偶变量给出 $\beta^*$ 对各约束 RHS 的导数，换算为 $\partial B^* / \partial b_i = -(B^*)^2 \cdot \partial \beta^* / \partial b_i$。对架构师而言，直接关心的是 $B^*$ 对物理参数的灵敏度：

| 约束 | 物理参数 | 灵敏度含义 |
|------|---------|---------|
| $L_e \le 1$ | 链路容量 | 扩容链路 $e$ 对 $B^*$ 的边际增益 |
| $\sum L_e B/R_e \le N_v^{\text{sig}}$ | $N_v^{\text{sig}}$ | 多一个信号 bump 对 $B^*$ 的边际增益 |
| $\sum P_{\text{lane}} L_e B/R_e \le A q_{\max}$ | $A q_{\max}$ | 多 1W 散热预算对 $B^*$ 的边际增益 |
| 翘曲约束（L1） | $\Delta T_{\max}$ | 放宽温差上限对 $B^*$ 的边际增益 |

影子价格的比值直接给出设计优先级：

$$\frac{\partial B^* / \partial N_v^{\text{sig}}}{|\partial B^* / \partial (A q_{\max})|} = \frac{\text{增加一个bump的边际收益}}{\text{增加1W散热的边际收益}}$$

若比值 > 1，优先投资 bump 改进；否则优先升级冷却。

### 6.2 约束松弛扫描

扫描约束 RHS 的连续变化 $\alpha \cdot b_i$，观察 $B^*(\alpha)$ 响应：

$$B^*(\alpha) = \max \{ B : \text{LP}, \text{约束}_i\text{的RHS} = \alpha \cdot b_i \}$$

当约束未绑定时 $\partial B^* / \partial b_i = 0$（改进无益）；绑定时对偶值给出 $B^*$ 对 RHS 的精确导数。

---

## 参考文献

1. Birkhoff, G. "Tres observaciones sobre el algebra lineal." *Univ. Nac. Tucumán Rev. Ser. A*, 1946.
2. Valiant, L.G. "A Scheme for Fast Parallel Communication." *SIAM J. Computing*, 1982.
3. UCIe Consortium. "Universal Chiplet Interconnect Express (UCIe) Specification, Revision 2.0." 2024.
4. Optical Internetworking Forum. "OIF-CEI-05.1: Common Electrical I/O (CEI)." 2023.
5. Kim, J. et al. "Technology-Driven, Highly-Scalable Dragonfly Topology." *ISCA*, 2008.
6. Ngo, H.Q. et al. "Analyzing Nonblocking Switching Networks using Linear Programming (Duality)." *INFOCOM*, 2010.
7. Berman, A. & Plemmons, R.J. "Nonnegative Matrices in the Mathematical Sciences." *SIAM*, 1994.
8. Zhang, R. et al. "MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D Chiplet Systems." *ACM TACO*, 2025.
9. Li, X. et al. "An Electrical-Thermal Co-Simulation Model of Chiplet Heterogeneous Integration Systems." *IEEE TCPMT*, 2024.
10. Dally, W.J. & Towles, B. "Principles and Practices of Interconnection Networks." *Morgan Kaufmann*, 2004.
