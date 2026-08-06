# 晶圆级交换机统一 DSE 框架：完整数理模型

## 0. 符号表

| 符号 | 含义 |
|------|------|
| $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ | 物理图：裸片为节点，链路为边 |
| $N$ | 裸片/终端数量 |
| $\delta(v)$ | 裸片 $v$ 上 incident 链路的集合 |
| $\mathbf{L} = (L_e)_{e \in \mathcal{E}}$ | 每条链路的归一化负载（$L_e=1$ 表示流量 $=B$） |
| $B$ | 端口带宽（**优化变量**） |
| $\boldsymbol{\ell} = (\ell_e)_{e \in \mathcal{E}}$ | 每条链路的物理 lane 数：$\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ |
| $\mathbf{S}_{\text{bw}}$ | 每 lane 带宽对角阵（互联标准决定） |
| $\mathbf{S}_{\text{dyn}}$ | 每 lane 动态功耗对角阵（互联标准决定） |
| $\mathbf{S}_{\text{in}}$ | 单 bump 供电能力对角阵 $\mathbf{S}_{\text{in}} = \operatorname{diag}(V_{\text{dd}} \cdot I_{\text{bump}})$ |
| $\mathbf{D}$ | 双随机流量矩阵 $D_{ij} \in [0,1]$ |
| $\mathcal{D}$ | 双随机矩阵多面体（Birkhoff 1946） |
| $\Pi(i,j)$ | $(i,j)$ 对的候选路径集合（Valiant 路由） |
| $f_{ij}^k$ | $(i,j)$ 对第 $k$ 条路径上的分流变量 |
| $N_v^{\text{total}}$ | 裸片 $v$ 的总 $\mu$bump 数 $= \eta A_v / p^2$ |
| $N_v^{\text{sig}}$ | 裸片 $v$ 的信号 bump 预算 $= N_v^{\text{total}} - N_v^{\text{power}}$ |
| $\mathbf{M}$ | 裸片-链路 incidence 矩阵 $M_{v,e}=1$ 若 $e \in \delta(v)$ |
| $\mathbf{P}_0$ | 静态功耗向量（与 $\boldsymbol{\ell}$ 无关） |
| $\mathbf{G}$ | 热导矩阵（M-矩阵，$\mathbf{G}^{-1} \ge 0$，Berman & Plemmons 1994） |
| $\mathbf{W}$ | 相邻裸片对的差分化矩阵：$W_{(i,j),i}=+1$, $W_{(i,j),j}=-1$ |
| $\mathbf{T}$ | 裸片温度向量 |
| $T_{\max}$ | 裸片温度上限 |
| $\Delta T_{\max}$ | 相邻裸片允许的最大温差（翘曲约束） |
| $q_{\max}$ | 冷却方案的散热能力 (W/mm$^2$) |

---

## 1. 性能约束

### 1.1 流量模型

$N$ 端口交换机，每端口以速率 $B$ 收发。归一化后每个端口发出 1 单位流量（$=B$ Gbps）。$\mathbf{D} \in \mathbb{R}^{N \times N}$ 为双随机流量矩阵：

$$\mathbf{D} \in \mathcal{D} = \{\mathbf{D} \ge 0 : \sum_j D_{ij} = 1,\; \sum_i D_{ij} = 1,\; D_{ii} = 0\}$$

Birkhoff--von Neumann 定理：$\mathcal{D}$ 的顶点恰好为排列矩阵。将离散排列搜索松弛为连续 LP 不损失精度。

Valiant 自适应路由允许每个 $(i,j)$ 对在 $|\Pi(i,j)|$ 条候选路径间拆分流量。分流变量 $f_{ij}^k \ge 0$，满足 $\sum_k f_{ij}^k = D_{ij}$。链路负载由分流之和定义：

$$L_e = \sum_{(i,j,k): e \in \text{path}} f_{ij}^k$$

归一化负载向量 $\mathbf{L} = (L_e)_{e \in \mathcal{E}}$ 包含了路由决策的全部信息。

### 1.2 L0：二分带宽

$$\sum_{e \in C} L_e \ge \frac{N}{4} \quad \forall\;\text{割}\; C$$

O(1)，不需要路由信息。适合快速淘汰，但过于松弛。

### 1.3 L1：Valiant 无阻塞条件

$$\max_{e \in \mathcal{E}} L_e \le 1$$

对 Dragonfly 拓扑（$g$ 个 group），$|\Pi(i,j)| = g-2$，总变量数 $\sim O(N^2 \cdot g)$。

---

## 2. 功耗模型

功耗模型是几何约束和热约束的共同基础。定义功耗向量 $\mathbf{P} = (P_v)_{v \in \mathcal{V}}$：

$$\boxed{\mathbf{P}(\boldsymbol{\ell}) = \mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}}$$

其中 $\mathbf{P}_0$ 为静态功耗向量，$\mathbf{M} \in \{0,1\}^{|\mathcal{V}| \times |\mathcal{E}|}$ 为裸片-链路 incidence 矩阵，$\mathbf{S}_{\text{dyn}}$ 为每条链路每 lane 动态功耗的对角阵，由互联标准决定（UCIe Advanced: 0.25--0.6 pJ/bit；SerDes VSR/MR/LR: 15--20 pJ/bit）。

$\mathbf{P}$ 向下游传递至两个约束族：几何约束中 $\mathbf{P}$ 决定电源 bump 需求 $\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}} \cdot \mathbf{P}$，挤占信号 bump 预算；热约束中 $\mathbf{P}$ 作为热源项进入热网络 $\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}$。

---

## 3. 几何约束

### 3.1 物理问题

每条链路需要 $\ell_e$ 条物理 lane，每条 lane 通过一个 $\mu$bump 从裸片引出至 interposer。裸片的 $\mu$bump 总数受面积和 pitch 限制，信号 bump 与电源 bump 竞争同一物理面积。

### 3.2 核心约束

裸片的总 bump 预算由面积和 pitch 决定：$\mathbf{N}^{\text{total}} = \eta \mathbf{A} / p^2$。

总 bump 在信号和电源之间分配。信号 bump 需求由 lane 数直接给出：

$$\mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell}$$

电源 bump 需求由功耗模型（§2）给出：

$$\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}} \cdot \mathbf{P} = \mathbf{S}_{\text{in}} \cdot (\mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell})$$

核心约束为两者之和不超过总预算：

$$\boxed{\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}}$$

$\boldsymbol{\ell}$ 同时出现在 $\mathbf{N}^{\text{sig}}$（直接）和 $\mathbf{N}^{\text{pwr}}$（通过 $\mathbf{P}$）中，形成闭环。取 $\mathbf{P}$ 的 TDP 使 $\mathbf{N}^{\text{pwr}}$ 固定为常数，约束退化为 $\boldsymbol{\ell}$ 上的严格线性不等式。

### 3.3 L0 与 L1

| | 约束 | 代价 |
|---|---|---|
| L0 | $\sum_e \ell_e \le \sum_v N_v^{\text{total}}$ | O(1)，忽略 per-die 分配 |
| L1 | $\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}$ | O($|\mathcal{V}|$) |

### 3.4 L2：布局感知布线容量

裸片布局确定后，grid 边 $g$ 上的走线需求约束：

$$\sum_{e} a_{g,e} \cdot \ell_e \le C_{\text{total}} \quad \forall g$$

矩阵形式 $\mathbf{A} \cdot \boldsymbol{\ell} \le \mathbf{c}$，与 L1 同构。

---

## 4. 热约束

### 4.1 物理问题

功耗转化为热。冷却方案有散热上限，且功耗的空间不均匀性导致温度梯度和翘曲风险。

### 4.2 L0：全局功率密度

$$\mathbf{1}^T \mathbf{P}(\boldsymbol{\ell}) \le A_{\text{total}} \cdot q_{\max}$$

一条不等式，O(1)。忽略热的空间分布。

### 4.3 L1：稳态热网络与温差约束

稳态热传导方程 $\nabla \cdot (k \nabla T) + \dot{q} = 0$ 是 Fourier 定律的直接结果——线性 PDE，温度对热源的依赖天然是线性的。离散化后：

$$\mathbf{G} \cdot \mathbf{T} = \mathbf{P}(\boldsymbol{\ell}) + \mathbf{b}$$

其中 $\mathbf{P}(\boldsymbol{\ell}) = \mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}$（§2），$\mathbf{b}$ 为环境温度项。温度约束和翘曲约束分别为：

$$\mathbf{T} \le T_{\max} \cdot \mathbf{1}$$

$$\mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max} \cdot \mathbf{1}$$

$\mathbf{G}$ 为 M-矩阵，$\mathbf{G}^{-1} \ge 0$（所有元素非负）。物理含义：任何位置增加功耗，任何位置温度只升不降（正线性单调性）。因此取 TDP + 稳态为最坏情况——若通过，所有非峰值和非稳态场景自动通过。精度可升级：无论离散化精度如何，约束形式始终为 $\boldsymbol{\ell}$ 上的线性不等式。

---

## 5. 统一线性规划

### 5.1 约束族与精度级别

三族约束各自提供 L0（粗筛）和 L1（精判）两级精度：

| | **L0（粗筛）** | **L1（精判）** |
|---|---|---|
| **性能** | $\sum_{e \in C} L_e \ge N/4$ | $L_e \le 1$，$\mathbf{D} \in \mathcal{D}$，Valiant 分流 |
| 计算代价 | O(1) | O(N²·g) |
| **几何** | $\sum_e \ell_e \le \sum_v N_v^{\text{total}}$ | $\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}$ |
| 计算代价 | O(1) | O($|\mathcal{V}|$) |
| **功耗** | $\mathbf{1}^T \mathbf{P} \le A \cdot q_{\max}$ | $\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}$，$\mathbf{T} \le T_{\max}$，$\mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max}$ |
| 计算代价 | O(1)，一条不等式 | $|\mathcal{V}| + |\mathcal{E}_{\text{adj}}|$ 条不等式 |

L0 用于大规模初筛，L1 用于关键设计点的精确判断。精度升级仅替换系数矩阵。

### 5.2 完整问题形式（L1 精度，max $B$）

$$\boxed{
\begin{aligned}
\max_{B,\; \mathbf{D},\; \mathbf{f},\; \mathbf{L},\; \boldsymbol{\ell},\; \mathbf{P},\; \mathbf{N}^{\text{sig}},\; \mathbf{T}} \quad & B \\[8pt]
\text{s.t.} \quad
& \mathbf{D} \in \mathcal{D}, \quad
\sum_k f_{ij}^k = D_{ij}, \quad
L_e = \sum_{(i,j,k):\, e \in \text{path}} f_{ij}^k
&& \text{（流量模型：BvN + Valiant 分流）} \\[4pt]
& \max_{e} {L_e} \le 1
&& \text{（性能：广义无阻塞）} \\[8pt]
& \boldsymbol{\ell} = B \, \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}
&& \text{（归一化负载 → 物理 lane 数）} \\[8pt]
& \mathbf{P} = \mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}
&& \text{（功耗模型：静态 + 拓扑 × 标准 × lane 数）} \\[4pt]
& \mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}} \cdot \mathbf{P}
&& \text{（电源 bump 需求）} \\[4pt]
& \mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell}
&& \text{（信号 bump 需求）} \\[4pt]
& \mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}
&& \text{（几何：bump 核心约束）} \\[8pt]
& \mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}
&& \text{（热网络：稳态热传导）} \\[4pt]
& \mathbf{T} \le T_{\max} \cdot \mathbf{1}
&& \text{（温度上限约束）} \\[4pt]
& \mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max} \cdot \mathbf{1}
&& \text{（翘曲约束：相邻温差 $\le \Delta T_{\max}$）} \\[8pt]
& \mathbf{D} \ge 0,\; \mathbf{f} \ge 0,\; \mathbf{L} \ge 0,\; \boldsymbol{\ell} \ge 0,\; B \ge 0
\end{aligned}
}$$

其中 $\mathbf{P}_0$、$\mathbf{M}$、$\mathbf{S}_{\text{bw}}$、$\mathbf{S}_{\text{dyn}}$、$\mathbf{S}_{\text{in}}$、$\mathbf{G}$、$\mathbf{W}$、$\mathbf{N}^{\text{total}}$、$T_{\max}$、$\Delta T_{\max}$、$\mathbf{b}$ 均由外层技术选型决定，为常数。

以上为 L1 精度，包含全部三族约束的完整形式。L0 精度将性能替换为 $\sum_{e \in C} L_e \ge N/4$、几何替换为 $\sum_e \ell_e \le \sum_v N_v^{\text{total}}$、功耗替换为 $\mathbf{1}^T \mathbf{P} \le A \cdot q_{\max}$，详见 §5.1。

$\boldsymbol{\ell} = B \, \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ 含 $B \cdot \mathbf{L}$ 双线性项。令 $\beta = 1/B$ 可将所有约束转化为 $(\beta, \mathbf{L}, \boldsymbol{\ell}, \mathbf{P}, \mathbf{N}^{\text{sig}}, \mathbf{T})$ 上的标准线性不等式（求解细节见 §7）。

### 5.3 解的判据

$B^*$ 是给定设计点在全部约束下可支撑的最大端口带宽。绑定约束直接揭示瓶颈：

| 绑定约束 | 诊断 | 改进方向 |
|---------|------|---------|
| $L_e = 1$，物理约束松弛 | 拓扑能力不足 | 优化路由、增大 $a$ 或 $p$ |
| bump 约束绑定 | 信号 bump 预算不足 | 缩 pitch、增大裸片面积 |
| 温度约束绑定 | 冷却能力不足 | 升级冷却方案 |
| 翘曲约束绑定 | 温度分布不均 | 调整裸片布局或功耗分布 |

优化过程的物理含义：推高 $B$ 同时放大 $\boldsymbol{\ell}$（$\ell_e = L_e B / R_e$），收紧所有物理约束。若物理资源充裕，$B$ 可一直增大到 $L_e = 1$（拓扑极限）；若物理资源紧缺，$B$ 先被 bump 或散热约束卡住，此时 $L_e < 1$——即便最优分流也不可行。

---

## 6. 两层 DSE 架构

### 6.1 外层：离散枚举与智能选型

外层决定离散架构选择，固定内层 LP 的所有系数矩阵：

| 外层参数 | 决定的内层系数 |
|---------|--------------|
| 拓扑 $(a,p,h)$ + 路由策略 | $\mathcal{E}$, $\Pi(i,j)$, 路径→链路 incidence |
| 互联标准 | $\mathbf{S}_{\text{bw}}$, $\mathbf{S}_{\text{dyn}}$, $\mathbf{S}_{\text{in}}$ |
| 裸片面积 $A_v$, bump pitch $p$ | $N_v^{\text{total}}$, $N_v^{\text{sig}}$ |
| 冷却方案 | $q_{\max}$ |
| 裸片布局（若用 L2） | $\mathbf{A}(p)$ |

外层策略可以是暴力枚举、启发式剪枝、或基于 agent 的智能选型。

### 6.2 内层：最大化端口带宽

内层求解 §5.2 中的统一问题，变量为 $\mathbf{L}$、$\boldsymbol{\ell}$ 和 $B$。返回最大可支撑带宽 $B^*$。若 $B^* < B_{\text{target}}$，对偶变量给出绑定约束的位置和边际改进空间。

### 6.3 两层解耦

两层通过物理参数接口解耦：外层参数确定后，内层所有系数矩阵均为常数，全部耦合发生在 $\boldsymbol{\ell}$ 上且为线性。

---

## 7. 求解与灵敏度

### 7.1 线性化

§5.2 的 max $B$ 形式含 $B \cdot \mathbf{L}$ 双线性项。令 $\beta = 1/B$，目标变为 $\min \beta$，lane 定义变为 $\boldsymbol{\ell} = (1/\beta) \, \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$。所有约束移项后均为 $(\beta, \mathbf{L}, \boldsymbol{\ell}, \mathbf{P}, \mathbf{N}^{\text{sig}}, \mathbf{T})$ 上的线性不等式，等价于标准 LP。求解器实现细节略。

### 7.2 对偶变量

LP 对偶变量给出 $\beta^*$ 对各约束 RHS 的灵敏度，换算为 $B^*$ 灵敏度：$\partial B^* / \partial b_i = -(B^*)^2 \cdot \partial \beta^* / \partial b_i$。

| 约束 | 物理参数 | 灵敏度含义 |
|------|---------|---------|
| $\max_e L_e \le 1$ | 链路容量 | 扩容对 $B^*$ 的边际增益 |
| $\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}$ | $N_v^{\text{total}}$ | 多一个 bump 预算对 $B^*$ 的边际增益 |
| 温度约束 | $T_{\max}$ | 放宽温度上限对 $B^*$ 的边际增益 |
| 翘曲约束 | $\Delta T_{\max}$ | 放宽温差上限对 $B^*$ 的边际增益 |

影子价格比值给出设计优先级：

$$\frac{\partial B^* / \partial N_v^{\text{total}}}{\partial B^* / \partial (A q_{\max})} = \frac{\text{增加一个 bump 的边际收益}}{\text{增加 1W 散热的边际收益}}$$

若比值 > 1，优先投资 bump 改进；否则优先升级冷却。

### 7.3 约束松弛扫描

扫描约束 RHS 的连续变化 $\alpha \cdot b_i$，观察 $B^*(\alpha)$ 响应。未绑定时 $\partial B^* / \partial b_i = 0$；绑定时对偶值给出精确导数。

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
