# 01 McKeown 1996 —— 输入排队交换机 100% 吞吐（最大权重匹配）

> 单级 $n\times n$ crossbar + VOQ。问题：何种调度能稳定所有 admissible 到达？答案：最大权重匹配（LQF / OCF）。本文给出**符号自洽、假设显式**的数学形式，不涉及求解细节。

## 0. 符号表（本节所有符号在此定义）

| 符号 | 定义 |
|------|------|
| $n$ | 输入（=输出）端口数，$i,j\in\{1,\dots,n\}$ |
| $t\in\mathbb{Z}_{\ge0}$ | 时隙（离散时间，一个时隙 = 传输一个定长 cell 的时间） |
| $A_{ij}(t)\in\{0,1\}$ | 时隙 $t$ 输入 $i$ 是否有 cell 去输出 $j$（到达指示） |
| $D_{ij}\in[0,1]$ | 到达率，$D_{ij}=\mathbb{E}[A_{ij}(t)]$（= 每个时隙的到达概率） |
| $q_{ij}(t)\in\mathbb{Z}_{\ge0}$ | 时隙 $t$ 末尾 VOQ$(i,j)$ 的队列长度（cell 数） |
| $S_{ij}(t)\in\{0,1\}$ | 时隙 $t$ 是否服务 VOQ$(i,j)$（服务指示） |
| $\mathbf{P}=(P_{ij})$ | 排列矩阵（匹配）：每行、每列恰一个 1，其余 0 |
| $\mathcal{S}$ | 全部 $n\times n$ 排列矩阵集合 |
| $\mu$ | 服务率，归一化 $\mu=1$ cell/时隙（每端口每时隙至多服务 1） |
| $\rho_{\text{row}},\rho_{\text{col}}$ | 最大行和、最大列和：$\rho_{\text{row}}=\max_i\sum_j D_{ij}$，$\rho_{\text{col}}=\max_j\sum_i D_{ij}$ |
| $\theta$ | 负载倍数（标量），$\theta\ge0$ |

内积 $\langle \mathbf{A},\mathbf{B}\rangle=\sum_{ij}A_{ij}B_{ij}$。

## 1. 模型定位

给定到达率矩阵 $\mathbf{D}$，输入排队（VOQ）交换机在何种调度下能稳定？答案：最大权重匹配，可稳定**所有 admissible** $\mathbf{D}$，即 **100% throughput**。

## 2. 模型假设（显式）

- **A1 拓扑**：$n\times n$ crossbar，无中间链路，无 speedup——每输入每时隙至多 1 到达、1 服务，每输出每时隙至多 1 服务。
- **A2 VOQ**：每输入 $i$ 对每输出 $j$ 一个独立 FIFO（共 $n^2$ 个队列），消除 HOL blocking。
- **A3 到达独立**：$\{A_{ij}(t)\}_{t\ge0}$ 跨 $t$ 独立同分布；不同输入 $i$ 之间相互独立；目的地 $j$ 分布固定（均匀或非均匀皆可）。
- **A4 每输入无突发**：对每个 $i$，$\sum_j A_{ij}(t)\le1$（每时隙每输入至多 1 个 cell 到达）。
- **A5 定长 cell**：所有 cell 等长，时隙 = 1 个 cell 的服务时间。

## 3. 队列动力学

$$
q_{ij}(t+1) = q_{ij}(t) + A_{ij}(t) - S_{ij}(t)
$$

其中服务指示满足匹配约束与「不服务空队列」约束：

$$
S_{ij}(t)\le q_{ij}(t)+A_{ij}(t),\qquad
\sum_j S_{ij}(t)\le1\ (\forall i),\qquad
\sum_i S_{ij}(t)\le1\ (\forall j)
$$

即 $\mathbf{S}(t)$ 是一个匹配（$\mathbf{S}(t)\in\mathcal{S}$ 的子集，允许部分行列为 0）。

## 4. 吞吐区域与优化形式

### 4.1 admissible 与吞吐区域

到达率矩阵 $\mathbf{D}$ 称为 **admissible**，若：

$$
\sum_j D_{ij}\le1\ (\forall i),\qquad \sum_i D_{ij}\le1\ (\forall j)
$$

即 $\mathbf{D}$ 是 doubly substochastic。**吞吐区域** = 所有可被稳定支撑的 $\mathbf{D}$ 的集合。McKeown 的主结果：

$$
\boxed{\ \text{吞吐区域} = \{\mathbf{D}\ge0:\ \rho_{\text{row}}\le1,\ \rho_{\text{col}}\le1\}\ }
$$

即吞吐区域**恰好是 admissible 多面体**。100% throughput 的严格含义：对**任意** admissible $\mathbf{D}$，系统稳定。

### 4.2 标量化（「最高吞吐」的优化形式）

固定流量形状 $\mathbf{D}$（$\mathbf{D}\ge0$，不含自流 $D_{ii}$），问最大可支撑的负载倍数 $\theta$：

$$
\theta^* = \max_{\theta\ge0}\ \theta \quad\text{s.t.}\quad
\theta\sum_j D_{ij}\le1\ (\forall i),\quad
\theta\sum_i D_{ij}\le1\ (\forall j)
$$

即 $\theta\mathbf{D}$ 需 admissible。显式解：

$$
\theta^* = \min\Big(\frac1{\rho_{\text{row}}},\ \frac1{\rho_{\text{col}}}\Big)
= \frac{1}{\max(\rho_{\text{row}},\rho_{\text{col}})}
$$

100% throughput ⟺ 对任意 admissible $\mathbf{D}$（$\rho_{\text{row}},\rho_{\text{col}}\le1$），都有 $\theta^*\ge1$。约束 $\sum_j D_{ij}\le1$ 的物理意义：单级 crossbar 无中间链路，**唯一瓶颈是端口容量**（每输入/输出每时隙 1 cell）。

## 5. 调度算法（时隙级）

每时隙选一个匹配 $\mathbf{P}(t)\in\mathcal{S}$，最大化权重和：

$$
\mathbf{P}(t)=\arg\max_{\mathbf{P}\in\mathcal{S}}\ \sum_{ij} w_{ij}(t)\,P_{ij}
$$

- **LQF**（longest queue first）：$w_{ij}(t)=q_{ij}(t)$（队列占用）。
- **OCF**（oldest cell first）：$w_{ij}(t)=$ 该 VOQ 队首 cell 已等待的时隙数（等待时间）。

服务指示 $\mathbf{S}(t)=\mathbf{P}(t)\wedge(\mathbf{q}(t)+\mathbf{A}(t)>0)$（只服务被选中且非空的队列）。

## 6. 稳定性定理与证明骨架

### 6.1 稳定性定义（强稳定 / 正递归）

$$
\sup_{t\ge0}\ \mathbb{E}\Big[\sum_{i,j}q_{ij}(t)\Big] < \infty
$$

### 6.2 主定理

LQF 与 OCF 对所有满足 A1–A5、且 $\mathbf{D}$ admissible 的到达过程，达到强稳定。

### 6.3 Lyapunov 证明骨架

取 $V(\mathbf{q})=\sum_{ij}q_{ij}^2$。单步漂移：

$$
\Delta V(t)=V(t+1)-V(t)
=\sum_{ij}\Big[(q_{ij}+A_{ij}-S_{ij})^2-q_{ij}^2\Big]
$$

展开，利用 $A_{ij},S_{ij}\in\{0,1\}$ 得 $(A_{ij}-S_{ij})^2\le1$：

$$
\Delta V(t) \le 2\sum_{ij}q_{ij}(A_{ij}-S_{ij}) + n^2
$$

取条件期望：

$$
\mathbb{E}[\Delta V\mid\mathbf{q}] \le 2\sum_{ij}q_{ij}\Big(D_{ij}-\mathbb{E}[S_{ij}\mid\mathbf{q}]\Big) + n^2
\tag{$\star$}
$$

**关键步（最大权重 + Birkhoff）**：由 Birkhoff，admissible $\mathbf{D}$ 可写成排列凸组合：

$$
\mathbf{D}\le\sum_k \gamma_k\mathbf{P}_k,\qquad \gamma_k\ge0,\quad \sum_k\gamma_k\le1,\quad \mathbf{P}_k\in\mathcal{S}
$$

于是对任意 $\mathbf{q}\ge0$：

$$
\sum_{ij}q_{ij}D_{ij}
\le \sum_k\gamma_k\sum_{ij}q_{ij}P_{k,ij}
\le \Big(\sum_k\gamma_k\Big)\max_{\mathbf{P}\in\mathcal{S}}\sum_{ij}q_{ij}P_{ij}
\le \sum_{ij}q_{ij}S_{ij}
$$

最后一步用了 $\sum_k\gamma_k\le1$ 与最大权重匹配的定义 $\sum_{ij}q_{ij}S_{ij}=\max_{\mathbf{P}}\sum_{ij}q_{ij}P_{ij}$。代回 $(\star)$，主项非正：

$$
\mathbb{E}[\Delta V\mid\mathbf{q}] \le n^2
$$

（此处漂移仅为常数，尚不足证稳定；原文进一步论证：当 $\lVert\mathbf{q}\rVert$ 足够大时，$\sum_{ij}q_{ij}(D_{ij}-S_{ij})$ 严格负且量级 $\sim-\delta\lVert\mathbf{q}\rVert$，$\delta>0$ 为「内积夹角有界远离 $0$」的引理——见原文 Lemma，此处不展开。由此得 Foster–Lyapunov 负漂移判据，系统正递归。）

### 6.4 FIFO 对照（为什么必须 VOQ + 权重）

单 FIFO（无 VOQ）有 HOL blocking，均匀 i.i.d. 下吞吐上限为 $2-\sqrt2\approx58.6\%$。maximum **size** matching（$w_{ij}=\mathbb{1}\{q_{ij}>0\}$，只看边数不看权重）在非均匀流量下不稳定——必须用「权重」感知背压。

## 7. 无阻塞与放宽

- **不是 strict-sense 无阻塞**（strict-sense 要求每时隙无排队接通）。这里是**吞吐意义**：平均跟上到达，允许有限稳定排队。
- **放宽路径**：$w_{ij}=\mathbb{1}\{q_{ij}>0\}$（maximum size）→ 仅均匀流量下 100%，非均匀下不稳定。

## 8. 功耗地位

**完全不建模**。无功耗、无面积、无 lane、无热。唯一代价是控制面复杂度 $O(n^{2.5})$（最大权重匹配），非功耗。

## 9. 与我们的对照

| 维度 | 我们（00_ours） | McKeown 1996 |
|------|----------------|--------------|
| 需求结构体 | 最坏排列 $\mathbf{P}\in\mathcal{R}$（确定性最坏） | 任意 admissible $\mathbf{D}$（随机稳定） |
| 判定对象 | 最大无阻塞带宽 $B^*$ | 稳定性 / 100% 吞吐 |
| 共享底座 | Birkhoff：排列是极端点 | Birkhoff：排列是极端点 |
| 输出 | $\mathbf{L}$ 负载包络 + $B^*$ | 队列占用 $q_{ij}$ 有界 |
| 延迟 | ❌ | ❌（只给稳定，不给界） |
| 功耗 | ✅（线性 + 静态） | ❌ |

**退化对应（$\theta^*\to B^*$）**：$\theta^*$ 是 $B^*$ 在「拓扑退化为单 crossbar」时的特例——单级无中间链路，唯一瓶颈是端口容量 $\sum_jD_{ij}\le1$；我们塞进拓扑后瓶颈升级为链路包络 $\mathbf{L}$ + 物理资源。即 $B^*\big|_{\text{单级}}=\theta^*$。「McKeown 是我们模型的边界情形」——结构性论据。

**可借鉴**：Birkhoff 凸包是共同底座；其 Lyapunov 漂移为「最大权重 ⇒ 最优」给出随机版严格理由，与我们的「确定性最坏排列」殊途同归。

**缺口**：无功耗、无多级拓扑、无 lane/物理映射；「稳定」是渐近概念，不给有限界（延迟/积压）——这是与 Chang 1999 的分工点（见 `02_chang_1999_birkhoff.md`）。
