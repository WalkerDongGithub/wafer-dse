# 02 Chang 1999 —— Birkhoff–von Neumann 容量分解与确定性服务保证

> 单级 $n\times n$ input-buffered crossbar。不做逐时隙匹配，而是把 doubly-substochastic 速率矩阵 $\mathbf{D}$ 经 von Neumann 补全 + Birkhoff 分解拆成排列的加权轮转（token-PGPS），对**所有非均匀流量统一**给出确定性服务保证。本文给出符号自洽、假设显式、推导逐步的数学形式；求解细节（pivoting / token 记账）见原文 Algorithm 1–3。

## 0. 符号表（本节所有符号在此定义）

| 符号 | 定义 | 原文符号 |
|------|------|---------|
| $n$ | 输入（=输出）端口数，$i,j\in\{1,\dots,n\}$ | $N$ |
| $t,s\in\mathbb{Z}_{\ge0}$ | 时隙（离散时间；一个时隙 = 传输一个定长 cell 的时间） | $t,s$ |
| $\mathbf{D}=(D_{ij})$ | 速率矩阵，$D_{ij}$ = 分配给 input $i\to$ output $j$ 的速率，$D_{ij}\in[0,1]$，单位 cell/时隙 | $\mathbf{R}=(r_{ij})$ |
| $\rho_{\text{row}},\rho_{\text{col}}$ | 最大行和、最大列和：$\rho_{\text{row}}=\max_i\sum_j D_{ij}$，$\rho_{\text{col}}=\max_j\sum_i D_{ij}$ | 同义 |
| $r_{\max}$ | $r_{\max}=\max(\rho_{\text{row}},\rho_{\text{col}})$（严格不等式时 $r_{\max}<1$） | 同义 |
| $\tilde{\mathbf{D}}=(\tilde D_{ij})$ | doubly stochastic 补全，$\tilde D_{ij}\ge D_{ij}$ | $\tilde{\mathbf{R}}=(\tilde r_{ij})$ |
| $\mathbf{P}_k=(P_{k,ij})$ | 第 $k$ 个排列矩阵，$P_{k,ij}\in\{0,1\}$，每行每列恰一个 1 | $\mathbf{P}_k$ |
| $\phi_k$ | 第 $k$ 个排列的轮转权重，$\phi_k>0$，$\sum_k\phi_k=1$ | $\phi_k$ |
| $K$ | 分解中排列个数，$K\le n^2-2n+2$ | $K$ |
| $E_{ij}=\{k:P_{k,ij}=1\}$ | 服务 $(i,j)$ 的排列下标集 | $E_{ij}$ |
| $C_{ij}(t)$ | 到 $t$ 为止分配给 $(i,j)$ 的累计时隙数，单位 slots | $C_{ij}(t)$ |
| $s_{ij}$ | $(i,j)$ 的服务滞后上界，单位 slots | $s_{ij}$ |
| $A_{ij}(t)$ | 到 $t$ 为止 $(i,j)$ 的累计到达，单位 cells | $A_{ij}(t)$ |
| $\sigma_{ij}$ | $(i,j)$ 到达的突发参数（$(\sigma,\rho)$ 上约束），单位 cells | $\sigma_{ij}$ |
| $\mu$ | 归一化服务率，$\mu=1$ cell/时隙 | — |
| $\mathcal{S}$ | 全部 $n\times n$ 排列矩阵集合，$\lvert\mathcal{S}\rvert=n!$ | — |

内积 $\langle \mathbf{A},\mathbf{B}\rangle=\sum_{ij}A_{ij}B_{ij}$。速率矩阵单位为 cell/时隙，时间单位为时隙；$\mu=1$ 即每端口每时隙至多服务 1 个 cell。

## 1. 模型定位

已知不过载的速率矩阵 $\mathbf{D}$，**不用逐时隙计算匹配**，能否给每个 input–output 对 $(i,j)$ 一个**确定性服务保证**？答案：用 von Neumann + Birkhoff 把二维速率分配问题降维成一维加权轮转（PGPS/WFQ），每时隙按权重 $\phi_k$ 轮转排列 $\mathbf{P}_k$。

## 2. 模型假设（显式）

- **A1 拓扑**：$n\times n$ input-buffered crossbar，时隙同步；每时隙连接模式 = 一个排列矩阵 $\mathbf{P}\in\mathcal{S}$；**无 speedup、无 framing**。
- **A2 队列**：每输入端口一个 segregated buffer（原文为 per-input buffer，**非** VOQ；服务保证是对每对 $(i,j)$ 给出的）。
- **A3 速率已知且不过载（no overbooking）**：$\mathbf{D}$ 已知且 **doubly substochastic**：
  $$
  \sum_j D_{ij}\le1\ (\forall i),\qquad \sum_i D_{ij}\le1\ (\forall j)
  $$
- **A4 归一化**：每端口每时隙至多服务 1 个 cell（$\mu=1$）。
- **A5（von Neumann 补全）**：doubly substochastic 矩阵可逐元素补全为 doubly stochastic 矩阵（见 §3.2）。
- **A6（Birkhoff 分解）**：doubly stochastic 矩阵是排列矩阵的凸组合（见 §3.3）。

## 3. 核心数学

### 3.1 定义：substochastic 与 stochastic

$\mathbf{D}\ge0$ 称 **doubly substochastic** 若 A3 成立；称 **doubly stochastic** 若 A3 两式皆取等号。

### 3.2 von Neumann 补全（原文 Algorithm 1）

**命题（原文 Prop 1）**：对任意 doubly substochastic $\mathbf{D}$，存在 doubly stochastic $\tilde{\mathbf{D}}\ge\mathbf{D}$（逐元素）。若 A3 取严格不等号，令 $r_{\max}=\max(\rho_{\text{row}},\rho_{\text{col}})<1$，则存在构造使

$$
\tilde D_{ij}\ \ge\ \frac{D_{ij}}{r_{\max}}.
$$

（补全的 pivoting 构造见原文 Algorithm 1；上式为原文式 (7) 的构造结论，用于差异化服务。）

### 3.3 Birkhoff 分解（原文 Algorithm 2，Dulmage–Halperin）

$$
\tilde{\mathbf{D}}=\sum_{k=1}^{K}\phi_k\mathbf{P}_k,\qquad \phi_k>0,\quad \sum_{k=1}^{K}\phi_k=1,\qquad K\le n^2-2n+2.
$$

算法（原文 Algorithm 2）：
1. 找置换 $(i_1,\dots,i_n)$ 使 $\prod_{k=1}^{n}\tilde D_{k,i_k}>0$（正对角线。由 doubly stochastic 矩阵的支撑必含完美匹配——Hall 定理保证存在，原文 [12][21]）。
2. 令 $\phi_1=\min_{1\le k\le n}\tilde D_{k,i_k}$，$\mathbf{P}_1$ = 该置换对应的排列矩阵，$\mathbf{R}_1=\tilde{\mathbf{D}}-\phi_1\mathbf{P}_1$。
3. 若 $\phi_1=1$ 则 $\mathbf{R}_1=0$ 结束；否则 $\mathbf{R}_1/(1-\phi_1)$ 仍 doubly stochastic，回到第 1 步。

每轮至少把一个元素归零，故至多 $n^2-n+1$ 轮（最后一轮归零 $n$ 个元素）；由 Marshall–Olkin（原文 [18]）可收紧到 $K\le n^2-2n+2$。每轮二分图最大匹配 $O(n^{2.5})$（最大流归约，原文 [22] Theorem 10.2），故 offline 总复杂度 $O(n^{4.5})$。

### 3.4 在线调度（原文 Algorithm 3，token-PGPS）

每个排列 $\mathbf{P}_k$ 一类 token；第 $\ell$ 个 class-$k$ token 的虚完成时间：

$$
F_k^{(1)}=\frac{1}{\phi_k},\qquad F_k^{(\ell+1)}=F_k^{(\ell)}+\frac{1}{\phi_k}.
$$

每时隙服务虚完成时间最小的 token，服务到 class $k$ 就把 crossbar 设为 $\mathbf{P}_k$。在线复杂度 $O(\log n)$（$K$ 个 token 的有序插入），内存 $O(n^3\log n)$（$O(n^2)$ 个排列，每个 $n\log_2 n$ bit）。

### 3.5 主定理：服务保证（原文 Theorem 3）

**定理**：对任意满足 A3 的 $\mathbf{D}$，Algorithm 1–3 给出：$\forall i,j,\ s\le t$，

$$
\sum_{k\in E_{ij}}\phi_k(t-s)-s_{ij}\ \le\ C_{ij}(t)-C_{ij}(s)\ \le\ \sum_{k\in E_{ij}}\phi_k(t-s)+s_{ij},
\tag{原文式 (11)}
$$

其中

$$
s_{ij}=\min\Big[\,K,\ \lvert E_{ij}\rvert+\sum_{k\in E_{ij}}\phi_k(K-1)\,\Big],
\tag{原文式 (12)}
$$

且 $s_{ij}\le n^2-2n+2$。又由分解式 $\sum_{k\in E_{ij}}\phi_k=\sum_k\phi_kP_{k,ij}=\tilde D_{ij}\ge D_{ij}$（原文式 (9)/(13)），得**服务下界**：

$$
C_{ij}(t)-C_{ij}(s)\ \ge\ D_{ij}(t-s)-(n^2-2n+2).
\tag{原文式 (3)}
$$

即每对 $(i,j)$ 获得「速率 $D_{ij}$、滞后有界 $n^2-2n+2$」的确定性 service curve $\beta_{ij}(t)=D_{ij}t-s_{ij}$。

**证明骨架（每步依据标注）**：设 $\tau_k^{(\ell)}$ = 第 $\ell$ 个 class-$k$ token 被服务的时隙，$D_k(t)$ = 到 $t$ 为止 class-$k$ token 的累计服务数。反演公式：

$$
D_k(t)=\sup\{\ell:\tau_k^{(\ell)}\le t\}.
\tag{原文式 (17)}
$$

**Lemma 4（原文）**：对所有 $k=1,\dots,K$，

$$
\phi_k t-1\ <\ D_k(t)\ \le\ \phi_k(t+K-1).
\tag{原文式 (18)(19)}
$$

（上界用反证：若 $D_k(t)\ge\lfloor\phi_k(t+K-1)\rfloor+1$，则到 $t$ 已服务的 token 数严格超过 $t$，矛盾；下界由「每个 token 不晚于其虚完成时间被服务」+ 反演公式 (17)。完整 token 记账见原文 Lemma 4 证明，此处不逐字展开。）

由 $C_{ij}(t)=\sum_{k\in E_{ij}}D_k(t)$ 与 $\sum_{k}D_k(t)=t$（每时隙恰服务一个 token，原文式 (23)）：对下界，(i) 由 (23) 结合 (19) 的下界得 $-K$ 项（原文式 (21)）；(ii) 由 (19) 的下界代 $t$、上界代 $s$ 得 $-|E|-\sum_{k\in E}\phi_k(K-1)$ 项（原文式 (22)）：

$$
\sum_{k\in E_{ij}}\big(D_k(t)-D_k(s)\big)\ \ge\ \Big(\sum_{k\in E_{ij}}\phi_k\Big)(t-s)-K,
\tag{原文式 (21)}
$$

$$
\sum_{k\in E_{ij}}\big(D_k(t)-D_k(s)\big)\ \ge\ \Big(\sum_{k\in E_{ij}}\phi_k\Big)(t-s)-\lvert E_{ij}\rvert-\Big(\sum_{k\in E_{ij}}\phi_k\Big)(K-1).
\tag{原文式 (22)}
$$

取 (21)(22) 两者中较大的下界（即取较小的滞后项）即得 (11) 的左半与 (12) 的 $s_{ij}$；上界同理交换 $s,t$ 所用之界。∎

### 3.6 派生确定性延迟/积压界（网络演算，原文 §IV 引 Cruz [9][10]）

设 $A_{ij}$ 为 $(\sigma_{ij},D_{ij})$-上约束：

$$
A_{ij}(t)-A_{ij}(s)\ \le\ \sigma_{ij}+D_{ij}(t-s)\quad(\forall s\le t).
$$

把 3.5 的服务下界当作 service curve $\beta$，网络演算给出（FIFO 下）：

$$
v=\sigma_{ij}+s_{ij}\ \ (\text{积压/buffer 界}),\qquad
h\ \le\ \Big\lceil\frac{s_{ij}+\sigma_{ij}}{D_{ij}}\Big\rceil\ \ (\text{延迟界}).
$$

（$\lceil x\rceil$ 为不小于 $x$ 的最小整数。延迟/积压界为**据正文交叉确认**：原文以文字给出该结果，引 Cruz [9][10] 的 calculus，此处系数 $s_{ij}+\sigma_{ij}$ 与 $\lceil\cdot\rceil$ 逐字来自原文 §IV。）

## 4. 模型输出

1. **确定性服务保证**（速率 $D_{ij}$ + 有界滞后 $s_{ij}\le n^2-2n+2$），对所有非均匀 $\mathbf{D}$ 统一成立。
2. **100% 吞吐**：$\mathbf{D}$ 满足严格不等式且到达平稳遍历时（原文引 [19][20] 的稳定判据）。
3. **随机保证**：到达为 $(\sigma(\theta),D_{ij}(\theta))$-上约束时，$P(q_{ij}(t)\ge X)\le\beta(\theta)e^{-\theta X}$（原文引 [5]）。
4. **差异化服务**：严格不等式下，令 $\phi_{K+1}=1-r_{\max}$、$\mathbf{P}_{K+1}=\mathbf{0}$，best-effort 用剩余带宽（原文式 (28)(29)）。

## 5. 无阻塞与放宽

- **不是 strict-sense 无阻塞**；是「服务保证」意义——任意 doubly substochastic $\mathbf{D}$ 都获速率保证，等价 100% throughput。显式代价是滞后 $s_{ij}=O(n^2)$，根源是排列个数上界 $K\le n^2-2n+2$。
- **放宽路径**：① $r_{\max}<1$ 压缩速率、把 $1-r_{\max}$ 让给 best-effort（用带宽换确定性/容错）；② 速率未知/非平稳时需在线测量自适应；③ WRR/帧方案是 Algorithm 2 在有理数速率下的特例（帧大小 ↔ 速率粒度/延迟取舍），Birkhoff 表示更紧凑。

## 6. 功耗地位

**完全不建模**。代价全在控制面：offline $O(n^{4.5})$、online $O(\log n)$、内存 $O(n^3\log n)$——是计算/存储复杂度，非功耗。无 per-lane 线性、无 radix² 超线性、无静态 $P_0$、无热。

## 7. 与我们的对照

| 维度 | 我们（00_ours） | Chang 1999 |
|------|----------------|------------|
| 需求结构体 | 最坏排列 $\mathbf{P}\in\mathcal{R}$（不需知道 $\mathbf{D}$） | 已知 doubly substochastic $\mathbf{D}$ |
| 判定对象 | 最大无阻塞带宽 $B^*$ | 确定性服务保证（速率 + 滞后） |
| Birkhoff 用法 | 存在性（最坏 = 排列） | **构造性**（显式分解 $\tilde{\mathbf{D}}=\sum_k\phi_k\mathbf{P}_k$） |
| 输出 | $\mathbf{L}$ 负载包络 + $B^*$ | $C_{ij}(t)$ 服务下界 + 延迟/积压界 |
| 延迟 | ❌ | ✅（$h$ 延迟界，网络演算入口） |
| 功耗 | ✅（线性 + 静态） | ❌ |

**可借鉴点**：① Chang 的分解是 Birkhoff 定理的**构造性算法**，给出 $\mathbf{D}\le\sum_k\phi_k\mathbf{P}_k$ 的显式系数——把「最坏 = 排列」从存在性推进到可计算；② 滞后项 $s_{ij}=O(n^2)$ 直接绑定分解项数 $K$，我们的群论归约把 $n!$ 压到 $p(n)$，等价于把 $K\le n^2-2n+2$ 压到代表元数 $\lvert\mathcal{R}\rvert$，可作为 LP 规模优势的对照锚点；③ Theorem 3 直接导出 service curve $\beta_{ij}(t)=D_{ij}t-s_{ij}$，是「无阻塞 × 延迟」联立（我们缺的延迟界）最现成的入口。

**缺口**：无功耗、无多级拓扑（仅单级 crossbar）、无 lane/物理映射；且假设 $\mathbf{D}$ 已知，比我们「最坏排列」更乐观（我们不需知道 $\mathbf{D}$，但更保守）。
