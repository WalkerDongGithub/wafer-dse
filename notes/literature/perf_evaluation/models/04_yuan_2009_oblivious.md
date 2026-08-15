# 04 Yuan 2009 —— fat-tree 上 oblivious 路由的性能比（单路径 vs 多路径）

> 流量需求 $\mathbf{D}$ 不确定时，与需求无关（oblivious）的路由最坏能差最优多少？答案：**多路径（均分所有最短路径，OMRMN）性能比 = 1**（对任意 $\mathbf{D}$ 与最优同优）；**单路径有下界**——$\mathrm{FT}(r;2)$ 为 $r/4$、$\mathrm{FT}(r;3)$ 为 $r/2$，并构造了达到下界的最优单路径方案 OSRM2/OSRM3。本文给出符号自洽、假设显式、推导逐步的数学形式；组合计数型引理（Lemmas 1–5、8）只陈述结论并标注「见原文」。

## 0. 符号表（本节所有符号在此定义）

| 符号 | 定义 | 原文符号 |
|------|------|---------|
| $r$ | 交换机端口数（radix），$r$ 为偶数 | $m$ |
| $t$ | 交换机层数（内部节点层数），$t\ge1$ | $n$ |
| $n=r(r/2)^{t}$ | 处理节点总数（= 终端数），$i,j\in\{0,\dots,n-1\}$ | 处理节点数 |
| $\mathrm{FT}(r;t)$ | $r$-port $t$-tree fat-tree 拓扑 | $\mathrm{FT}(m;n)$ |
| $\mathrm{SUBFT}(r;l)$ | 含 $l$ 层交换机的子 fat-tree（$l=0,\dots,t-1$） | $\mathrm{SUBFT}(m;l)$ |
| $\mathbf{D}=(D_{ij})$ | 流量矩阵，$D_{ij}\ge0$ = i→j 流量率，单位归一化（链路容量=1） | $\Lambda=(\lambda_{ij})$ |
| $A_i=\sum_j D_{ij}$ | 源节点 $i$ 的总发出流量 | 同义 |
| $L^{B}(\mathbf{D})$ | base load（节点接入瓶颈下界），见 §3.2 | 同义 |
| $\mathcal{P}_{ij}$ | SD 对 $(i,j)$ 的最短路径集合；$h_{ij}=\lvert\mathcal{P}_{ij}\rvert=(r/2)^{l}$ | 同义 |
| $f^{p}_{ij}$ | 路径 $p\in\mathcal{P}_{ij}$ 分流的流量分数，$f^p_{ij}\ge0$，$\sum_{p\in\mathcal{P}_{ij}}f^p_{ij}=1$ | 同义 |
| $L^{g}(\mathbf{D})$ | 路由方案 $g$ 下的最大链路负载（逐向 link load） | 同义 |
| $L^{*}(\mathbf{D})$ | 给定 $\mathbf{D}$ 的最优最大链路负载 | 同义 |
| $PR(g,\mathbf{D})$ | 路由 $g$ 在 $\mathbf{D}$ 上的性能比 | 同义 |
| $PR(g)$ | oblivious 性能比（对所有 $\mathbf{D}$ 取最坏） | 同义 |
| $MDS_{g}(e)$ | 单路径路由 $g$ 下链路 $e$ 的最大 node-disjoint SD 对数 | max disjoint size |

链路编号约定：交换机层从根到叶编为 $0,\dots,t-1$；level-$\ell$ 链路（$\ell=1,\dots,t$）连接 level-$(\ell-1)$ 与 level-$\ell$ 交换机，level-$t$ 链路连接 level-$(t-1)$ 交换机与处理节点。所有链路双向、同容量（归一化容量 = 1），故「最大链路负载」⇔「最大链路利用率」。**链路负载按逐向（up channel / down channel）度量**——这是 $L^B$ 与 Theorem 1 等式自洽所要求的口径（见 §3.2 备注）。

## 1. 模型定位

给定 fat-tree 拓扑、流量需求 $\mathbf{D}$ **未知且变化**，一个**确定性、demand-oblivious**（路径不随需求变）的路由方案，其最大链路负载最坏能比「知道 $\mathbf{D}$ 的最优路由」差多少倍？输出是**性能比（competitive ratio）**，而非绝对带宽。

## 2. 模型假设（显式）

- **A1 拓扑**：$\mathrm{FT}(r;t)$，$r$ 为偶数；所有链路双向、同容量（归一化 = 1）；处理节点数 $n=r(r/2)^t$。
- **A2 需求不确定**：$\mathbf{D}\ge0$ 任意非负矩阵，**不给定具体值**，在最坏 $\mathbf{D}$ 上取性能比。
- **A3 路由 oblivious**：路由与 $\mathbf{D}$ 无关；分**单路径**（每 SD 对恰一条路径）与**多路径**（每条路径按分数 $f^p_{ij}$ 分流）。
- **A4 性能度量**：最大链路负载 $L^{g}(\mathbf{D})$；比较基准为「给定 $\mathbf{D}$ 的最优路由」$L^{*}(\mathbf{D})$。

## 3. 核心数学

### 3.1 定义方程：负载、最优负载、性能比

多路径 $mr$（单路径 $sp$ 为其特例，$f^p_{ij}\in\{0,1\}$）：

$$
L^{mr}(\mathbf{D})=\max_{e\in\mathrm{Links}}\sum_{(i,j)}\sum_{\substack{p\in\mathcal{P}_{ij}\\ e\in p}}f^p_{ij}\,D_{ij},
\qquad
L^{sp}(\mathbf{D})=\max_{e\in\mathrm{Links}}\sum_{(i,j):\,e\in p_{ij}}D_{ij}.
$$

$$
L^{*}(\mathbf{D})=\min_{g\ \text{是路由}}L^{g}(\mathbf{D}),\qquad
PR(g,\mathbf{D})=\frac{L^{g}(\mathbf{D})}{L^{*}(\mathbf{D})}\ge1,\qquad
PR(g)=\max_{\mathbf{D}}PR(g,\mathbf{D}).
$$

$PR(g,\mathbf{D})=1$ 当且仅当 $g$ 在 $\mathbf{D}$ 上最优；$PR(g)$ 是路由 $g$ 的 oblivious 性能比。

### 3.2 base load 与最优负载的下界

**定义（base load）**：处理节点 $i$ 只有一条接入链路，其出向流量 $\sum_j D_{ij}$ 必须经 up channel、入向流量 $\sum_j D_{ji}$ 必须经 down channel，与路由无关。故任何路由的逐向最大链路负载至少受**行和与列和的最大者**下界约束：

$$
L^{B}(\mathbf{D})=\max\Big\{\max_i\sum_j D_{ij},\ \max_j\sum_i D_{ji}\Big\},
\qquad
L^{*}(\mathbf{D})\ \ge\ L^{B}(\mathbf{D}).
$$

> **据正文交叉确认 + 自洽性说明**：原文以文字描述「节点 $i$ 的接入链路（双向）必须承载其全部出/入流量，故任何路由都受此下界约束」（原文 §III 前段），并据此断言「任何路由的 $L^{*}\ge L^{B}$」（原文 Corollary 1）。因原文公式为位图未能逐字提取，此处按与 Theorem 1 的等式结论 $L^{OMRMN}=L^{B}$ 及逐向负载口径**自洽的最紧形式**书写为 $\max(\text{行和},\text{列和})$。若误写为 $\max_i(\sum_j D_{ij}+\sum_j D_{ji})$（双向合并口径），则与「逐向链路负载」证明不自洽（反例：均匀矩阵 $D_{ij}=5/n$ 时行和=列和=5，逐向最大负载=5，而合并口径 $L^B=10>5$ 与 $L^{*}\ge L^B$ 矛盾）。

### 3.3 多路径最优：OMRMN（原文 Theorem 1）

**OMRMN**：对每个 SD 对 $(i,j)$，在全部 $h_{ij}$ 条最短路径上**均分**流量：$f^p_{ij}=1/h_{ij}$。

**Theorem 1（原文）**：对任意 $\mathbf{D}$，$L^{OMRMN}(\mathbf{D})=L^{B}(\mathbf{D})$，故 $PR(\mathrm{OMRMN})=1$。

**推导（每步依据标注）**：

(i) **均分性质（原文 Property 4）**：固定源 $s$。其总流量 $A_s=\sum_j D_{sj}$ 经 OMRMN 均分后，每条 level-$\ell$ up link 承载 $s$ 的流量至多 $A_s/(r/2)^{t-\ell}$。理由：$s$ 在 level-$\ell$ 处有 $(r/2)^{t-\ell}$ 条可用 up link（扇出结构），且对每个目的 $j$，$s\to j$ 的流量在 level-$\ell$ 各链路上的分数至多 $1/(r/2)^{t-\ell}$（原文 Property 4，扇出 $(r/2)$ 每层一次）。

(ii) **扇入性质（原文 Property 5）**：一条 level-$\ell$ up link 至多承载 $(r/2)^{t-\ell}$ 个源节点的流量（$\ell=t$ 时为 1 个处理节点；每降一层乘 $(r/2)$）。

(iii) 设 $S_{(\ell)}$ 为该 level-$\ell$ up link 可承载的源节点集，$\lvert S_{(\ell)}\rvert\le(r/2)^{t-\ell}$。则该链路负载：

$$
L_{(\ell)}\ \le\ \sum_{s\in S_{(\ell)}}\frac{A_s}{(r/2)^{t-\ell}}
\ \le\ (r/2)^{t-\ell}\cdot\frac{\max_s A_s}{(r/2)^{t-\ell}}
\ =\ \max_s\sum_j D_{sj}
\ \le\ L^{B}(\mathbf{D}).
$$

三个「$\le$」依次来自：(i)、(ii)、$\max_s\sum_j D_{sj}\le\max(\text{行和},\text{列和})=L^B$。

(iv) down link 与 up link 对称，同理 $L_{(\ell)}\le L^{B}$。故 $L^{OMRMN}(\mathbf{D})\le L^{B}(\mathbf{D})$。

(v) 由 §3.2 的 $L^{*}\ge L^{B}$ 与 $L^{*}\le L^{OMRMN}$（$L^{*}$ 是最小值），得 $L^{B}\le L^{*}\le L^{OMRMN}\le L^{B}$，故三者相等，$PR=1$。∎

> **修正说明**：旧稿此处把性质写为「level-$l$ 链路被 $(r/2)^l$ 个源使用 / 在 $(r/2)^l$ 条链路上均分」，指数应为 $(r/2)^{t-l}$（level-$t$=处理节点链路只有 1 个源；level-$1$=根链路有 $(r/2)^{t-1}$ 个源）。已按原文 Property 4/5 的文字描述（「$l=n$ 时 level-$n$ 链路直接连处理节点，只承载 1 个节点；每降一层乘 $r/2$」）修正。

### 3.4 单路径下界机制：max disjoint size（原文 §IV）

**定义（node disjoint，原文 Def 1）**：SD 对集合 $\mathcal{A}$ 称 node disjoint，若其中每个节点至多作为源出现一次、至多作为目的出现一次（同一节点可同时作源与目的）。

**定义（max disjoint size，原文）**：对单路径路由 $g$，链路 $e$ 上承载的 SD 对集合的最大 node-disjoint 子集大小记为 $MDS_g(e)$；$MDS(g)=\max_e MDS_g(e)$。

**Lemma 7（原文）**：若单路径路由 $g$ 下存在链路 $e$ 承载 $q$ 个 node-disjoint SD 对，则 $PR(g)\ge q$。

> 证明骨架（原文 Lemma 7）：取 $\mathbf{D}$ 使这些 $q$ 个 SD 对为 1、其余为 0。由原文 Lemma 6（辅助拓扑 SEFT2 中任意 $q$ 个 node-disjoint SD 对可被 link-disjoint 路径路由），存在路由使每条链路负载 $\le1$，故 $L^{*}(\mathbf{D})=1$；而在 $g$ 下链路 $e$ 负载 $=q$，$L^{g}(\mathbf{D})\ge q$。故 $PR(g)\ge q/1=q$。∎（SEFT2 是原文引入的辅助「扩展二层 fat-tree」，见原文 Fig. 6/7。）

**Lemma 9（原文）**：若单路径路由 $g$ 使每条链路承载的 SD 对「至多来自 $X$ 个源」或「至多去往 $X$ 个目的」，则 $PR(g)\le X$。

> 证明骨架（原文 Lemma 9）：任取 $\mathbf{D}$，若链路 $e$ 至多来自 $X$ 个源，则 $L_e\le\sum_{s\in\mathrm{sources}(e)}\sum_j D_{sj}\le X\cdot\max_i\sum_j D_{ij}\le X\,L^{B}\le X\,L^{*}$；去往目的的情形对称。故 $L^{g}(\mathbf{D})\le X L^{*}(\mathbf{D})$，即 $PR\le X$。∎

### 3.5 单路径下界（原文 Theorems 2–5）

$$
PR(g)\ \ge\ \frac{r}{4}\quad\big(\forall\ \text{单路径 } g\ \text{on}\ \mathrm{FT}(r;2)\big),
\qquad
PR(g)\ \ge\ \frac{r}{2}\quad\big(\forall\ \text{单路径 } g\ \text{on}\ \mathrm{FT}(r;3)\big).
$$

> 证明骨架（原文 Theorem 2 + Lemma 8）：$\mathrm{FT}(r;2)$ 中必须经上层交换机路由的 SD 对足够多，而层 0 链路上必有一条承载 $\ge r/4$ 个 node-disjoint SD 对（原文 Lemma 8，对 SEFT2 的计数归纳）；再由 Lemma 7 得 $PR\ge r/4$。$\mathrm{FT}(r;3)$ 同理得 $r/2$（原文 Theorem 4）。$\mathrm{FT}(r;t),\,t\ge4$ 有同机制下界（原文 Theorem 5，值为位图未逐字提取，见原文），但论文只对 $t=2,3$ 构造了达到下界的方案。

### 3.6 达到下界的最优单路径方案（原文 Theorems 6–7）

- **OSRM2**（$\mathrm{FT}(r;2)$）：把每个 level-1 交换机下的 $r/2$ 个节点分成 2 组（每组 $r/4$ 个），按组调度 SD 对经过不同 level-0 交换机，使每条 level-0 up link 恰承载 $\le r/4$ 个源、每条 down link 恰承载 $\le r/4$ 个目的（具体端口→交换机映射见原文 Fig. 8/9）。由 Lemma 9 得 $PR\le r/4$，结合 §3.5 下界得 **$PR(\mathrm{OSRM2})=r/4$**（当 $r/4$ 为整数；非整数情形原文另有推广）。
- **OSRM3**（$\mathrm{FT}(r;3)$）：把每个 $\mathrm{SUBFT}(r;2)$ 视为一个「$(r/2)$ 端口、$(r/2)^2$ 个节点」的伪交换机，按 OSRM2 同法调度 level-0 链路，使每条链路承载 $\le r/2$ 个源/目的（见原文 Fig. 10）。由 Lemma 9 + §3.5 下界得 **$PR(\mathrm{OSRM3})=r/2$**。

## 4. 模型输出

- **多路径 OMRMN**：$PR=1$——对任意 $\mathbf{D}$ 与最优路由同优，且**无需**运行一般拓扑上的高复杂度最优 oblivious 路由算法。
- **单路径**：$\mathrm{FT}(r;2)$ 最优 oblivious 比 $=r/4$、$\mathrm{FT}(r;3)$ 最优 $=r/2$，以及达到它们的显式方案 OSRM2/OSRM3。
- **定量差距**：单路径 vs 多路径的保证差距随 radix 线性放大（$r/4$、$r/2$ vs $1$）——直接论证「大 fat-tree 上必须用多路径」。

## 5. 无阻塞与放宽

- **严格无阻塞**：多路径 OMRMN 意义下成立——最坏负载 $=L^{B}$（节点接入带宽决定的固有下界），任何路由都不可能更低，故「多路径 + 均分最短路径」是 fat-tree 上的**最优 oblivious 无阻塞**。
- **放宽路径**：① 单路径是最严格的放宽（路径数=1），代价是最坏比 $r/4$（$t=2$）/ $r/2$（$t=3$），随 radix 恶化；② 现实系统限制路径数（如 InfiniBand 最多 128 条）→ 介于二者之间，**无法保证达到 $PR=1$**；③ 论文实验显示最优单路径方案在平均情形（均匀/热点流量）不劣于现有 MLID/WSR，但在 clustered 流量下最坏比显著大于 1。

## 6. 功耗地位

**完全不建模**。只给「相对性能比」，无功耗、无面积、无 lane、无热。控制面代价是路径枚举/建立（可集中式或分布式），属路由表计算而非功耗。

## 7. 与我们的对照

| 维度 | 我们（00_ours） | Yuan 2009 |
|------|----------------|-----------|
| 需求结构体 | 最坏排列 $\mathbf{P}\in\mathcal{R}$（枚举，确定性最坏） | 任意不确定 $\mathbf{D}$（competitive ratio） |
| 判定对象 | 最大无阻塞带宽 $B^{*}$ | 性能比 $PR$（相对最优） |
| 拓扑 | vertex-transitive 一般拓扑 | fat-tree $\mathrm{FT}(r;t)$ |
| 枢纽量 | 负载包络 $\mathbf{L}$ | 最大链路负载 $L^{g}(\mathbf{D})$（逐向） |
| 输出 | $B^{*}$ + 约束账本 | $PR$ + 显式路由方案 |
| 延迟 | ❌ | ❌ |
| 功耗 | ✅（线性 + 静态） | ❌ |

**可借鉴点**：① oblivious 框架是「**不枚举最坏 $\mathbf{D}$ 也敢给最坏保证**」的替代路径——用 ratio 而非枚举，对我们「排列枚举 + LP」是互补视角；② **多路径 $PR=1$** 说明 fat-tree 上「均分所有最短路径」就是最优 oblivious 路由，为我们的「最优自适应路由 = 潜能判定」提供 fat-tree 侧的严格背书；③ **max disjoint size** 是 fat-tree 上最坏负载的廉价组合估计（一个组合量即给下界），可作我们 $\mathbf{L}$ 包络的快速上/下界锚点。

**缺口**：不联立功耗；只给**相对**比不给绝对带宽 $B^{*}$；延迟不在模型内；拓扑限定 fat-tree（我们的一般拓扑群论归约更广，但依赖 vertex-transitive）。
