# 00 我们的模型 —— Birkhoff 排列 + 群论归约 + LP 包络

> 基准模型，也是「严谨数学形式」的范本（与 01 同标准）。符号沿用 v4（`MATH_MODEL_COMPLETE_V4.md`），此处自成一体重新定义。

## 0. 符号表

| 符号 | 定义 |
|------|------|
| $\mathcal{G}=(\mathcal{V},\mathcal{E})$ | 逻辑拓扑图：$\mathcal{V}$ 端口节点集，$\mathcal{E}$ 有向链路集 |
| $n=\lvert\mathcal{V}\rvert$ | 端口（终端）数 |
| $e\in\mathcal{E}$ | 有向链路（端口对 $(u,v)$） |
| $B\in\mathbb{R}_{\ge0}$ | 端口带宽（决策变量，二分搜索定 $B^*$） |
| $\mathrm{Aut}(\mathcal{G})$ | $\mathcal{G}$ 的自同构群 |
| $\mathcal{R}$ | 排列代表元集合（$\mathrm{Aut}(\mathcal{G})$ 在 $S_n$ 上的共轭轨道代表） |
| $\mathbf{D}^{(r)}\in\{0,1\}^{n\times n}$ | 模式 $r$ 的排列需求矩阵：$D^{(r)}_{ij}=1$ 若 $i$ 发往 $j$ |
| $\mathbf{f}^{(r)}=(f^{k,(r)}_{ij})$ | 模式 $r$ 的分流变量：$f^{k,(r)}_{ij}\ge0$ 为 i→j 在路径 $k$ 上的流量 |
| $\mathbf{L}^{(r)}=(L^{(r)}_e)$ | 模式 $r$ 的链路负载向量 |
| $\mathbf{L}=(L_e)$ | 负载包络：$L_e=\max_r L^{(r)}_e$ |
| $\boldsymbol{\ell}=(\ell_e)$ | 物理 lane 数（链路 $e$ 配置的并行物理通道数） |
| $\mathbf{S}_{\text{bw}}$ | 每 lane 带宽对角阵：$\mathrm{diag}(S_{\text{bw},e})$，on-die 取 $\infty$ |
| $\mathbf{S}_{\text{dyn}}$ | 每 lane 动态功耗对角阵，on-die 取 0 |
| $\mathbf{M}$ | die–链路 incidence：$M_{v,e}=1$ 若链路 $e$ 的源或宿是 die $v$（on-die 两端同 die 只记一次） |
| $\mathbf{P}=(P_v)$ | die 功耗向量 |
| $P_0,\ \beta_P$ | die 静态功耗、每带宽功耗系数（$P_{peak}(B)=P_0+\beta_P B$） |
| $V_{dd},\ I_{bump}$ | 供电电压、单 bump 载流 |
| $p,\ \eta$ | bump pitch、阵列面积利用率 |
| $\mathbf{N}^{\text{sig}},\mathbf{N}^{\text{pwr}},\mathbf{N}^{\text{total}}$ | 信号 bump、电源 bump、总 bump 向量 |
| $\mathbf{G},\ \mathbf{b}$ | 热导矩阵（对角占优 M-矩阵）、环境温度贡献向量 |
| $\mathbf{T},\ T_{\max}$ | die 温度向量、结温上限 |

向量/矩阵按分量运算；$\mathbf{S}_{\text{in}}=\mathrm{diag}(V_{dd}I_{bump})$。

## 1. 模型定位

给定拓扑 $\mathcal{G}$，求**最大无阻塞端口带宽 $B^*$**：所有 admissible 流量都能被物理资源（lane / bump / 热）同时支撑的最大每端口带宽。

## 2. 模型假设（显式）

- **A1 拓扑对称**：$\mathcal{G}$ 是 vertex-transitive（自同构群足够大，使群论归约可行）。
- **A2 最优自适应路由**：判定的是「潜能」——存在最优分流使所有模式可行；真实路由可能更差，但若最优都不够，次优更不够。
- **A3 物理代价线性**：功耗、bump 需求、布线需求都经 $\boldsymbol{\ell}$ 线性连接（$\boldsymbol{\ell}$ 是唯一物理桥梁）。
- **A4 定长流量单位**：排列需求 $D^{(r)}_{ij}\in\{0,1\}$，$B$ 是缩放这些单位的每端口带宽。

## 3. 核心数学模型

### 3.1 最坏流量 = 排列（定理 1）

> **定理 1**：设 $\mathcal{G}$ vertex-transitive，负载均衡策略 $\mathrm{Aut}(\mathcal{G})$-不变，则最差流量模式必为排列矩阵 $\mathbf{D}^{(r)}\in\mathcal{R}$。

依据：Birkhoff——任意 admissible $\mathbf{D}$（doubly substochastic）是排列凸组合，故其极端情形是排列。（严格证明见 `SYMMETRY_REDUCTION.md`。）

### 3.2 群论归约（定理 2）

> **定理 2**：两个排列产生同构流图，当且仅当它们在 $\mathrm{Aut}(\mathcal{G})$ 下共轭；等价类 = $\mathrm{Aut}(\mathcal{G})$ 在 $S_n$ 上的共轭轨道。

代表元数 $|\mathcal{R}|$：$K_n$（完全图）时为整数分拆数 $p(n)$（$p(16)=231$）；对称 Dragonfly 时更小。（证明见 `SYMMETRY_REDUCTION.md`。）

### 3.3 统一 LP（对每个模式 $r\in\mathcal{R}$，固定 $B$ 判可行性）

**(a) 分流守恒**（每个排列的流量必须被分流路径满足）：

$$
\sum_k f^{k,(r)}_{ij} = D^{(r)}_{ij}\qquad \forall i,j
$$

**(b) 链路负载**（链路 $e$ 上的负载 = 经过 $e$ 的所有分流之和）：

$$
L^{(r)}_e = \sum_{(i,j,k):\, e\in\mathrm{path}(i,j,k)} f^{k,(r)}_{ij}\qquad \forall e
$$

**(c) 包络**（物理资源按最坏模式配置）：

$$
L_e \ge L^{(r)}_e\qquad \forall e,\ \forall r
$$

### 3.4 物理桥梁（把 $\mathbf{L}$ 变成物理代价）

$$
\boldsymbol{\ell} = B\,\mathbf{S}_{\text{bw}}^{-1}\,\mathbf{L}
\qquad\Rightarrow\qquad
\mathbf{P} = P_0\,\mathbf{1}+\beta_P B\,\mathbf{1} + \mathbf{M}\,\mathbf{S}_{\text{dyn}}\,\boldsymbol{\ell}
$$

$$
\mathbf{N}^{\text{sig}}=\mathbf{M}\boldsymbol{\ell},\quad
\mathbf{N}^{\text{pwr}}=\mathbf{S}_{\text{in}}^{-1}\mathbf{P},\quad
\mathbf{N}^{\text{sig}}+\mathbf{N}^{\text{pwr}}\le\mathbf{N}^{\text{total}}(B)
$$

$$
\mathbf{G}\,\mathbf{T}=\mathbf{P}+\mathbf{b},\qquad \mathbf{T}\le T_{\max}\mathbf{1}
$$

### 3.5 求解（二分搜索）

固定 $B$ 判可行性（纯线性，无目标函数），二分搜索：

$$
B^* = \sup\{B\ge0 : \text{LP}(B)\ \text{可行}\}
$$

每次迭代解一个线性可行 LP，$\log_2(B_{\max}/\varepsilon)$ 次收敛。

## 4. 模型输出

- $B^*$：最大无阻塞端口带宽（主输出）。
- $\mathbf{L}$：负载包络（所有排列下每链路最坏负载）——整个 LP 的枢纽变量。
- 约束账本：每条约束的利用率/余量；对偶变量 = 影子价格（灵敏度分析）。

## 5. 无阻塞与放宽

- **严格无阻塞**：在 A1（vertex-transitive）假设下成立。
- **放宽路径（RNB）**：换 Clos 分解（`CLOS_DECOMPOSITION.md`）——不依赖对称性，条件更强（充分不必要），作可行域下界对照。

## 6. 功耗地位

**有，但只有线性 + 静态两项**：

$$
\mathbf{P} = \underbrace{P_0\mathbf{1}+\beta_P B\mathbf{1}}_{\text{静态 + 每带宽线性}} + \underbrace{\mathbf{M}\mathbf{S}_{\text{dyn}}\boldsymbol{\ell}}_{\text{per-lane 线性}}
$$

**缺失**：核心交换的 `radix²` 超线性项（真实交换机功耗随 radix quadratic，见 `real_chip_catalog/00_BANDWIDTH_AREA_POWER_SCALING.md`）。当前把核心功耗当常数 $P_0$，大 radix 下会低估。

## 7. 与文献对照

| 维度 | 我们 | 文献空白 |
|------|------|---------|
| 无阻塞 × 功耗联立 | ✅ 唯一 | 其他全无 |
| 延迟 | ❌ 只判带宽 | 网络演算/queueing 有，但不联立功耗 |
| 流量模型 | 排列（最坏，静态） | oblivious（Yuan）更一般，但也不联立 |

**独特价值**：群论归约把 $n!$ 个排列压到 $p(n)$ 个，使「无阻塞带宽 + 功耗 + 热」能放进一个可解 LP——这是「无阻塞 × 功耗」联立且**可求解**的唯一实现。**与 McKeown 的退化对应**：$B^*\big|_{\text{单级}}=\theta^*$（见 `01_mckeown_1996_100pct.md` §9）。
