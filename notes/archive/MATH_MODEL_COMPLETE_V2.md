# 晶圆级交换机统一 DSE 框架：完整数理模型（v3）

> **v3 更新（2026-08-10）**：
> - 架构拆分为组内/组间两个独立子问题：$B^* = \min(B^*_{\text{intra}}, B^*_{\text{inter}})$
> - 布线模型扩展为 边容量 + 点容量
> - C4 bump 约束用面积和 pitch 直接计算（去除"pad"概念）
> - 热 G 矩阵从 MFIT 式 die 布局推导（placement → G）
> - 互联标准 per-link 异构（UCIe / SerDes 不同 $S_{\text{bw}}$, $S_{\text{dyn}}$）

---

## 0. 符号表

| 符号 | 含义 |
|------|------|
| $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ | 物理拓扑图：die 为节点，链路为边 |
| $\mathcal{E}_{\text{intra}}$ | 组内链路集合（UCIe，interposer 上走线） |
| $\mathcal{E}_{\text{inter}}$ | 组间链路集合（SerDes，经 C4 出 interposer） |
| $B$ | 端口带宽（待判定变量，二分搜索确定 $B^*$） |
| $\mathcal{R}$ | $\text{Aut}(\mathcal{G})$ 共轭轨道代表元集合 |
| $\mathbf{D}^{(r)}$ | 第 $r \in \mathcal{R}$ 个排列矩阵（外生固定） |
| $f_{ij}^{k,(r)}$ | 模式 $r$ 下 $(i,j)$ 对在第 $k$ 条候选路径上的分流 |
| $L_e$ | 链路 $e$ 的负载包络：$L_e = \max_{r} L_e^{(r)}$ |
| $\ell_e$ | 链路 $e$ 的物理 lane 数 |
| $S_{\text{bw},e}$ | 链路 $e$ 的每 lane 带宽（UCIe: 32 Gbps, SerDes: 106 Gbps） |
| $S_{\text{dyn},e}$ | 链路 $e$ 的每 lane 动态功耗（UCIe: 16 mW, SerDes: 425 mW） |
| $P_v$ | die $v$ 的总功耗 |
| $P_{0,v}$ | die $v$ 的静态功耗 |
| $V_{\text{dd}}$ | 供电电压 |
| $I_{\text{bump}}$ | 单电源 bump 载流能力 |
| $N_v^{\text{total}}$ | die $v$ 的总 μbump 数 = $\eta A_v / p^2$ |
| $T_v$ | die $v$ 的稳态温度 |
| $\mathbf{G}$ | 热导矩阵（M-矩阵，$\mathbf{G}^{-1} \ge 0$） |
| $\mathbf{b}$ | 环境温度贡献向量 |
| $\mathcal{G}_{\text{grid}} = (\mathcal{V}_{\text{grid}}, \mathcal{E}_{\text{grid}})$ | 布线网格图 |
| $\mathcal{Q}_e$ | 链路 $e$ 在网格上的候选 L 形路径集合（$\vert\mathcal{Q}_e\vert \le 2$） |
| $x_{e,q}$ | 链路 $e$ 在候选路径 $q$ 上分配的 lane 数 |
| $C_g$ | 网格边 $g$ 的物理容量（金属层数 × 走线密度 × 通道宽度） |
| $C_v$ | 网格点 $v$ 的通过容量 |
| $N_{\text{C4}}^{\text{SerDes}}$ | C4 bump 中可用于 SerDes 的总数 |

---

## 1. 架构：组内 / 组间分离

Dragonfly 交换机在物理上分两层实现：

| | 介质 | 互联 | 约束族 |
|---|---|---|---|
| **组内** | Interposer 金属层 | UCIe（die → die） | 性能 + μbump + 热 + 布线 |
| **组间** | Substrate（经 C4 bump） | 由布局决定：距离短走 UCIe，距离长走 SerDes | 性能 + C4 + 热 + 布线 |

两组物理资源完全独立。互联标准不是预先硬编码的——布局决定 die 间距离，距离决定链路用 UCIe 还是 SerDes。总带宽取极小：

$$\boxed{B^* = \min(B^*_{\text{intra}},\; B^*_{\text{inter}})}$$

- 组内子问题：**FullMesh(a, p)** 拓扑（$a$ 个 die 全互连，每 die $p$ 个终端端口）
- 组间子问题：**Dragonfly(a, p, h)** 完整拓扑（组内链路容量无限，仅组间链路受物理约束）

---

## 2. 性能约束

对每个排列代表元 $r \in \mathcal{R}$：

**流量守恒**：
$$\sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)} \quad \forall i,j$$

**链路负载**：
$$L_e^{(r)} = \sum_{(i,j,k):\, e \in \text{path}} f_{ij}^{k,(r)} \quad \forall e$$

**包络**：
$$L_e \ge L_e^{(r)} \quad \forall e,\; \forall r \in \mathcal{R}$$

目标：$\min \sum_e L_e$（使 $L_e$ 压至真实包络下界）。

---

## 3. 物理约束

### 3.1 功耗

$$\ell_e = \frac{B \cdot L_e}{S_{\text{bw},e}} \quad \forall e$$

$$P_v = P_{0,v} + \sum_{e \in \delta(v)} S_{\text{dyn},e} \cdot \ell_e \quad \forall v$$

$S_{\text{bw},e}$ 和 $S_{\text{dyn},e}$ 由布局决定。每条链路 $e = (i,j)$ 的物理距离：
$$\text{dist}(i,j) = |x_i - x_j| + |y_i - y_j|$$

距离 ≤ UCIe 最大可达距离（Standard: ~25mm, Advanced: ~2mm）→ UCIe，否则必须走 SerDes。

- UCIe Advanced：32 Gbps, 16 mW/lane
- SerDes 112G VSR：106 Gbps, 425 mW/lane

因此同一个拓扑，die 摆得紧凑（UCIe 多）和摆得松散（SerDes 多）会导致不同的 $S_{\text{bw},e}$, $S_{\text{dyn},e}$，进而影响 LP 的功耗和 B*。

### 3.2 μbump 预算（仅组内链路）

**信号 bump 需求**：
$$\mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell}$$

**电源 bump 需求**：
$$\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P}, \quad \mathbf{S}_{\text{in}} = \operatorname{diag}(V_{\text{dd}} \cdot I_{\text{bump}})$$

**核心约束**（信号 + 电源 竞争同一物理面积）：
$$\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}$$

其中 $N_v^{\text{total}} = \eta A_v / p^2$，$\mathbf{M} \in \{0,1\}^{|\mathcal{V}| \times |\mathcal{E}|}$ 为 die-链路 incidence 矩阵。$\boldsymbol{\ell}$ 同时出现在 $\mathbf{N}^{\text{sig}}$（直接）和 $\mathbf{N}^{\text{pwr}}$（通过 $\mathbf{P}$）中，形成闭环。

### 3.3 C4 bump 预算（仅组间链路）

C4 bump 是 interposer 底面的焊球阵列。总数由面积和 pitch 决定：

$$N_{\text{C4}}^{\text{total}} = \frac{A_{\text{interposer}}}{p_{\text{C4}}^2}$$

其中一部分用于电源和地，剩余为信号 bump。SerDes 链路只能使用信号 bump 中的一部分：

$$N_{\text{C4}}^{\text{SerDes}} = \eta_{\text{C4}} \cdot N_{\text{C4}}^{\text{total}}$$

其中 $\eta_{\text{C4}}$ 是经验系数（典型值 ~0.5，含电源/地开销和信号分配比）。

核心约束：所有组间链路的 SerDes lane 总数不超过可用 C4 bump 数：

$$\sum_{e \in \mathcal{E}_{\text{inter}}} \ell_e \;\le\; N_{\text{C4}}^{\text{SerDes}}$$

### 3.4 热

稳态热传导方程离散化后：

$$\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}$$

$$\mathbf{T} \le T_{\max} \cdot \mathbf{1}$$

其中 $\mathbf{G}$ 从 die placement 构建（MFIT 式 nodal analysis，§8），为 M-矩阵（$\mathbf{G}^{-1} \ge 0$）。取 TDP + 稳态为最坏情况——若通过，所有非峰值和非稳态场景自动满足。

### 3.5 布线

Interposer 金属层上的走线建模为网格图 $\mathcal{G}_{\text{grid}} = (\mathcal{V}_{\text{grid}}, \mathcal{E}_{\text{grid}})$。每条链路 $e$ 有候选 L 形路径集 $\mathcal{Q}_e$（至多 2 条）——沿网格边先水平后垂直，或先垂直后水平。分流变量 $x_{e,q} \ge 0$ 表示在路径 $q$ 上分配的 lane 数。

网格边容量 $C_g$ 由通道宽度、金属层数和走线密度决定：

$$C_g = w_g \cdot \lambda \cdot n_{\text{metal}}$$

其中 $w_g$ 是通道宽度（相邻 die 间隙），$\lambda$ 是走线密度（lanes/mm/layer），$n_{\text{metal}}$ 是可用金属层数。

网格点容量 $C_v$ 限制经过每个交点的总 lane 数（包含直行和转弯）。

**需求约束**：
$$\sum_{q \in \mathcal{Q}_e} x_{e,q} = \ell_e \quad \forall e$$

**边容量约束**（平行走线）：
$$\sum_{e,q:\, g \in q} x_{e,q} \le C_g \quad \forall g \in \mathcal{E}_{\text{grid}}$$

**点容量约束**（交点通过流量）：
$$\sum_{e,q:\, v \in q} x_{e,q} \le C_v \quad \forall v \in \mathcal{V}_{\text{grid}}$$

---

## 4. 约束族总览

| 约束族 | 数学形式 | 变量 | 作用域 |
|--------|---------|------|--------|
| 性能 | $\sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)},\; L_e \ge L_e^{(r)}$ | $f, L$ | intra + inter |
| 功耗 | $P_v = P_{0,v} + \sum_{e \in \delta(v)} S_{\text{dyn},e} \cdot \ell_e$ | $P$ | intra + inter |
| μbump | 信号 + 电源 ≤ $N_v^{\text{total}}$ | $\ell, P$ | intra only |
| C4 bump | $\sum \ell_e \le N_{\text{C4}}^{\text{SerDes}}$ | $\ell$ | inter only |
| 热 | $\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b},\; \mathbf{T} \le T_{\max}$ | $T$ | intra + inter |
| 布线边 | $\sum_{e,q: g \in q} x_{e,q} \le C_g$ | $x$ | intra + inter |
| 布线点 | $\sum_{e,q: v \in q} x_{e,q} \le C_v$ | $x$ | intra + inter |
| 布线需求 | $\sum_q x_{e,q} = \ell_e$ | $x, \ell$ | intra + inter |

---

## 5. 完整 LP（组内子问题，固定 $B$，L1 精度）

$$\boxed{
\begin{aligned}
\text{find} \quad & \{\mathbf{f}^{(r)}\}_{r \in \mathcal{R}},\; \{\mathbf{L}^{(r)}\}_{r \in \mathcal{R}},\; \mathbf{L},\; \boldsymbol{\ell},\; \mathbf{P},\; \mathbf{N}^{\text{sig}},\; \mathbf{N}^{\text{pwr}},\; \mathbf{T},\; \{x_{e,q}\} \\[8pt]
\text{s.t.} \quad & \forall r \in \mathcal{R}: \\[4pt]
& \qquad \sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)} \quad \forall i,j
&& \text{（排列流量固定——外生，不可选）} \\[4pt]
& \qquad L_e^{(r)} = \sum_{(i,j,k):\, e \in \text{path}} f_{ij}^{k,(r)} \quad \forall e
&& \text{（模式 $r$ 的链路负载 = 分流之和）} \\[4pt]
& \qquad L_e \ge L_e^{(r)} \quad \forall e
&& \text{（包络：每条边取各模式最大负载）} \\[8pt]
& \boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}
&& \text{（包络负载 → 物理 lane 数）} \\[4pt]
& \mathbf{P} = \mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}
&& \text{（功耗模型）} \\[4pt]
& \mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P} \\[4pt]
& \mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell} \\[4pt]
& \mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}
&& \text{（μbump：信号 + 电源 竞争同一物理面积）} \\[8pt]
& \mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}
&& \text{（热网络：稳态热传导）} \\[4pt]
& \mathbf{T} \le T_{\max} \cdot \mathbf{1}
&& \text{（温度上限约束）} \\[4pt]
& \mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max} \cdot \mathbf{1}
&& \text{（翘曲约束：相邻温差 $\le \Delta T_{\max}$）} \\[8pt]
& \sum_{q \in \mathcal{Q}_e} x_{e,q} = \ell_e \quad \forall e
&& \text{（布线需求：每条链路的 lane 必须分配到网格路径上）} \\[4pt]
& \sum_{e,q:\, g \in q} x_{e,q} \le C_g \quad \forall g \in \mathcal{E}_{\text{grid}}
&& \text{（布线边容量：每条网格边不超物理上限）} \\[4pt]
& \sum_{e,q:\, v \in q} x_{e,q} \le C_v \quad \forall v \in \mathcal{V}_{\text{grid}}
&& \text{（布线点容量：每个网格交点不超通过上限）} \\[8pt]
& \mathbf{f}^{(r)} \ge 0,\; \mathbf{L}^{(r)} \ge 0,\; \mathbf{L} \ge 0,\; \boldsymbol{\ell} \ge 0,\; x_{e,q} \ge 0
\end{aligned}
}$$

其中 $\mathbf{D}^{(r)}$（$\forall r \in \mathcal{R}$）、$\mathcal{R}$、$\mathbf{P}_0$、$\mathbf{M}$、$\mathbf{S}_{\text{bw}}$、$\mathbf{S}_{\text{dyn}}$、$\mathbf{S}_{\text{in}}$、$\mathbf{G}$、$\mathbf{W}$、$\mathbf{N}^{\text{total}}$、$T_{\max}$、$\Delta T_{\max}$、$\mathbf{b}$、$C_g$、$C_v$ 均由外层技术选型决定，为常数。$B$ 在每次 LP 调用中固定。

**$\mathbf{L}$ 的角色**：它是整张 LP 的枢纽——一端接收 $\mathcal{R}$ 个模式的路由需求，另一端通过 $\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ 把需求转化为物理代价。$\mathbf{L}$ 值大 → $\boldsymbol{\ell}$ 涨 → bump 和热约束收紧。LP 有动力让各模式的路由尽量均匀，因为某条边被任一模式拉出峰值，整条边的物理 lane 都跟着涨。

求解时用 $\min \sum_e L_e$ 目标将 $\mathbf{L}$ 压至真实包络下界，避免 feasibility LP 中 solver 将 $L_e$ 放大到无意义的值。这不是模型定义的一部分，是求解策略。目标不影响可行域边界，仅选取可行域中物理资源消耗最小的那个点。

---

### 5.2 组间子问题

组间子问题的 LP 与组内相同，差异仅在**作用域**和**常数矩阵**：

| | 组内 | 组间 |
|---|---|---|
| 拓扑 | FullMesh(a, p) | Dragonfly(a, p, h) |
| 物理链路 | $\mathcal{E}_{\text{intra}}$（UCIe） | $\mathcal{E}_{\text{inter}}$（SerDes） |
| $S_{\text{bw},e}$ | 32 Gbps | 106 Gbps |
| $S_{\text{dyn},e}$ | 16 mW | 425 mW |
| bump 约束 | μbump（$\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}$） | C4（$\sum \ell_e \le N_{\text{C4}}^{\text{SerDes}}$，§3.3） |
| 组内链路 | 参与全部约束 | $S_{\text{bw}} = \infty$，$S_{\text{dyn}} = 0$（无限容量，零功耗） |

两个子问题独立求解，$B^* = \min(B^*_{\text{intra}},\; B^*_{\text{inter}})$。

---

## 6. 两层 DSE 架构

### 6.1 外层：离散枚举

外层选定拓扑参数和工艺参数后，所有系数矩阵固定为常数：

| 外层参数 | 决定的内层系数 |
|---------|--------------|
| 拓扑 $(a,p,h)$ + 路由策略 | $\mathcal{E}$, $\pi(i,j)$, $\mathcal{R}$ |
| die 布局 (placement) | $\mathbf{G}$, $\mathcal{G}_{\text{grid}}$ |
| 互联标准 (UCIe / SerDes 选型) | $S_{\text{bw},e}$, $S_{\text{dyn},e}$（per-link 数组） |
| bump 工艺 (pitch, 电流, Vdd) | $N_v^{\text{total}}$ |
| 冷却方案 + interposer 热参数 | $\mathbf{G}$, $\mathbf{b}$, $T_{\max}$ |
| 金属层数, 走线密度 | $C_g$, $C_v$, $C_{\text{C4},p}$ |

### 6.2 内层：二分搜索 $B^*$

```
对每个子问题（intra / inter）：
  lo = B_min,  hi = B_max
  while hi - lo > ε:
      mid = (lo + hi) / 2
      求解 §5 的 LP（固定 B = mid）
      if feasible: lo = mid  else: hi = mid
  return lo

B* = min(B*_intra, B*_inter)
```

$\log_2(B_{\max}/\varepsilon)$ 次 LP 调用即可收敛。

---

## 7. 瓶颈诊断

求解器返回的对偶变量直接揭示绑定约束：

| 绑定约束 | 诊断 | 改进方向 |
|---------|------|---------|
| 布线边/点容量 | 金属层走线通道不足 | 增加金属层数、提高走线密度 |
| C4 bump 约束绑定 | SerDes 带宽超出 C4 bump 数量 | 增大 interposer 面积、缩 C4 pitch |
| μbump 约束 | die 信号 bump 预算不足 | 缩 pitch、增大 die 面积 |
| 热约束 | 功耗密度过高 | 升级冷却、降低 SerDes 速率、active interposer |
| 所有物理约束松 | 拓扑路由达 Valiant 极限 | 调整 $(a,p,h)$ 改善 bisection |

$B$ 增大 → $\ell_e$ 等比例放大 → 布线 / bump / 热同步收紧 → $B^*$ 即最紧约束的极限值。

---

## 8. 热 G 矩阵构建（MFIT 式）

从 die placement 构建 $\mathbf{G}$，参考 Zhang et al., ACM TACO 2025：

1. 每个 die 为一个热节点，$n$ 个 die → $n \times n$ 矩阵
2. 垂直热导：$G_{ii}^{\text{vert}} = 1 / R_{\text{vert}}$（die → ambient 集总等效热阻）
3. 横向热导（面邻接 die 对，半单元串联公式）：

$$G_{ij} = \frac{2 \cdot k_{\text{interposer}} \cdot t \cdot \text{overlap}}{d_i + d_j + \text{gap}} \quad (i \neq j,\; \text{die}_i \text{ 与 } \text{die}_j \text{ 面邻接})$$

4. 组装：
$$G_{ii} = G_{ii}^{\text{vert}} + \sum_{j \neq i} G_{ij},\qquad G_{ij} = -G_{ij}\;(i \neq j)$$

5. 环境项：$\mathbf{b}_i = G_{ii}^{\text{vert}} \cdot T_{\text{ambient}}$
6. $\mathbf{G}$ 自动满足 M-矩阵（$\mathbf{G}^{-1} \ge 0$），保证热单调性

---

## 参考文献

1. Birkhoff, G. "Tres observaciones sobre el algebra lineal." *Univ. Nac. Tucumán Rev. Ser. A*, 1946.
2. Valiant, L.G. "A Scheme for Fast Parallel Communication." *SIAM J. Computing*, 1982.
3. Ngo, H.Q. et al. "Analyzing Nonblocking Switching Networks using Linear Programming (Duality)." *INFOCOM*, 2010.
4. Kim, J. et al. "Technology-Driven, Highly-Scalable Dragonfly Topology." *ISCA*, 2008.
5. UCIe Consortium. "Universal Chiplet Interconnect Express (UCIe) Specification, Revision 2.0." 2024.
6. Berman, A. & Plemmons, R.J. "Nonnegative Matrices in the Mathematical Sciences." *SIAM*, 1994.
7. Zhang, R. et al. "MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D Chiplet Systems." *ACM TACO*, 2025.
8. Li, X. et al. "An Electrical-Thermal Co-Simulation Model of Chiplet Heterogeneous Integration Systems." *IEEE TCPMT*, 2024.
9. Dally, W.J. & Towles, B. "Principles and Practices of Interconnection Networks." *Morgan Kaufmann*, 2004.
10. Clos, C. "A Study of Non-Blocking Switching Networks." *Bell System Technical Journal*, 1953.

---

## 相关文档

- [CONJUGACY_AND_PARTITIONS.md](CONJUGACY_AND_PARTITIONS.md) — 为什么 S_n 的共轭类 = n 的整数分拆（群论基础）
- [SYMMETRY_REDUCTION.md](SYMMETRY_REDUCTION.md) — 对称图最差流量下界的群论归约
- [CLOS_DECOMPOSITION.md](CLOS_DECOMPOSITION.md) — Clos 分解视角
- [SUBSTRATE_RNB.md](SUBSTRATE_RNB.md) — Substrate 层 RNB 的数学表述
- [plan_placement.md](plan_placement.md) — die 布局枚举（D₄ 轨道压缩）
- [plan_routing.md](plan_routing.md) — 布线网格多商品流模型
