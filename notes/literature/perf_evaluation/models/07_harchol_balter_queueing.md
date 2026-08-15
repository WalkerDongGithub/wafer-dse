# 07 Harchol-Balter —— 排队论（平均延迟/队列长度）

> 计算机系统性能建模的排队论教程。给定到达过程与服务时间分布，用 Markov 链 + 稳态分析给**平均**延迟 $\bar{W}$、平均队列长度 $\bar{N}$、吞吐 $X$、利用率 $\rho$ 等均值指标；与网络演算的「最坏界」互补（一个给均值，一个给上界）。核心工具链：Little's law（运算律）→ M/M/1 → M/M/k（Erlang-C/B）→ M/G/1（Pollaczek–Khinchin）→ Jackson 网络（product form）→ 功耗优化（ON/IDLE vs ON/OFF）。

## 0. 符号表（本节所有符号在此定义）

| 符号 | 定义（含取值域 / 单位） |
|------|------------------------|
| $\lambda$ | 到达率（Poisson 到达的平均速率）。单位：作业/时间 |
| $\lambda_i$、$r_i$ | 服务器 $i$ 的总到达率、外部到达率（Jackson 网络） |
| $S$ | 服务时间随机变量，$\mathbb{E}[S]=1/\mu$，$\mathbb{E}[S^2]<\infty$。单位：时间 |
| $\mu$ | 服务率 $=1/\mathbb{E}[S]$（单服务器），单位：作业/时间 |
| $\rho$ | 利用率（load）：单服务器 $\rho=\lambda/\mu$；$k$ 服务器 $\rho=\lambda/(k\mu)$ |
| $C_S^2$ | 服务时间变异系数平方 $=\mathrm{Var}(S)/\mathbb{E}[S]^2$（无量纲） |
| $N$、$N_Q$ | 系统内作业数、队列中（等待）作业数（随机变量） |
| $\bar{N}=\mathbb{E}[N]$、$\bar{N}_Q=\mathbb{E}[N_Q]$ | 平均队长、平均排队长度 |
| $T$、$T_Q$ | 作业在系统内时间（响应时间）、排队时间（随机变量，书中记法 $T,T_Q$） |
| $\bar{W}=\mathbb{E}[T]$、$\bar{W}_Q=\mathbb{E}[T_Q]$ | 平均响应时间、平均排队延迟（统一符号 $\bar{W}$；书中记 $\mathbb{E}[T],\mathbb{E}[T_Q]$） |
| $X$ | 吞吐 = 系统完成作业的速率（稳态下 $X=\lambda$） |
| $k$、$R$ | 服务器数、资源需求 $R=\lambda/\mu$（最少服务器数） |
| $P_Q$、$P_{\text{block}}$ | Erlang-C 排队概率、Erlang-B 阻塞概率 |
| $P_{ij}$ | 路由概率：作业离开服务器 $i$ 后去服务器 $j$ 的概率 |
| $P_{on},P_{idle},P_{off}$ | 静态功耗三态（ON / IDLE / OFF）。单位：功率 |
| $I$ | 开机 setup 时间（随机变量），$\mathbb{E}[I],\mathbb{E}[I^2]<\infty$ |

> **与统一符号的对应**：$\lambda_{ij}\leftrightarrow D_{ij}$（逐流需求率的连续化），$\mu\leftrightarrow B\cdot S_{\text{bw}}$（服务率的物理对应），$\rho=\lambda/\mu$ 同表。$\bar{W}$、$\bar{N}$ 即统一符号表的平均延迟、平均队长。

---

## 1. 模型定位

给定到达过程（Poisson，速率 $\lambda$）与服务时间分布 $S$，求**平均延迟、平均队列长度、吞吐/利用率**，并回答容量规划与调度的「what-if」问题（加倍 $\lambda,\mu$ 后延迟如何变？单快机 vs $k$ 台慢机哪个好？）。给的是**稳态均值**，不给最坏界。

## 2. 全书共同假设（显式）

- **A1 稳态遍历（ergodicity）**：所有随机过程的时间平均 = 集合平均，且极限存在（Little's law 与一切稳态量依赖此假设；原文 Ch.5、Ch.9）。
- **A2 到达-服务独立**：到达过程与各作业的服务时间序列相互独立（PASTA 所需，原文 §13.3 脚注）。
- **A3 稳定条件**：$\rho<1$（单服务器 $\lambda<\mu$；$k$ 服务器 $\lambda<k\mu$）——稳态分布存在且非平凡的充分必要条件。
- **A4 服务纪律**：FCFS（除显式说明的 PS / 优先级 / SRPT 等变体）。

---

## 3. 核心数学模型

### 3.1 Little's law 与运算律（最普适）

**假设（本节）**：A5 系统**任意**（不必 Markov、不必 FCFS、不必单服务器），仅需 A1 遍历 + $\lambda=X$（到达率 = 完成率；无丢失/无滞留时自动成立）。

**定理 3.1（Little's law，开系统；原文 Theorem 6.1/6.3）**：

$$
\boxed{\ \bar{N}=\lambda\,\bar{W}\ }
\qquad
\boxed{\ \bar{N}_Q=\lambda\,\bar{W}_Q\ }
$$

**推导骨架（原文 §6.4，不依赖服务次序与服务器数）**：设第 $i$ 个到达作业在系统内停留 $T_i$，$A(t),C(t)$ 为 $[0,t]$ 内到达/完成数。把「作业-时间」面积按水平求和（$\sum_{i}T_i$）与按垂直求和（$\int_0^t N(s)\,ds$）对照：

$$
\sum_{i\in C(t)}T_i\ \le\ \int_0^t N(s)\,ds\ \le\ \sum_{i\in A(t)}T_i
$$

同除 $t$ 并取 $t\to\infty$，用 $\frac{\sum_{i\in C(t)}T_i}{C(t)}\to\bar{W}$、$\frac{C(t)}{t}\to X=\lambda$（及到达侧的对称极限）夹逼得 $\bar{N}=\lambda\bar{W}$。∎（对「在队列中的时间」重复同一论证即得第二条。）

**推论（利用率定律，原文 Corollary 6.5）**：单设备 $i$ 的忙时占比

$$
\rho_i=\frac{\lambda_i}{\mu_i}=\lambda_i\,\mathbb{E}[S_i]=X_i\,\mathbb{E}[S_i]
$$

（把「系统」取为不含队列的服务设施，其中作业数在 $\{0,1\}$、期望 $=\rho_i$，再用 Little's law。）

**性质**：Little's law 是 $\bar{N},\bar{W},\lambda$ 之间的恒等式，本身不解出延迟，但任意模型解出一者即可推出另一者；它对闭系统仍成立（$N=X\,\bar{W}$，原文 Theorem 6.2）。

### 3.2 M/M/1（单服务器指数队列）

**假设（本节）**：A6 Poisson 到达（速率 $\lambda$）；A7 i.i.d. 指数服务（速率 $\mu$，$\mathbb{E}[S]=1/\mu$）；A8 单服务器 + 无穷缓冲；A9 FCFS；A10 稳定 $\rho=\lambda/\mu<1$。

**生灭链与稳态分布（原文 §13.1）**：状态 $n=$ 系统内作业数，转移率 $\lambda$（生）、$\mu$（灭）。全局平衡方程：

$$
\pi_0\lambda=\pi_1\mu,\qquad
\pi_n(\lambda+\mu)=\pi_{n-1}\lambda+\pi_{n+1}\mu\ \ (n\ge1)
$$

猜测 $\pi_n=\rho^n\pi_0$（$\rho=\lambda/\mu$）代入验证满足；由归一化 $\sum_{n\ge0}\pi_n=1$ 得 $\pi_0=1-\rho$，故

$$
\mathbb{P}\{N=n\}=\pi_n=(1-\rho)\rho^n,\qquad n\ge0
$$

**均值推导**：

$$
\bar{N}=\sum_{n\ge0}n\,\pi_n=\rho(1-\rho)\sum_{n\ge1}n\rho^{n-1}
=\rho(1-\rho)\frac{d}{d\rho}\Big(\frac{1}{1-\rho}\Big)=\frac{\rho}{1-\rho}
$$

再用 Little's law 与 $\bar{W}=\bar{W}_Q+1/\mu$：

$$
\boxed{\ \bar{W}=\frac{1}{\mu-\lambda},\qquad
\bar{N}=\frac{\rho}{1-\rho},\qquad
\bar{W}_Q=\frac{\rho}{\mu-\lambda}\ }
$$

（另：$\mathrm{Var}(N)=\rho/(1-\rho)^2$，原文 Exercise 13.12。）

**PASTA（原文 §13.3）**：Poisson 到达看到的稳态概率 = 时间平均概率（$a_n=p_n$），故「到达发现 $n$ 个作业」的概率就是 $\pi_n$。这是 M/M/1、M/M/k、M/G/1 推导中「到达者看到的队长 = 平均队长」的依据。

**关键结论**：$\rho\to1$ 时 $\bar{W},\bar{N}\to\infty$（饱和）；$\lambda,\mu$ 同乘 $k$ 时 $\rho$ 不变而 $\bar{W}$ 降到 $1/k$（时钟加速）；统计复用（合并为一条 M/M/1）比频分复用（$k$ 条独立通道）延迟小 $k$ 倍。

### 3.3 M/M/k 与 M/M/k/k（server farm）

**假设（本节）**：A11 $k$ 个同质并行服务器、各服务率 $\mu$、无穷缓冲、FCFS；A12 Poisson 到达（$\lambda$）、指数服务；A13 稳定 $\rho=\lambda/(k\mu)<1$。

**稳态分布（原文 §14.3）**：$\rho=\lambda/(k\mu)$，资源需求 $R=\lambda/\mu$（= 最少服务器数 = 期望占用服务器数）：

$$
\pi_i=\begin{cases}
\dfrac{(k\rho)^i}{i!}\pi_0, & 0\le i\le k\\[4pt]
\dfrac{\rho^i k^k}{k!}\pi_0, & i>k
\end{cases},\qquad
\pi_0=\left(\sum_{i=0}^{k-1}\frac{(k\rho)^i}{i!}+\frac{(k\rho)^k}{k!(1-\rho)}\right)^{-1}
$$

**Erlang-C（排队概率，原文式 (14.5)）**：由 PASTA，到达者需排队 ⟺ 看到 $\ge k$ 个作业：

$$
P_Q=\mathbb{P}\{\text{到达时 } k \text{ 个服务器全忙}\}=\sum_{i=k}^{\infty}\pi_i=\frac{(k\rho)^k}{k!(1-\rho)}\,\pi_0
$$

**均值（原文式 (14.7)–(14.10)）**：给定「已排队」条件下，$M/M/k$ 的 CTMC 与「到达率 $\lambda$、服务率 $k\mu$」的 M/M/1 相同（负载 $\rho$），故

$$
\bar{N}_Q=P_Q\cdot\frac{\rho}{1-\rho},\qquad
\bar{W}_Q=\frac{\bar{N}_Q}{\lambda}=\frac{P_Q\,\rho}{(1-\rho)\lambda},\qquad
\bar{W}=\bar{W}_Q+\frac{1}{\mu},\qquad
\bar{N}=P_Q\frac{\rho}{1-\rho}+k\rho
$$

**Erlang-B（有损 M/M/k/k，无队列；原文 §14.2）**：

$$
P_{\text{block}}=\mathbb{P}\{N=k\}=\frac{(k\rho)^k/k!}{\sum_{j=0}^{k}(k\rho)^j/j!}
$$

（$P_{\text{block}}$ 与 $P_Q$ 的关系：$P_{\text{block}}=\dfrac{(1-\rho)P_Q}{1-\rho P_Q}$，原文 Theorem 14.5。）

### 3.4 M/G/1（一般服务分布，Pollaczek–Khinchin）

**假设（本节）**：A14 Poisson 到达（$\lambda$）；A15 i.i.d. **一般**服务时间 $S$（只要求 $\mathbb{E}[S^2]<\infty$，$\mathbb{E}[S]=1/\mu$）；A16 单服务器 + 无穷缓冲 + FCFS；A17 稳定 $\rho=\lambda\mathbb{E}[S]<1$。

**推导（原文 §23.2，tagged job + PASTA + 剩余服务）**：到达作业 $A$ 的排队时间 = 排队中 $N_Q^A$ 个作业的服务时间之和 + 正在服务作业的剩余时间 $S_e$：

$$
\bar{W}_Q=\mathbb{E}[N_Q^A]\,\mathbb{E}[S]+\mathbb{P}\{\text{服务中}\}\,\mathbb{E}[S_e]
$$

由 PASTA：$\mathbb{E}[N_Q^A]=\bar{N}_Q$、$\mathbb{P}\{\text{服务中}\}=\rho$（服务设施忙时占比）。再用 $\bar{N}_Q=\lambda\bar{W}_Q$：

$$
\bar{W}_Q=\lambda\bar{W}_Q\,\mathbb{E}[S]+\rho\,\mathbb{E}[S_e]
=\rho\,\bar{W}_Q+\rho\,\mathbb{E}[S_e]
\ \Rightarrow\ \bar{W}_Q=\frac{\rho}{1-\rho}\,\mathbb{E}[S_e]
$$

**剩余服务期望**（renewal-reward，原文 §23.3–23.4，标准结果）：$\mathbb{E}[S_e]=\dfrac{\mathbb{E}[S^2]}{2\mathbb{E}[S]}=\dfrac{\mathbb{E}[S]}{2}(C_S^2+1)$。代入得 **Pollaczek–Khinchin 公式**（原文式 (23.13)–(23.15)）：

$$
\boxed{\ \bar{W}_Q=\frac{\lambda\,\mathbb{E}[S^2]}{2(1-\rho)}
=\frac{\rho}{1-\rho}\cdot\frac{\mathbb{E}[S^2]}{2\mathbb{E}[S]}
=\frac{\rho}{1-\rho}\cdot\frac{\mathbb{E}[S]}{2}\left(C_S^2+1\right)\ }
$$

$$
\bar{W}=\mathbb{E}[S]+\bar{W}_Q
=\mathbb{E}[S]+\frac{\lambda\,\mathbb{E}[S^2]}{2(1-\rho)}
$$

**关键结论**：延迟由**服务时间二阶矩** $\mathbb{E}[S^2]$（即 $C_S^2$）主导——即使 $\rho$ 很低，若 $C_S^2$ 巨大（重尾），$\bar{W}_Q$ 仍爆炸（例：$\rho=0.5$、$\mathbb{E}[S]=1$、$C_S^2=25$ 时 $\bar{W}_Q=13$，原文 §23.6）。这是 queueing 框架对「平均无阻塞」的根本警示：均值 $\mu$ 不够，还要方差。特例：M/D/1 的 $\bar{W}_Q=\rho/(1-\rho)\cdot(1/(2\mu))$（$M/M/1$ 的一半）。

### 3.5 Jackson 网络（开网络 + 概率路由，product form）

**假设（本节）**：A18 $k$ 个服务器、各指数服务率 $\mu_i$；A19 Poisson 外部到达率 $r_i$（相互独立）；A20 概率路由矩阵 $P=(P_{ij})$（含离网概率 $P_{i,\text{out}}$），路由与服务、到达独立；A21 各队列 $\rho_i=\lambda_i/\mu_i<1$。

**流量方程（原文式 (17.1)）**：总到达率 $\lambda_i$ = 外部 + 内部：

$$
\lambda_i=r_i+\sum_{j=1}^{k}\lambda_j P_{ji}
$$

（解此线性方程组得全部 $\lambda_i$。注意：有反馈时进入各服务器的到达过程**不是** Poisson 过程——原文 §17.2 的反例——故不能用「独立 M/M/1」直接证，需局部平衡。）

**乘积形式（原文 §17.3–17.4）**：稳态分布为

$$
\boxed{\ \pi(n_1,\dots,n_k)=\prod_{i=1}^{k}(1-\rho_i)\,\rho_i^{n_i},\qquad \rho_i=\frac{\lambda_i}{\mu_i}\ }
$$

即各队列「如同独立的 M/M/1」。由局部平衡（local balance）验证此猜测满足全局平衡方程（原文 §17.4，构造 $k+1$ 组局部平衡 $A=A', B_i=B_i'$），故

$$
\bar{N}_i=\frac{\rho_i}{1-\rho_i},\qquad
\bar{W}_i=\frac{\bar{N}_i}{\lambda_i}=\frac{1}{\mu_i-\lambda_i}
$$

这是把单队列结论推广到「多跳交换网络」的现成工具（$\lambda_i$ 由外部到达 + 路由概率解线性方程组得到；闭网络与 BCMP/PS 推广见原文 Ch.19、Ch.22，此处不展开）。

### 3.6 功耗优化（第 27 章，ON/IDLE vs ON/OFF）

**假设（本节）**：A22 M/G/1（FCFS）单服务器；A23 三态静态功耗 $P_{on}>P_{idle}>P_{off}=0$（OFF 态功耗为零）；A24 ON/OFF 策略下每个忙期首个作业经历 setup 时间 $I$（$\mathbb{E}[I],\mathbb{E}[I^2]<\infty$），setup 期间功耗为 $P_{on}$。

**M/G/1 忙期**（原文式 (27.5)/(27.6)）：$\mathbb{E}[B]=\dfrac{\mathbb{E}[S]}{1-\rho}$，$\mathbb{E}[B^2]=\dfrac{\mathbb{E}[S^2]}{(1-\rho)^3}$（由 $B$ 的 Laplace 变换自洽方程 $\widetilde B(s)=\widetilde S(s+\lambda-\lambda\widetilde B(s))$ 求导得到）。

**带 setup 的 M/G/1**（原文式 (27.9)/(27.14)）：含 setup 的忙期 $B^{\text{setup}}$ 由「工作量 $I+S$」启动，故 $\mathbb{E}[B^{\text{setup}}]=\dfrac{\mathbb{E}[I]+\mathbb{E}[S]}{1-\rho}$；由此 busy 时间占比

$$
\rho_{\text{setup}}=\frac{\mathbb{E}[B^{\text{setup}}]}{\mathbb{E}[B^{\text{setup}}]+1/\lambda}
=\frac{\lambda\mathbb{E}[I]+\rho}{\lambda\mathbb{E}[I]+1}
$$

带 setup 的平均排队延迟（原文式 (27.14)，经 $z$-变换/Laplace 变换推导）：

$$
\bar{W}_Q^{\text{setup}}=\frac{\lambda\mathbb{E}[S^2]}{2(1-\rho)}+\frac{2\mathbb{E}[I]+\lambda\mathbb{E}[I^2]}{2(1+\lambda\mathbb{E}[I])}
$$

（$I\sim\mathrm{Exp}(\alpha)$ 时 $\mathbb{E}[I^2]=2\mathbb{E}[I]^2$，退化为加法项 $\bar{W}_Q^{\text{setup}}=\bar{W}_Q+\mathbb{E}[I]$，原文式 (27.15)。）

**ON/IDLE**（原文式 (27.16)/(27.17)）：响应时间 = 无 setup 的 M/G/1；功耗 = 忙时 $P_{on}$ + 闲时 $P_{idle}$：

$$
\mathbb{E}[P]_{\text{ON/IDLE}}=\rho P_{on}+(1-\rho)P_{idle},\qquad
\bar{W}_{\text{ON/IDLE}}=\frac{\lambda\mathbb{E}[S^2]}{2(1-\rho)}+\mathbb{E}[S]
$$

**ON/OFF**（原文式 (27.18)/(27.19)）：OFF 时功耗为 0，ON/SETUP 时功耗 $P_{on}$：

$$
\mathbb{E}[P]_{\text{ON/OFF}}=\rho_{\text{setup}}\,P_{on}
=\frac{\lambda\mathbb{E}[I]+\rho}{\lambda\mathbb{E}[I]+1}\,P_{on}
$$

$$
\bar{W}_{\text{ON/OFF}}=\frac{\lambda\mathbb{E}[S^2]}{2(1-\rho)}+\frac{2\mathbb{E}[I]+\lambda\mathbb{E}[I^2]}{2(1+\lambda\mathbb{E}[I])}+\mathbb{E}[S]
$$

**性能-功耗比**（原文 §27.4）：

$$
\text{Performance-per-Watt}=\frac{1}{\mathbb{E}[P]\cdot\bar{W}}
$$

结论（原文 Table 27.1）：低负载 + 低 setup 开销时 ON/OFF 更优（Perf/W 比可到 ~0.15，即 ON/OFF 约 6× 好）；低负载 + 高 setup 时 ON/IDLE 更优（比可到 ~4.7）。

---

## 4. 模型输出

- $\bar{W},\bar{W}_Q$：平均响应时间 / 平均排队延迟（主输出）。
- $\bar{N},\bar{N}_Q$：平均队长（经 Little's law 与 $\bar{W}$ 互换）。
- $P_Q$（Erlang-C）、$P_{\text{block}}$（Erlang-B）：排队/阻塞概率。
- $X=\lambda$（吞吐）、$\rho$（利用率）、$\mathbb{E}[P]$（平均功耗）、Perf/W。

## 5. 无阻塞与放宽

- **严格无阻塞**：平均框架**不定义**无阻塞（不给最坏保证）。稳定条件 $\rho<1$ 只保证「平均不拥塞」——存在非空的稳态分布。
- **放宽路径**：$\rho<1$ 给「平均无阻塞」（有限平均延迟），但 P-K 显示远非充分——$\mathbb{E}[S^2]$（服务变异）巨大时即使 $\rho$ 很低延迟也爆炸（重尾警告，第 20、23 章）。要「差不多无阻塞」，除 $\rho<1$ 外还需服务变异小（$C_S^2$ 低）。调度策略（PS/SRPT/优先级，第 30–33 章）是另一条放宽手段：不增加资源、靠重排服务顺序降延迟（如 SRPT 对重尾工作负载可显著优于 FCFS/PS）。

## 6. 功耗地位

**有，但只有静态状态功耗**：$P_{on}/P_{idle}/P_{off}$ 三态 + 开机 setup 成本（第 27 章）。对应我们功耗模型里的「静态 $P_0$」项，且是**常数三态**，不随负载连续变化；ON/OFF 的功耗表达式中 $\rho_{\text{setup}}=\dfrac{\lambda\mathbb{E}[I]+\rho}{\lambda\mathbb{E}[I]+1}$ 是唯一的负载相关因子。

**缺失**：没有 per-lane 线性项（$\boldsymbol{\ell}$ 相关）、没有 radix² 超线性项（核心交换功耗随 radix 平方增长）。因此它无法回答「多开一个 lane / 提高 radix 的功耗代价」——那是我们 `real_chip_catalog` 里才有的事。

## 7. 与我们的对照

| 维度 | Queueing | 我们（00_ours） |
|------|---------|----------------|
| 输出 | $\bar{W},\bar{N}$（均值） | $B^*$（无阻塞带宽）+ $\mathbf{L}$ |
| 确定性/平均 | 平均（稳态） | 确定性（worst-case） |
| 需求结构体 | $\lambda$（或 $\lambda_{ij}$）、服务分布 $S$ | 排列 $\mathbf{P}$ |
| 供给 | $\mu$（服务率，$=B\cdot S_{\text{bw}}$ 的随机版） | lane/bump/热约束 |
| 功耗 | 静态三态 + setup（$P_0$ 级） | 线性 + 静态（缺 radix²） |
| 拓扑 | 单队列 / server farm / Jackson 网络 | vertex-transitive + 群论归约 |

**可借鉴点**：① 符号桥梁 $\lambda_{ij}\leftrightarrow D_{ij}$、$\mu\leftrightarrow B\cdot S_{\text{bw}}$、$\rho=\lambda/\mu$ 已在统一符号下打通；② P-K 的 $\mathbb{E}[S^2]$ 项提醒：我们的 $\mathbf{L}$ 包络若只给**均值**负载会低估延迟——最坏排列 + 服务时间变异需同时纳入；③ Perf/W $=1/(\mathbb{E}[P]\cdot\bar{W})$ 是现成的「性能-功耗」联合指标，可移植到我们的「$B^*$ 每瓦」；④ Jackson product form 是「$n$ 端口交换网络」多队列联立的现成工具（对应把我们的 $\mathbf{L}$ 包络换成逐链路 $\rho_i$）。

**缺口**：无 radix² 超线性功耗、无热、无无阻塞带宽 $B^*$；平均指标无法给「所有 admissible 流量都能支撑」的保证（那是我们 Birkhoff + LP 的独有位置）。
