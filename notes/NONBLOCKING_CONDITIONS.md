# 性能约束：无阻塞条件的精确表述

> 本文修正 MATH_MODEL_COMPLETE.md §1 和 §5.2 中性能约束的表述。
> 旧版的 `max L_e ≤ 1` + D 作为优化变量 在逻辑上是错的——D 是外生流量，网络不能自己选。

---

## 0. 前提声明：对称性是方法论的边界

本文提出的无阻塞判定方法**预设物理拓扑是高度对称的**。这不是对 Dragonfly 拓扑的事后观察，而是方法本身的入场条件：

- 只有 vertex-transitive 的拓扑，其自同构群 $\text{Aut}(H)$ 才足够大，能将 $n!$ 个排列压缩到可控数量的共轭轨道代表元。
- 对称性不足的拓扑**不在本方法的讨论范围内**。对这类拓扑，仍有两条路：（1）缩小规模，暴力枚举全部排列；（2）换用更保守的无阻塞定义（如 RNB，见 §5）。

**这不是数学缺陷，是取舍。** 对称性假设换来了线性规划的可解性——在这个边界内，方法是严格的；边界之外，另起炉灶。

---

## 1. 无阻塞的语义：潜能，而非保证

### 1.1 我们判定的不是"一定无阻塞"

本文的"无阻塞"含义是：

> 在最优自适应路由（optimal adaptive routing）下，物理资源足以支撑所有指定流量模式的同时交换。**网络有可能达到无阻塞。**

这里有两个层面的放松：

1. **路由是最优的**——对每个流量模式，LP 可以选择最佳分流方案。真实硬件中的路由算法和流控可能做不到最优，但这不影响物理资源的判定：如果最优路由都不够，任何次优路由更不够。
2. **L 是包络（≥ 不等式），不是等式**——$L_e \ge L_e^{(r)}$ 意味着每条边的物理资源配置（lane 数）按最坏模式配置，但并不要求每种模式下每条边都刚好用满。路由可以灵活利用未被某模式用满的边。

### 1.2 这个模型在 DSE 流程中的位置

```
对称拓扑 + 有限排列代表元 → LP 可行性判定
                              ↓
                         通过？→ 进入 NoC 仿真（路由算法、流控、拥塞）
                              ↓
                         不通过？→ 物理资源不够，剪枝
```

它是一个**早筛工具**：假阴性（该过的没过）不可接受，假阳性（该剪的没剪）留给仿真消化。

---

## 2. 群论归约：从 $n!$ 到可控数量

此部分理论推导见 [SYMMETRY_REDUCTION.md](SYMMETRY_REDUCTION.md)。核心结论：

**定理 1** 设 $H$ vertex-transitive 且负载均衡策略 $\text{Aut}(H)$-不变，则最差流量模式必为排列矩阵。

**定理 2** 两个排列产生同构流图当且仅当它们在 $\text{Aut}(H)$ 下共轭。等价类 = $\text{Aut}(H)$ 在 $S_n$ 上的共轭轨道。

**轨道计数：**

| 拓扑 | $\text{Aut}(H)$ | $n=8$ | $n=16$ |
|------|-----------------|-------|--------|
| $K_n$ | $S_n$ | $p(8)=22$ | $p(16)=231$ |
| Dragonfly $(a,p,h)$，正则布线 | $\sim S_a \wr S_p$ | — | 远小于 231 |

记轨道代表元集合为 $\mathcal{R}$，$|\mathcal{R}|$ 是 LP 规模的决定因子。$|\mathcal{R}|$ 可控（几十到几百）→ 方法可行。

---

## 3. 统一 LP：可行性形式（固定 $B$）

对固定端口带宽 $B$，判定在全部约束下是否存在可行配置。决策变量为分流变量 $\{\mathbf{f}^{(r)}\}$、包络 $\mathbf{L}$、物理 lane 数 $\boldsymbol{\ell}$、功耗 $\mathbf{P}$、bump 分配 $\mathbf{N}^{\text{sig}}, \mathbf{N}^{\text{pwr}}$ 和温度 $\mathbf{T}$。

### 3.1 符号

| 符号 | 含义 |
|------|------|
| $\mathcal{R}$ | $\text{Aut}(H)$ 共轭轨道代表元集合 |
| $\mathbf{D}^{(r)}$ | 第 $r$ 个排列矩阵（**固定，非变量**） |
| $\mathbf{f}^{(r)} = (f_{ij}^{k,(r)})$ | 模式 $r$ 的分流变量 |
| $\mathbf{L}^{(r)} = (L_e^{(r)})$ | 模式 $r$ 下的链路负载向量 |
| $\mathbf{L} = (L_e)$ | 所有模式的负载包络——**每条边在所有模式下的最大负载** |
| 其余符号 | 与 MATH_MODEL_COMPLETE.md §0 一致 |

### 3.2 完整 LP

$$\boxed{
\begin{aligned}
\text{find} \quad & \{\mathbf{f}^{(r)}\}_{r \in \mathcal{R}},\; \{\mathbf{L}^{(r)}\}_{r \in \mathcal{R}},\; \mathbf{L},\; \boldsymbol{\ell},\; \mathbf{P},\; \mathbf{N}^{\text{sig}},\; \mathbf{N}^{\text{pwr}},\; \mathbf{T} \\[8pt]
\text{s.t.} \quad & \forall r \in \mathcal{R}: \\[4pt]
& \qquad \sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)} \quad \forall i,j
&& \text{（排列流量固定）} \\[4pt]
& \qquad L_e^{(r)} = \sum_{(i,j,k):\, e \in \text{path}} f_{ij}^{k,(r)} \quad \forall e
&& \text{（链路负载 = 分流之和）} \\[4pt]
& \qquad L_e \ge L_e^{(r)} \quad \forall e
&& \text{（包络：每条边取各模式最大值）} \\[8pt]
& \boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}
&& \text{（包络负载 → 物理 lane 数）} \\[4pt]
& \mathbf{P} = \mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}
&& \text{（功耗模型）} \\[4pt]
& \mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P} \\[4pt]
& \mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell} \\[4pt]
& \mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}
&& \text{（几何：bump 约束）} \\[8pt]
& \mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b} \\[4pt]
& \mathbf{T} \le T_{\max} \cdot \mathbf{1} \\[4pt]
& \mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max} \cdot \mathbf{1}
&& \text{（热约束）} \\[8pt]
& \mathbf{f}^{(r)} \ge 0,\; \mathbf{L}^{(r)} \ge 0,\; \mathbf{L} \ge 0,\; \boldsymbol{\ell} \ge 0
\end{aligned}}
$$

### 3.3 与原版的本质区别

| | 原版 §5.2 | 修正版 |
|---|---|---|
| $\mathbf{D}$ | **变量**，LP 自选 | **外生固定**，$\mathcal{R}$ 个排列由群论归约预先确定 |
| $\mathbf{L}$ 的含义 | 约束目标（$\max L_e \le 1$） | **需求包络**（$L_e \ge L_e^{(r)}$），物理资源按最坏情况配置 |
| 问题类型 | 优化（max $B$，含双线性） | **可行性判定**（固定 $B$，纯线性不等式组） |
| $B$ 的上界 | 由 $\max L_e \le 1$ 给出 | 由物理约束（bump、热）绑定——拓扑能力隐含在 $\mathbf{L}$ 和物理资源的相互作用中 |

$\mathbf{L}$ 是整张 LP 的枢纽：它一端接收 $\mathcal{R}$ 个模式的路由需求，另一端通过 $\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ 把需求转化为物理代价。$\mathbf{L}$ 往上走 → $\boldsymbol{\ell}$ 涨 → bump 和热约束收紧。可行当且仅当存在路由方案使包络不突破物理资源。

---

## 4. 二分搜索求 $B^*$

问题退化为可行性判定后，$B^*$ 通过对数次 LP 求解得到：

```
输入: B_low = 0, B_high = B_max, ε
输出: B*（ε-近似的最大可行带宽）

while B_high - B_low > ε:
    B_mid = (B_low + B_high) / 2
    if LP_feasible(B_mid):
        B_low = B_mid
    else:
        B_high = B_mid
return B_low
```

每次迭代求解 §3.2 的可行 LP（纯线性约束，无目标函数）。$\log_2(B_{\max}/\varepsilon)$ 次 LP 调用即可收敛。$B$ 不出现在目标函数里意味着每次 LP 规模更小、求解更稳定。

---

## 5. 方案二：可重排无阻塞（RNB）—— 另一条路

当对称性假设不成立、或用户需要一个调度无关的硬保证时，可以将无阻塞定义升级为**可重排无阻塞（Rearrangeably Nonblocking, RNB）**。详见 [CLOS_DECOMPOSITION.md](CLOS_DECOMPOSITION.md) 和 [SUBSTRATE_RNB.md](SUBSTRATE_RNB.md)。

RNB 的优势是不依赖拓扑对称性，但条件更强——是充分而非必要。两类方案的对比：

| | 方案一（对称 + 排列 LP） | 方案二（RNB） |
|---|---|---|
| 前提 | vertex-transitive 拓扑 | 可分解为 Clos 结构 |
| 无阻塞语义 | 潜能（最优路由下可达成） | 保证（任何连接请求下可重排实现） |
| 可行域 | 大（必要且充分，在对称假设下） | 小（充分不必要） |
| 计算 | $|\mathcal{R}|$ 组分流变量，一个 LP | 结构不等式，O(1) |

**建议**：以方案一为主，方案二在实验部分作为可行域下界对比。

---

## 6. 与 MATH_MODEL_COMPLETE.md 的关系

本文档是 MATH_MODEL_COMPLETE.md §1（性能约束）和 §5.2（统一 LP）的**修正和替代**。

- MATH_MODEL_COMPLETE.md §2–§4（功耗、几何、热）不变——它们接收 $\mathbf{L}$ 作为输入，不关心 $\mathbf{L}$ 的内部结构
- MATH_MODEL_COMPLETE.md §6（两层 DSE 架构）的"外层枚举 → 内层 LP"结构不变
- MATH_MODEL_COMPLETE.md §7（灵敏度分析）仍然适用——二分搜索找到的 $B^*$ 处绑定约束的对偶变量给出相同的边际信息

未来合并时，将本文 §3 的 LP 直接替换 MATH_MODEL_COMPLETE.md §5.2。

---

## 参考文献

1. Birkhoff, G. "Tres observaciones sobre el algebra lineal." *Univ. Nac. Tucumán Rev. Ser. A*, 1946.
2. Valiant, L.G. "A Scheme for Fast Parallel Communication." *SIAM J. Computing*, 1982.
3. Clos, C. "A Study of Non-Blocking Switching Networks." *Bell System Technical Journal*, 1953.
4. Slepian, D. "Two Theorems on a Particular Crossbar Switching Network." Unpublished, 1952.
5. 自引：[SYMMETRY_REDUCTION.md](SYMMETRY_REDUCTION.md)——对称图最差流量下界的群论归约
6. 自引：[CLOS_DECOMPOSITION.md](CLOS_DECOMPOSITION.md)——晶圆级交换机的 Clos 分解
7. 自引：[SUBSTRATE_RNB.md](SUBSTRATE_RNB.md)——Substrate 层 RNB 的数学表述
