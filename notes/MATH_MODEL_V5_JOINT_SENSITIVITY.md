# 组内/组间分离模型（v5）

> **v5**：三层物理实体（die/Interposer/Substrate）+ 三段约束（die 段/I2I 段/跨层耦合段）+ 静态 oblivious Valiant 性能包络。
> 本文件是**全文唯一权威模型文档**——只回答"模型是什么"：唯一参考符号体系 + 唯一参考模型标准 + 必要符号解释 + 必要约束项物理意义。代码服务本文件，不服务 `docs/paper/`（下游产物）；冲突时改代码。
> **释经（派生内容）**：insight 解读见 `notes/INSIGHT_READING.md`；实现对表/参考文献/推导细节见 `notes/IMPLEMENTATION_MAP.md`；模型性质与求解讨论见 `notes/MODEL_PROPERTIES.md`；版本历史见 `notes/V5_CHANGELOG.md`；决策与待定案见 `.dsh/team/decisions.md`；灵敏度/实验设计见 `.dsh/team/artifacts/`。

---

## 0. 模型对象与物理图像

### 0.1 模型对象：额定出入口带宽 $B$

本模型以 $B$（**有服务质量保证的额定出入口带宽**：端口负载不超过 $B$ 时交换按扩展比包络完成）为设计点的量化指标，将"可行性"刻画为**可行域大小的连续量**：$B$ 越大，该拓扑排布容忍的工况越宽。

**双旋钮参数化（要求 R × 约束 C）**——$B$ 是要求与约束的函数，四档可独立组合（正交：R 只作用于性能包络 §7.3，C 只作用于物理 rhs §2.8）：

| 档位 | 要求旋钮 R | 约束旋钮 C | 语义 | B\* 相对大小 |
|---|---|---|---|---|
| **R_qos × C_peak**（默认/最严） | QoS 无阻塞（双随机包络，置换矩阵最坏情形） | 峰值工况（$P_{\text{peak}}(B)=P_0+\beta_P B$） | 参考档，保守下界 | 最低 |
| R_qos × C_rated | QoS 无阻塞 | 额定工况（$\beta_P B$ 项置 0） | 放宽功耗悲观度 | ↑ |
| R_peak × C_peak | 仅出入口峰值（单对包络，§7.3b） | 峰值工况 | 放宽性能要求 | ↑↑ |
| R_peak × C_rated（最松） | 仅出入口峰值 | 额定工况 | 最乐观档 | 最高 |

- **要求旋钮 R**：R_qos = 任意 admissible 流量（双随机）下无阻塞（BvN 置换矩阵最坏情形，§7.3）；R_peak = 仅出入口可达 $B$（单对流量包络 $L_e^{*} = \max_{(i,j)} c_{ij}^{e}$，闭式解，≤ 1，§7.3b）。
- **约束旋钮 C**：C_peak = die 峰值功耗随 $B$ 线性增长（$\beta_P B$ 计入 bump/热 rhs）；C_rated = 峰值项置 0（$P_{\text{peak}} = P_0$，只留静态 + 链路动态功耗，§2.8）。

### 0.2 物理分层

模型严格对应三层物理实体：
- **die 级（Interposer 内部）**：Interposer 内部的 die 之间的互连。关注 die 级的温度分布 $\mathbf{T}_{\text{die}}$ 和功耗 $\mathbf{P}_{\text{die}}$。热网络粒度为 die。
- **Interposer 级（聚合实体）**：一个 Interposer 包含多个 die，通过 $\mathbf{M}_{\text{die} \to \text{inter}}$ 聚合得到 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$。
- **sub 级（Substrate 层面）**：Interposer 之间通过 Substrate 的互连。关注 Interposer 挂载点的温度 $\mathbf{T}_{\text{sub}}$。热网络粒度为 Interposer。

### 0.3 跨层耦合：Substrate 是桥梁

三层实体通过**边界条件**耦合：
- **Substrate → Interposer**：Substrate 上某点的温度 $T_{\text{sub},i}$（其中 $i$ 是 Interposer 的索引）是 Interposer 的 Ambient（环境温度），决定 $\mathbf{b}_{\text{inter}}$。
- **die → Interposer**：多个 die 的功耗 $\mathbf{P}_{\text{die}}$ 通过 $\mathbf{M}_{\text{die} \to \text{inter}}$ 聚合成 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$。
- **Interposer → Substrate**：Interposer 总功耗 $P_{\text{inter},i}$ 是 Substrate 的 Heat Source（热源），决定 Substrate 热方程的右端项。

**三层在数学上独立**，通过共享变量（$\mathbf{b}_{\text{inter}}$ 和 $\mathbf{P}_{\text{inter}}$）联立成单一模型。

### 0.4 SerDes PHY 功耗物理落点

SerDes PHY 集成在 switch ASIC die 内，功耗进 die 级功耗 $\mathbf{P}_{\text{die}}$。**不存在**独立的 $\mathbf{P}_{\text{sub}}$ 向量。Substrate 层面的热源完全来自 Interposer 的总功耗 $\mathbf{P}_{\text{inter}}$。

---

## 1. 符号表（唯一参考符号体系）

| 符号 | 含义 | 单位 | 备注 |
|------|------|------|------|
| $\mathcal{E}_{\text{D2D}}, \mathcal{E}_{\text{I2I}}$ | D2D/I2I 链路集：$\mathcal{E}_{\text{D2D}} \subseteq \mathcal{E}_{\text{UCIe}} \cup \mathcal{E}_{\text{on-die}}$（组内），$\mathcal{E}_{\text{I2I}} \subseteq \mathcal{E}_{\text{SerDes}}$（组间，经 C4 出 interposer）。链路族定义：$\mathcal{E}_{\text{on-die}}$ = die 内链路（零物理代价：$\lambda=\infty,\ p=0$）；$\mathcal{E}_{\text{UCIe}}$ = UCIe 链路（die 间，距离 ≤ UCIe 可达范围）；$\mathcal{E}_{\text{SerDes}}$ = SerDes 链路（组间，经 C4 出 interposer） | — | — |
| $B$ | 端口（出入口）额定带宽（有 QoS 保证：端口负载 ≤ $B$ 时无阻塞） | Gbps | 决策标量；即"扩展比的基准" |
| $\mathbf{L}_{\text{D2D}}, \mathbf{L}_{\text{I2I}}$ | 链路**扩展比**向量：链路实际带宽 $= B\,L_e$ | — | **无量纲** |
| $\mathbf{L}_{\text{D2D}}^{*}, \mathbf{L}_{\text{I2I}}^{*}$ | 扩展比包络（§7 预解，仅依赖拓扑与性能要求） | — | 与 $B$ 无关，主 LP 的下界输入 |
| $\boldsymbol{\ell}_{\text{D2D}}, \boldsymbol{\ell}_{\text{I2I}}$ | D2D/I2I 信号 lane 数向量 | — | $\boldsymbol{\ell} = \left(\mathbf{S}^{\text{bw}}\right)^{-1}(B\,\mathbf{L})$ |
| $\mathbf{T}_{\text{die}}, \mathbf{T}_{\text{inter}}, \mathbf{T}_{\text{sub}}$ | 温度向量（下标表物理层级：die/inter/sub） | K | 三层独立温度场 |
| $\mathbf{P}_{\text{die}}, \mathbf{P}_{\text{inter}}$ | 功耗向量（下标表层级；$\mathbf{P}_{\text{inter}}$ 由 §4 (C3) 定义） | W | $\mathbf{P}_{\text{die}} = \mathbf{P}_{\text{die}}^{\text{peak}}(B) + \mathbf{P}_{\text{D2D}}^{\text{dyn}} + \mathbf{P}_{\text{I2I}}^{\text{dyn}}$ |
| $\mathbf{P}_{\text{die}}^{\text{peak}}(B)$ | die 峰值功耗：$\mathbf{P}_{\text{die}}^{\text{peak}}(B) = P_0 + \beta_P B$ | W | **线性**（§2.8 die 缩放）；由材料/工艺决定 |
| $P_0, \beta_P$ | 静态功耗 / 峰值功耗随 $B$ 的增长率 | W, W/Gbps | §2.8 |
| $\mathbf{P}_{\text{D2D}}^{\text{dyn}}, \mathbf{P}_{\text{I2I}}^{\text{dyn}}$ | D2D/I2I 链路动态功耗 | W | 与 $\boldsymbol{\ell}$ 线性 |
| $\mathbf{b}_{\text{die}}, \mathbf{b}_{\text{inter}}, \mathbf{b}_{\text{sub}}$ | 散热边界项（下标表层级；$\mathbf{b}_{\text{die}}, \mathbf{b}_{\text{sub}}$ 预计算常数，$\mathbf{b}_{\text{inter}}$ 由 §4 (C4) 定义） | W | — |
| $\mathbf{G}_{\text{die}}, \mathbf{G}_{\text{sub}}, \mathbf{G}_{\text{inter}}^{\text{amb}}$ | 热导矩阵（下标表层级；T 和 P 的线性关系；$\mathbf{G}_{\text{inter}}^{\text{amb}}$ 为 Interposer 向 Substrate 散热的边界热导） | W/K | G 为对角占优 M-矩阵，$\mathbf{G}^{-1} \ge 0$ |
| $\mathbf{M}_{X \to Y}$ | 隶属求和映射（$X \to Y$ 方向，见下方注） | — | die→inter, D2D→die, I2I→die, I2I→inter, route→D2D, f→D |
| $\mathbf{S}_{\text{D2D}}^{\text{bw}}, \mathbf{S}_{\text{I2I}}^{\text{bw}}$ | 带宽系数（每 lane 承载比特率） | Gbps/lane | on-die 链路取 $\infty$ |
| $\mathbf{S}_{\text{D2D}}^{\text{dyn}}, \mathbf{S}_{\text{I2I}}^{\text{dyn}}$ | 每 lane 动态功耗对角阵 | W/lane | on-die 链路取 0 |
| $\mathbf{N}_{\text{C4}}^{\text{pwr}}, \mathbf{N}_{\text{C4}}^{\text{total}}$ | 电源 C4 数（§4 (C2)）/ 总 C4 数（常量，$\eta_{\text{C4}} A_{\text{inter}} / p_{\text{C4}}^2$） | — | — |
| $\mathbf{S}_{\text{C4}}^{\text{pwr}}$ | 每个 C4 bump 承载功率（$= V_{dd}\,I_{\text{C4}}$） | W/bump | — |
| $\mathbf{N}_{\text{die}}^{\text{pwr}}, \mathbf{N}_{\text{die}}^{\text{total}}(B)$ | die 侧电源 μbump 数 / 总 μbump 数 | — | $N_{\text{die}}^{\text{pwr}} = \lceil P_{\text{peak}}(B)/(V_{dd} I_{\text{bump}}) \rceil$；$N_{\text{die}}^{\text{total}}(B) = \eta A_{\text{die}}(B)/p^2$（对 $B$ **二次**，见 §2.8） |
| $V_{dd}$ | 供电电压 | V | — |
| $I_{\text{bump}}, I_{\text{C4}}$ | 单 μbump / 单 C4 载流能力 | mA | 电源 bump 计算：$N_{\text{pwr}} = \lceil P/(V_{dd}\,I) \rceil$；$\mathbf{S}_{\text{C4}}^{\text{pwr}} = V_{dd}\,I_{\text{C4}}$ |
| $p, \eta$ | μbump pitch / 面积利用率 | μm, — | $N_{\text{die}}^{\text{total}} = \eta A_{\text{die}}/p^2$ |
| $p_{\text{C4}}, \eta_{\text{C4}}$ | C4 pitch / C4 面积利用率 | μm, — | $N_{\text{C4}}^{\text{total}} = \eta_{\text{C4}} A_{\text{inter}}/p_{\text{C4}}^2$ |
| $T_{\text{amb}}$ | 环境温度 | K | 散热边界基准（§2.6：$b = g_{\text{vert}} T_{\text{amb}}$） |
| $\mathbf{W}, \mathbf{C}$ | interposer 布线资源占用矩阵 / 容量向量（多商品流） | — | $\mathbf{W} = [\mathbf{W}_{\text{edge}}; \mathbf{W}_{\text{vert}}; \mathbf{W}_{\text{pad}}]$ |
| $\mathbf{x}_{\text{D2D}}$ | **lane 布线决策**向量（链路 × 候选布线路径） | — | 与流量路由无关（流量路由已固定，见 §7） |
| $\mathbf{D}$ | 流量矩阵（$N \times N$ 双随机，$\in$ Birkhoff 多面体） | — | §7.3 性能子 LP 的决策变量 |
| $\mathbf{f}$ | 分流向量（**静态固定**：均匀分流 $f_k(i,j) = D_{ij}/K_{ij}$） | Gbps | **非决策变量**（§7.1） |
| $\mathcal{P}$ | 静态 oblivious 路由矩阵（$\mathbf{L} = \mathcal{P}\,\mathbf{f}$） | — | 设计期固定 |
| $K_{ij}$ | OD 对 $(i,j)$ 的候选路径数 | — | §7.3 |
| $d_0, \alpha_d$ | die 基线边长 / 边长随 $B$ 增长率 | mm, mm/Gbps | §2.8 |
| $c_{\text{pwr}}$ | power 走线 lane 当量系数（Power/GND 走线对 RDL 容量的占用） | — | §2 (2d)；参数 YAML `c_pwr_lane_per_w`，默认 0 = 关闭 |
| $T_{\max}$ | 温度上限（结温；sub 层上限可独立设定，见 §6） | K | — |

**注**：
- **命名约定**：下标表示"物理层级/主体"，上标表示"属性/修饰符"。
- **关于 $\mathbf{M}$**：所有 $\mathbf{M}_{X \to Y}$ 矩阵都是**隶属求和关系**——将 $X$ 空间的向量按归属关系（求和）映射到 $Y$ 空间。元素为 0/1（或加权 0/1），表示 $X$ 中若干分量隶属于 $Y$ 中某一分量。模型中出现的 $\mathbf{M}_{X \to Y}$ 包括：die→inter（功耗聚合）、D2D→die（lane→μbump）、I2I→die（SerDes lane→μbump/PHY）、I2I→inter（lane→C4 信号池）、route→D2D（布线路径→链路）、f→D（分流→需求）。
- **关于 $\mathbf{L}$ 的量纲**：$\mathbf{L}$ 是**扩展比向量（无量纲）**，链路实际带宽 $= B\,L_e$。$\mathbf{L}^*$ 是"扩展比包络"——某拓扑为满足某性能要求必须保证的最小扩展比（如额定带宽 QoS 保证下某链路最多承担 2 倍额定带宽流量，则该链路扩展比至少为 2）。

---

## 2. die 段（单一模型的一部分）

此段含 D2D（Interposer 内部）的性能侧 + 物理约束：

$$
\boxed{
\begin{aligned}
\text{find}\quad & \mathbf{L}_{\text{D2D}},\; \boldsymbol{\ell}_{\text{D2D}},\; \mathbf{P}_{\text{die}},\; \mathbf{T}_{\text{die}},\; \mathbf{T}_{\text{inter}},\; \mathbf{x}_{\text{D2D}} \\[6pt]
\text{s.t.}\quad & \text{(2a) 性能包络（由 §7 静态 oblivious Valiant 路由下的子 LP 预解出）：} \\
&\quad \mathbf{L}_{\text{D2D}} \ge \mathbf{L}_{\text{D2D}}^{*} \\
& \text{(2b) lane 数：}\;\boldsymbol{\ell}_{\text{D2D}} = \left(\mathbf{S}_{\text{D2D}}^{\text{bw}}\right)^{-1}\,(B\,\mathbf{L}_{\text{D2D}}) \\
& \text{(2c) die 级功耗：}\\
&\quad \mathbf{P}_{\text{die}} = \mathbf{P}_{\text{die}}^{\text{peak}}(B) + \mathbf{P}_{\text{D2D}}^{\text{dyn}} + \mathbf{P}_{\text{I2I}}^{\text{dyn}} \\
&\quad \mathbf{P}_{\text{D2D}}^{\text{dyn}} = \mathbf{M}_{\text{D2D} \to \text{die}}\,\mathbf{S}_{\text{D2D}}^{\text{dyn}}\,\boldsymbol{\ell}_{\text{D2D}} \\
&\quad \mathbf{P}_{\text{I2I}}^{\text{dyn}} = \mathbf{M}_{\text{I2I} \to \text{die}}\,\mathbf{S}_{\text{I2I}}^{\text{dyn}}\,\boldsymbol{\ell}_{\text{I2I}} \\
& \text{(2d) interposer 布线（多商品流，$\mathbf{x}_{\text{D2D}}$ 为 lane 布线决策）：}\\
&\quad \mathbf{M}_{\text{route} \to \text{D2D}}\,\mathbf{x}_{\text{D2D}} = \boldsymbol{\ell}_{\text{D2D}} \\
&\quad \mathbf{W}\,\mathbf{x}_{\text{D2D}} \le \mathbf{C} \\
&\qquad \left(\mathbf{W} = \begin{bmatrix}\mathbf{W}_{\text{edge}} \\ \mathbf{W}_{\text{vert}} \\ \mathbf{W}_{\text{pad}}\end{bmatrix},\;\;\mathbf{C} = \begin{bmatrix}\mathbf{C}_{\text{edge}} \\ \mathbf{C}_{\text{vert}} \\ \mathbf{C}_{\text{pad}}\end{bmatrix}\right) \\
& \text{(2e) 热方程（块矩阵，die 与 interposer 温度场耦合）：}\\
&\quad \mathbf{G}_{\text{die}}\begin{bmatrix}\mathbf{T}_{\text{die}} \\ \mathbf{T}_{\text{inter}}\end{bmatrix} = \begin{bmatrix}\mathbf{P}_{\text{die}} \\ \mathbf{0}\end{bmatrix} + \begin{bmatrix}\mathbf{b}_{\text{die}} \\ \mathbf{b}_{\text{inter}}\end{bmatrix} \\
&\quad \begin{bmatrix}\mathbf{T}_{\text{die}} \\ \mathbf{T}_{\text{inter}}\end{bmatrix} \le T_{\max}\mathbf{1} \\
& \text{(2f) die 面积上界：}\\
&\quad A_{\text{die}}(B) = d(B)^2 \le A_{\max} \\
&\qquad \left(A_{\max} \text{ 随布局而定（粗上界 } \approx A_{\text{interposer}}/N_{\text{dies}}\text{）；由 §2.8 } d(B) = d_0 + \alpha_d B \Rightarrow \alpha_d B \le \sqrt{A_{\max}} - d_0\right) \\
& \mathbf{L}_{\text{D2D}} \ge 0 \\
& \mathbf{x}_{\text{D2D}} \ge 0
\end{aligned}
}$$

**说明**：
- **find 列表不含 $\mathbf{b}$**：$\mathbf{b}_{\text{die}}$ 是常数，$\mathbf{b}_{\text{inter}}$ 由 §4 (C4) 定义，二者都不是自由变量。
- **(2b) 的量纲**：$\boldsymbol{\ell} = \left(\mathbf{S}^{\text{bw}}\right)^{-1}(B\,\mathbf{L})$——$B\,L_e$ 是链路实际带宽（Gbps），除以每 lane 比特率得到 lane 数。$\mathbf{L}$ 本身无量纲。
- **(2d) 布线的物理意义**：power/gnd 与信号走线共享 interposer RDL 资源——**布线预算/布线面积共享纳入主优化模型**（布线饱和常先于 bump 成为绑定约束）。（power 走线占用 RDL 容量的约束式见 `notes/IMPLEMENTATION_MAP.md` §3。）
- **(2f) 面积上界的物理意义**：die 面积有硬上界（布局确定后每 die 最大尺寸固定；粗上界 ≈ interposer 面积 ÷ 芯粒数）。面积上界与布线共享是跨约束共享资源的耦合要素。

### 2.6 热导矩阵 $\mathbf{G}_{\text{die}}$ 和 $\mathbf{G}_{\text{sub}}$

根据传热学基本原理，$\mathbf{T}$ 和 $\mathbf{P}$ 永远是线性关系。影响 $\mathbf{G}$ 的两个旋钮：
1. **网格粒度**：决定 G 的维度。粒度越粗，G 越小（早筛模型取最粗粒度，如 die 级）；粒度越细，G 越大（如单元级）。
2. **封装方式**：决定 G 的元素值。不同封装（如 2.5D vs 3D 堆叠）有不同的传热路径（散热板、Substrate、underfill 等），进而产生不同的热阻网络和 G 值。

- $\mathbf{b}_{\text{die}}$：常数（die 向散热板散热）
- $\mathbf{b}_{\text{inter}}$：变量（由 §4 (C4) 定义，Interposer 向 Substrate 散热）

### 2.7 关于 $\mathbf{T}_{\text{inter}}$ 行源项为零

块矩阵第二块源项为 $\mathbf{0}$，隐含**Interposer 自身无焦耳热源**（功耗全部落在 die 节点上）——见 §6 假设 A5。Interposer 只承担热传导（横向面邻接 + 纵向集总热阻），其温度由 die 功耗经 $\mathbf{G}_{\text{die}}$ 决定。

### 2.8 die 缩放

die 的物理尺寸与峰值功耗建模为 $B$ 的函数（`DieParams` / `DieBumpBudget`）：

$$
d(B) = d_0 + \alpha_d\,B,\qquad A_{\text{die}}(B) = d(B)^2,\qquad P_{\text{peak}}(B) = P_0 + \beta_P\,B
$$

由此：
- $N_{\text{die}}^{\text{total}}(B) = \eta\,A_{\text{die}}(B)/p^2$——对 $B$ **二次**（面积随边长平方增长；带宽需求越大，die 需容纳更多 SerDes/PHY，面积按 $\alpha_d$ 缩放，μbump 预算随之增长）。
- $N_{\text{die}}^{\text{pwr}}(B) = \lceil P_{\text{peak}}(B)/(V_{dd}\,I_{\text{bump}}) \rceil$——随 $B$ **线性**增长。
- $P_{\text{die}}^{\text{peak}}(B) = P_0 + \beta_P\,B$——**线性**。
- **面积上界（§2 (2f)）**：$A_{\text{die}}(B) \le A_{\max} \Rightarrow \alpha_d B \le \sqrt{A_{\max}} - d_0$——$\alpha_d > 0$ 时面积约束直接给出 $B$ 的上界（"B 只有上限没有下限"）。
- 默认 $\alpha_d = \beta_P = 0$（退化特例：面积与峰值功耗不随 $B$ 变，toy 手算锚点）。

**约束旋钮 C_rated（额定功耗工况）**——峰值项 $\beta_P B$ 置 0，静态 $P_0$ 保留：

$$
P_{\text{peak}}^{\text{rated}} = P_0 \quad (\text{即 } \beta_P := 0)
$$

两处 rhs 落点：
- **BumpModel rhs（die 侧电源 bump 数，§4 C2）**：$N_{\text{die}}^{\text{pwr}} = \lceil P_{\text{peak}}(B)/(V_{dd} I_{\text{bump}}) \rceil \to N_{\text{die}}^{\text{pwr}} = \lceil P_0/(V_{dd} I_{\text{bump}}) \rceil$——**常数**，不随 $B$ 变。
- **SteadyStateModel rhs（热方程 (2e)）**：$\mathbf{P}_{\text{die}} = \mathbf{P}_{\text{die}}^{\text{peak}}(B) + \mathbf{P}_{\text{D2D}}^{\text{dyn}} + \mathbf{P}_{\text{I2I}}^{\text{dyn}} \to \mathbf{P}_{\text{die}} = P_0 \mathbf{1} + \mathbf{P}_{\text{D2D}}^{\text{dyn}} + \mathbf{P}_{\text{I2I}}^{\text{dyn}}$——$\beta_P B$ 项置 0；**链路动态功耗 $\mathbf{P}^{\text{dyn}}$ 保留**（C_rated 只取消 die 峰值随 $B$ 增长项，不取消链路动态功耗，后者是流量的直接函数）。

物理语义：C_peak（最严）考虑 die 满负荷峰值功耗随 $B$ 线性增长；C_rated（宽松）只按额定功耗（静态 $P_0$ + 链路动态）评估——可承诺 $B$ 推高。

---

## 3. I2I 段（单一模型的一部分）

此段含 I2I（Substrate 层面）的约束。$\mathbf{P}_{\text{inter}}$（Interposer 总功耗）和 $\mathbf{b}_{\text{inter}}$（Interposer 边界条件）是共享变量，本段不写其表达式（由 §4 定义）。

$$
\boxed{
\begin{aligned}
\text{find}\quad & \mathbf{L}_{\text{I2I}},\; \boldsymbol{\ell}_{\text{I2I}},\; \mathbf{T}_{\text{sub}} \\[6pt]
\text{s.t.}\quad & \text{(3a) 性能包络（由 §7 静态 oblivious Valiant 路由下的子 LP 预解出）：} \\
&\quad \mathbf{L}_{\text{I2I}} \ge \mathbf{L}_{\text{I2I}}^{*} \\
& \text{(3b) lane 数：}\;\boldsymbol{\ell}_{\text{I2I}} = \left(\mathbf{S}_{\text{I2I}}^{\text{bw}}\right)^{-1}\,(B\,\mathbf{L}_{\text{I2I}}) \\
& \text{(3c) C4 预算（per-interposer，经 }\mathbf{M}_{\text{I2I} \to \text{inter}}\text{ 聚合；共享变量 }\mathbf{N}_{\text{C4}}^{\text{pwr}}\text{ 由 §4 (C2) 定义）：}\\
&\quad \mathbf{M}_{\text{I2I} \to \text{inter}}\,\boldsymbol{\ell}_{\text{I2I}} + \mathbf{N}_{\text{C4}}^{\text{pwr}} \le \mathbf{N}_{\text{C4}}^{\text{total}} \\
& \text{(3d) sub 热方程：}\\
&\quad \mathbf{G}_{\text{sub}}\,\mathbf{T}_{\text{sub}} = \mathbf{P}_{\text{inter}} + \mathbf{b}_{\text{sub}} \\
&\quad \mathbf{T}_{\text{sub}} \le T_{\max}^{\text{sub}}\mathbf{1} \\
& \mathbf{L}_{\text{I2I}} \ge 0
\end{aligned}
}$$

**特点**：
- **find 列表只含自由变量**：$\mathbf{P}_{\text{inter}}$、$\mathbf{N}_{\text{C4}}^{\text{pwr}}$、$\mathbf{b}_{\text{inter}}$ 均由 §4 定义，非决策变量。
- (3c) 的聚合：$\boldsymbol{\ell}_{\text{I2I}}$ 是 link 级向量，$\mathbf{N}_{\text{C4}}^{\text{pwr}}$/$\mathbf{N}_{\text{C4}}^{\text{total}}$ 是 interposer 级向量，两者相加前必须经 $\mathbf{M}_{\text{I2I} \to \text{inter}}$（某 I2I 链路从哪个 interposer 的 C4 出，就计入该 interposer 的信号池）。$N_{\text{C4}}^{\text{total}} = \eta_{\text{C4}}\,A_{\text{inter}}/p_{\text{C4}}^2$。
- 不含独立的功耗向量 $\mathbf{P}_{\text{sub}}$，Substrate 的热源完全来自 Interposer 总功耗 $\mathbf{P}_{\text{inter}}$（§0.4）。
- 不含布线约束（Substrate 内走线不考虑，简化模型）。
- $T_{\max}^{\text{sub}}$ 为 Substrate/挂载点温度上限，可与结温 $T_{\max}$ 分层设定（§6）。

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

**表述上三段分离，整体闭合**：die 段与 I2I 段各有独立约束，通过 §4 跨层耦合段定义共享变量（$\mathbf{b}_{\text{inter}}$、$\mathbf{P}_{\text{inter}}$、$\mathbf{N}_{\text{C4}}^{\text{pwr}}$）使整体闭合，无自由变量。热、电、几何、性能四类约束在**同一**模型联立。

---

## 6. 关键假设

| 编号 | 假设 | 内容 | 影响 |
|------|------|------|------|
| A1 | Substrate 温度均匀 | Interposer 挂载点处 Substrate 温度作为 Interposer 的统一 Ambient | 简化热模型，忽略 Substrate 厚度方向的温度梯度 |
| A2 | Interposer 面内温度显式建模 | die 级热网络刻画 Interposer 内部温度梯度 | die 间横向耦合经 $\mathbf{G}_{\text{die}}$ 显式表达 |
| A3 | SerDes PHY 在 die 上 | I2I SerDes PHY 集成在 switch ASIC die 内 | PHY 功耗进 $\mathbf{P}_{\text{die}}$（§0.4） |
| A4 | 链路功耗只计 PHY 动态功耗 | 每 lane 动态功耗 $p_e$ 随流量线性；峰值功耗单列在 $P_{\text{peak}}(B)$ | 动态/静态分通道计入 bump 电流 |
| A5 | Interposer 自身无焦耳热源 | 功耗全部落在 die 节点，Interposer 只传热 | §2 块矩阵第二行源项为 $\mathbf{0}$（§2.7） |
| A6 | 温度上限可分层 | 结温 $T_{\max}$ 与 Substrate 温度上限 $T_{\max}^{\text{sub}}$ 可独立设定 | 避免一个 $T_{\max}$ 通吃 die/sub |
| A7 | 信号完整性靠规范内嵌 | SI（串扰/误码）由互联标准（UCIe reach、OIF-CEI VSR/MR/LR）内嵌保证，不显式建模 | 约束集不含 SI 项 |
| A8 | D2D/I2I 包络独立、可同时满载 | 两段包络分别求解，互不制约 | 隐含两段可同时达到最坏流量（保守方向）；D2D/I2I 流量分割比不作为参数（见释经·待定案） |

---

## 7. 性能模型：静态 oblivious Valiant 路由下的 $L$ 包络最大化

### 7.1 设计选择：放弃 $\mathbf{f}$ 的可变性

若把分流 $\mathbf{f}$ 也当作决策变量，子 LP 会把它变成"攻击网络的工具"——通过选择 $\mathbf{f}$ 让某条链路过载。这违背了 $\mathbf{f}$ 的本意：$\mathbf{f}$ 是**网络设计者**为优化网络而选择的路由方案，不应作为攻击向量。

**决策**：放弃 $\mathbf{f}$ 的可变性，采用**静态 oblivious Valiant 负载均衡**——路由方案在网络设计阶段即固定，对所有 traffic pattern 一视同仁（oblivious）。具体地，$\mathbf{f}$ **固定为均匀分流**：

$$
f_k(i,j) = \frac{D_{ij}}{K_{ij}}, \qquad k = 1, \dots, K_{ij}
$$

其中 $K_{ij}$ 是 OD 对 $(i,j)$ 的候选路径数（Valiant 中间节点展开）。$f$ 是 $D$ 的**线性像**而非决策变量——攻击自由度只剩流量矩阵 $\mathbf{D}$。

### 7.2 物理含义

静态 oblivious Valiant 路由下，网络对所有 traffic pattern 提供相同的路由策略。$L$ 包络在此固定路由下计算得到，**不依赖 $B$**（$\mathbf{L}$ 是扩展比包络）——性能模型独立于物理模型。

这是**最严苛的性能约束**：网络必须在 oblivious 路由下承载最坏流量模式（对所有 traffic pattern 都可承载）——这正是"额定出入口带宽 $B$ 有 QoS 保证"（端口负载 ≤ $B$ 时无阻塞）所要求的最小承载能力。

### 7.3 $L$ 包络最大化的子 LP

给定静态 oblivious Valiant 路由（$\mathbf{f}$ 固定为均匀分流），每条链路 $e$ 的负载是流量矩阵 $\mathbf{D}$ 的**线性函数**：

$$
L_e(\mathbf{D}) = \sum_{(i,j)} c_{ij}^{e}\,D_{ij}, \qquad
c_{ij}^{e} = \frac{\#\{k : e \in \text{path}_k(i,j)\}}{K_{ij}}
$$

$c_{ij}^{e}$ 是"通过链路 $e$ 的候选路径数 $\div$ 候选路径总数"，即均匀分流下 OD 对 $(i,j)$ 对链路 $e$ 的单位贡献。性能侧的子 LP 以 $\mathbf{D}$ 为决策变量，最大化某条链路 $e$ 的负载 $L_e$：

$$
\boxed{
\begin{aligned}
\max_{\mathbf{D}}\quad & L_e(\mathbf{D}) \\
\text{s.t.}\quad & \mathbf{D} \in \text{Birkhoff} \\
& \mathbf{D} \ge 0
\end{aligned}
}
$$

其中：
- $\mathbf{D} \in \text{Birkhoff}$（$N \times N$ **双随机矩阵多面体**：$\mathbf{D}\mathbf{1} = \mathbf{1}$、$\mathbf{D}^{\top}\mathbf{1} = \mathbf{1}$、$\mathbf{D} \ge 0$）是**决策变量**——通过寻找进攻性的 $\mathbf{D}$ 把 $L_e$ 往大了逼
- $\mathbf{f}(\mathbf{D})$ 由均匀分流给出：$f_k(i,j) = D_{ij}/K_{ij}$，**不是变量**（§7.1）
- **Birkhoff–von Neumann 定理**：Birkhoff 多面体的顶点恰为置换矩阵；线性目标在顶点取最优 $\Rightarrow$ 最坏流量模式是**置换矩阵**（每源一目标、每目标一源）——恰对应 QoS 保证（可重排非阻塞，RNB）的最坏情形。因此每个子 LP 等价于在置换矩阵上取 $\max L_e$，$L_e^{*}$ 有干净的组合解释。
- 解出 $\mathbf{D}_e^{*}$ 后，$L_e^{*} = L_e(\mathbf{D}_e^{*})$
- 子 LP 与主 LP 结构相同（都是 LP），但**完全独立**：子 LP 只依赖拓扑（$c_{ij}^{e}$ 由 $\mathcal{P}$ 决定），不依赖任何物理参数。

### 7.3b 要求旋钮 R_peak（仅出入口峰值）—— 单对流量包络

R_qos（§7.3）对应"无阻塞"语义：任意 admissible 流量（双随机）下保证无阻塞，最坏情形为置换矩阵。**R_peak（仅出入口峰值）**只要求**任意单对 $(i,j)$ 流量可达 $B$**（网络连通 + 单对全带宽），不承诺多对并发无阻塞。

数学形态（**闭式解，无需新子 LP**）：单对流量 $B$ 均匀分流 $K_{ij}$ 条路径，链路 $e$ 负载 $= c_{ij}^{e} B$；要求 $c_{ij}^{e} B \le B L_e \Rightarrow L_e \ge c_{ij}^{e}$，对所有 OD 对取最坏：

$$
L_e^{*}(\text{R\_peak}) = \max_{(i,j)} c_{ij}^{e} \le 1
$$

- 直接对路由系数 $c_{ij}^{e}$（§7.3 已定义）逐链路取 max，**O($|E| \cdot N^2$) 闭式计算**，替代 Birkhoff 子 LP 结果。
- 与 R_qos 包络对比：R_qos = max over 双随机（Valiant 两阶段下通常 = 2）；R_peak = max c（≤ 1，通常 = 1）——**严格更松**，同构型下 $B^*$ 更大。
- **为何不用次随机放宽（行/列和 ≤ 1）**：次随机多面体与双随机多面体的包络最大值**相等**——部分置换矩阵可由 Hall 定理扩展为满置换，且 $c_{ij}^{e} \ge 0$ 使扩展不减少 $L_e$，故 $\max_{\text{次随机}} = \max_{\text{双随机}}$（BvN 顶点均可达）。次随机放宽无区分度，不采用。

### 7.4 $L$ 包络的构造

对每条链路 $e$ 分别求解上述子 LP，得到 $L_e^{*}$。所有链路的 $L_e^{*}$ 组合构成 $L$ 包络：

$$
\mathbf{L}^{*} = (L_1^{*}, L_2^{*}, \dots, L_{|\mathcal{E}|}^{*})^{\top}
$$

该 $\mathbf{L}^{*}$ 作为主 LP (2a)/(3a) 的性能包络输入——主 LP 不再需要枚举 traffic pattern，直接使用 $\mathbf{L}^{*}$ 作为链路负载的下界约束。

**D2D/I2I 两个包络独立**：D2D 段（组内）和 I2I 段（组间）各有独立的 $L$ 包络，分别执行上述子 LP 求解，互不影响（两段可同时满载，见 §6 A8）。

### 7.5 与主 LP 的对接

主 LP (2a)/(3a) 的路由约束简化为：

$$
\mathbf{L}_{\text{D2D}} \ge \mathbf{L}_{\text{D2D}}^{*},\qquad \mathbf{L}_{\text{I2I}} \ge \mathbf{L}_{\text{I2I}}^{*}
$$

即主 LP 只需保证链路负载不低于性能包络。性能模型与物理模型解耦：性能模型一次性产出 $\mathbf{L}^{*}$，物理模型以 $\mathbf{L}^{*}$ 为输入，$B$ 的缩放只发生在物理约束的 `build(ctx, B)` 里。

---

## 释经指引（派生内容去向）

- **insight 解读**（作者意图、术语定案、耦合案例）→ `notes/INSIGHT_READING.md`
- **实现对表 / 参考文献 / 推导细节**（含 power 走线双分支、fixed_paths）→ `notes/IMPLEMENTATION_MAP.md`
- **模型性质与求解讨论**（闭合性论证、非凸但多项式全局最优、单调性注意、灵敏度入口）→ `notes/MODEL_PROPERTIES.md`
- **版本历史**（v5.9 → v5.28）→ `notes/V5_CHANGELOG.md`
- **决策与待定案**（Gate 裁决、分割比 ρ、die 缩放单调性验证等）→ `.dsh/team/decisions.md`
- **灵敏度设计 / 实验设计 / 数据报告** → `.dsh/team/artifacts/`
