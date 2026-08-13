# 晶圆级交换机统一 DSE 框架：完整数理模型（v3）

> **v3（2026-08-11）**：
> - 布局假设：相对位置固定，网格已划分，gap = 0。
> - die 面积和功耗随 $B$ 线性缩放。
> - G 矩阵常数（$G_{ij} = k \cdot t$，不随 $B$ 变）。
> - 组内/组间分离，互连标准由布局距离决定。

---

## 0. 符号表

| 符号 | 含义 |
|------|------|
| $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ | 物理拓扑图（die 为节点，链路为边） |
| $\mathcal{E}_{\text{UCIe}}$ | UCIe 链路集合（距离 $\le$ UCIe 可达范围） |
| $\mathcal{E}_{\text{SerDes}}$ | SerDes 链路集合（距离 $>$ UCIe 可达范围） |
| $B$ | 端口带宽（待判定变量，二分搜索确定 $B^*$） |
| $\mathcal{R}$ | 排列代表元集合（$S_n$ 共轭类近似，Aut(G) 归约 TODO） |
| $\mathbf{D}^{(r)}$ | 第 $r \in \mathcal{R}$ 个排列矩阵（外生固定） |
| $f_{ij}^{k,(r)}$ | 模式 $r$ 下 $(i,j)$ 对在第 $k$ 条路径上的分流 |
| $L_e$ | 链路 $e$ 的负载包络：$L_e = \max_r L_e^{(r)}$ |
| $\ell_e$ | 链路 $e$ 的物理 lane 数 |
| $S_{\text{bw},e}$ | 链路 $e$ 的每 lane 带宽（UCIe: 32, SerDes: 106 Gbps/lane） |
| $S_{\text{dyn},e}$ | 链路 $e$ 的每 lane 动态功耗（UCIe: 0.016, SerDes: 0.425 W/lane） |
| $d(B)$ | die 边长：$d(B) = d_0 + \alpha_d \cdot B$ |
| $A_{die}(B)$ | die 面积：$A_{die}(B) = d(B)^2$ |
| $N_v^{\text{total}}(B)$ | die $v$ 的 μbump 总数 $= \eta \cdot A_{die}(B) / p^2$ |
| $P_{peak}(B)$ | die 峰值功耗：$P_{peak}(B) = P_0(B) + \beta_P \cdot B$ |
| $P_v$ | die $v$ 的总功耗（峰值 + PHY 动态） |
| $\mathbf{G}$ | 热导矩阵（常数，gap=0 时 $G_{ij} = k \cdot t$） |
| $\mathbf{T}$ | die 温度向量：$\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}$ |
| $\mathcal{G}_{\text{grid}}$ | 布线网格图 |
| $x_{e,q}$ | 链路 $e$ 在候选路径 $q$ 上分配的 lane 数 |

---

## 1. 四大硬物理约束

晶圆级交换机物理建模的核心只有四个问题，它们共用一个变量空间 $\{L_e\}, B$：

| 约束 | 物理本质 | 硬上限 |
|------|---------|--------|
| **面积** | reticle 极限 | interposer ≤ 858 mm²，三方竞争：die + 走线通道 + C4 |
| **功耗** | 散热能力 | $\sum P_v \le A_{ip} \cdot q_{max}$。SerDes 功耗高但走线距离短，UCIe 功耗低但面积大 |
| **走线距离** | UCIe 可达范围 | die 间 Manhattan 距离 ≤ UCIe 最大可达（~25mm）。die 大了绕路过远 → 逼着用 SerDes |
| **走线容量** | 金属层 lane 上限 | 绕 die 走线挤占通道。die 大了间隙窄 → 布线容量降，可能比 bump 先绑 |

四个约束交织——不是独立不等式，是一个紧耦合空间。整个 LP 的意义就是把它们写成同一组 $L$ 和 $B$ 上的不等式，让求解器自己找可行域边界。

---

## 2. 架构

$$B^* = \min(B^*_{\text{intra}},\; B^*_{\text{inter}})$$

| | 组内 | 组间 |
|---|---|---|
| 拓扑 | FullMesh(a, p) | Dragonfly(a, p, h) |
| 链路 | $\mathcal{E}_{\text{UCIe}}$（interposer 内） | $\mathcal{E}_{\text{SerDes}}$（经 C4） |
| bump | μbump（$N_{sig} + N_{pwr} \le N_{total}$） | C4（$\sum \ell_e \le N_{C4}$） |

互连标准由布局距离决定——不是硬编码的"组内=UCIe"。

---

## 2. die 缩放模型

每端口带宽增大 → die 面积线性放大 → 峰值功耗线性增长：

$$d(B) = d_0 + \alpha_d \cdot B$$
$$A_{die}(B) = d(B)^2$$
$$P_{peak}(B) = P_0(B) + \beta_P \cdot B$$

其中 $P_0(B) \propto A_{die}(B)$（静态功耗 ∝ 面积）。

---

## 3. 物理约束

### 3.1 功耗

$$\ell_e = \frac{B \cdot L_e}{S_{\text{bw},e}}$$

$$P_v = P_{peak}(B) + \sum_{e \in \delta(v)} S_{\text{dyn},e} \cdot \ell_e$$

### 3.2 μbump（仅 UCIe 链路）

$$\mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell}$$
$$\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P}$$
$$\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}(B)$$

其中 $N_v^{\text{total}}(B) = \eta \cdot A_{die}(B) / p^2$。

### 3.3 C4 bump（仅 SerDes 链路）

$$\sum_{e \in \mathcal{E}_{\text{SerDes}}} \ell_e \le N_{\text{C4}}^{\text{SerDes}}$$

### 3.4 热

$$\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b},\qquad \mathbf{T} \le T_{\max} \cdot \mathbf{1}$$

gap = 0 假设下 $G_{ij} = k \cdot t$（常数），$G_{ii} = \frac{1}{R_{vert}} + \sum_{j \neq i} |G_{ij}|$。

$P_{peak}(B)$ 随 $B$ 线性增长 → rhs 随 $B$ 线性收紧。

### 3.5 翘曲

> **状态（2026-08-13）：移出论文约束集。** 实现（`WarpModel`）与测试（test0402）保留作技术记录，但 LP 实验与可行域图不启用本约束。理由：①die 间温差只是 CTE 失配翘曲的间接代理，真实翘曲由多层界面、全局弯曲形态、瞬态工况共同决定，标量代理撑不起；②$\Delta T_{\max}$ 缺文献支撑；③当前均匀场景下约束恒不绑定，是花瓶。待热保真度（MFIT 温度场）数据就位后再决定是否复活。论文约束集只保留温度极限（§3.4）。

物理来源：Si die（CTE $\sim$3 ppm/°C）和 organic substrate（CTE $\sim$15 ppm/°C）热膨胀系数失配，bump 处剪切应力最大。温度不均匀 → 各处膨胀量不同 → bump 受力不均 → 翘曲。

当前用 die 间温差作为代理（精细模型应建模 die↔interposer 和 interposer↔substrate 两个界面的温差）：

$$|T_i - T_j| \le \Delta T_{\max} \quad \forall\ \text{邻接}(i,j)$$

等价于 $\mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max} \cdot \mathbf{1}$，其中 $\mathbf{W}$ 每行是一个 $(+1, -1)$ 对（反向再加一行 $(-1, +1)$）。

和温度约束完全同构——代入 $\mathbf{T} = \mathbf{G}^{-1}(\mathbf{P} + \mathbf{b})$ 消去 $\mathbf{T}$：

$$B \cdot \underbrace{\mathbf{W} \cdot \mathbf{K}}_{warp\_coeff} \cdot \mathbf{L} \le \underbrace{\Delta T_{\max} \cdot \mathbf{1} - \mathbf{W} \cdot \mathbf{G}^{-1}(\mathbf{P}_{peak}(B) + \mathbf{b})}_{warp\_rhs}$$

翘曲约束通常比温度约束更紧（$\Delta T_{\max} \sim$ 10-30K vs $T_{\max} - T_{amb} \sim$ 100K）。

### 3.6 布线

$$\sum_{q \in \mathcal{Q}_e} x_{e,q} = \ell_e \quad \forall e$$

$$\sum_{e,q: g \in q} x_{e,q} \le C_g \quad \forall g \in \mathcal{E}_{\text{grid}}$$

$$\sum_{e,q: v \in q} x_{e,q} \le C_v \quad \forall v \in \mathcal{V}_{\text{grid}}$$

---

## 4. 完整 LP（组内子问题，固定 B）

$$\boxed{
\begin{aligned}
\text{find} \quad & \{\mathbf{f}^{(r)}\}_{r \in \mathcal{R}},\; \{\mathbf{L}^{(r)}\}_{r \in \mathcal{R}},\; \mathbf{L},\; \boldsymbol{\ell},\; \mathbf{P},\; \mathbf{N}^{\text{sig}},\; \mathbf{N}^{\text{pwr}},\; \mathbf{T},\; \{x_{e,q}\} \\[8pt]
\text{s.t.} \quad & \forall r \in \mathcal{R}: \\[4pt]
& \qquad \sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)} \quad \forall i,j \\[4pt]
& \qquad L_e^{(r)} = \sum_{(i,j,k): e \in \text{path}} f_{ij}^{k,(r)} \quad \forall e \\[4pt]
& \qquad L_e \ge L_e^{(r)} \quad \forall e \\[8pt]
& \boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L} \\[4pt]
& \mathbf{P} = \mathbf{P}_{peak}(B) + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell} \\[4pt]
& \mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P} \\[4pt]
& \mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell} \\[4pt]
& \mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}(B) \\[8pt]
& \mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b} \\[4pt]
& \mathbf{T} \le T_{\max} \cdot \mathbf{1} \\[4pt]
& \mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max} \cdot \mathbf{1} \\[8pt]
& \sum_{q \in \mathcal{Q}_e} x_{e,q} = \ell_e \quad \forall e \\[4pt]
& \sum_{e,q: g \in q} x_{e,q} \le C_g \quad \forall g \\[4pt]
& \sum_{e,q: v \in q} x_{e,q} \le C_v \quad \forall v \\[8pt]
& \mathbf{f} \ge 0,\; \mathbf{L} \ge 0,\; \boldsymbol{\ell} \ge 0,\; \mathbf{x} \ge 0
\end{aligned}
}$$

其中 $\mathbf{P}_{peak}(B)$ 和 $\mathbf{N}^{\text{total}}(B)$ 都是 $B$ 的已知函数。$B$ 固定时它们退化为常数。

---

## 5. 关键简化与假设

| 假设 | 内容 | 影响 |
|------|------|------|
| gap = 0 | $G_{ij} = k \cdot t$，常数 | G 矩阵不随 B 变 |
| 翘曲代理 | die 间温差替代 bump 界面应力 | **已移出论文约束集（2026-08-13）**，见 §3.5 状态注 |
| 布局固定 | die 相对位置不变，只等比例缩放 | 网格结构不变 |
| 面积 ∝ B | $A_{die}(B) = (d_0 + \alpha_d B)^2$ | bump 总数随 B 变 |
| 功耗 ∝ B | $P_{peak}(B) \propto B$ | 热 rhs 随 B 线性收紧 |
| $S_n$ 共轭类 | Aut(G) 轨道 TODO | 排列代表元偏多（保守） |

---

## 6. B* 二分搜索

每轮二分时，$B$ 变化 → $A_{die}(B)$ 和 $P_{peak}(B)$ 更新 → bump 预算和热 rhs 重算。约束始终是 $L$ 上的线性不等式，凸性不变。

---

## 参考文献

1. Birkhoff, G. "Tres observaciones sobre el algebra lineal." 1946.
2. Valiant, L.G. "A Scheme for Fast Parallel Communication." *SIAM J. Computing*, 1982.
3. Kim, J. et al. "Technology-Driven, Highly-Scalable Dragonfly Topology." *ISCA*, 2008.
4. UCIe Consortium. "UCIe Specification, Revision 2.0." 2024.
5. Berman, A. & Plemmons, R.J. "Nonnegative Matrices in the Mathematical Sciences." *SIAM*, 1994.
6. Zhang, R. et al. "MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D Chiplet Systems." *ACM TACO*, 2025.
7. Passas, G. et al. "The Combined Input-Output Queued Crossbar Architecture for High-Radix On-Chip Switches." *IEEE Micro*, 2015.
