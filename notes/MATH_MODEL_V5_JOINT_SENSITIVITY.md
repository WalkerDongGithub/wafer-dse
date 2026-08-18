# 组内/组间分离模型（v5）

> **v5（2026-08-18）**：聚焦模型建构本身，移除求解流程与灵敏度分析。
> 核心结构：三层物理实体（die/Interposer/Substrate）+ 三段约束（die 段/I2I 段/跨层耦合段）+ 静态 oblivious Valiant 性能包络。
> 本文件**取代** `design_joint_model.md`、`design_sensitivity.md`、v5.x 系列草案。
> 前置：`MATH_MODEL_COMPLETE_V4.md`（§0–§7 总纲）。

---

## 0. 核心定位与物理图像

### 0.1 模型定位：$B$ 作为拓扑排布的特征值

传统 DSE 输出"可行/不可行"的二元判断，无法刻画可行域的大小——而可行与不可行之间存在大量灰色地带（某些方案在严格约束下不可行，放宽某个约束即可行）。本模型用 $B$（无阻塞带宽）作为拓扑排布的特征值，将"可行性"从二元判断提升为**可行域大小的连续刻画**：$B$ 越大，该拓扑排布容忍的工况越宽，越 robust。

$B$ 是交换机最自然的特征值——其本身就是核心性能指标，与工程评价直接对齐。

**本模型在 DSE pipeline 中的位置**：v5 算出初始 $B^*$（worst-case 下的特征值），从大量设计空间中筛出有潜力的拓扑；后续 DSE 工作通过逐步放宽约束、提高路由效率，将 $B$ 从初始值上推，看能否达到 $B_{\text{target}}$。例：初始 $B^* = 600\text{G}$，放宽约束后可上推至 $800\text{G}$。本模型是整个 DSE 的第一步，也是最重要的一环——没有 $B^*$，后续 DSE 无从展开。

### 0.2 物理分层（核心图像）

模型严格对应三层物理实体：
- **die 级（Interposer 内部）**：Interposer 内部的 die 之间的互连。关注 die 级的温度分布 $\mathbf{T}_{\text{die}}$ 和功耗 $\mathbf{P}_{\text{die}}$。热网络粒度为 die。
- **Interposer 级（聚合实体）**：一个 Interposer 包含多个 die，通过 $\mathbf{M}_{\text{die} \to \text{inter}}$ 聚合得到 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$。
- **sub 级（Substrate 层面）**：Interposer 之间通过 Substrate 的互连。关注 Interposer 挂载点的温度 $\mathbf{T}_{\text{sub}}$。热网络粒度为 Interposer。

### 0.2 跨层耦合：Substrate 是桥梁

三层实体通过**边界条件**耦合：
- **Substrate → Interposer**：Substrate 上某点的温度 $T_{\text{sub},i}$ (其中 $i$ 是 Interposer 的索引) 是 Interposer 的 Ambient（环境温度），决定 $\mathbf{b}_{\text{inter}}$。
- **die → Interposer**：多个 die 的功耗 $\mathbf{P}_{\text{die}}$ 通过 $\mathbf{M}_{\text{die} \to \text{inter}}$ 聚合成 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$。
- **Interposer → Substrate**：Interposer 总功耗 $P_{\text{inter},i}$ 是 Substrate 的 Heat Source（热源），决定 Substrate 热方程的右端项。

**三层在数学上独立**，通过共享变量（$\mathbf{b}_{\text{inter}}$ 和 $\mathbf{P}_{\text{inter}}$）联立成单一模型。

### 0.3 SerDes PHY 功耗物理落点

SerDes PHY 集成在 switch ASIC die 内，功耗进 die 级功耗 $\mathbf{P}_{\text{die}}$。**不存在**独立的 $\mathbf{P}_{\text{sub}}$ 向量。Substrate 层面的热源完全来自 Interposer 的总功耗 $\mathbf{P}_{\text{inter}}$。

---

## 1. 增补符号表（V4 §0 之外新增）

| 符号 | 含义 | 单位 | 备注 |
|------|------|------|------|
| $\mathcal{E}_{\text{D2D}}, \mathcal{E}_{\text{I2I}}$ | D2D/I2I 链路集（$\subseteq \mathcal{E}_{\text{UCIe}} \cup \mathcal{E}_{\text{on-die}}$） | — | — |
| $\mathbf{L}_{\text{D2D}}, \mathbf{L}_{\text{I2I}}$ | D2D/I2I 链路负载向量（共享标量 $B$） | Gbps | — |
| $\boldsymbol{\ell}_{\text{D2D}}, \boldsymbol{\ell}_{\text{I2I}}$ | D2D/I2I 信号 lane 数向量 | — | — |
| $\mathbf{T}_{\text{die}}, \mathbf{T}_{\text{inter}}, \mathbf{T}_{\text{sub}}$ | 温度向量（下标表物理层级：die/inter/sub） | K | 三层独立温度场 |
| $\mathbf{P}_{\text{die}}, \mathbf{P}_{\text{inter}}$ | 功耗向量（下标表层级；$\mathbf{P}_{\text{inter}}$ 由 §4 (C3) 定义） | W | $\mathbf{P}_{\text{die}} = \mathbf{P}_{\text{die}}^{\text{peak}}(B) + \mathbf{P}_{\text{D2D}}^{\text{dyn}} + \mathbf{P}_{\text{I2I}}^{\text{dyn}}$ |
| $\mathbf{P}_{\text{die}}^{\text{peak}}(B)$ | die 峰值功耗（$B$ 的二次函数） | W | 由材料/工艺决定 |
| $\mathbf{P}_{\text{D2D}}^{\text{dyn}}, \mathbf{P}_{\text{I2I}}^{\text{dyn}}$ | D2D/I2I 链路动态功耗 | W | — |
| $\mathbf{b}_{\text{die}}, \mathbf{b}_{\text{inter}}, \mathbf{b}_{\text{sub}}$ | 散热边界项（下标表层级；$\mathbf{b}_{\text{die}}, \mathbf{b}_{\text{sub}}$ 预计算常数，$\mathbf{b}_{\text{inter}}$ 由 §4 (C4) 定义） | W | — |
| $\mathbf{G}_{\text{die}}, \mathbf{G}_{\text{sub}}, \mathbf{G}_{\text{inter}}^{\text{amb}}$ | 热导矩阵（下标表层级；T 和 P 的线性关系；$\mathbf{G}_{\text{inter}}^{\text{amb}}$ 为 Interposer 向 Substrate 散热的边界热导） | W/K | — |
| $\mathbf{M}_{X \to Y}$ | 隶属求和映射（$X \to Y$ 方向，详见下方注） | — | die→inter, D2D→die, I2I→die, route→D2D, f→D |
| $\mathbf{S}_{\text{D2D}}^{\text{bw}}, \mathbf{S}_{\text{I2I}}^{\text{bw}}$ | 带宽系数（每 lane 承载比特率） | Gbps/lane | — |
| $\mathbf{S}_{\text{D2D}}^{\text{dyn}}, \mathbf{S}_{\text{I2I}}^{\text{dyn}}$ | 每 lane 动态功耗对角阵 | W/lane | — |
| $\mathbf{N}_{\text{C4}}^{\text{pwr}}, \mathbf{N}_{\text{C4}}^{\text{total}}$ | 电源 C4 数（共享变量，由 §4 (C2) 定义）/ 总 C4 数（常量） | — | — |
| $\mathbf{S}_{\text{C4}}^{\text{pwr}}$ | 每个 C4 bump 承载功率 | W/bump | — |
| $\mathbf{N}_{\text{die}}^{\text{pwr}}, \mathbf{N}_{\text{die}}^{\text{total}}(B)$ | die 侧电源 μbump 数 / 总 μbump 数（$B$ 的二次函数） | — | — |
| $\mathbf{W}, \mathbf{C}$ | interposer 布线资源占用矩阵 / 容量向量（多商品流，V4 §2.4） | — | — |

**注**：
- **命名约定**：下标表示"物理层级/主体"，上标表示"属性/修饰符"。
- **关于 $\mathbf{M}$ 的统一说明**：所有 $\mathbf{M}_{X \to Y}$ 矩阵都是**隶属求和关系**——将 $X$ 空间的向量按归属关系（求和）映射到 $Y$ 空间。元素为 0/1（或加权 0/1），表示 $X$ 中若干分量隶属于 $Y$ 中某一分量。下标 $X \to Y$ 明确映射方向。模型中出现的 $\mathbf{M}_{X \to Y}$ 包括：die→inter（功耗聚合）、D2D→die（lane→μbump）、I2I→die（SerDes lane→μbump/PHY）、route→D2D（路径流量→链路 lane）、f→D（分流→需求）。

---

## 2. die 段（单一模型的一部分）

此段含 D2D（Interposer 内部）的性能侧 + 物理约束：

$$
\boxed{
\begin{aligned}
\text{find}\quad & \mathbf{L}_{\text{D2D}},\; \boldsymbol{\ell}_{\text{D2D}},\; \mathbf{P}_{\text{die}},\; \mathbf{T}_{\text{die}},\; \mathbf{T}_{\text{inter}},\; \mathbf{x}_{\text{D2D}},\; \mathbf{b} \\[6pt]
\text{s.t.}\quad & \text{(2a) 性能包络（由 §7 静态 oblivious Valiant 路由下的子 LP 预解出）：} \\
&\quad \mathbf{L}_{\text{D2D}} \ge \mathbf{L}_{\text{D2D}}^{*} \\
& \text{(2b) lane 数：}\;\boldsymbol{\ell}_{\text{D2D}} = \left(\mathbf{S}_{\text{D2D}}^{\text{bw}}\right)^{-1}\,(B\,\mathbf{L}_{\text{D2D}}) \\
& \text{(2c) die 级功耗：}\\
&\quad \mathbf{P}_{\text{die}} = \mathbf{P}_{\text{die}}^{\text{peak}}(B) + \mathbf{P}_{\text{D2D}}^{\text{dyn}} + \mathbf{P}_{\text{I2I}}^{\text{dyn}} \\
&\quad \mathbf{P}_{\text{D2D}}^{\text{dyn}} = \mathbf{M}_{\text{D2D} \to \text{die}}\,\mathbf{S}_{\text{D2D}}^{\text{dyn}}\,\boldsymbol{\ell}_{\text{D2D}} \\
&\quad \mathbf{P}_{\text{I2I}}^{\text{dyn}} = \mathbf{M}_{\text{I2I} \to \text{die}}\,\mathbf{S}_{\text{I2I}}^{\text{dyn}}\,\boldsymbol{\ell}_{\text{I2I}} \\
& \text{(2d) interposer 布线（多商品流）：}\\
&\quad \mathbf{M}_{\text{route} \to \text{D2D}}\,\mathbf{x}_{\text{D2D}} = \boldsymbol{\ell}_{\text{D2D}} \\
&\quad \mathbf{W}\,\mathbf{x}_{\text{D2D}} \le \mathbf{C} \\
&\qquad \left(\mathbf{W} = \begin{bmatrix}\mathbf{W}_{\text{edge}} \\ \mathbf{W}_{\text{vert}} \\ \mathbf{W}_{\text{pad}}\end{bmatrix},\;\;\mathbf{C} = \begin{bmatrix}\mathbf{C}_{\text{edge}} \\ \mathbf{C}_{\text{vert}} \\ \mathbf{C}_{\text{pad}}\end{bmatrix}\right) \\
& \text{(2e) 热方程：}\\
&\quad \mathbf{G}_{\text{die}}\begin{bmatrix}\mathbf{T}_{\text{die}} \\ \mathbf{T}_{\text{inter}}\end{bmatrix} = \begin{bmatrix}\mathbf{P}_{\text{die}} \\ \mathbf{0}\end{bmatrix} + \begin{bmatrix}\mathbf{b}_{\text{die}} \\ \mathbf{b}_{\text{inter}}\end{bmatrix} \\
&\quad \begin{bmatrix}\mathbf{T}_{\text{die}} \\ \mathbf{T}_{\text{inter}}\end{bmatrix} \le T_{\max}\mathbf{1} \\
& \mathbf{L}_{\text{D2D}} \ge 0 \\
& \mathbf{x}_{\text{D2D}} \ge 0
\end{aligned}
}$$

**关于 $\mathbf{G}_{\text{die}}$ 和 $\mathbf{G}_{\text{sub}}$（热导矩阵）**：根据传热学基本原理算出，$\mathbf{T}$ 和 $\mathbf{P}$ 永远是线性关系。影响 $\mathbf{G}$ 的两个旋钮：
1. **网格粒度**：决定 G 的维度。粒度越粗，G 越小（早筛模型取最粗粒度，如 die 级）；粒度越细，G 越大（如单元级）。
2. **封装方式**：决定 G 的元素值。不同封装（如 2.5D vs 3D 堆叠）有不同的传热路径（散热板、Substrate、underfill 等），进而产生不同的热阻网络和 G 值。
- $\mathbf{b}_{\text{die}}$：常数（die 向散热板散热）
- $\mathbf{b}_{\text{inter}}$：变量（由 §4 (C4) 定义，Interposer 向 Substrate 散热）

---

## 3. I2I 段（单一模型的一部分）

此段含 I2I（Substrate 层面）的约束。$\mathbf{P}_{\text{inter}}$（Interposer 总功耗）和 $\mathbf{b}_{\text{inter}}$（Interposer 边界条件）是共享变量，本段不写其表达式。

$$
\boxed{
\begin{aligned}
\text{find}\quad & \mathbf{L}_{\text{I2I}},\; \boldsymbol{\ell}_{\text{I2I}},\; \mathbf{T}_{\text{sub}},\; \mathbf{P}_{\text{inter}},\; \mathbf{N}_{\text{C4}}^{\text{pwr}} \\[6pt]
\text{s.t.}\quad & \text{(3a) 性能包络（由 §7 静态 oblivious Valiant 路由下的子 LP 预解出）：} \\
&\quad \mathbf{L}_{\text{I2I}} \ge \mathbf{L}_{\text{I2I}}^{*} \\
& \text{(3b) lane 数：}\;\boldsymbol{\ell}_{\text{I2I}} = \left(\mathbf{S}_{\text{I2I}}^{\text{bw}}\right)^{-1}\,(B\,\mathbf{L}_{\text{I2I}}) \\
& \text{(3c) C4 总量（}\mathbf{N}_{\text{C4}}^{\text{pwr}}\text{ 作共享变量）：}\\
&\quad \boldsymbol{\ell}_{\text{I2I}} + \mathbf{N}_{\text{C4}}^{\text{pwr}} \le \mathbf{N}_{\text{C4}}^{\text{total}} \\
& \text{(3d) sub 热方程：}\\
&\quad \mathbf{G}_{\text{sub}}\,\mathbf{T}_{\text{sub}} = \mathbf{P}_{\text{inter}} + \mathbf{b}_{\text{sub}} \\
&\quad \mathbf{T}_{\text{sub}} \le T_{\max}\mathbf{1} \\
& \mathbf{L}_{\text{I2I}} \ge 0
\end{aligned}
}$$

**特点**：
- 不含独立的功耗向量 $\mathbf{P}_{\text{sub}}$，Substrate 的热源完全来自 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$。
- 不含布线约束（Substrate 内走线不考虑，简化模型）。

---

## 4. 跨层耦合段（桥梁连接）

四组等式关系，**定义 §2、§3 中共享变量的表达式**。

$$
\boxed{
\begin{aligned}
\textbf{(C1) μbump 跨层分配（die 侧共享资源）：}\\
& \mathbf{M}_{\text{D2D} \to \text{die}}\,\boldsymbol{\ell}_{\text{D2D}} + \mathbf{M}_{\text{I2I} \to \text{die}}\,\boldsymbol{\ell}_{\text{I2I}} + \mathbf{N}_{\text{die}}^{\text{pwr}} \le \mathbf{N}_{\text{die}}^{\text{total}}(B) \\[6pt]
\textbf{(C2) C4 电源数跨层（电源 C4 依赖 Interposer 总功耗）：}\\
& \mathbf{N}_{\text{C4}}^{\text{pwr}} = \left(\mathbf{S}_{\text{C4}}^{\text{pwr}}\right)^{-1}\,\mathbf{P}_{\text{inter}} \\[6pt]
\textbf{(C3) die → Interposer（功耗聚合）：}\\
& \mathbf{P}_{\text{inter}} = \mathbf{M}_{\text{die} \to \text{inter}}\,\mathbf{P}_{\text{die}} \\[6pt]
\textbf{(C4) sub → Interposer（温度反馈）：}\\
& \mathbf{b}_{\text{inter}} = \mathbf{G}_{\text{inter}}^{\text{amb}}\,\mathbf{T}_{\text{sub}}
\end{aligned}
}$$

**耦合方向与物理含义**：

| 编号 | 方向 | 物理含义 | 性质 |
|------|------|---------|------|
| C1 | 跨层（die 侧） | I2I SerDes PHY 出 die 侧占用 μbump，挤压 D2D 信号预算 | 线性不等式 |
| C2 | inter → C4 | Interposer 总功耗 $\mathbf{P}_{\text{inter}}$ 决定电源 C4 数（每个 C4 bump 承载功率 $\mathbf{S}_{\text{C4}}^{\text{pwr}}$） | 线性等式 |
| C3 | die → inter | die 级功耗聚合成 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$ | 线性等式 |
| C4 | sub → inter | Substrate 温度 $\mathbf{T}_{\text{sub}}$ 决定 Interposer 的 Ambient $\mathbf{b}_{\text{inter}}$ | 线性等式 |

---

## 5. 整体结构

### 5.1 单一模型，三段表述，整体闭合

```
单一模型：
  ├─ §2 die 段（路由 + 功耗 + 布线 + die-interposer 块矩阵热方程）
  │   └─ 块矩阵热方程统一 T_die 和 T_inter 的耦合
  ├─ §3 I2I 段（I2I 路由 + sub 热 + C4 约束）
  └─ §4 跨层耦合段（C1-C4 定义共享变量表达式）
```

**表述上三段分离，整体闭合**：die 段与 I2I 段各有独立约束，通过 §4 跨层耦合段定义共享变量（$\mathbf{b}_{\text{inter}}$、$\mathbf{P}_{\text{inter}}$、$\mathbf{N}_{\text{C4}}^{\text{pwr}}$）使整体闭合，无自由变量。

### 5.2 闭合性

- $\mathbf{b}_{\text{inter}}$、$\mathbf{P}_{\text{inter}}$、$\mathbf{N}_{\text{C4}}^{\text{pwr}}$ 均由 §4 定义，不是自由变量。
- 模型整体有界，无冗余自由度。

---

## 6. 关键假设

| 假设 | 内容 | 影响 |
|------|------|------|
| Substrate 温度均匀 | Interposer 挂载点处 Substrate 温度作为 Interposer 的统一 Ambient | 简化热模型，忽略 Substrate 厚度方向的温度梯度 |
| Interposer 内部热均匀 | die 级热网络刻画 Interposer 内部温度梯度 | 精细热模型 |
| SerDes PHY 在 die 上 | I2I SerDes PHY 集成在 switch ASIC die 内 | PHY 功耗进 $\mathbf{P}_{\text{die}}$ |

---

## 7. 性能模型：静态 oblivious Valiant 路由下的 $L$ 包络最大化

### 7.1 设计选择：放弃 $\mathbf{f}$ 的可变性

若把分流 $\mathbf{f}$ 也当作决策变量，子 LP 会把它变成"攻击网络的工具"——通过选择 $\mathbf{f}$ 让某条链路过载。这违背了 $\mathbf{f}$ 的本意：$\mathbf{f}$ 是**网络设计者**为优化网络而选择的路由方案，不应作为攻击向量。

**决策**：放弃 $\mathbf{f}$ 的可变性，采用**静态 oblivious Valiant 负载均衡**——路由方案在网络设计阶段即固定，对所有 traffic pattern 一视同仁（oblivious）。

### 7.2 物理含义

静态 oblivious Valiant 路由下，网络对所有 traffic pattern 提供相同的路由策略。$L$ 包络在此固定路由下计算得到，**不依赖 $B$**——性能模型可独立于物理模型单独求解。

这是**最严苛的性能约束**：网络必须在 oblivious 路由下满足无阻塞条件（即对所有 traffic pattern 都可承载）。这种"先做足够严格的，再讨论放松"的策略符合早筛模型的定位——先以最严苛标准筛除必然失败的方案，再讨论对大量物理和性能约束逐步降低期待的方法。

### 7.3 $L$ 包络最大化的子 LP

给定静态 oblivious Valiant 路由 $\mathcal{P}$（即 $\mathbf{L} = \mathcal{P}\,\mathbf{f}$ 中的 $\mathcal{P}$ 已固定），性能侧的子 LP 以 $\mathbf{D}$ 为决策变量，最大化某条链路 $e$ 的负载 $L_e$：

$$
\boxed{
\begin{aligned}
\max_{\mathbf{D}}\quad & L_e(\mathbf{D}) \\
\text{s.t.}\quad & \mathbf{L} = \mathcal{P}\,\mathbf{f}(\mathbf{D}) \\
& \mathbf{M}_{\text{f} \to \text{D}}\,\mathbf{f}(\mathbf{D}) = \mathbf{D} \\
& \mathbf{D} \in \text{Birkhoff} \\
& \mathbf{f} \ge 0
\end{aligned}
}
$$

其中：
- $\mathbf{D} \in \text{Birkhoff}$（$N \times N$ 双随机矩阵多面体）是**决策变量**——通过寻找进攻性的 $\mathbf{D}$ 把 $L_e$ 往大了逼
- $\mathcal{P}$ 是**固定的**静态 oblivious Valiant 路由矩阵（非变量）
- $\mathbf{f}(\mathbf{D})$ 是给定 $\mathbf{D}$ 后由 $\mathbf{M}_{\text{f} \to \text{D}}\,\mathbf{f} = \mathbf{D}$ 解出的中间量
- 解出 $\mathbf{D}_e^{*}$ 后，$L_e^{*} = L_e(\mathbf{D}_e^{*})$

### 7.4 $L$ 包络的构造

对每条链路 $e$ 分别求解上述子 LP，得到 $L_e^{*}$。所有链路的 $L_e^{*}$ 组合构成 $L$ 包络：

$$
\mathbf{L}^{*} = (L_1^{*}, L_2^{*}, \dots, L_{|\mathcal{E}|}^{*})^{\top}
$$

该 $\mathbf{L}^{*}$ 作为主 LP (2a)/(3a) 的性能包络输入——主 LP 不再需要枚举 traffic pattern，直接使用 $\mathbf{L}^{*}$ 作为链路负载的下界约束。

**D2D/I2I 两个包络独立**：D2D 段（组内）和 I2I 段（组间）各有独立的 $L$ 包络，分别执行上述子 LP 求解，互不影响。

### 7.5 与主 LP 的对接

主 LP (2a)/(3a) 的路由约束简化为：

$$
\mathbf{L}_{\text{D2D}} \ge \mathbf{L}_{\text{D2D}}^{*},\qquad \mathbf{L}_{\text{I2I}} \ge \mathbf{L}_{\text{I2I}}^{*}
$$

即主 LP 只需保证链路负载不低于性能包络。性能模型与物理模型完全解耦：性能模型一次性产出 $\mathbf{L}^{*}$，物理模型以 $\mathbf{L}^{*}$ 为输入。

---

## 8. 待定案

- [ ] $\mathbf{G}_{\text{die}}^{\text{amb}}$ 的构建
- [ ] 静态 oblivious Valiant 路由矩阵 $\mathcal{P}$ 的具体构造

---
**v5.15 修正日志**：
1.  **用块矩阵形式表示 die 和 interposer 两个温度场的耦合**：
    *   $\mathbf{G}_{\text{die-inter}}[\mathbf{T}_{\text{die}}; \mathbf{T}_{\text{inter}}] = [\mathbf{P}_{\text{die}}; \mathbf{0}] + \mathbf{b}_{\text{die-inter}}$
    *   引入 $\mathbf{G}_{\text{die} \to \text{inter}}$ 和 $\mathbf{G}_{\text{inter} \to \text{die}}$ 热耦合矩阵
    *   引入 $\mathbf{T}_{\text{inter}}$ 和 $\mathbf{b}_{\text{inter}}$ 新符号
2.  **恢复第 3 节 sub 热方程**：Substrate 的热源来自 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$
3.  **恢复第 4 节 C3、C4**：
    *   C3: $\mathbf{P}_{\text{inter}} = \mathbf{M}_{\text{die} \to \text{inter}}\mathbf{P}_{\text{die}}$（die → Interposer 功耗聚合）
    *   C4: $\mathbf{b}_{\text{inter}} = \mathbf{G}_{\text{inter}}^{\text{amb}}\mathbf{T}_{\text{sub}}$（sub → Interposer 温度反馈）

**v5.14 修正日志**：
1.  **用块矩阵形式统一热方程**（清晰展示 die 和 sub 温度场的耦合）：
    *   $\mathbf{G}[\mathbf{T}_{\text{die}}; \mathbf{T}_{\text{sub}}] = [\mathbf{P}_{\text{die}}; \mathbf{0}] + \mathbf{b}$
    *   耦合项（Substrate → die）和 $-\mathbf{M}_{\text{die} \to \text{inter}}$（die → Substrate）整合到块矩阵中
2.  **简化第 3 节**：移除 sub 热方程，保留 I2I 路由和 C4 约束
3.  **简化第 4 节**：移除 C3、C4（已整合到块矩阵），保留 C1、C2（资源耦合）

**v5.13 修正日志**：
1.  **引入 Interposer 物理层级**（明确 agg 是操作不是物理层级）：
    *   $\mathbf{P}_{\text{die}}^{\text{agg}}$ → $\mathbf{P}_{\text{inter}}$：明确是 Interposer 层级的总功耗
    *   $\mathbf{M}_{\text{die} \to \text{agg}}$ → $\mathbf{M}_{\text{die} \to \text{inter}}$：明确映射是 die → Interposer
2.  **更新物理图像**：将两层热网络更新为三层实体（die / Interposer / sub）
3.  **全面更新文档**：更新了 0.3、0.4、0.5、1、3、4、5 节中所有相关符号。

**v5.12 修正日志**：
1.  **统一映射矩阵命名**（所有映射矩阵统一用 M，明确映射方向）：
    *   $\mathbf{A}_{\text{die}}^{\text{agg}}$ → $\mathbf{M}_{\text{die} \to \text{agg}}$：明确是 die 功耗到聚合功耗的映射
    *   $\mathbf{A}$ → $\mathbf{M}_{\text{route} \to \text{D2D}}$：明确是路径流量到 D2D 链路的映射
2.  **全面更新文档**：更新了 1、2、4 节中所有相关符号。

**v5.11 修正日志**：
1.  **修正 M 矩阵命名**（明确映射方向）：
    *   $\mathbf{M}$ → $\mathbf{M}_{\text{D2D} \to \text{die}}$：明确是 D2D lane 到 die 侧的映射
    *   $\mathbf{M}_{\text{PHY}}$ → $\mathbf{M}_{\text{I2I} \to \text{die}}$：明确是 I2I SerDes lane 到 die 侧的映射
2.  **全面更新文档**：更新了 1、2、4 节中所有相关符号。

**v5.10 修正日志**：
1.  **修正 agg 符号命名**（明确聚合主体层级）：
    *   $\mathbf{P}_{\text{agg}}$ → $\mathbf{P}_{\text{die}}^{\text{agg}}$：明确是 die 层级的聚合功耗
    *   $\mathbf{A}_{\text{agg}}$ → $\mathbf{A}_{\text{die}}^{\text{agg}}$：明确是 die 层级的聚合矩阵
2.  **全面更新文档**：更新了 0.4、0.5、1、3、4、5 节中所有相关符号。

**v5.9 修正日志**：
1.  **修正 LaTeX 渲染问题**：
    *   修复了上标堆叠导致的渲染失败（如 $\mathbf{S}_{\text{D2D}}^{\text{bw}}^{-1}$ → $\left(\mathbf{S}_{\text{D2D}}^{\text{bw}}\right)^{-1}$）
    *   修复了第 94 行多余的 `"` 符号
2.  **严格执行命名约定**（下标表层级/主体，上标表属性/修饰符）：
    *   ${\mathbf{P}}^{\text{peak}}(B)$ → $\mathbf{P}_{\text{die}}^{\text{peak}}(B)$
    *   $\mathbf{N}^{\text{total}}_{\text{die}}(B)$ → $\mathbf{N}_{\text{die}}^{\text{total}}(B)$
    *   $\mathbf{N}^{\text{total}}_{\text{C4}}$ → $\mathbf{N}_{\text{C4}}^{\text{total}}$
3.  **符号表更新**：在符号表中添加了 $\mathbf{P}_{\text{die}}^{\text{peak}}(B)$、$\mathbf{N}_{\text{C4}}^{\text{total}}$、$\mathbf{N}_{\text{die}}^{\text{total}}(B)$ 等符号。