# 08 Kiasari 2013 —— NoC 分析延迟模型（PQ 模型）

> 出处：A. E. Kiasari, Z. Lu, A. Jantsch, "An Analytical Latency Model for Networks-on-Chip," IEEE TVLSI 21(1), 2013, pp. 113–123。
> 问题：给 wormhole 交换、确定性路由的**任意拓扑** NoC，快速解析估计**平均包延迟** $\bar W_{ij}$ 与路由器阻塞时间。

> **公式来源说明**：本文 PDF 的全部编号公式（(1)–(20)）均为位图，无法逐字提取。以下方程依据正文文字描述交叉确认；凡涉及具体系数、且正文未逐字给出的，均标注「据正文交叉确认」或「见原文」。教科书标准式（Allen–Cunneen、非抢占优先级等待、残差近似）正文明确引用其出处（Bolch [3]、Takagi [22]、Kleinrock [14]），可按标准形式给出。

## 0. 符号表（本节所有符号在此定义）

| 符号 | 定义 |
|------|------|
| $\mathcal{V}$，$n=\lvert\mathcal{V}\rvert$ | 节点集合（IP core + 路由器）、节点数 |
| $\mathcal{C}$ | 通道（有向边）集合；$c=(u,v)$ 为 $u$ 的输出通道、$v$ 的输入通道 |
| $D_{sd}$ | 源 $s$→目的 $d$ 的包注入率（packets/cycle），即统一符号的流量需求矩阵 $\mathbf{D}=(D_{ij})$ |
| $r_{sd}(c)\in\{0,1\}$ | 确定性路由函数：$s\!\to\!d$ 路径经过通道 $c$ 取 1，否则 0 |
| $\Pr(s\!\to\!d)$ | 一个包在 $s$ 生成且去 $d$ 的概率（全网加权用） |
| $\lambda^{(c)}$ | 通道 $c$ 的聚合包到达率（packets/cycle），$\lambda^{(c)}=\sum_{s,d}D_{sd}r_{sd}(c)$ |
| $\lambda_{c\to c'}$ | 从通道 $c$ 转入通道 $c'$ 的到达率 |
| $p_{c\to c'}$ | 转发概率：进入 $c$ 的包从 $c'$ 离开的比例，$p_{c\to c'}=\lambda_{c\to c'}/\lambda^{(c)}$ |
| $S_c$ | 通道 $c$ 的服务时间（随机变量，cycles） |
| $\mathbb{E}[S_c],\ \mathbb{E}[S_c^2]$ | 服务时间的一、二阶矩 |
| $\mu_c$ | 通道 $c$ 的服务率，$\mu_c=1/\mathbb{E}[S_c]$ |
| $\rho_c$ | 通道 $c$ 利用率，$\rho_c=\lambda^{(c)}/\mu_c$ |
| $C_A,\ C_B$ | 到达间隔、服务时间的变异系数（CV），$C_X^2=\operatorname{Var}[X]/\mathbb{E}[X]^2$ |
| $C_A^{\text{net}}$ | 全网统一到达 CV（近似，见假设 A5） |
| $\bar W$ | 平均排队等待时间 |
| $S_e$ | 残差服务时间（incoming head flit 看到的剩余服务时间期望）。**注意**：与统一符号的网络演算累计流量 $\mathbf{R}(t)$ 无关，仅同名 |
| $t_{\text{inj}},\ t_{\text{sw}},\ t_w,\ t_{\text{ej}}$ | 注入通道、路由器（路由决策+crossbar）、相邻路由器间 wire、弹出通道的传递延迟（cycles） |
| $L^{\text{fix}}_{sd}$ | $s\!\to\!d$ 无争用（零负载）延迟 |
| $\bar W_{sd},\ \bar W^{\text{head}}_{sd},\ \bar W^{\text{body}}_{sd}$ | $s\!\to\!d$ 的平均包延迟及其 head flit、body flit 分量 |
| $\bar m,\ \sigma_m$ | 包长（flits）的均值、标准差 |
| $B_{\text{in}},\ B_{\text{out}}$ | 路由器输入、输出 buffer 容量（flits） |

## 1. 模型定位

输入四元组（应用通信图 $\mathbf{D}$、拓扑图、映射向量、路由矩阵）→ 输出平均包延迟 $\bar W_{ij}$ 与路由器阻塞时间。核心做法：把每个输出通道建模为**非抢占优先级 G/G/1 队列**，逐通道求等待时间，再沿确定性路由路径求和得到端到端延迟。

## 2. 模型假设（显式）

- **A1 拓扑**：任意有向图 $G=(\mathcal{V},\mathcal{C})$，顶点 = IP core + 路由器，边 = 物理通道。
- **A2 交换**：wormhole；消息拆成包；**通道按包分配**——整包通过后通道才释放。
- **A3 路由**：确定性（最小或非最小均可），$r_{sd}(c)$ 预先给定，与流量无关。
- **A4 队列**：每通道一个**有限** FIFO；每个输出通道建模为**非抢占优先级 G/G/1** 队列（各输入通道 = 各优先级类）。
- **A5 到达**：包注入过程为一般分布，只由前两阶矩（均值 $D_{sd}$、CV $C_A$）刻画；逐通道到达间隔 CV 未知，**近似为全网统一** $C_A^{(c)}=C_A^{\text{net}}$（本文的关键简化，避免了 wormhole 阻塞反馈下逐通道 CV 的精确求解）。
- **A6 服务**：服务时间一般分布，由前两阶矩（$\mathbb{E}[S_c],\mathbb{E}[S_c^2]$）刻画。
- **A7 目的消费**：包到目的地立即被消费（ejection 通道后不再排队）。
- **A8 仲裁**：每输出通道的输入通道按顺时针方向降序优先级，注入通道优先级最高；由流控保证路由器永不过载、低优先类不饥饿。

## 3. 核心方程

### 3.1 基础队列式（式 (1)–(3)）

单队列平均等待用 **Allen–Cunneen** 近似（G/G/1，正文引 Bolch [3]）：

$$
\boxed{\ \bar W=\frac{\rho}{1-\rho}\cdot\frac{C_A^2+C_B^2}{2}\cdot\frac{1}{\mu}\ },\qquad \rho=\frac{\lambda}{\mu}
\tag{1}
$$

非抢占优先级（类 $i$ 的等待，正文引 Takagi [22]）：

$$
\bar W_i=\frac{S_e}{\big(1-\sum_{k<i}\rho_k\big)\big(1-\sum_{k\le i}\rho_k\big)}
\tag{2}
$$

其中残差服务时间在 G/G/1 下近似为（正文引 Bolch [3]）：

$$
S_e\approx\frac{\rho}{2\mu}\big(C_A^2+C_B^2\big)
\tag{3}
$$

**推导依据**：式 (2) 的分母是「高优先级占用时间」与「同类及更高优先级占用时间」两个剩余容量因子的乘积——一个到达的类 $i$ 顾客须先等完当前正在服务的残差 $S_e$，再等完所有 $k<i$ 类已排队工作 $(\sum_{k<i}\rho_k)$，而自身排队期间又有 $k\le i$ 类新到达（因子 $1-\sum_{k\le i}\rho_k$）。式 (3) 是 G/G/1 下 $S_e=\lambda\mathbb{E}[S^2]/2$ 的 CV 形式（见 §3.3 残差式 (12) 的同一写法）。

### 3.2 延迟分解（式 (4)–(7)）

包延迟 = head flit 延迟 + body flit 流水延迟：

$$
\bar W_{sd}=\bar W^{\text{head}}_{sd}+\bar W^{\text{body}}_{sd}
\tag{4}
$$

head flit 延迟 = 各跳等待之和 + 无争用固定延迟：

$$
\bar W^{\text{head}}_{sd}=\sum_{\text{hops }c\in s\to d}\bar W^{(c)} + L^{\text{fix}}_{sd}
\tag{5}
$$

其中单跳无争用延迟（图 3 的一跳流）由注入、路由器、wire、弹出四段组成：

$$
L^{\text{fix}}_{sd}=t_{\text{inj}}+t_{\text{sw}}+t_w+t_{\text{sw}}+t_{\text{ej}}\quad(\text{一跳})
$$

body flit 的流水周期（每条 body flit 比 head 晚到达的时间）取决于缓冲结构：

$$
\bar W^{\text{body}}_{sd}=\begin{cases}
(\bar m-1)\cdot\max(t_{\text{sw}},\,t_w), & \text{输入+输出缓冲}\\[4pt]
(\bar m-1)\cdot(t_{\text{sw}}+t_w), & \text{仅输入或仅输出缓冲}
\end{cases}
\tag{6,7}
$$

**推导依据**：head flit 到达目的地后，body flit 以「流水周期」逐个跟进；输入+输出缓冲时上游与下游重叠，瓶颈周期取 $\max(t_{\text{sw}},t_w)$；仅单侧缓冲时两段串行，取 $t_{\text{sw}}+t_w$（正文引 [4] 的通用参考架构）。

### 3.3 等待时间：wormhole 有限缓冲修正（式 (8)–(13)）

式 (2) 假设无限队列，但 wormhole 每 buffer 只存有限 flits，故不能直接套用，需为「类 $i$ 的 head flit」重写（正文：*"we cannot use (2)… compute the average waiting time for the head of class i in this special case"*）：

$$
\bar W_i=\frac{S_e_i}{\big(1-\sum_{k<i}\rho_k\big)\big(1-\sum_{k\le i}\rho_k\big)}
\tag{8}
$$

其中 $\rho_k$ 是通道被类 $k$ 包占用的时间比例（= 利用率）：

$$
\rho_k=\frac{\lambda_k}{\mu_k}
\tag{9}
$$

残差（同式 (3) 的 G/G/1 形式）：

$$
S_e\approx\frac{\rho}{2\mu}\big(C_A^2+C_B^2\big)
\tag{10}
$$

**关键近似（全网统一 CV）**：逐通道 $C_A^{(c)}$ 无法显式求，令其等于到达网络的 CV：

$$
C_A^{(c)}=C_A^{\text{net}},\quad\forall c
\tag{11}
$$

将 $\rho_c=\lambda^{(c)}/\mu_c$ 与式 (11) 代入，式 (10) 改写为：

$$
S_e^{(c)}\approx\frac{\lambda^{(c)}}{2\mu_c^2}\big((C_A^{\text{net}})^2+C_B^{(c)\,2}\big)
\tag{12}
$$

代回式 (8) 得逐通道逐类的最终等待式：

$$
\bar W_i^{(c)}=\frac{S_e^{(c)}}{\big(1-\sum_{k<i}\rho_k^{(c)}\big)\big(1-\sum_{k\le i}\rho_k^{(c)}\big)}
\tag{13}
$$

（式 (12)、(13) 的具体代数形式为位图，此式**据正文交叉确认**，精确系数见原文。）至此，$\bar W_i^{(c)}$ 只依赖两类量：① 通道到达率 $\lambda^{(c)}$（§3.4）；② 服务时间一、二阶矩 $\mathbb{E}[S_c],\mathbb{E}[S_c^2]$（§3.5）。

### 3.4 到达率沿确定性路由传播（式 (14)–(15)）

通道 $c$ 的聚合到达率 = 所有经过它的流之和：

$$
\lambda^{(c)}=\sum_{s,d} D_{sd}\,r_{sd}(c),\qquad r_{sd}(c)=1\ \text{当 } s\!\to\!d\text{ 经过 }c
\tag{14}
$$

输出通道的到达率 = 各输入通道转到它的到达率之和：

$$
\lambda^{(c)}=\sum_{c'}\lambda_{c'\to c}
\tag{15}
$$

### 3.5 服务时间矩反向递归（式 (16)–(19)，本文核心贡献）

服务时间不能正向算（下游排队会回压上游），故按「到目的地最大距离」给通道分 index（ejection 通道 index $0$，其余 $1\dots$ 网络直径），从 index $0$ 向源端**升序**递归。上游通道的服务时间 = 下游通道的服务时间（按转发概率加权）**减去** buffer 重叠：

$$
\mathbb{E}[S_c]=\sum_{c'}p_{c\to c'}\,\mathbb{E}[S_{c'}]-\Delta_{\text{buffer}}
\tag{16}
$$

$$
p_{c\to c'}=\frac{\lambda_{c\to c'}}{\lambda^{(c)}}
\tag{17}
$$

$$
\mathbb{E}[S_c^2]\approx\sum_{c'}p_{c\to c'}\,\mathbb{E}[S_{c'}^2]
\tag{18}
$$

$$
C_B^{(c)}=\frac{\sqrt{\mathbb{E}[S_c^2]-\mathbb{E}[S_c]^2}}{\mathbb{E}[S_c]}
\tag{19}
$$

**推导依据（不跳步）**：图 6(a) 中包 $u\!\to\!v\!\to\!w$，通道 $(v,w)$ 的服务在尾 flit 到达位置 2 时结束，通道 $(u,v)$ 的服务在尾 flit 到达位置 1 时结束，故 $\mathbb{E}[S_{(u,v)}]=\mathbb{E}[S_{(v,w)}]$ 减去「从位置 1 到位置 2 的时间」。这个减项 $\Delta_{\text{buffer}}$ 由上下游 buffer 容量 $B_{\text{in}},B_{\text{out}}$ 决定（**精确系数为位图，见原文式 (16)**）。图 6(b) 中一个通道可能通向多个下游，故对转发概率 $p_{c\to c'}$ 加权。式 (18) 是二阶矩的同一加权近似，式 (19) 是 CV 的定义式。ejection 通道的初值：head 在 $t_{\text{ej}}$、body 在 1 cycle 内被接受，配合已知的 $\bar m,\sigma_m$ 得 $\mathbb{E}[S],\mathbb{E}[S^2]$。

### 3.6 全网平均（式 (20)）

$$
\bar W=\sum_{s,d}\Pr(s\!\to\!d)\,\bar W_{sd}
\tag{20}
$$

## 4. 算法流程与复杂度

五步：① 通信图提取时空特征 $O(n)$；② 映射后算通道到达率 $O(nd_{\text{net}})$；③ 服务时间矩递归 $O(nd_{\text{net}}\bar p^2)$；④ 等待时间 $O(n\bar p)$；⑤ 全网平均 $O(nd_{\text{net}})$。总复杂度：

$$
O\big(n\,d_{\text{net}}\,\bar p^2\big)
$$

2D mesh 中 $d_{\text{net}}\propto\sqrt n$、$\bar p=5$，故 $O(n^{3/2})$。与仿真比快 $6\times10^4$–$2.6\times10^5$ 倍（3×3 到 20×20 mesh）。

## 5. 模型输出与精度

- 每流平均包延迟 $\bar W_{sd}$、全网加权平均 $\bar W$、路由器阻塞时间（= 等待分量）。
- 均匀流量（Poisson）误差 7.5%；bursty MMPP 误差 4.7%；非饱和区 <10%。饱和点附近偏差来自全网统一 CV 近似（A5）。

## 6. 无阻塞与放宽

**不答无阻塞**。这是平均延迟模型：$\rho\to1$ 时 $\bar W\to\infty$ 只表示饱和，从不给「哪些 admissible $\mathbf{D}$ 能被无阻塞支撑」的带宽保证。作者在结论中明示：未来把平均模型与 worst-case 模型整合（针对实时系统）。它与我们的 $\mathbf{L}$ 包络互补——一个给平均延迟、一个给最坏负载；二者在「带宽 × 延迟」上无交集。

## 7. 功耗地位

**完全不建模**。输入输出只有 $(\mathbf{D},\text{拓扑},\text{映射},\text{路由})\to(\bar W_{sd},\text{阻塞时间})$，无任何功耗/面积/热项。

## 8. 与我们的对照

| 维度 | 我们（00_ours） | Kiasari 2013 |
|------|----------------|-------------|
| 需求结构体 | 排列 $\mathbf{P}$（最坏） | 任意 $\mathbf{D}$（平均，一般分布，含 MMPP） |
| 拓扑假设 | vertex-transitive（群论归约） | 任意有向图 |
| 输出 | 无阻塞 $B^*$ + $\mathbf{L}$ 包络 | 平均延迟 $\bar W_{sd}$ |
| 确定性/平均 | 确定性最坏 | 平均 |
| 功耗 | 线性 + 静态 | 无 |

**可借鉴点**：① 式 (14)「到达率沿确定性路由传播」+ 式 (16)–(19)「服务时间矩从出口反向递归」——若要把我们的 $\mathbf{L}$ 时间化成 arrival/service curve $\alpha(t)/\beta(t)$（填补「带宽 × 延迟」空格的入口），这套 per-hop 分解是现成桥接；② 任意拓扑 + 非均匀 $\mathbf{D}$ 的处理方式比我们更一般。

**缺口**：不答无阻塞、不碰功耗、不联立带宽与延迟。
