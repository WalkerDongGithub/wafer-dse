# 晶圆级交换机 DSE：统一数理模型

> **核心主张**：可行性 = $\mathbf{L}$ 落入四个线性多面体的交集。$\mathbf{L}$（链路负载向量）是连接性能、几何、功耗、布线的唯一桥梁。

---

## 0. 符号

| 符号 | 含义 |
|---|---|
| $\mathbf{L} = (L_e)_{e \in \mathcal{E}}$ | 每条链路的归一化负载 |
| $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ | die 为节点、链路为边的物理图 |
| $\delta(v)$ | die $v$ 上 incident 链路的集合 |
| $\mathcal{P}_e$ | 指示集：哪些 $(i,j)$ 的路由经过 $e$ |
| $B$ | 端口目标带宽（800 Gbps） |
| $R_e$ | 链路 $e$ 的 lane 速率（布线决定） |
| $N_v$ | die $v$ 的信号 bump 预算（给定） |
| $V_{\text{dd}}, I_{\text{bump}}$ | 供电电压、单 bump 载流 |

---

## 1. 性能约束

$N$ 端口，每端口速率 $B$，归一化发出 1 单位。$\mathbf{D} \in \mathcal{D}$ 为双随机流量矩阵。分流变量 $f_{ij}^k$。

$$\boxed{
\mathcal{L}_{\text{perf}} = \Big\{ \mathbf{L} \ge 0 \;\Big|\; \exists(\mathbf{D}, \mathbf{f}) : \;
    \mathbf{D} \in \mathcal{D},\;
    \sum_k f_{ij}^k = D_{ij},\;
    \sum_{(i,j,k) \in \mathcal{P}_e} f_{ij}^k \le L_e \;\; \forall e \Big\}
}$$

$\mathcal{L}_{\text{perf}}$ 给 $\mathbf{L}$ 一个**下界**（严格必要条件，现实乘 $\eta_{\text{impl}} \approx 0.8$）。

---

## 2. 几何约束

每条链路 $e$ 消耗 $L_e \cdot B/R_e$ 条 lane。信号 lane + 电源 bump 竞争 die $v$ 的 bump 预算 $N_v$：

$$\boxed{\sum_{e \in \delta(v)} L_e \cdot \frac{B}{R_e} + \frac{P_v}{V_{\text{dd}} I_{\text{bump}}} \le N_v \qquad \forall v \in \mathcal{V}}$$

等价于 $\mathbf{M} \cdot \mathbf{L} \le \mathbf{b}$，$M_{v,e} = B/R_e$（$e \in \delta(v)$）。

---

## 3. 功耗约束

### 3.1 单 die 功耗

$$P_v = \underbrace{P_{\text{static}} + M \cdot B \cdot E_{\text{switch}}}_{P_{0v}} + \sum_{e \in \delta(v)} c_e L_e, \qquad c_e = \frac{B}{R_e} \cdot P_{\text{lane}}(R_e)$$

传导：$L_e \to L_e B$ Gbps $\to L_e B/R_e$ lane $\to c_e L_e$ W。每步乘常数 → 线性。

### 3.2 热约束

晶圆级热网络 $\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}_{\text{thermal}}$，$\mathbf{G}$ 为 M-矩阵（$\mathbf{G}^{-1} \ge 0$）。$\mathbf{T} \le T_{\text{max}}$ 等价于：

$$\boxed{\mathbf{C} \cdot \mathbf{L} \le \mathbf{G} \cdot (T_{\text{max}} \cdot \mathbf{1}) - \mathbf{b}_{\text{thermal}} - \mathbf{P}_0}$$

$P_v$ 同时进入几何约束（§2）的电源 bump 项——$\mathbf{L}$ 交叉连接几何和功耗。

---

## 4. 布线约束

### 4.1 Placement

die 放到 interposer 网格位置上：

$$p: \mathcal{V} \to \mathcal{Z} = \{0,\ldots,N-1\}^2 \quad \text{（单射）}$$

$$d_e(p) = \Delta \cdot (|x_u - x_v| + |y_u - y_v|)$$

### 4.2 距离 → 标准 → lane

距离决定互连标准，标准决定 lane 速率：

$$R_e(p) = \phi(d_e(p))$$

$\phi$ 为分片常数函数（UCIe 32G 短距 / SerDes 112G 长距 / ...）。固定 placement 后 $R_e$ 固定。$\phi$ 可线性松弛以降低求解难度。

$$d_e(\mathbf{L}, p) = L_e \cdot \frac{B}{R_e(p)}$$

### 4.3 布线 incidence 约束

信号 lane + 电源走线共享 interposer 金属层。对每条 grid 边 $g$：

$$\boxed{\sum_{e \in \mathcal{E}} a_{g,e}(p) \cdot d_e(\mathbf{L}, p) + \kappa \cdot I_g(\mathbf{L}, p) \le C_{\text{total}} \qquad \forall g \in \mathcal{E}_{\text{grid}}}$$

- $a_{g,e}(p) \in \{0,1\}$：链路 $e$ 的 Manhattan 路径是否经过 grid 边 $g$
- $I_g$：grid 边 $g$ 上的电源电流，$\propto \sum_v P_v \propto \mathbf{L}$
- $\kappa$：电流 → 等效 lane 换算系数
- $C_{\text{total}} = L_{\text{max}} \cdot C_0$：grid 边物理容量（层数 × 每层 lane 数）

### 4.4 布线多面体

固定 $p$ 后，$\mathbf{A}(p)$、$\mathbf{R}(p)$ 均为常数：

$$\boxed{\mathcal{L}_{\text{routing}}(p) = \left\{ \mathbf{L} \ge 0 \;\middle|\; \mathbf{A}(p) \cdot \text{diag}(B/R_e) \cdot \mathbf{L} \le \mathbf{c} \right\}}$$

**与几何约束 $\mathbf{M} \cdot \mathbf{L} \le \mathbf{b}$ 完全同构。** $\mathbf{c}$ 是扣除电源后的剩余容量向量。

### 4.5 placement 与几何的交叉

$p$ 同时决定 die-to-interposer 分组（$\mathcal{V}_k = \{v : p(v) \in Z_k\}$），几何约束的 $N_v$ 按 interposer 汇总。$p$ 固定后 $\mathcal{L}_{\text{geom}}$ 和 $\mathcal{L}_{\text{routing}}$ 均固定。

> **布线创新点**：网格架构、placement、incidence 约束形式均沿袭 FPIA（Jiao et al., TCASI 2024）。本文贡献在将此约束与性能/几何/功耗联立为 $\mathbf{L}$ 上的统一线性系统。

---

## 5. 统一可行集

$$\boxed{
\begin{aligned}
\text{find} \quad & \mathbf{L} \\[4pt]
\text{s.t.} \quad & \mathbf{L} \in \mathcal{L}_{\text{perf}} && \text{(1) 性能：下界} \\[4pt]
& \mathbf{M} \cdot \mathbf{L} \le \mathbf{b} && \text{(2) 几何：上界} \\[4pt]
& \mathbf{C} \cdot \mathbf{L} \le \mathbf{d} && \text{(3) 功耗：上界} \\[4pt]
& \exists p \in \mathcal{P}: \mathbf{A}(p) \cdot \text{diag}(B/R_e(p)) \cdot \mathbf{L} \le \mathbf{c} && \text{(4) 布线：上界}
\end{aligned}}
$$

## 6. 两层 DSE 架构

### 6.1 搜索视角：芯粒库驱动

离散决策不由 DSE 自由优化——它们由**芯粒库**决定。可选的交换芯片就那么几种：每种有固定的 die 面积 $A_{\text{die}}$、crossbar 端口数 $M$、功耗 $P_0$、bump pitch $p_{\text{ubump}}$。DSE 的角色不是"设计最优 die"，而是回答：

> **给定芯粒库，哪些选型组合能集成到晶圆上？哪个物理约束会杀死不可行的组合？**

网格划分 $N$ 反过来由所选芯粒的尺寸决定——大 die → 少 zone，细粒度 die → 多 zone。$N$ 和芯粒选型是绑定的。

### 6.2 两层结构

```
═══════════════════════════════════════════════════════════
外层（离散枚举）
  ├── 拓扑选择：谁和谁连 → 𝒢 = (𝒱, ℰ)
  ├── 布局选择：谁放哪   → p: 𝒱 → 𝒵
  └── 策略：SA / QP / 穷举（小规模）→ 精简枚举点
───────────────────────────────────────────────────────────
内层（纯线性，固定 𝒢 和 p）
  find  L
  s.t.  L ∈ ℒ_perf              (1) 性能 LP 多面体
        M·L ≤ b                 (2) 几何 incidence 约束
        C·L ≤ d                 (3) 功耗 + 热传导
        A·diag(B/R_e)·L ≤ c     (4) 布线 incidence 约束
───────────────────────────────────────────────────────────
输出：L 存在 → feasible，不存在 → infeasible
      对偶变量 → 识别 binding constraint
═══════════════════════════════════════════════════════════
```

**外层**：从芯粒库选型，确定 $\mathcal{G}$ 和 $p$。每个芯粒有固定参数（$A_{\text{die}}, M, P_0, p_{\text{ubump}}$），选型即定常数。面积约束退化为 $A_{\text{circuit}} \le A_{\text{die}} \le A_{\text{max}}$ 的常数检查，不进入内层 LP。bump 预算 $N_v = \eta \rho A_{\text{die}}$ 随之固定。

**内层**：唯一变量 $\mathbf{L}$，四组线性不等式。一个 LP 判 feasible/infeasible，对偶变量精确指出哪个约束在边界上。

**整个 DSE = 外层枚举离散架构 + 内层解一个多约束线性耦合的超级 LP。**
