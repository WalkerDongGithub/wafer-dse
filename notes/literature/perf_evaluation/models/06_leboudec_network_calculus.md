# 06 Le Boudec & Thiran —— 网络演算（确定性延迟/积压界）

> 确定性（worst-case）队列系统理论。给定「流量上界」（arrival curve $\alpha$）与「节点服务下界」（service curve $\beta$），用 min-plus 代数给出**任何**满足约束的流量样本路径都成立的最坏情况延迟上界 $h(\alpha,\beta)$ 与积压（缓冲）上界 $v(\alpha,\beta)$——给上界而非平均值。

## 0. 符号表（本节所有符号在此定义）

| 符号 | 定义（含取值域 / 单位） |
|------|------------------------|
| $t,s,u\in\mathbb{R}_{\ge0}$（或 $\mathbb{Z}_{\ge0}$） | 时间（连续或离散；离散模型经线性插值映射到连续，全书结果两者通用） |
| $\mathbf{R}(t)$ | 累计到达函数：$[0,t]$ 内到达的比特数，宽增（$s\le t\Rightarrow \mathbf{R}(s)\le\mathbf{R}(t)$）、$\mathbf{R}(0)=0$、左连续（约定）。单位：数据量（bit / cell） |
| $\mathbf{R}^*(t)$ | 累计离开函数：$[0,t]$ 内离开系统的比特数，同上约定 |
| $d(t)$ | 虚拟延迟（virtual delay）：$t$ 时刻到达的比特经历的延迟。单位：时间 |
| $\alpha(t)$ | arrival curve（需求上界）：宽增函数，$\alpha:\mathbb{R}_{\ge0}\to\mathbb{R}_{\ge0}\cup\{+\infty\}$ |
| $\gamma_{r,b}(t)$ | 仿射（leaky-bucket）到达曲线：$r$ = 可持续速率，$b$ = 突发容忍 |
| $v_{P,\tau}(t)$ | 阶梯（stair）到达曲线：$P$ = 周期（interval），$\tau$ = 容忍（tolerance） |
| $\beta(t)$ | service curve（供给下界）：宽增、$\beta(0)=0$ |
| $\beta_{\mu,\theta}(t)$ | rate-latency 服务曲线：$\mu$ = 服务率（常量），$\theta$ = 服务延迟（latency） |
| $\delta_\theta(t)$ | 延迟脉冲函数：$\delta_\theta(t)=0\ (t\le \theta)$，$\delta_\theta(t)=+\infty\ (t>\theta)$ |
| $\otimes$ | min-plus 卷积：$(f\otimes g)(t)=\inf_{0\le s\le t}\{f(s)+g(t-s)\}$ |
| $\oslash$ | min-plus 反卷积：$(f\oslash g)(t)=\sup_{u\ge0}\{f(t+u)-g(u)\}$ |
| $h(\alpha,\beta)$ | 水平偏差（延迟界）：$h=\sup_{t\ge0}\inf\{d\ge0:\alpha(t)\le\beta(t+d)\}$ |
| $v(\alpha,\beta)$ | 垂直偏差（积压界）：$v=\sup_{t\ge0}\{\alpha(t)-\beta(t)\}$ |
| $r,\ b$ | leaky bucket 参数：可持续速率（数据/时间）、突发容忍（数据） |
| $\mu,\ \theta$ | rate-latency 参数：服务率（数据/时间）、延迟参数（时间） |
| $C,\ L_{\max},\ \phi_i$ | GPS/GR 调度器：总速率、最大包长、流 $i$ 的权重 |

> **与统一符号的对应**：$r \leftrightarrow \lambda$（可持续到达率），$\mu$ 即统一符号表的服务率（$B\cdot S_{\text{bw}}$ 的时序化），$\alpha \leftrightarrow \mathbf{D}$ 的「时序化」（给累计到达在任意窗口上的增量上界，而非静态矩阵），$\beta \leftrightarrow$ 供给 $B\cdot S_{\text{bw}}$ 的时序化。$h$、$v$ 即统一符号表的延迟界、积压界。

---

## 1. 模型定位

给定「流量上界 $\alpha$」与「节点服务下界 $\beta$」，求**最坏情况下**端到端延迟上界 $h(\alpha,\beta)$ 和缓冲区需求上界 $v(\alpha,\beta)$。与 queueing 理论（给均值）互补：网络演算给的是**确定性界**——任何满足 $\alpha$ 约束的到达样本路径、任何提供 $\beta$ 服务的系统，其延迟与积压都不超过该界。

## 2. 全书共同假设（显式）

- **A1 流量用累计函数描述**：一条流由累计到达函数 $\mathbf{R}(t)$ 完全描述，$\mathbf{R}(0)=0$ 且宽增。
- **A2 无损耗系统**：系统 lossless（缓冲无限、不丢包）；输入 $\mathbf{R}$ 与输出 $\mathbf{R}^*$ 可同时观测。
- **A3 因果**：$\mathbf{R}^*(t)\le\mathbf{R}(t)$（输出不超过输入；系统不能「预支」未到达的数据）。
- **A4 时间域**：$t\in\mathbb{R}_{\ge0}$（连续）或 $\mathbb{Z}_{\ge0}$（离散）；离散模型按 $\mathbf{R}$ 在时隙间线性插值映射到连续，故下文结论两者通用（见原文 §1.1.1 式 (1.1)）。

---

## 3. 核心数学模型

### 3.1 累计到达、积压与虚拟延迟（基础量）

由输入/输出函数直接导出两个量（原文 Definition 1.1.1）：

$$
\text{积压（backlog）}\ \mathbf{R}(t)-\mathbf{R}^*(t),\qquad
d(t)=\inf\{d\ge0:\ \mathbf{R}(t)\le\mathbf{R}^*(t+d)\}
$$

积压是 $t$ 时刻系统内滞留的数据量（单缓冲即队列长度）；虚拟延迟是「$t$ 时刻到达的比特在它之前所有比特都被服务后」经历的延迟。流模型下（输入输出连续），$d(t)$ 是使 $\mathbf{R}(t)=\mathbf{R}^*(t+d)$ 成立的最小值。积压 = 输入输出函数间的**垂直**距离，虚拟延迟 = **水平**距离。

### 3.2 arrival curve $\alpha$（需求上界）

**假设（本节）**：A5 $\alpha$ 宽增、定义于 $t\ge0$。

**定义 3.2（arrival curve，原文 Definition 1.2.1）**：流 $\mathbf{R}$ 被 $\alpha$ 约束（记作 $\mathbf{R}$ 是 $\alpha$-smooth），当且仅当对任意 $s\le t$：

$$
\mathbf{R}(t)-\mathbf{R}(s)\le\alpha(t-s)
$$

即在**任意**宽度 $t-s$ 的窗口内，到达量不超过 $\alpha(t-s)$。常用的「good function」要求：$\alpha$ 宽增、次可加（$\alpha(t+s)\le\alpha(t)+\alpha(s)$）、$\alpha(0)=0$。

**（a）仿射曲线 / leaky bucket**：

$$
\gamma_{r,b}(t)=rt+b\ \ (t>0),\qquad \gamma_{r,b}(0)=0
$$

$b$ = 突发容忍（数据单位），$r$ = 可持续速率（数据/时间单位）。$\gamma_{r,b}$ 允许源一次突发 $b$，长期速率不超过 $r$。**等价刻画**（原文 Lemma 1.2.2 及其推论）：一个以速率 $r$ 漏空、容量 $b$ 的 leaky bucket 控制器，恰强制流量满足到达曲线 $\gamma_{r,b}$——凡使桶溢出的数据判为 non-conformant。$\gamma_{0,b}$ 表示「总流量至多 $b$」；$\gamma_{r,0}$ 表示峰值速率 $r$ 受限。

**（b）阶梯函数 / GCRA**：定长分组（尺寸 $k$，如 ATM cell $k=1$）按最小间隔 $P$ 到达，则到达曲线为 $k\,v_{P,\tau}$，其中

$$
v_{P,\tau}(t)=\left\lceil\frac{t+\tau}{T}\right\rceil\ (t>0),\qquad v_{P,\tau}(0)=0
$$

$\lceil x\rceil$ 为不小于 $x$ 的最小整数。**周期流 + 有界抖动**（原文 Proposition 1.2.1）：周期 $P$、定长 $k$、端到端抖动 $\le\tau$ 的流，有 $k\,v_{P,\tau}$ 作为到达曲线。GCRA$(P,\tau)$ 控制器对应此约束。

**（c）定长分组下仿射与阶梯等价**（原文 Proposition 1.2.2）：若分组尺寸恒为 $k$，取 $r=k/P$、$b=k\tau/P$（即 $\tau=b/r$），则 $\gamma_{r,b}$ 与 $k\,v_{P,\tau}$ 对 $\mathbf{R}$ 的约束**等价**。注意：仅当分组尺寸 $k$ 等于阶梯步长时二者等价；多条 ATM 流的聚合不再满足此条件（见原文 §1.4.1 的 ATM 例子）。

**（d）次可加闭包（sub-additive closure）**：任意 $\alpha$ 可用其次可加闭包 $\bar\alpha$ 替换——$\bar\alpha=\inf_{n\ge0}\alpha^{(n)}$，其中 $\alpha^{(0)}=\delta_0$（恒等元）、$\alpha^{(n)}=\alpha\otimes\alpha^{(n-1)}$。约束 $\mathbf{R}\le\alpha$ 与 $\mathbf{R}\le\bar\alpha$ **等价**，且 $\bar\alpha$ 是「good」函数、更紧。

### 3.3 service curve $\beta$（供给下界）

**假设（本节）**：A6 $\beta$ 宽增、$\beta(0)=0$。

**定义 3.3（service curve，原文 Definition 1.3.1）**：系统 $\mathcal{S}$ 对流提供 service curve $\beta$，当且仅当 $\beta(0)=0$ 且对任意 $t\ge0$：

$$
\mathbf{R}^*(t)\ \ge\ (\mathbf{R}\otimes\beta)(t)=\inf_{0\le s\le t}\{\mathbf{R}(s)+\beta(t-s)\}
$$

几何意义：输出 $\mathbf{R}^*$ 必须位于所有曲线 $s\mapsto\mathbf{R}(s)+\beta(t-s)$ 的下包络之上。若 $\beta$ 连续，性质等价于「对任意 $t$ 存在 $s_0\le t$ 使 $\mathbf{R}^*(t)\ge\mathbf{R}(s_0)+\beta(t-s_0)$」（原文 Proposition 1.3.1）。

**（a）strict service curve（原文 Definition 1.3.2）**：若在任意时长 $u$ 的忙期（backlogged period）内输出至少 $\beta(u)$，则称 $\mathcal{S}$ 提供 strict service curve $\beta$。strict service curve $\Rightarrow$ service curve（原文 Proposition 1.3.5）；但反向不成立（贪婪整形器提供其整形曲线作为 service curve，却不满足 strict 性质）。

**（b）rate-latency 曲线**（最常用，GPS / Intserv 节点的标准抽象）：

$$
\beta_{\mu,\theta}(t)=\mu\,[t-\theta]^+=\max(0,\ \mu(t-\theta))
$$

$\mu$ = 服务率，$\theta$ = 延迟参数。其物理来源（原文 Proposition 1.3.4）：速率 $C$ 的服务器对**高优先级**流提供 $\beta_{C,\ L_{\max}^L/C}$（$L_{\max}^L$ 为低优先级最大包长）；对**低优先级**流（若高优先级被 $\gamma_{r,b}$ 约束且 $r<C$）提供 $\beta_{C-r,\ \theta}$ 形式的 rate-latency 曲线（$\theta$ 的闭式见原文 Proposition 1.3.4）。延迟上界 $\theta$ 的节点等价于 service curve $\delta_\theta$（原文 Proposition 1.3.3）。

**（c）VBR / TSPEC**：Intserv 的 TSPEC$(p,M,r,b)$ 对应到达曲线

$$
\alpha(t)=\min(pt+M,\ rt+b)\ \ (t>0),\qquad \alpha(0)=0
$$

（$p$ 峰值速率、$M$ 最大包长、$r$ 可持续速率、$b$ 突发容忍，$p\ge r$，$M\le b$）。它是 $\gamma_{p,M}$ 与 $\gamma_{r,b}$ 的逐点 $\min$（$\wedge$），也是 good 函数。

### 3.4 min-plus 工具：$\otimes$、$\oslash$、$\delta_\theta$

- **dioid**：在 $(\mathbb{R}\cup\{+\infty\},\wedge,+)$ 上，$+$ 是「乘法」、$\wedge$（取 $\min$）是「加法」；$\varepsilon=+\infty$ 是零元，$0$ 是单位元。
- **卷积**（对应「级联」）：$(f\otimes g)(t)=\inf_{0\le s\le t}\{f(s)+g(t-s)\}$。满足结合律、交换律、对 $\wedge$ 分配律；$\delta_0$ 是恒等元（$f\otimes\delta_0=f$），$\delta_\theta\otimes f$ 是 $f$ 右移 $\theta$。
- **反卷积**（用于输出曲线 / 最小到达曲线）：$(f\oslash g)(t)=\sup_{u\ge0}\{f(t+u)-g(u)\}$。
- **偏差**：垂直偏差 $v(\alpha,\beta)=\sup_{t\ge0}\{\alpha(t)-\beta(t)\}$；水平偏差 $h(\alpha,\beta)=\sup_{t\ge0}\inf\{d\ge0:\alpha(t)\le\beta(t+d)\}$（即把 $\alpha,\beta$ 当作虚拟系统的输入/输出时的虚拟延迟上确界）。

### 3.5 三个界（核心结论）

**假设（本节）**：A7 流 $\mathbf{R}$ 被 $\alpha$ 约束；A8 系统提供 service curve $\beta$；A9 系统 lossless（A2）。

**① 积压界（原文 Theorem 1.4.1）**：

$$
\boxed{\ \mathbf{R}(t)-\mathbf{R}^*(t)\ \le\ v(\alpha,\beta)\ }
$$

**推导（每步写明依据）**：固定 $t$，由 service curve 取（或 $\varepsilon$-逼近）下确界元 $s\le t$：

$$
\mathbf{R}^*(t)\ \ge\ \mathbf{R}(s)+\beta(t-s)\ \ge\ \underbrace{\mathbf{R}(t)-\alpha(t-s)}_{\text{由 }\alpha\text{ 约束：}\mathbf{R}(t)-\mathbf{R}(s)\le\alpha(t-s)}+\ \beta(t-s)
$$

于是 $\mathbf{R}(t)-\mathbf{R}^*(t)\le\alpha(t-s)-\beta(t-s)\le\sup_{u\ge0}\{\alpha(u)-\beta(u)\}=v(\alpha,\beta)$。∎

**② 延迟界（原文 Theorem 1.4.2）**：

$$
\boxed{\ d(t)\ \le\ h(\alpha,\beta)\ }
$$

**推导**：令 $d=h(\alpha,\beta)$。由 service curve 在时刻 $t+d$ 的下界：

$$
\mathbf{R}^*(t+d)\ge\inf_{0\le s\le t+d}\{\mathbf{R}(s)+\beta(t+d-s)\}
$$

只需证该下确界 $\ge\mathbf{R}(t)$。对**任意** $s\in[0,t+d]$：

- 若 $s\le t$：由 arrival curve 有 $\mathbf{R}(s)\ge\mathbf{R}(t)-\alpha(t-s)$；由 $d=h(\alpha,\beta)$ 的定义又有 $\alpha(t-s)\le\beta(d+(t-s))$，故
$$\mathbf{R}(s)+\beta(t+d-s)\ \ge\ \mathbf{R}(t)-\alpha(t-s)+\beta(d+(t-s))\ \ge\ \mathbf{R}(t)$$
- 若 $t<s\le t+d$：由宽增性 $\mathbf{R}(s)\ge\mathbf{R}(t)$，且 $\beta\ge0$，故 $\mathbf{R}(s)+\beta(t+d-s)\ge\mathbf{R}(t)$。

于是 $\inf_{0\le s\le t+d}\{\mathbf{R}(s)+\beta(t+d-s)\}\ge\mathbf{R}(t)$，即 $\mathbf{R}^*(t+d)\ge\mathbf{R}(t)$。再由 $d(t)$ 的定义得 $d(t)\le d=h(\alpha,\beta)$。∎

**③ 输出到达曲线（原文 Theorem 1.4.3）**：输出流 $\mathbf{R}^*$ 有到达曲线

$$
\boxed{\ \alpha^*=\alpha\oslash\beta\ }
$$

**推导**：对任意 $s\le t$，因果性（A3）给 $\mathbf{R}^*(t)-\mathbf{R}^*(s)\le\mathbf{R}(t)-\mathbf{R}^*(s)$；service curve 给 $-\mathbf{R}^*(s)\le-\inf_{0\le u\le s}\{\mathbf{R}(u)+\beta(s-u)\}$，故

$$
\mathbf{R}^*(t)-\mathbf{R}^*(s)\ \le\ \sup_{0\le u\le s}\{\mathbf{R}(t)-\mathbf{R}(u)-\beta(s-u)\}
\ \le\ \sup_{0\le u\le s}\{\alpha(t-u)-\beta(s-u)\}
$$

（最后一步用 $\mathbf{R}(t)-\mathbf{R}(u)\le\alpha(t-u)$）。换元 $v=s-u\ge0$：$\alpha(t-u)-\beta(s-u)=\alpha((t-s)+v)-\beta(v)$，其中 $v\in[0,s]$，故上确界 $\le\sup_{v\ge0}\{\alpha((t-s)+v)-\beta(v)\}=(\alpha\oslash\beta)(t-s)$。∎

**界的紧性**：当 $\alpha$ 为 good 函数、$\beta$ 宽增且 $\beta(0)=0$ 时，积压界与延迟界是**紧的**（存在因果系统与贪婪源同时达到两界，原文 Theorem 1.4.4）；输出界在 $\beta$ 左连续、$\alpha$ 无上界的附加条件下也紧（原文 Theorem 1.4.5，证明技术性较强，见原文 §1.9）。

**特例：leaky bucket $\gamma_{r,b}$ + rate-latency $\beta_{\mu,\theta}$（$r\le \mu$）**：

$$
v(\gamma_{r,b},\beta_{\mu,\theta})=b+r\theta,\qquad
h(\gamma_{r,b},\beta_{\mu,\theta})=\theta+\frac{b}{\mu}
$$

**推导（$v$）**：$\sup_{t\ge0}\{\gamma_{r,b}(t)-\beta_{\mu,\theta}(t)\}=\sup_{t\ge0}\{b+rt-\mu[t-\theta]^+\}$。$t\le \theta$ 时为 $b+rt$（增），最大值在 $t=\theta$ 取 $b+r\theta$；$t\ge \theta$ 时为 $b+r\theta+(r-\mu)(t-\theta)\le b+r\theta$（因 $r\le \mu$）。故上确界 $=b+r\theta$。∎

**推导（$h$）**：需 $\inf\{d:b+rt\le \mu[t+d-\theta]^+\}$。$t\le \theta$ 时解得 $d=\theta-t+(b+rt)/\mu=\theta+b/\mu+t(r/\mu-1)$，因 $r/\mu\le1$ 在 $t=0$ 取最大值 $\theta+b/\mu$；$t\ge \theta$ 时 $d\ge \theta-t+(b+rt)/\mu=\theta+b/\mu+t(r/\mu-1)$，因 $r/\mu\le1$ 在 $t=\theta$ 取最大值 $\theta(r/\mu)+b/\mu\le \theta+b/\mu$。故上确界 $=\theta+b/\mu$。∎

若 $r>\mu$，两界均为 $+\infty$（供给无法消化需求）。对 TSPEC 曲线 $\alpha=\gamma_{p,M}\wedge\gamma_{r,b}$ 的闭式界见原文 Proposition 1.4.1（缓冲界与延迟界在 $\alpha$ 或 $\beta$ 的角点处取得，本书 §1.4.1 给出 Intserv 闭式），此处不展开以防记错。

### 3.6 级联与「pay bursts only once」

**假设（本节）**：A10 流依次经过两个（或多个）系统，前一节点的输出恰为后一节点的输入。

**级联定理（原文 Theorem 1.4.6）**：节点 1、2 分别提供 $\beta_1,\beta_2$，则串联整体提供

$$
\boxed{\ \beta=\beta_1\otimes\beta_2\ }
$$

**推导**：记 $\mathbf{R}_1$ 为节点 1 输出（=节点 2 输入）。$\mathbf{R}_1(t)\ge(\mathbf{R}\otimes\beta_1)(t)$，且 $\mathbf{R}^*(t)\ge(\mathbf{R}_1\otimes\beta_2)(t)$。由 $\otimes$ 的结合性、对 $\wedge$ 分配性与单调性：

$$
\mathbf{R}^*(t)\ \ge\ ((\mathbf{R}\otimes\beta_1)\otimes\beta_2)(t)=(\mathbf{R}\otimes(\beta_1\otimes\beta_2))(t)
$$

即串联整体提供 $\beta_1\otimes\beta_2$。∎

**两个 rate-latency 节点**：$\beta_i=\beta_{\mu_i,\theta_i}$ 时（原文 §1.4.3 计算）：

$$
\beta_{\mu_1,\theta_1}\otimes\beta_{\mu_2,\theta_2}=\beta_{\min(\mu_1,\mu_2),\ \theta_1+\theta_2}
$$

即**速率取 min、延迟相加**。同理 rate-latency 可分解为「延迟 $\delta_\theta$ 与恒速服务器 $\beta_{\mu,0}$ 的级联」。

**pay bursts only once**：端到端延迟界（全局 service curve + 定理 1.4.2）为

$$
h_{\text{end}}=\theta_1+\theta_2+\frac{b}{\min(\mu_1,\mu_2)}
$$

而逐节点迭代（先算节点 1 界 $\theta_1+b/\mu_1$，再算其输出曲线 $\gamma_{r,\,b+r\theta_1}$ 过节点 2 的界）得

$$
h_{\text{per-node}}=\theta_1+\theta_2+\frac{b}{R_1}+\frac{b+r\theta_1}{R_2}\ \ge\ h_{\text{end}}
$$

全局界更紧：突发项 $b/\min(\mu_1,\mu_2)$ 只出现一次（「只付一次突发」），且节点 1 造成的突发增大 $rT_1$ 不再转化为端到端延迟增量。端到端延迟界与节点顺序无关（定理 1.4.6 的推论）。

### 3.7 GPS / GR 调度器（rate-latency 的现实来源）

**假设（本节）**：A11 分组化到达；调度器工作保持（work-conserving）或为 GR 型。

- **GPS**（原文 §2.1.2）：流 $i$ 获得权重 $\phi_i$ 对应的服务率 $\mu_i=\frac{\phi_i}{\sum_j\phi_j}C$，GPS 节点对流 $i$ 提供 rate-latency service curve $\beta_{\mu_i,\ \theta}$，其中 $\theta=L_{\max}/C$（$L_{\max}$ 为最大包长，$C$ 为总速率）。
- **GR 调度器**（原文 Definition 2.1.1 / Theorem 2.1.1）：速率为 $\mu$、延迟为 $E$ 的 guaranteed-rate 调度器等价于「service curve $\beta_{\mu,E}$ 的元素 + 分组器」的级联，故提供最小 service curve $\beta_{\mu,E}$（原文 Corollary 2.1.1）。PGPS 是 GR 调度器（Proposition 2.1.1）。
- **Intserv 路由器模型**（原文 Fact 2.2.1）：路由器对流提供的 service curve 恒为 rate-latency 型，参数满足 $\theta=E+L_{\max}/C$ 型关系（$E$ 为调度器延迟）。对 $\gamma_{r,b}$ 约束的流过一串 GR 节点的端到端延迟闭式见原文式 (2.5)。

---

## 4. 模型输出

- $h(\alpha,\beta)$：端到端**延迟上界**（主输出；对 $\gamma_{r,b}+\beta_{\mu,\theta}$ 为 $\theta+b/\mu$）。
- $v(\alpha,\beta)$：**积压/缓冲上界**（即所需缓冲容量；对 $\gamma_{r,b}+\beta_{\mu,\theta}$ 为 $b+r\theta$）。
- $\alpha^*=\alpha\oslash\beta$：输出流的 arrival curve（供下一跳继续计算；对 $\gamma_{r,b}$ 过 $\beta_{\mu,\theta}$ 为 $\gamma_{r,\,b+r\theta}$——突发被放大 $rT$）。
- 端到端 service curve $\beta_1\otimes\beta_2$（级联），以及 GPS/GR 节点给出的 rate-latency 参数。

## 5. 无阻塞与放宽

- **严格无阻塞的确定性对应物**：框架不定义「无阻塞」，但存在确定性对应——若 $\alpha(t)\le\beta(t)$ 对任意 $t\ge0$（需求曲线被供给曲线**逐点覆盖**），则 $v=h=0$（零积压、零延迟），即最坏流量下也无排队。这是「供给处处不小于需求」的强版本，比我们的 Birkhoff 排列判据更强（充分不必要）。
- **放宽路径**：① 级联定理本身即最强放宽之一（不必逐节点重付 burst）；② aggregate scheduling（第 6 章，FIFO 汇聚、流不隔离）给更松但有限的界，并有环形网络稳定性的讨论；③ 有损系统（第 9 章）放宽 lossless 假设，转给 loss rate 上界；④ adaptive / packet-scale rate guarantee（第 7 章）放宽「恒速」到包粒度。条件 $r\le \mu$（即 $\rho<1$）是 $h,v$ 有限的前提——满足即「差不多无阻塞」，不满足则界发散。

## 6. 功耗地位

**完全不建模**。全书无功耗、lane 数 $\boldsymbol{\ell}$、radix²、热等任何物理代价概念。service curve 的 $\mu$ 只作为「服务率」出现，与它背后的物理实现（多少 lane、多少功耗）无关联；GPS 的权重 $\phi_i$ 是调度共享比例，不是物理资源。

## 7. 与我们的对照

| 维度 | 网络演算 | 我们（00_ours） |
|------|---------|----------------|
| 确定性框架 | ✅ worst-case 界 | ✅ worst-case（枚举最坏排列） |
| 输出 | $h$（延迟界）+ $v$（积压界） | $B^*$（无阻塞带宽）+ $\mathbf{L}$ |
| 需求结构体 | $\alpha(t)$（$\mathbf{D}$ 的时序化） | 排列 $\mathbf{P}$（$\mathbf{D}$ 的最坏代表） |
| 供给 | $\beta(t)$（$\mu=B\cdot S_{\text{bw}}$ 的时序化） | lane/bump/热约束下的物理资源 |
| 功耗 | ❌ | ✅（线性 + 静态） |
| 拓扑 | 节点串接（抽象，级联定理） | vertex-transitive（群论归约） |

**可借鉴点**：$h(\alpha,\beta)$ 是「带宽 × 延迟」空缺格子的现成入口（见 `01_CORE_MATHEMATICAL_MODELS.md` §2.1）——把我们的 $\beta$ 写成 $\beta_{\mu,\theta}(t)=\mu[t-\theta]^+$、把最坏排列流量写成 $\alpha(t)=\gamma_{r,b}(t)$，即可在同一确定性框架里同时读出 $B^*$（由 $\mu$ 反解）和延迟界 $\theta+b/\mu$。

**缺口**：不联立功耗/热（$R$ 背后的物理代价缺失）；单流模型需扩展为 $n$ 端口交换矩阵（多流竞争同一链路时 $\beta$ 的共享问题，对应我们的 $\mathbf{L}$ 包络）；「$\alpha\le\beta$ 逐点覆盖」的无阻塞判据强于 Birkhoff 判据（充分不必要），无法直接给出可解 LP。
