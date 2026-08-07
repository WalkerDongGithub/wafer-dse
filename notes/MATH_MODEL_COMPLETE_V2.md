# 晶圆级交换机统一 DSE 框架：完整数理模型（v2）

> **与 v1（MATH_MODEL_COMPLETE.md）的区别**：
> 性能约束从 `D 为变量 + max L_e ≤ 1` 修正为 `D 外生固定 + R 个排列代表元 + L 为包络`。
> v1 的 D-变量形式在逻辑上是错的——交换机不能自己选流量矩阵。v2 在此修正。
> 功耗、几何、热三族约束不变。

---

## 0. 符号表

| 符号 | 含义 |
|------|------|
| $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ | 物理图：裸片为节点，链路为边 |
| $N$ | 裸片/终端数量 |
| $\delta(v)$ | 裸片 $v$ 上 incident 链路的集合 |
| $\pi(i,j)$ | $(i,j)$ 对的候选路径集合（Valiant 路由） |
| $B$ | 端口带宽（**待判定变量**，二分搜索确定 $B^*$） |
| $\mathcal{R}$ | $\text{Aut}(\mathcal{G})$ 共轭轨道代表元集合（**群论归约给出**） |
| $R = |\mathcal{R}|$ | 轨道数 |
| $\mathbf{D}^{(r)}$ | 第 $r \in \mathcal{R}$ 个排列矩阵（**外生固定，非变量**） |
| $\mathbf{f}^{(r)} = (f_{ij}^{k,(r)})$ | 模式 $r$ 的分流变量 |
| $\mathbf{L}^{(r)} = (L_e^{(r)})_{e \in \mathcal{E}}$ | 模式 $r$ 下的链路负载向量 |
| $\mathbf{L} = (L_e)_{e \in \mathcal{E}}$ | 所有模式的负载**包络**（$\mathbf{L} \ge \mathbf{L}^{(r)},\; \forall r$） |
| $\boldsymbol{\ell} = (\ell_e)_{e \in \mathcal{E}}$ | 每条链路的物理 lane 数：$\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ |
| $\mathbf{S}_{\text{bw}}$ | 每 lane 带宽对角阵（互联标准决定） |
| $\mathbf{S}_{\text{dyn}}$ | 每 lane 动态功耗对角阵（互联标准决定） |
| $\mathbf{S}_{\text{in}}$ | 单 bump 供电能力对角阵 $\mathbf{S}_{\text{in}} = \operatorname{diag}(V_{\text{dd}} \cdot I_{\text{bump}})$ |
| $N_v^{\text{total}}$ | 裸片 $v$ 的总 $\mu$bump 数 $= \eta A_v / p^2$ |
| $\mathbf{N}^{\text{sig}}$ | 信号 bump 需求向量 |
| $\mathbf{N}^{\text{pwr}}$ | 电源 bump 需求向量 |
| $\mathbf{M}$ | 裸片-链路 incidence 矩阵 $M_{v,e}=1$ 若 $e \in \delta(v)$ |
| $\mathbf{P}_0$ | 静态功耗向量（与 $\boldsymbol{\ell}$ 无关） |
| $\mathbf{P}$ | 裸片功耗向量 |
| $\mathbf{G}$ | 热导矩阵（M-矩阵，$\mathbf{G}^{-1} \ge 0$，Berman & Plemmons 1994） |
| $\mathbf{W}$ | 相邻裸片对的差分化矩阵：$W_{(i,j),i}=+1$, $W_{(i,j),j}=-1$ |
| $\mathbf{T}$ | 裸片温度向量 |
| $T_{\max}$ | 裸片温度上限 |
| $\Delta T_{\max}$ | 相邻裸片允许的最大温差（翘曲约束） |
| $q_{\max}$ | 冷却方案的散热能力 (W/mm$^2$) |

---

## 1. 性能约束

### 1.1 前提声明：对称性是方法论边界

本方法**预设物理拓扑 $\mathcal{G}$ 是高度对称的**（vertex-transitive），负载均衡策略为 $\text{Aut}(\mathcal{G})$-不变。对称性不足的拓扑不在讨论范围内——群论归约所需的轨道压缩依赖于足够大的自同构群。

**这不是数学缺陷，是取舍。** 对称性假设换来了线性规划的可解性。非对称拓扑需另起炉灶（缩小规模暴力枚举，或换用 RNB 等更保守的无阻塞定义）。

### 1.2 无阻塞的语义：潜能，非保证

本文判定的"无阻塞"含义：

> 在最优自适应路由下，物理资源足以支撑所有指定流量模式的同时交换。**网络有可能达到无阻塞。**

- **路由是最优的**——LP 可选择最佳分流。真实路由算法可能做不到，但不影响物理资源判定：最优不够，次优更不够。
- **$\mathbf{L}$ 是包络（$\ge$ 不等式，非 $=$）**——每条边的物理配置按最坏模式定，但路由可以灵活利用未被当前模式用满的边。

此模型是**早筛工具**：通过 → 进入 NoC 仿真进一步验证；不通过 → 物理资源不够，剪枝。

### 1.3 群论归约：从 $N!$ 到 $R$

理论推导见 [SYMMETRY_REDUCTION.md](SYMMETRY_REDUCTION.md)。核心结论：

**定理 1** 设 $\mathcal{G}$ vertex-transitive 且负载均衡策略 $\text{Aut}(\mathcal{G})$-不变，则最差流量模式必为排列矩阵。

**定理 2** 两个排列产生同构流图当且仅当它们在 $\text{Aut}(\mathcal{G})$ 下共轭。等价类 = $\text{Aut}(\mathcal{G})$ 在 $S_N$ 上的**共轭轨道**。

记轨道代表元集合为 $\mathcal{R}$。$R = |\mathcal{R}|$ 对实际对称拓扑可控（$N \le 16$ 时，典型 $R$ 在几十到百余）。$\mathcal{R}$ 由外层在选定拓扑后一次性计算，内层 LP 中使用其作为固定输入。

### 1.4 L0：二分带宽

$$\sum_{e \in C} L_e \ge \frac{N}{4} \quad \forall\;\text{割}\; C$$

O(1)，不需要路由信息。适合大规模初筛。忽略 $\mathcal{R}$ 的结构信息，过于松弛。

### 1.5 L1：多排列包络条件

$\mathcal{R}$ 个排列代表元同时进入 LP。对每个 $r \in \mathcal{R}$，流量矩阵固定为 $\mathbf{D}^{(r)}$（$D^{(r)}_{ij} = \delta_{j, \sigma_r(i)}$），分流变量 $\mathbf{f}^{(r)}$ 决定链路负载 $\mathbf{L}^{(r)}$。

**包络** $\mathbf{L}$ 取各模式的最大值：

$$L_e \ge L_e^{(r)} \quad \forall e,\; \forall r \in \mathcal{R}$$

优化会将 $L_e$ 压至 $\max_{r} L_e^{(r)}$。$\mathbf{L}$ 是性能侧和物理侧之间唯一的耦合变量——它一端接收 $\mathcal{R}$ 个模式的路由需求，另一端通过 $\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ 驱动全部物理约束。

**关键**：$\mathbf{D}^{(r)}$ 是固定的，不是变量。交换机不能选流量——每条链路必须按最坏情况配置。

---

## 2. 功耗模型

功耗模型是几何约束和热约束的共同基础。定义功耗向量 $\mathbf{P} = (P_v)_{v \in \mathcal{V}}$：

$$\boxed{\mathbf{P}(\boldsymbol{\ell}) = \mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}}$$

其中 $\mathbf{P}_0$ 为静态功耗向量，$\mathbf{M} \in \{0,1\}^{|\mathcal{V}| \times |\mathcal{E}|}$ 为裸片-链路 incidence 矩阵，$\mathbf{S}_{\text{dyn}}$ 为每条链路每 lane 动态功耗的对角阵，由互联标准决定（UCIe Advanced: 0.25–0.6 pJ/bit；SerDes VSR/MR/LR: 15–20 pJ/bit）。

$\mathbf{P}$ 向下游传递至两个约束族：几何约束中 $\mathbf{P}$ 决定电源 bump 需求 $\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P}$，挤占信号 bump 预算；热约束中 $\mathbf{P}$ 作为热源项进入热网络 $\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}$。

---

## 3. 几何约束

### 3.1 物理问题

每条链路需要 $\ell_e$ 条物理 lane，每条 lane 通过一个 $\mu$bump 从裸片引出至 interposer。裸片的 $\mu$bump 总数受面积和 pitch 限制，信号 bump 与电源 bump 竞争同一物理面积。

### 3.2 核心约束

裸片的总 bump 预算由面积和 pitch 决定：$\mathbf{N}^{\text{total}} = \eta \mathbf{A} / p^2$。

信号 bump 需求由 lane 数直接给出：

$$\mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell}$$

电源 bump 需求由功耗模型（§2）给出：

$$\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P} = \mathbf{S}_{\text{in}}^{-1} \cdot (\mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell})$$

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

| | **L0（粗筛）** | **L1（精判）** |
|---|---|---|
| **性能** | $\sum_{e \in C} L_e \ge N/4$ | $\mathcal{R}$ 个排列，$\mathbf{L} \ge \mathbf{L}^{(r)}$，分流变量 |
| 计算代价 | O(1) | O($R \cdot N^2 \cdot g$) |
| **几何** | $\sum_e \ell_e \le \sum_v N_v^{\text{total}}$ | $\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}$ |
| 计算代价 | O(1) | O($|\mathcal{V}|$) |
| **功耗** | $\mathbf{1}^T \mathbf{P} \le A \cdot q_{\max}$ | $\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}$，$\mathbf{T} \le T_{\max}$，$\mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max}$ |
| 计算代价 | O(1) | $|\mathcal{V}| + |\mathcal{E}_{\text{adj}}|$ 条不等式 |

L0 用于大规模初筛，L1 用于关键设计点的精确判断。精度升级仅替换系数矩阵。

### 5.2 完整 LP：可行性形式（固定 $B$，L1 精度）

$$\boxed{
\begin{aligned}
\text{find} \quad & \{\mathbf{f}^{(r)}\}_{r \in \mathcal{R}},\; \{\mathbf{L}^{(r)}\}_{r \in \mathcal{R}},\; \mathbf{L},\; \boldsymbol{\ell},\; \mathbf{P},\; \mathbf{N}^{\text{sig}},\; \mathbf{N}^{\text{pwr}},\; \mathbf{T} \\[8pt]
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
&& \text{（几何：bump 核心约束）} \\[8pt]
& \mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}
&& \text{（热网络：稳态热传导）} \\[4pt]
& \mathbf{T} \le T_{\max} \cdot \mathbf{1}
&& \text{（温度上限约束）} \\[4pt]
& \mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max} \cdot \mathbf{1}
&& \text{（翘曲约束：相邻温差 $\le \Delta T_{\max}$）} \\[8pt]
& \mathbf{f}^{(r)} \ge 0,\; \mathbf{L}^{(r)} \ge 0,\; \mathbf{L} \ge 0,\; \boldsymbol{\ell} \ge 0
\end{aligned}
}$$

其中 $\mathbf{D}^{(r)}$（$\forall r \in \mathcal{R}$）、$\mathcal{R}$、$\mathbf{P}_0$、$\mathbf{M}$、$\mathbf{S}_{\text{bw}}$、$\mathbf{S}_{\text{dyn}}$、$\mathbf{S}_{\text{in}}$、$\mathbf{G}$、$\mathbf{W}$、$\mathbf{N}^{\text{total}}$、$T_{\max}$、$\Delta T_{\max}$、$\mathbf{b}$ 均由外层技术选型决定，为常数。$B$ 在每次 LP 调用中固定。

**$\mathbf{L}$ 的角色**：它是整张 LP 的枢纽——一端接收 $\mathcal{R}$ 个模式的路由需求，另一端通过 $\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ 把需求转化为物理代价。$\mathbf{L}$ 值大 → $\boldsymbol{\ell}$ 涨 → bump 和热约束收紧。LP 有动力让各模式的路由尽量均匀，因为某条边被任一模式拉出峰值，整条边的物理 lane 都跟着涨。

### 5.3 解的判据与瓶颈诊断

对给定 $B$，LP 有可行解 → $B$ 可支撑。$B^*$ 通过二分搜索确定。

绑定约束的对偶变量直接揭示瓶颈：

| 绑定约束 | 诊断 | 改进方向 |
|---------|------|---------|
| $L_e \ge L_e^{(r)}$ 绑定（大部分 $L_e^{(r)}$ 接近 $L_e$） | 某排列模式导致链路负载集中 | 调整拓扑增大 bisection、增加路由路径多样性 |
| bump 约束绑定 | 信号 bump 预算不足 | 缩 pitch、增大裸片面积 |
| 温度约束绑定 | 冷却能力不足 | 升级冷却方案 |
| 翘曲约束绑定 | 温度分布不均 | 调整裸片布局或功耗分布 |

$B$ 增大时 $\boldsymbol{\ell}$ 等比例放大，所有物理约束同步收紧。$B^*$ 即物理资源或拓扑能力的瓶颈值。

---

## 6. 两层 DSE 架构

### 6.1 外层：离散枚举与轨道计算

外层决定离散架构选择，固定内层 LP 的所有系数矩阵，并**计算 $\mathcal{R}$**：

| 外层参数 | 决定的内层系数 |
|---------|--------------|
| 拓扑 $(a,p,h)$ + 路由策略 | $\mathcal{E}$, $\pi(i,j)$, 路径→链路 incidence |
| $\text{Aut}(\mathcal{G})$ 计算（nauty 或手工） | $\mathcal{R}$（轨道代表元集合） |
| 互联标准 | $\mathbf{S}_{\text{bw}}$, $\mathbf{S}_{\text{dyn}}$, $\mathbf{S}_{\text{in}}$ |
| 裸片面积 $A_v$, bump pitch $p$ | $\mathbf{N}^{\text{total}}$ |
| 冷却方案 | $q_{\max}$ |
| 裸片布局（若用 L2） | $\mathbf{A}(p)$ |

外层策略可以是暴力枚举、启发式剪枝、或基于 agent 的智能选型。

### 6.2 内层：二分搜索确定 $B^*$

内层不求解 max $B$ 优化问题——改为对固定 $B$ 求解 §5.2 的可行 LP（纯线性约束，无目标函数），通过二分搜索找到 $B^*$：

```
B_low = 0,  B_high = B_max
while B_high - B_low > ε:
    B_mid = (B_low + B_high) / 2
    求解 §5.2 的可行 LP（固定 B = B_mid）
    if feasible:  B_low = B_mid
    else:         B_high = B_mid
return B_low
```

$\log_2(B_{\max}/\varepsilon)$ 次 LP 调用即可收敛。每次 LP 为纯可行性问题，求解器可更激进地剪枝。$B$ 不在目标函数中意味着每次迭代规模更小、更稳定。

### 6.3 两层解耦

两层通过物理参数接口解耦：外层参数确定后，内层所有系数矩阵（包括 $\mathcal{R}$）均为常数，全部耦合发生在 $\mathbf{L}$ 和 $\boldsymbol{\ell}$ 上且为线性。

---

## 7. 灵敏度分析

### 7.1 对偶变量

在 $B^*$ 处的可行 LP 绑定约束上，对偶变量给出物理参数的边际价值。对 bump 预算 $N_v^{\text{total}}$：

$$\frac{\partial\;(\text{feasibility})}{\partial N_v^{\text{total}}}\Big|_{B^*} < 0 \;\Longrightarrow\; \text{增加 bump 预算可支撑更大 } B$$

对冷却能力 $q_{\max}$、温度上限 $T_{\max}$ 等参数同理。

### 7.2 影子价格比值

比较不同约束的对偶变量给出设计优先级：

$$\frac{\partial B^* / \partial N_v^{\text{total}}}{\partial B^* / \partial (A q_{\max})} = \frac{\text{增加一个 bump 的边际收益}}{\text{增加 1W 散热的边际收益}}$$

若比值 > 1，优先投资 bump 改进；否则优先升级冷却。

### 7.3 约束松弛扫描

对给定设计点，在 $B^*$ 附近扫描约束 RHS 的连续缩放 $\alpha \cdot b_i$，观察可行性边界变化。未绑定时约束松弛无效果；绑定时对偶值给出精确导数。

---

## 8. 限制与扩展方向

### 8.1 本模型的边界

1. **对称性假设**：$\mathcal{G}$ 须 vertex-transitive，否则 $\mathcal{R}$ 不再可控。非对称拓扑需换用 RNB（§8.2）或暴力枚举。
2. **无阻塞潜能，非保证**：通过本 LP 只意味着最优路由下有足够的物理资源。NoC 层面的路由算法、流控、拥塞需仿真进一步验证。
3. **单晶圆假设**：当前模型不处理多晶圆级联。多晶圆扩展需重新建模 inter-wafer 互联和全局带宽分配。
4. **稳态热假设**：热模型为稳态，不覆盖瞬态热点。但 M-矩阵的单调性保证稳态 + TDP 为最坏情况。

### 8.2 替代路径：可重排无阻塞（RNB）

当对称性假设不成立时，可将无阻塞定义升级为 RNB。详见 [CLOS_DECOMPOSITION.md](CLOS_DECOMPOSITION.md) 和 [SUBSTRATE_RNB.md](SUBSTRATE_RNB.md)。RNB 为结构条件（如 Clos 网络的 $m \ge n$），不依赖拓扑对称性，但条件更强（充分非必要），会给出更保守的可行域。

---

## 相关文档

- [SYMMETRY_REDUCTION.md](SYMMETRY_REDUCTION.md) — 对称图最差流量下界的群论归约
- [NONBLOCKING_CONDITIONS.md](NONBLOCKING_CONDITIONS.md) — 无阻塞条件修正的详细讨论（v1 → v2 的变更说明）
- [CLOS_DECOMPOSITION.md](CLOS_DECOMPOSITION.md) — Clos 分解视角
- [SUBSTRATE_RNB.md](SUBSTRATE_RNB.md) — Substrate 层 RNB 的数学表述

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
11. Slepian, D. "Two Theorems on a Particular Crossbar Switching Network." Unpublished, 1952.
