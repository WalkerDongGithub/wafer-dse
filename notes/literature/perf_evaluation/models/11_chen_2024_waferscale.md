# 11 Chen 2024 —— Waferscale 网络交换机（radix 上限 × 超线性功耗）

> 出处：C. Chen, S. Pal, R. Kumar, "Waferscale Network Switches," ISCA 2024。
> 本篇的性能输出是 **radix 上限 $n^*$**（给定基板尺寸/工艺/冷却下最多摆多少端口），**不是**无阻塞带宽 $B^*$。核心贡献是**功耗的超线性（near-quadratic）radix 标度** $P_{\text{core}}\propto k^2$，以及**内部带宽 / 外部带宽 / 功耗密度三瓶颈**对 radix 的联合限制。本文给出符号自洽、假设显式的数学形式；原文未写成单一优化式的部分据原文文字重构并注明。

## 0. 符号表（本节所有符号在此定义）

| 符号 | 定义 | 单位 / 取值域 |
|------|------|------|
| $n$ | 系统总端口数（= overall radix，本模型的目标变量） | $n\in\mathbb{N}$ |
| $k$ | 单个子交换机（SSC）的端口数（subswitch radix）；TH-5 基线 $k=256$ | $k\in\mathbb{N}$ |
| $B$ | 每端口带宽（线速） | $B\in\mathbb{R}_{>0}$，Gbps；基线 200 |
| $A_{\text{sub}}$ | 单 SSC 面积（TH-5） | 800 mm² |
| $S$ | 方形基板边长 | $S\in\{100,200,300\}$ mm |
| $N_{\text{chip}}$ | 基板上 SSC 数（2 级 Clos 时 $=3n/k$，见表 VI 的 Clos 项） | $N_{\text{chip}}\in\mathbb{N}$ |
| $\rho_{\text{int}}$ | 内部链路带宽密度（Si-IF：3200/6400；InFO-SoW：12800） | Gbps/mm |
| $\rho_{\text{ext}}$ | 外部 I/O 带宽密度（SerDes/Optical 按周长计，Area 按面积计） | Gbps/mm 或 Gbps/mm² |
| $E_{\text{bit}}$ | 每 bit 传输能量 | pJ/bit |
| $V_{dd},\ V_{th}$ | 供电电压、阈值电压 | V |
| $P_{\text{core}}(k)$ | radix-$k$ 的**单个** SSC 核心（非 I/O）功耗 | W |
| $P_{\text{IO}}^{\text{int}},\ P_{\text{IO}}^{\text{ext}}$ | 内部 I/O、外部 I/O 功耗 | W |
| $P_{\text{tot}}$ | 系统总功耗 | W |
| $p_{\text{dens}}$ | 功耗密度 $=P_{\text{tot}}/S^2$ | W/mm² |
| $q_{\text{cool}}$ | 冷却能力（可散热功率密度上限） | W/mm² |
| $G$ | 逻辑拓扑（本文取 2 级 Clos） | — |
| $M$ | floorplan：chiplet $\to$ 基板网格位置的映射 | — |
| $C(M)$ | 映射 $M$ 下，任意相邻 chiplet 对之间逻辑链路数的最大值 | $C(M)\in\mathbb{N}$ |
| $\mathrm{RTT}$ | 链路往返时间 | ns |
| $m$ | 单条链路上的流数（Appenzeller 公式中的 $n$，改名避免与端口数冲突） | $m\in\mathbb{N}$ |
| $S_{\text{buf}}$ | 缓冲尺寸 | bit |

> 符号约定：本文 $P$ 一律指**功耗**（标量）；统一符号表中的排列矩阵 $\mathbf{P}$、流量矩阵 $\mathbf{D}$、链路负载 $\mathbf{L}$ 在本篇**不出现**——Chen 2024 没有流量需求结构体（见 §9）。

## 1. 模型定位

问题：WSI 能否把交换机 radix 大幅提高？答案分两层：

1. **只看面积**（理想情形）：300mm 基板可到 $n=8192$ 端口 $=32\times k_{\text{TH-5}}$，200mm 16×、100mm 4×。
2. **看真实物理约束**：radix **不由面积限制**，而由**内部带宽、外部带宽、功耗密度**三者联合限制。无优化时收益极小（SerDes 300mm 仅 $n=512$ 端口 $=2\times$）；经异构 + deradixing + Optical/Area I/O 优化后 300mm 才回到 $n=8192$。

即：性能输出是 $n^*$，作为（$S$、$\rho_{\text{int}}$、外部 I/O 技术、$q_{\text{cool}}$）的函数。

## 2. 模型假设（显式）

- **A1 拓扑**：逻辑 2 级 Clos（无阻塞性质直接借用 Clos [27]）映射到物理 mesh（chiplet-based WSI：Si-IF / InFO-SoW；相邻 SSC 经 4µm 间距无源互连线相连，非相邻经中间 SSC 作 repeater 多跳）。
- **A2 SSC**：TH-5 类 chiplet——$k=256$ 端口、$B=200$ Gbps、$P_{\text{tot}}=500$ W（I/O 功耗 100 W，非 I/O $P_{\text{core}}=400$ W）、$A_{\text{sub}}=800$ mm²；可换 128×400 / 64×800 配置。I/O 能量按 2 pJ/bit 计 [10]。
- **A3 映射保无阻塞**：每条逻辑链路**不共享物理布线**，故每条逻辑链路保证 $\ge B=200$ Gbps；映射带来的非均匀链路延迟由 SSC 输入缓冲吸收 [20]。
- **A4 相邻延迟**：相邻 SSC 间连接延迟 1 ns；最坏远端延迟 $2\sqrt{N_{\text{chip}}}$ ns（原文：$2N$ ns，其中 SSC 数为 $N^2$）。
- **A5 内部互连参数**：Si-IF 基线 $\rho_{\text{int}}=3200$ Gbps/mm、$E_{\text{bit}}=0.06$ pJ/bit；加倍到 6400（4 层，1600 Gbps/mm/层）；InFO-SoW 12800 Gbps/mm、1.5 pJ/bit。
- **A6 外部 I/O 参数**：SerDes 512 Gbps/mm（1 层，8 pJ/bit）、Optical 800 Gbps/mm（4 层，5 pJ/bit）、Area 16 Gbps/mm²（1 层，8 pJ/bit）。
- **A7 冷却**：air < water $\approx0.5$ W/mm² < multiphase（原文 Figure 16 三条 envelope；原文正文一处记作 kW/mm²，与后文 0.48 W/mm² 及 Cerebras WSE-2 的 0.4976 W/mm² 对照应为 W/mm² 笔误）。
- **A8 功耗超线性**：SSC 核心功耗随 radix **near-quadratic**：$P_{\text{core}}(k)\propto k^2$（依据：Ahn [19] 的 quadratic 模型 + TH/TeraLynx 系列实测标定，见 §6.1）。

## 3. radix 上限问题（输入 / 约束 / 目标）

论文**未**写成单一优化式，而是逐配置枚举 + 映射启发式 + 实测标定实现。以下约束结构据原文文字（§IV–§V）重构，标注处为重构：

$$
n^* \;=\; \max\ n \quad\text{s.t.}
$$

- **(C1) 面积约束**：2 级 Clos 所需 SSC 数 $N_{\text{chip}}=3n/k$（表 VI 的 Clos 项：$3(N/k)$）个 $A_{\text{sub}}$ 面积 chiplet 可放进 $S\times S$ 基板。**只施加 C1 即「理想情形」**：$n^*=32\times k$（300mm）。
- **(C2) 内部带宽约束**：Clos 高层逻辑连接在相邻 SSC 对之间汇聚，映射 $M$ 下最坏相邻对的逻辑链路数 $C(M)$ 受物理带宽密度 $\rho_{\text{int}}$ 限制（重构：$C(M)\cdot B\le \rho_{\text{int}}\times\text{相邻间距}$）。这是最先饱和的瓶颈。
- **(C3) 外部带宽约束**：$n\cdot B \le$ 外部总带宽 $=$ $\rho_{\text{ext}}\times$周长（SerDes/Optical）或 $\rho_{\text{ext}}\times S^2$（Area I/O）。
- **(C4) 功耗密度约束**：$p_{\text{dens}}=P_{\text{tot}}(n)/S^2 \le q_{\text{cool}}$。

瓶颈叠加速度：C1 单独给 32×；加 C3（SerDes 周长限制）降到 2×（$n=512$）；Optical/Area I/O 缓解 C3 后，C2 在 3200 Gbps/mm 下成为硬顶（200→300mm 时 $n^*$ 不增）；把 $\rho_{\text{int}}$ 翻倍到 6400 后 $n^*$ 恢复 4×；再叠加 C4（功耗），最终 $n^*$ 由冷却决定（§5）。

## 4. 映射子问题（min-max，离散组合优化）

给定逻辑拓扑 $G$，floorplan $M$，$C(M)=$ 任意相邻 chiplet 对之间逻辑链路数的最大值：

$$
\min_{M}\; C(M),\qquad C(M)=\max_{\text{相邻对 }(u,v)}\ \#\{\text{逻辑链路经过 }u\text{—}v\}
$$

- **不可微、无解析解**：每个映射是离散排列，$N_{\text{chip}}$ 个 chiplet 有 $N_{\text{chip}}!$ 种放置，暴力搜索不可行。
- **求解**：成对交换启发式（Algorithm 1）——初始映射，逐对交换 chiplet 位置，若 $C(M)$ 下降则保留、否则换回，直至无可再换；跑 1000 次随机初始化取最优（原文：各次差异 $<1\%$）。
- **效果**：相比随机初始化，启发式把最坏内部 I/O 带宽/端口提高 **147.6%**。

## 5. 三瓶颈的量级（原文报告值）

| 瓶颈 | 关键数字 |
|------|---------|
| 内部带宽（C2） | 3200 Gbps/mm 下 Optical/Area 在 200→300mm 时 $n^*$ 持平（饱和）；6400 下 300mm 达 $n=8192$（4×） |
| 外部带宽（C3） | SerDes 300mm 仅 $n=512$；Optical/Area 比 SerDes 高至 4×，仍比理想低 50–75% |
| 功耗密度（C4） | 3200 下 $P_{\text{tot}}>14$ kW；6400 下最高 62 kW（8192 radix，3.5×）；InFO-SoW 92.5 kW；内部 I/O + 外部 I/O 占 33%–43.8% |

优化收益（§5.B–C）：**异构设计**降功耗 30.8%–33.5% → 使 $p_{\text{dens}}$ 从 0.69 降到 0.48 W/mm²（低于 WSE-2 的 0.4976 W/mm²，水冷可承载）→ radix 4×；**deradixing**（SSC radix 减半、面积不变，把省下的 I/O 转为 feedthrough）→ 整体 radix 2×（300mm 从 2048→4096）。

## 6. 功耗模型（重点）

### 6.1 核心功耗超线性：$P_{\text{core}}\propto k^2$

**结论**（原文明确）：SSC 核心功耗随 radix **超线性（near-quadratic）**：

$$
P_{\text{core}}(k)\;=\; c_2 k^2 + c_1 k + c_0,\qquad c_2>0
$$

**为什么是平方（crosspoint 计数机制）**：一个 radix-$k$ 的 crossbar 是 $k\times k$ 交换点阵，crosspoint 数为 $k^2$。每个 crosspoint 在 CMOS 实现中是一个三态缓冲器（保持状态的传输门 + 反相器对），持续消耗静态功耗（泄漏）；故静态项 $P_{\text{stat}}\propto(\text{crosspoint 数})=k^2$。动态项（每端口输入缓冲、仲裁器、crossbar 输出线驱动）为 $O(k)$ 线性。大 $k$ 下静态项主导 ⟹ near-quadratic。（此为机制层说明；Ahn [19] 对 monolithic 与 hierarchical crossbar 的精确功耗分解见原文。）

**数据依据（Figure 15）**：Broadcom Tomahawk 系列（TH-1/3/4/5）与 Marvell TeraLynx 系列（TL-7/8/10）的**归一化 non-I/O 功耗**，用 Stillmaker–Baas 的 scaling equations [57] 归一化到 5nm 节点，数据点**贴合 quadratic 曲线**（与 Ahn [19] 建议的 quadratic 标度一致）。

**直接推论（两个 half-radix 优于一个 full）**：

$$
P_{\text{core}}\!\big(\tfrac{k}{2}\big)+P_{\text{core}}\!\big(\tfrac{k}{2}\big)
= 2\Big[c_2\big(\tfrac{k}{2}\big)^2 + c_1\tfrac{k}{2}+c_0\Big]
= \tfrac{c_2}{2}k^2 + c_1 k + 2c_0
\;<\; c_2k^2 + c_1k + c_0 = P_{\text{core}}(k)
$$

（当 $c_2k^2$ 主导时严格成立。）这正是**异构设计**的依据：把 Clos 的 leaf SSC 拆成两个 half-radix SSC，总核心功耗下降而系统 radix 不变，省出的功耗预算转投内部 I/O 带宽（以能效换带宽）→ 支撑更高 $n^*$。

### 6.2 I/O 功耗–电压–带宽：$P\propto V_{dd}^2$、$B\propto (V_{dd}-V_{th})^2/V_{dd}$

原文引用 Rabaey [51] 的器件关系（原文记每 bit 能量为 $P$、线带宽为 $B$；此处用 $E_{\text{bit}}$、$B_w$ 避免与端口带宽冲突）：

$$
E_{\text{bit}}\propto V_{dd}^2,\qquad
B_w\propto \frac{(V_{dd}-V_{th})^2}{V_{dd}}
$$

**推导（关键步）**：

1. **每 bit 能量**：栅极/线电容 $C_{\text{eff}}$ 每次切换充放电能量 $=C_{\text{eff}}V_{dd}^2$ ⟹
   $$
   E_{\text{bit}}\;=\;C_{\text{eff}}\,V_{dd}^2 \;\propto\; V_{dd}^2
   $$

2. **开关频率（= 带宽）**：速度饱和漏电流（alpha-power law，$\alpha\in[1,2]$，长沟道 $\alpha=2$、短沟道 $\alpha\to1$）：
   $$
   I_d \;\propto\; (V_{dd}-V_{th})^{\alpha}
   $$

3. **传播延迟** $\tau=C_{\text{eff}}V_{dd}/I_d$，故频率 $f=1/\tau\propto I_d/(C_{\text{eff}}V_{dd})$。取 $\alpha=2$（论文取长沟道平方律）：
   $$
   B_w\;\propto\; f\;\propto\; \frac{(V_{dd}-V_{th})^2}{V_{dd}}
   $$

**用法**：Si-IF 从 3200→6400 Gbps/mm 通过**加倍链路频率 + 相应提升 $V_{dd}$** 实现；两式联立给出「提带宽 ⟹ $V_{dd}\!\uparrow$ ⟹ $E_{\text{bit}}\propto V_{dd}^2$ 超线性上升」的能效–带宽取舍，用于建模 6400 Gbps/mm 下的内部 I/O 功耗。这是 §5 中「以能效换带宽」的物理基础。

## 7. 缓冲尺寸（微架构）

Appenzeller 缓冲定径 [20]（原文 $B=\mathrm{RTT}\times BW/\sqrt{n}$，$n$ 为流数）：

$$
S_{\text{buf}} \;=\; \frac{\mathrm{RTT}\cdot B_w}{\sqrt{m}}
$$

晶圆内 $\mathrm{RTT}$ 低（on-wafer 10–20 ns vs 机架内 PCB 100–200 ns vs 100m 光 350 ns）⟹ 缓冲可大幅缩小，进而用快 SRAM 替代慢 DRAM，同时降面积、功耗与延迟。该式属微架构收益，与 §6 的功耗模型相互独立。

## 8. 无阻塞与放宽

- **无阻塞本身借自 Clos [27]**：性能轴是 radix 上限 $n^*$ 而非无阻塞带宽 $B^*$。论文只算「物理约束下最多摆多少端口」，**不**验证给定流量矩阵 $\mathbf{D}$ 下是否无阻塞（无 $\mathbf{D}$ 结构体）；非均匀链路延迟由输入缓冲吸收（A3）。
- **放宽路径（明示取舍）**：非 Clos 拓扑 radix 更高——Butterfly/DragonFly/FlattenButterfly/Mesh 理想情形比 TH-5 高 19×–44×；Mesh 因 2D 布局容易比 Clos 多 10% radix，但 bisection 低、阻塞强；Butterfly 优化后比 Clos 高 10% 但 bisection 与路径多样性低；DragonFly/FlattenButterfly 因 direct 拓扑外部带宽需求大，比 Clos 低 1.7×–3.2×。即「放宽无阻塞换 radix」的显式 trade-off。
- **为何不用 crossbar 变体**：hierarchical / modular crossbar 需 $(n/k)^2$ 个 chiplet，Clos 只需 $3n/k$（表 VI）——面积、功耗、成本上 crossbar 变体不可行，故 Clos 是唯一合理底座。

## 9. 与我们的对照

| 维度 | 我们（00_ours） | Chen 2024 |
|------|----------------|-----------|
| 输出 | 无阻塞带宽 $B^*$（给定拓扑、最坏排列） | radix 上限 $n^*$（给定基板/工艺/冷却） |
| 需求结构体 | 排列 $\mathbf{P}\in\mathcal{R}$、$\mathbf{L}$ 包络 | 无 $\mathbf{D}$，默认 Clos 无阻塞 |
| 功耗 | 线性 per-lane + 静态 $P_0$ | **超线性 $k^2$** + per-lane（pJ/bit）+ 静态 |
| 求解 | LP 精确 + 二分搜索 | 成对交换启发式 + 实测标定 |

**可借鉴点**：把 $P_{\text{core}}\propto k^2$ 并入我们的功耗桥 $\mathbf{P}=P_0+\beta_P B+\mathbf{M}\mathbf{S}_{\text{dyn}}\boldsymbol{\ell}+\gamma\,k^2$，即可让「无阻塞 × 功耗」在 wafer-scale 大 radix 下不失真——这是四篇里唯一补上我们功耗短板的一篇。其 I/O 的 $E_{\text{bit}}\propto V_{dd}^2$ 与 $B_w\propto(V_{dd}-V_{th})^2/V_{dd}$ 亦给出 per-lane 系数随带宽非线性上升的物理依据。

**缺口**：无 $\mathbf{D}$ 结构体、无 $\mathbf{L}$ 包络；$n^*$ 是启发式/实测标定而非 LP 精确解；radix（性能）与无阻塞（Clos 性质）分离，不联立判定——「最多摆多少端口」与「给定流量是否无阻塞」之间无闭环。
