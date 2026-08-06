# 晶圆级交换机的 Clos 分解与无阻塞带宽最大化

> 本文取代 [NONBLOCKING_LP_EXPLAINED.md](NONBLOCKING_LP_EXPLAINED.md) 中的性能模型。
> 核心变化：无阻塞不再是"用 LP 证明"，而是"用 Clos 构造保证"。
> DSE 的目标从"判断 feasible 与否"变为"最大化无阻塞带宽 $B$"。

---

## 0. 物理前提：interposer 是最小重复单元

晶圆被划分为 $N$ 个完全相同的 interposer，每个 interposer 是一个物理基板，
集成若干 die 并通过高密度 $\mu$bump 互联。

每个 interposer 对外提供两类接口：

| 接口 | 数量 | 连接对象 | 物理介质 | 每 lane 速率 | 每 bit 功耗 |
|------|------|---------|---------|-------------|-----------|
| **外部端口** | $M$ | 外部网络（其他交换机/服务器） | 面板 SerDes/光口 | 112 Gbps | 15-20 pJ |
| **内部上联** | $K$ | 其他 interposer | 晶圆内 SerDes/UCIe | 32-112 Gbps | 0.25-5 pJ |

**$K$ 的上限由物理约束决定**（bump 预算、功耗、热），这正是 DSE 要回答的问题。

整个晶圆级交换机 = $N$ 个 interposer × $M$ 端口 = 总共 $N \times M$ 个外部端口。

---

## 1. 分层无阻塞构造

### 1.1 内层：interposer 内部

每个 interposer 内部是一个 $M \times K$ 的小型交换网络：
- $M$ 个外部端口进，$K$ 个上联端口出（入方向同理）
- 内部互联距离 ≤ interposer 尺寸（~50mm），使用 UCIe Advanced 等高密度低功耗互联

**构造性无阻塞**：在 interposer 内部，$M$ 和 $K$ 的规模（几十到几百）使得
crossbar 或 fat-tree 在面积和功耗上都可行。这不是要"证明"的——选已知的非阻塞
拓扑即可。

判据（严格无阻塞）：内部 crossbar 有 $M \times K$ 个 crosspoint，
每个端口速率 $B$。Crossbar 本身不引入内部阻塞（单个 crossbar slice 是严格无阻塞的）。

**内层不是 DSE 的求解对象。它是构造。**

### 1.2 外层：interposer 之间

外层是 $N$ 个节点、每节点度 $K$ 的网络。
总交换容量 = $N \times M$ 端口 × $B$ 速率。

**关键洞察**：$N$ 个完全相同的节点、每节点度 $K$，恰好是 Clos 网络的输入/输出级。

三阶折叠 Clos：

```
Stage 1 (输入): N 个 M×K 模块  ← 每个 interposer 的入口侧
Stage 2 (中间): K 个 N×N 模块  ← 分布式实现在各 interposer 上
Stage 3 (输出): N 个 K×M 模块  ← 每个 interposer 的出口侧
```

其中 Stage 2 的 $K$ 个 $N \times N$ 模块**不是独立硬件**——它们分布实现在
$N$ 个 interposer 的剩余交换容量上。每个 interposer 同时扮演 Stage 1、Stage 2
（部分）、Stage 3 三个角色。

---

## 2. 无阻塞条件（图论，O(1)，不进入 LP）

### 2.1 Clos 条件

**定理**（Slepian-Duguid, 1959 / Clos, 1953）：

对于 $M$ 个入口、$K$ 条中间路径、$M$ 个出口的三阶 Clos 网络：

| 条件 | 含义 | 工程选择 |
|------|------|---------|
| $K \ge M$ | 可重排无阻塞（需要调度算法重新排列已有连接） | 需重排逻辑 |
| $K \ge 2M-1$ | 严格无阻塞（新连接永远能找到空闲路径） | 无重排，但硬件成本翻倍 |

**对 DSE 的意义**：选定 $K/M$ 的比值，无阻塞性立即由定理保证。
不需要 LP 证明、不需要检查所有排列、不需要对策论。

### 2.2 外层链路负载：确定性

在 Clos 构造下，外层每条链路的负载是**确定的**，不是对手可操纵的变量：

- 每个 interposer 有 $K$ 条外层链路
- 每条外层链路承载 $B$ 的流量（Clos 中间级的每条链路在重排后恰好承载一个端口带宽）
- 物理 lane 数：$\ell = B / R$，其中 $R$ 是互联标准的单 lane 速率

**没有"对手选排列"这一层。** Clos 构造已经处理了全部 $N!$ 种排列——
这是 Clos 定理的结论。物理层只需要承受确定的负载。

### 2.3 可选的拓扑族

Clos 是**构造模板**，不是唯一选择。外层拓扑可以用不同的方式实现中间级：

| 外层构造 | 度需求 $K$ | 单链路负载 | 适用场景 |
|---------|-----------|-----------|---------|
| 折叠 Clos（分布式中间级） | $\ge M$（可重排）或 $\ge 2M-1$（严格） | $B/$lane | $N \le K$ |
| 全网格（无中间级，直连） | $N-1$ | $M \times B$ | $N$ 小（≤8） |
| Dragonfly（Valiant 中转） | $h \ge 1$ | $B/$lane（中转分摊） | $N$ 大（≥16） |
| Benes（多级 Clos，$\log N$ 级） | $2$ | $B/$lane | $N$ 很大（≥64），多跳 |

**DSE 外层枚举这些构造族，内层 LP 检查同一个东西：物理约束是否支撑所需的 $B$ 和 lane 数。**

---

## 3. 统一 LP：最大化无阻塞带宽

### 3.1 变量

| 变量 | 含义 | 维度 |
|------|------|------|
| $B$ | 每端口无阻塞带宽（**优化目标**） | 标量 |
| $\mathbf{L} = (L_e)_{e \in \mathcal{E}_{\text{outer}}}$ | 每条外层链路的归一化负载 | $|\mathcal{E}_{\text{outer}}|$ |
| $\boldsymbol{\ell} = (\ell_e)$ | 每条外层链路的物理 lane 数 | $|\mathcal{E}_{\text{outer}}|$ |
| $\mathbf{P} = (P_v)_{v=1}^N$ | 每个 interposer 的总功耗 | $N$ |

### 3.2 性能约束：由构造决定

外层链路负载由选定的构造族唯一确定，**是常数下界，不是优化变量**：

$$L_e \ge L_e^{\text{min}}(\text{构造}) \quad \forall e \in \mathcal{E}_{\text{outer}}$$

例如：
- 折叠 Clos ($K=M$)：$L_e^{\text{min}} = 1$（每条外层链路承载一个端口的流量）
- 全网格：$L_{ij}^{\text{min}} = M$（$(i,j)$ 链路承载 $i$ 全部 $M$ 个端口到 $j$ 的流量）
- Dragonfly ($a,p,h$)：$L_e^{\text{min}}$ 由松弛 LP（$\min_{D,f} \max_e L_e$）给出乐观下界

**性能约束退化为常数下界** $\mathbf{L} \ge \mathbf{L}^{\text{min}}$。没有 min-max，没有对策论。

### 3.3 物理 lane 数

$$\ell_e = L_e \cdot \frac{B}{R_e}$$

$R_e$ 由链路 $e$ 的物理长度对应的互联标准决定（外层固定后为常数）。

### 3.4 几何约束：bump 预算

每个 interposer $v$ 的信号 bump 消耗（发射 + 接收）：

$$\sum_{e \in \delta_{\text{out}}(v)} \ell_e + \sum_{e \in \delta_{\text{in}}(v)} \ell_e \le N_v^{\text{sig}}$$

其中 $\ell_e = L_e \cdot B / R_e$，$N_v^{\text{sig}} = N_v^{\text{total}} - N_v^{\text{pwr}}$。

**$L_e$ 固定（构造给定），$B$ 是变量 → 这是 $B$ 上的线性不等式。**

$$B \cdot \sum_{e \in \delta(v)} \frac{L_e}{R_e} \le N_v^{\text{sig}} \quad \forall v$$

等价地：

$$\boxed{B \le \frac{N_v^{\text{sig}}}{\sum_{e \in \delta(v)} L_e / R_e} \quad \forall v}$$

### 3.5 功耗约束

每个 interposer $v$ 的总功耗：

$$P_v = P_0 + \sum_{e \in \delta(v)} \ell_e \cdot P_{\text{lane}}(R_e) = P_0 + B \cdot \sum_{e \in \delta(v)} \frac{L_e}{R_e} \cdot P_{\text{lane}}(R_e)$$

**$P_v$ 是 $B$ 的线性函数。**

全局热约束（L0，O(1)）：

$$\sum_v P_v \le A_{\text{total}} \cdot q_{\max}$$

展开为 $B$ 的不等式：

$$B \le \frac{A_{\text{total}} \cdot q_{\max} - N \cdot P_0}{\sum_v \sum_{e \in \delta(v)} L_e \cdot P_{\text{lane}}(R_e) / R_e}$$

热网络约束（L1，$N$ 条不等式）：

$$\mathbf{G}^{-1} (\mathbf{P}_0 + B \cdot \mathbf{p}_1 + \mathbf{b}) \le T_{\max} \cdot \mathbf{1}$$

其中 $(\mathbf{p}_1)_v = \sum_{e \in \delta(v)} L_e \cdot P_{\text{lane}}(R_e) / R_e$。

**全部是 $B$ 上的线性不等式。**

### 3.6 完整 LP：最大化 $B$

$$\boxed{
\begin{aligned}
\max_{B} \quad & B \\[8pt]
\text{s.t.} \quad & K \ge \gamma \cdot M && \text{(Clos 无阻塞条件，图形参数检查)} \\[4pt]
& B \le \frac{N_v^{\text{sig}} \cdot R_e}{\sum_{e \in \delta(v)} L_e} \quad \forall v && \text{(几何：bump 预算)} \\[8pt]
& \mathbf{G}^{-1} (\mathbf{P}_0 + B \cdot \mathbf{p}_1 + \mathbf{b}) \le T_{\max} \cdot \mathbf{1} && \text{(功耗：热网络)} \\[8pt]
& B \ge 0
\end{aligned}
}
$$

其中：
- $\gamma = 1$（可重排无阻塞）或 $\gamma = 2$（严格无阻塞，此时 $K \ge 2M-1 \approx 2M$）
- $L_e$ 是**常数**（由外层构造族决定，$\mathbf{L} = \mathbf{L}^{\text{min}}$）
- $R_e$ 是**常数**（由互联标准和物理距离决定）
- 所有约束在 $B$ 上是**线性的**

**这是一个单变量线性规划。** 求解成本 ≈ 检查 $O(N)$ 条不等式的上界 → O(N)，毫秒级。

---

## 4. 两层 DSE 架构（不变，但更简单）

```
═══════════════════════════════════════════════════════════
外层（离散枚举）
  ├── N: interposer 数量
  ├── M: 每 interposer 端口数（总端口 = N×M）
  ├── γ: 无阻塞等级（1 = 可重排，2 = 严格）
  ├── 外层构造族: Clos / Dragonfly / full-mesh / Benes
  ├── interconnect: UCIe / SerDes / 光学（决定 R_e, P_lane）
  └── cooling: 空冷 / 液冷（决定 q_max）
───────────────────────────────────────────────────────────
内层（单变量 LP，毫秒级）
  max  B
  s.t. B ≤ B_geom(v)   ∀v  (bump bound per interposer)
       B ≤ B_therm      (global thermal bound)
       B ≤ B_therm_l1   (RC network bound, optional)
  
  输出: B* = 最大无阻塞带宽 / 绑定约束
═══════════════════════════════════════════════════════════
```

### 4.1 $L_e$ 的计算（内层 LP 之外，一次性的常数计算）

$L_e$ 由外层构造决定，在进入 LP 之前就已固定：

| 构造 | $L_e$ 计算 |
|------|-----------|
| Clos ($K=M$) | $L_e = 1$ 对所有外层链路（平衡分布） |
| Clos ($K=2M-1$) | $L_e = 1$ 对所有外层链路（更多路径，每路径负载不变） |
| 全网格 | $L_{ij} = M$（直连，无分摊） |
| Dragonfly | 松弛 LP：$\min_{D,\mathbf{f}} \max_e L_e$（乐观下界，用作淘汰筛） |
| Benes | $L_e = 1$（多级平衡分布） |

### 4.2 $B^*$ 的含义

$B^*$ 是给定外层枚举选择下，**物理上可支撑的最大每端口无阻塞带宽**。

- 如果 $B^* \ge B_{\text{target}}$（如 800G）：该设计点可行
- 如果 $B^* < B_{\text{target}}$：绑定约束给出瓶颈位置和边际改进空间
- $\partial B^* / \partial N_v^{\text{sig}}$：多一个 bump 对 $B^*$ 的增益
- $\partial B^* / \partial q_{\max}$：多 1W/mm² 散热对 $B^*$ 的增益

---

## 5. 和原模型的对比

| | 原模型 | 新模型 |
|---|---|---|
| 无阻塞判据来源 | Valiant LP（min $t$ over D, f） | Clos 构造（图论定理） |
| 求解难度 | 对策论/min-max（或错误的 min-min） | O(1) 参数检查 + 单变量 LP |
| $L$ 的角色 | 变量（LP 求解的对象） | 常数（构造给定） + 物理约束中的系数 |
| 优化变量 | $t$, D, f, L, B | 仅 $B$ |
| 无阻塞保证 | 依赖 LP 语义正确性（之前有 bug） | 依赖 Clos 定理（1953，无可争议） |
| 工程可信度 | 理想化路由 + $\eta_{\text{impl}}$ 兜底 | 已知构造 + 真实硬件路由 |
| 论文叙事 | "我们证明了这个拓扑无阻塞" | "我们用已知无阻塞构造搭建系统，DSE 回答物理能否支撑" |

---

## 6. 遗留问题与讨论边界

### 6.1 分布式中间级的实现细节

Clos 构造要求 Stage 2（中间级）有 $K$ 个 $N \times N$ 模块。
当这些模块分布实现在 $N$ 个 interposer 上时，每个 interposer 需要额外提供
$K \times N / N = K$ 端口的中间级交换容量。

这部分容量**消耗 interposer 内部的交换资源**——但在 $N \le 16$ 时，
$K \le M$ 且 $K \le 16$，一个 16×16 的 crossbar 在 interposer 面积内是 trivial 的。

论文中可以讨论 $N$ 更大时中间级的实现策略（如 Benes 多级网络），
但原理不变——Clos 构造保证无阻塞。

### 6.2 当 $K < M$ 时

如果物理约束不允许 $K \ge M$（bump 不够、功耗太高），
系统是 oversubscribed 的。此时可保证的无阻塞带宽按比例缩放：

$$B_{\text{eff}} = \frac{K}{M} \cdot B$$

这个公式可以作为"非理想情况"在论文的 Discussion 中讨论。

### 6.3 M 矩阵（长距 vs 短距的约束分层）仍然成立

外层链路使用长距互联（SerDes VSR/MR/LR），
内层链路使用短距互联（UCIe Advanced）。
二者的 $R$ 和 $P_{\text{lane}}$ 差一个数量级，
这被 $\mathbf{L} = \mathbf{L}^{\text{min}}$ 的系数矩阵自然捕获。
几何约束的 bump 预算和功耗约束的热网络都不需要改变——它们本来就不关心拓扑长什么样，
只关心每条链路的 $\ell_e$ 和 $P_e$。
