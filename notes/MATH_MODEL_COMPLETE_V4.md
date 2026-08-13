# 晶圆级交换机统一 DSE 框架：完整数理模型（v4）

> **v4（2026-08-13）**：
> - $\mathbf{M}$（die-链路 incidence）进符号表精确定义。
> - 翘曲移出论文约束集（实现保留作技术记录）。
> - 约束按**物理位置**组织；主体保持矩阵记号，线性化形式统一收进 §4 实现注记。
> - 补 C4 pad 约束、on-die 零代价假设。
> - 附实现状态对照表（代码正确性核对的底稿）。

---

## 0. 符号表

| 符号 | 含义 |
|------|------|
| $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ | 逻辑拓扑图（端口为节点，链路为有向边） |
| $\mathcal{E}_{\text{on-die}}$ | die 内链路（零物理代价） |
| $\mathcal{E}_{\text{UCIe}}$ | UCIe 链路（die 间，距离 ≤ UCIe 可达范围） |
| $\mathcal{E}_{\text{SerDes}}$ | SerDes 链路（组间，经 C4 出 interposer） |
| $B$ | 端口带宽（二分搜索确定 $B^*$） |
| $\mathcal{R}$ | 排列代表元集合（$S_n$ 共轭类近似，Aut(G) TODO） |
| $\mathbf{D}^{(r)}$ | 模式 $r$ 的排列需求矩阵（外生固定） |
| $\mathbf{f}^{(r)}$ | 模式 $r$ 的分流变量 |
| $\mathbf{L}^{(r)}, \mathbf{L}$ | 模式 $r$ 负载；负载包络 $\mathbf{L} = \max_r \mathbf{L}^{(r)}$（共享变量） |
| $\boldsymbol{\ell}$ | 物理 lane 数：$\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ |
| $\mathbf{S}_{\text{bw}}$ | 每 lane 带宽对角阵（on-die 取 $\infty$） |
| $\mathbf{S}_{\text{dyn}}$ | 每 lane 动态功耗对角阵（on-die 取 0） |
| $\mathbf{M}$ | **die-链路 incidence**：$M_{v,e}=1 \iff$ 链路 $e$ 的源或宿是 die $v$（有向链路两端 die 各记一次；on-die 两端同 die 只记一次） |
| $V_{dd}, I_{bump}$ | 供电电压；单 bump 载流能力 |
| $p, \eta$ | bump pitch；阵列面积利用率 |
| $\mathbf{N}^{\text{total}}(B)$ | μbump 总数：$N_v^{\text{total}} = \eta \cdot A_{die}(B)/p^2$ |
| $\mathbf{S}_{\text{in}}$ | 功率-bump 换算对角阵：$[\mathbf{S}_{\text{in}}]_{vv} = V_{dd} \cdot I_{bump}$ |
| $P_{peak}(B)$ | die 峰值功耗：$P_{peak}(B) = P_0 + \beta_P \cdot B$ |
| $\mathbf{P}$ | die 功耗向量：$\mathbf{P} = \mathbf{P}_{peak}(B) + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}$ |
| $\mathbf{G}, \mathbf{b}$ | 热导矩阵（对角占优 M-矩阵，$\mathbf{G}^{-1}\ge 0$）；环境温度贡献向量 |
| $\mathbf{T}, T_{\max}$ | die 温度：$\mathbf{G}\cdot\mathbf{T} = \mathbf{P} + \mathbf{b}$；结温上限 |
| $\mathbf{x}$ | 布线分配变量（链路 × 候选路径） |
| $\mathbf{A}, \mathbf{R}$ | 布线 incidence：$\mathbf{A}\mathbf{x} = \boldsymbol{\ell}$（需求）；$\mathbf{R}\mathbf{x} \le \mathbf{C}$（容量） |
| $N_{C4}^{\text{SerDes}}$ | C4 信号焊球中分配给 SerDes 的份额 |

---

## 1. 变量空间

全部约束共享同一组变量：$\mathbf{f},\; \mathbf{L},\; \boldsymbol{\ell},\; \mathbf{P},\; \mathbf{N},\; \mathbf{T},\; \mathbf{x}$，以及标量 $B$。$\boldsymbol{\ell}$ 是唯一的物理桥梁：

$$
\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}
\qquad\Longrightarrow\qquad
\mathbf{P} = \mathbf{P}_{peak}(B) + \mathbf{M}\mathbf{S}_{\text{dyn}}\boldsymbol{\ell}
$$

---

## 2. 按位置的模型约束

### 2.1 路由层（拓扑，与位置无关）

$$
\forall r \in \mathcal{R}:
\qquad
\sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)},\qquad
\mathbf{L}^{(r)} = \mathcal{P}_r \cdot \mathbf{f}^{(r)},\qquad
\mathbf{L} \ge \mathbf{L}^{(r)}
$$

（$\mathcal{P}_r$ 为模式 $r$ 的路径 incidence；求解用 $\min \sum_e L_e$ 压包络下界。）

### 2.2 die 内（on-die）

$$
S_{\text{bw},e} = \infty,\quad S_{\text{dyn},e} = 0 \qquad \forall e \in \mathcal{E}_{\text{on-die}}
$$

$\ell_e \to 0$，不产生 bump、热、布线需求。

### 2.3 die ↔ interposer 界面（μbump）

$$
\mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell},
\qquad
\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P},
\qquad
\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}(B)
$$

信号 lane 与电源共享同一批焊球——零和竞争。

### 2.4 interposer 布线层

$$
\mathbf{A} \cdot \mathbf{x} = \boldsymbol{\ell},
\qquad
\mathbf{R} \cdot \mathbf{x} \le \mathbf{C}
\qquad
\left(\mathbf{R} = \begin{bmatrix}\mathbf{R}_{\text{edge}} \\ \mathbf{R}_{\text{vert}} \\ \mathbf{R}_{\text{pad}}\end{bmatrix},\;
\mathbf{C} = \begin{bmatrix}\mathbf{C}_{\text{edge}} \\ \mathbf{C}_{\text{vert}} \\ \mathbf{C}_{\text{pad}}\end{bmatrix}\right)
$$

边容量、点容量、C4 pad 容量统一为一条容量不等式。

### 2.5 interposer 热系统

$$
\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b},
\qquad
\mathbf{T} \le T_{\max} \cdot \mathbf{1}
$$

### 2.6 interposer ↔ substrate 界面（C4）

$$
\mathbf{1}^T \cdot \boldsymbol{\ell}_{\text{SerDes}} \;\le\; N_{C4}^{\text{SerDes}}
$$

### 2.7 组间（SerDes 全局链路）

组间链路无独立约束——代价经三个位置体现：C4（2.6）、动态功耗（进 2.3 与 2.5）、pad 容量（2.4）。拓扑侧在 2.1 统一处理。

### 2.8 die 缩放模型

$$
d(B) = d_0 + \alpha_d \cdot B,
\qquad
A_{die}(B) = d(B)^2,
\qquad
P_{peak}(B) = P_0 + \beta_P \cdot B
$$

（实现状态：文档已定，代码未接入 LP——当前 $\alpha_d = \beta_P = 0$ 特例。）

---

## 3. 完整 LP（固定 $B$）

$$
\boxed{
\begin{aligned}
\text{find} \quad & \{\mathbf{f}^{(r)}\}_{r\in\mathcal{R}},\; \{\mathbf{L}^{(r)}\},\; \mathbf{L},\; \boldsymbol{\ell},\; \mathbf{P},\; \mathbf{N}^{\text{sig}},\; \mathbf{N}^{\text{pwr}},\; \mathbf{T},\; \mathbf{x} \\[6pt]
\text{s.t.} \quad & \text{（2.1）}\;\; \textstyle\sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)},\quad
\mathbf{L}^{(r)} = \mathcal{P}_r \mathbf{f}^{(r)},\quad
\mathbf{L} \ge \mathbf{L}^{(r)} \qquad \forall r \\[6pt]
& \text{（2.2）}\;\; S_{\text{bw},e}=\infty,\; S_{\text{dyn},e}=0 \;\; \forall e \in \mathcal{E}_{\text{on-die}} \\[6pt]
& \boldsymbol{\ell} = B\, \mathbf{S}_{\text{bw}}^{-1} \mathbf{L},\qquad
\mathbf{P} = \mathbf{P}_{peak}(B) + \mathbf{M}\mathbf{S}_{\text{dyn}}\boldsymbol{\ell} \\[6pt]
& \text{（2.3）}\;\; \mathbf{N}^{\text{sig}} = \mathbf{M}\boldsymbol{\ell},\quad
\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1}\mathbf{P},\quad
\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}(B) \\[6pt]
& \text{（2.4）}\;\; \mathbf{A}\mathbf{x} = \boldsymbol{\ell},\qquad \mathbf{R}\mathbf{x} \le \mathbf{C} \\[6pt]
& \text{（2.5）}\;\; \mathbf{G}\mathbf{T} = \mathbf{P} + \mathbf{b},\qquad \mathbf{T} \le T_{\max}\mathbf{1} \\[6pt]
& \text{（2.6）}\;\; \mathbf{1}^T \boldsymbol{\ell}_{\text{SerDes}} \le N_{C4}^{\text{SerDes}} \\[6pt]
& \mathbf{f} \ge 0,\;\; \mathbf{L} \ge 0,\;\; \mathbf{x} \ge 0
\end{aligned}
}$$

组内/组间分离：$B^* = \min(B^*_{\text{intra}},\; B^*_{\text{inter}})$——组内用 $\mathcal{E}_{\text{UCIe}}$ + μbump；组间用 $\mathcal{E}_{\text{SerDes}}$ + C4 + 套娃热（组粒度聚合，见 plan_inter_group）。

---

## 4. 线性化与预计算（实现注记）

主体约束（§2/§3）是物理形式。LP 求解前做一次消元与预计算，全部系数成为常数：

**热**：消去 $\mathbf{T},\mathbf{P}$（利用 $\mathbf{G}^{-1}\ge 0$）：

$$
B \cdot \underbrace{\mathbf{G}^{-1}\mathbf{M}\mathbf{S}_{\text{dyn}}\mathbf{S}_{\text{bw}}^{-1}}_{\mathbf{K}} \cdot \mathbf{L}
\;\le\; \underbrace{T_{\max}\mathbf{1} - \mathbf{G}^{-1}(\mathbf{P}_{peak}(B)\cdot\mathbf{1} + \mathbf{b})}_{\mathbf{rhs}}
$$

**μbump**：动态功耗的 bump 需求折进 lane 系数，静态功耗留在 rhs 取整：

$$
\textstyle\sum_{e\in\delta(v)} \frac{1}{S_{\text{bw},e}}\left(1+\frac{S_{\text{dyn},e}}{V_{dd}I_{bump}}\right) B\,L_e
\;\le\; N_v^{\text{total}}(B) - \left\lceil\frac{P_0}{V_{dd}I_{bump}}\right\rceil
$$

**L0 精度**（粗筛）：$\mathbf{1}^T\mathbf{P} \le A_{ip}\cdot q_{\max}$。

---

## 5. 关键简化与假设

| 假设 | 内容 | 影响 |
|------|------|------|
| 最坏情况稳态 | 所有模式同时以包络负载运行 | 保守（温度上界） |
| gap = 0 | 网格紧贴，$\mathbf{G}$ 不随 $B$ 变 | 热矩阵预计算 |
| 布局固定 | die 相对位置不变 | 网格结构不变 |
| 集总 $R_{vert}$ | die→ambient 全路径一个热阻 | die 级热粒度（B7 待对标） |
| $S_n$ 共轭类 | 代表元用整数分拆生成 | 偏保守（Aut(G) TODO） |
| on-die 零代价 | die 内链路不计物理代价 | 高估 $B^*$（die 内物理待建） |
| 套娃热 | 组间把 interposer 聚合为单热节点 | 丢组内温度梯度（论文交代） |

---

## 6. B* 二分搜索

可行性关于 $B$ 单调（$B$ 越大物理约束越紧），二分收敛：

```
lo 可行, hi 不可行; while hi − lo > step: mid=(lo+hi)/2, 可行→lo=mid, 否则 hi=mid
```

每轮固定 $B$ → 系数与 rhs 为常数 → LP 线性。查询按 `(query_id, B, cache_key)` 缓存。

---

## 7. 实现状态对照表（代码正确性核对底稿）

| 约束 | 代码 | 状态 |
|------|------|------|
| 2.1 路由 | `SelectedEnvelopeModel` | ✓ |
| 2.2 on-die | `lp/builder.py`（lr=∞/ppl=0） | ✓ |
| 2.3 μbump | `BumpModel` | ✓ |
| 2.4 布线 | `WiringModel` | ✓（未进 exp 场景） |
| 2.5 热 L1 | `SteadyStateModel` + `ThermalNetworkBuilder` | ✓ |
| 2.5 热 L0 | `GlobalPowerModel` | ✓（无 cache_key） |
| 2.6 C4 | `C4Model` | ✓ |
| 2.7 组间 | — | 待建（plan_inter_group S2） |
| 2.8 die 缩放 | — | **未实现** |

---

## 参考文献

1. Birkhoff, G. "Tres observaciones sobre el algebra lineal." 1946.
2. Valiant, L.G. "A Scheme for Fast Parallel Communication." *SIAM J. Computing*, 1982.
3. Kim, J. et al. "Technology-Driven, Highly-Scalable Dragonfly Topology." *ISCA*, 2008.
4. UCIe Consortium. "UCIe Specification, Revision 2.0." 2024.
5. Berman, A. & Plemmons, R.J. "Nonnegative Matrices in the Mathematical Sciences." *SIAM*, 1994.
6. Zhang, R. et al. "MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D Chiplet Systems." *ACM TACO*, 2025.
7. Landman, B.S. & Russo, R.L. "On a Pin Versus Block Relationship for Partitions of Logic Graphs." *IEEE Trans. Computers*, 1971.
