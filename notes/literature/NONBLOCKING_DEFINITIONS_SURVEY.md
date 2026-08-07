# 广义无阻塞：跨领域定义、松弛与构造

> 调研日期：2026-07-31
> 问题：不同领域如何定义和松弛"无阻塞"？我们的"广义无阻塞"（$B_{\text{nb}} = B_{\text{link}}/L^*$，允许链路共享只要降速后仍 ≥ 目标带宽）在已有文献谱系中处于什么位置？

---

## 0. 文献谱系总图

```
                       无阻塞（Nonblocking）
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   确定性的               概率的              构造视角的
   （经典交换理论）        （排队论/流量工程）    （图论/expander）
        │                   │                   │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
  SNB  WSNB  RNB    随机无阻塞  有效无阻塞  广义连接器  VNB/ANB
  (严格)(宽感)(可重排) (blocking   (effective  (Pippenger (Zheng)
                      prob < ε)  nonblocking)  1980s)    (2005+)
                          │
                    多速率无阻塞 ←── 我们在这附近
                    (multirate NB)
```

---

## 1. 经典交换理论：SNB / WSNB / RNB

### 1.1 严格无阻塞 (Strictly Nonblocking, SNB)

**定义**（Clos 1953; Benes 1965）：对任意空闲输入 $i$ 和空闲输出 $o$，以及任意已建立的连接集合 $\mathcal{P}$（从 $I \setminus \{i\}$ 到 $O \setminus \{o\}$ 的顶点不相交路径），**存在**一条从 $i$ 到 $o$ 的路径，与 $\mathcal{P}$ 中所有路径顶点不相交。且**任意**可用的无冲突路径都可以选择——不依赖路由算法。

**图论等价定义**（Pippenger 1978）：一个 SNB $n$-连接器是一个有向无环图，对任意 $i \in I, o \in O$ 和任意从 $I \setminus \{i\}$ 到 $O \setminus \{o\}$ 的顶点不相交路径集 $\mathcal{P}$，存在从 $i$ 到 $o$ 的路径与 $\mathcal{P}$ 顶点不相交。

**Clos 条件**：三阶 Clos $C(n, m, r)$ 严格无阻塞当且仅当 $m \ge 2n-1$。

**代价**：crossbar $O(N^2)$，Clos $O(N^{1.5})$。已知下界：$\Omega(N \log N)$ crosspoints（Shannon 1950）。

### 1.2 宽感无阻塞 (Wide-Sense Nonblocking, WSNB)

**定义**（Benes 1965）：存在一个**路由算法** $\mathcal{A}$，使得按照 $\mathcal{A}$ 的规则选择路径时，任何新连接都可以在不干扰已有连接的情况下建立。与 SNB 的区别：路径不能任意选，必须遵守 $\mathcal{A}$ 的规则。

**形式化定义**（Feldman, Friedman & Pippenger 1988）：一个网络 $\mathcal{N}$ 是 WSNB $n$-连接器，如果存在一个**安全状态**集合 $\mathcal{S}$（路径集的偏序），满足：
1. $\emptyset \in \mathcal{S}$（空状态是安全的）
2. 向下封闭：$S \in \mathcal{S}$ 且 $S' \subseteq S \Rightarrow S' \in \mathcal{S}$
3. 扩展性：对任何 $S \in \mathcal{S}$ 和兼容的新请求 $(i, o)$，存在 $S' \in \mathcal{S}, S' \supseteq S$ 使得 $S'$ 包含满足 $(i, o)$ 的路由

**关键困难**：WSNB 的证明通常比 SNB 更困难，因为必须同时考虑连接的到达**和**离开。路由历史影响当前可达状态。SNB 只需要考虑当前快照。

**Benes 经典结果**：$C(n, m, 2)$ 在 $m \ge \lfloor 3n/2 \rfloor$ 时是 WSNB（通过 packing 路由算法）。

**与我们的关系**：WSNB 的形式化定义（路由算法依赖的无阻塞）为我们提供了概念定位——我们用松弛 LP（$\min_{D,\mathbf{f}} \max_e L_e$）判断拓扑是否"有潜力"实现无阻塞（即存在某个路由策略和流量分配使负载 ≤ 1），这对应 WSNB 的"存在某个路由算法"的精神，但不要求构造出该算法。

### 1.3 可重排无阻塞 (Rearrangeably Nonblocking, RNB)

**定义**（Slepian 1952; Duguid 1959; Benes 1965）：对任意一组兼容的连接请求（任意排列），**存在**一组顶点不相交的路径同时满足所有请求。可以重排已有连接来腾出路径。

**Slepian-Duguid 定理**：$C(n, m, r)$ 可重排无阻塞当且仅当 $m \ge n$。

**Benes 网络**：递归构造，$O(N \log N)$ crosspoints，达到渐近最优下界。

**与我们的关系**：我们的 Clos 分解方案——interposer 间用 $K \ge M$ 保证可重排无阻塞——直接引用 Slepian-Duguid。

### 1.4 三者的关系

$$\text{SNB} \subset \text{WSNB} \subset \text{RNB}$$

| | SNB | WSNB | RNB |
|---|---|---|---|
| 是否需要路由算法 | 否 | **是** | 否 |
| 是否重排已有连接 | 否 | 否 | **是** |
| Clos 条件 ($r=2$) | $m \ge 2n-1$ | $m \ge \lfloor 3n/2\rfloor$ | $m \ge n$ |
| 代价 | 最高 | 中 | 最低（可达 $O(N \log N)$） |

---

## 2. 图论/组合视角：广义连接器与 Expander

### 2.1 广义连接器 (Generalized Connector)

**定义**（Pippenger 1978; Feldman, Friedman & Pippenger 1988）：

一个**广义 $n$-连接器**是一个有向无环图，有 $n$ 个输入和 $n$ 个输出。对任意一对多映射 $\phi$（每个输入映射到一组不相交的输出），存在一组**顶点不相交的树**将每个输入 $i$ 连接到输出集 $\phi(i)$。

- 普通 $n$-连接器：一对一（路径）。广义连接器：一对多（树 = multicast）。
- 广义连接器 → 支持 multicast 的非阻塞网络。

**WSNB 广义连接器**（Feldman et al. 1988）：大小 $O(n \log n)$，深度 $k$ 时大小 $O(n^{1+1/k} (\log n)^{1-1/k})$。

### 2.2 Expander 图构造

**核心问题**：能否用 $O(N \log N)$ edges 显式构造 SNB 网络？

**Bassalygo & Pinsker（1970s，非构造性）**：利用 expander 图（随机图）证明了 $O(N \log N)$ crosspoints、$O(\log N)$ 深度的 SNB 网络**存在**。但不能显式构造。

**Shao & Oruç（1995，显式构造）**：结合 Bassalygo-Pinsker 的递归架构与 Gabber-Galil 显式 expander，给出了第一个显式的 $O(N \log N)$ crosspoints、$O(\log N)$ 深度的 SNB 网络：
- 精确 crosspoint 数：$-765.18N + 352.8N \log N$
- 深度：$2 + \log(N/5)$
- 并行路由时间：$O(\log N)$ bit-steps

**与我们的关系**：Expander 构造的思路是"用图论保证无阻塞，不管路由算法"。这在数学上很漂亮，但工程上不实用——常数因子太大（$352.8N \log N$），且路由复杂。我们的 Clos 分解更务实。

---

## 3. 概率/排队论视角：随机无阻塞

### 3.1 阻塞概率

**定义**：$$P_B = 1 - P(\text{连接不被阻塞})$$

当 $m < 2n-1$（不满足 SNB 条件）时，Clos 网络有非零阻塞概率。但 $P_B$ 可以非常小。

### 3.2 有效无阻塞 (Effective Nonblocking)

虽然没有形式化定义，但实践中广泛接受：$P_B \le 10^{-6}$（电信级）或 $P_B \le 10^{-9}$（运营商级）即可视为"有效无阻塞"。

**Lee 模型**（1955）、**Jacobaeus 模型**（1950）：Clos 网络阻塞概率的早期解析模型。但两者在 SNB 条件 ($m=2n-1$) 下不归零——这是一个已知的模型缺陷。后续模型修正了这一点。

### 3.3 与我们的关系

我们的"广义无阻塞"——$B_{\text{nb}} = B_{\text{link}}/L^*$，允许 $L^* > 1$ 只要降速后仍 ≥ 目标——**不是概率性的**。我们仍然假设最坏情况排列，但接受链路共享（降速）。这是确定性框架内的松弛，不是概率松弛。

---

## 4. 多速率交换：最接近我们的范式

### 4.1 多速率无阻塞 (Multirate Nonblocking)

**问题设定**（Melen & Turner, IEEE Trans. Comm. 1993）：不同连接需要不同的带宽（如 64 Kbps 语音 + 2 Mbps 视频），共享同一交换网络。每条内部链路有总容量 $C$。一个连接请求 $(i, o, b)$ 需要带宽 $b$。

**多速率 WSNB**：存在路由算法，使得任意一组速率兼容的连接请求（每个入口总带宽 ≤ $C$，每个出口总带宽 ≤ $C$）都可以在不干扰已有连接的情况下建立。

**多速率 SNB**：不需要特定路由算法。

**关键结果**（Ngo & Vu, 2004; Ngo et al. 2010）：多速率 Clos 的 SNB/WSNB 条件比单速率严格得多。对于离散速率集，条件涉及 bin-packing 论据。

### 4.2 与我们的关系

**我们的"广义无阻塞"本质上是多速率无阻塞的一个特例**：
- 每条流需要带宽 $B$（= 一个"端口带宽单位"）
- 内部链路容量为 $B_{\text{link}}$（也是 1 单位）
- $L^*$ 条流共享一条链路 → 每条流分到 $B_{\text{link}}/L^*$
- 要求 $B_{\text{link}}/L^* \ge B$ → $L^* \le B_{\text{link}}/B$

在经典多速率术语中，我们考虑的是**均匀速率、确定性最坏情况流量**的特殊情形。

但与经典多速率文献的关键区别：
- 多速率文献关注**异构速率**（不同连接要不同带宽）
- 我们关注**同构速率 + 链路共享**（所有连接要同样的 $B$，但链路可能被多条流共享）
- 我们的"松弛"来自自适应路由对瓶颈的缓解，不是来自速率异构

---

## 5. Virtual Nonblocking (VNB) 与 Almost Nonblocking (ANB)

### 5.1 VNB（Zheng, 2005+）

**定义**：VNB 网络在任意 I/O 对之间提供**多条路径**。对同一个 I/O 对，可以临时存在多条路径（用于 handoff），但不同 I/O 对的路径始终是链路不相交的。通过 **handoff** 操作（无缝切换已有连接到新路径），VNB 网络可以**完美模拟 SNB 网络**。

- 内部用 RNB 级成本（$O(N \log N)$）
- 对外表现为 SNB（无需重排，无需特定路由算法）
- 代价：handoff 需要临时冗余路径

**两种 handoff 策略**：
- Lazy handoff：只在找不到空闲路径时触发
- Eager handoff：每次新连接到达时主动触发

### 5.2 ANB（Zheng, 2005+）

**定义**：ANB 网络有**极低但非零**的阻塞概率，新连接建立时不干扰已有连接。可以视为"概率无阻塞"的工程实现——$O(N \log N)$ 成本，$P_B \to 0$ 但不严格等于 0。

**SANB / WSANB**：对应 SNB/WSNB 的 probabilistic 版本。WSANB 与特定路由算法耦合设计以最小化 $P_B$。

### 5.3 与我们的关系

VNB 的核心思想——"用冗余路径 + 快速切换实现 SNB 等价行为"——为我们的广义无阻塞提供了另一种辩护：

> 不需要链路严格无阻塞。只需要有足够多（$L^*$ 条）的冗余路径/容量，加上足够快的流控，外部行为就等价于无阻塞。

---

## 6. HPC 互连网络中的"无阻塞"

### 6.1 Dragonfly 的"无阻塞"

**经典定义**（Kim, ISCA 2008）：Dragonfly 的 "nonblocking" 不是经典交换理论意义上的。它指的是：**在均匀随机流量下，minimal routing 可以达到接近 100% 的注入吞吐**。

**平衡条件**：$a = 2p$ 且 $h = p$（$a$：global links/switch，$p$：switches/group，$h$：local links/switch）。

在平衡配置下，minimal routing 达到 ~95% 注入吞吐（均匀流量）。

### 6.2 Valiant 路由下的"无阻塞"

- Valiant 路由在均匀流量下只能达到 ~50% minimal routing 的吞吐（因为每条流用两次 global link）
- 但在**对抗性流量**（bit complement 等）下，Valiant 保持 ~50%，而 minimal routing 崩溃到 1.38%
- **Valiant Any** 变体在对抗性流量下可以达到接近均匀流量的性能

### 6.3 与我们的关系

HPC 社区的"无阻塞"是**仿真驱动的经验定义**——"在这些流量模式下吞吐 ≥ X%"。没有形式化的最坏情况保证。

我们做的是**确定性最坏情况分析**——"对任意排列，链路负载 ≤ 多少"。这是比 HPC 社区更强的保证（不需要假设流量分布），但也更保守（实际流量几乎永远达不到最坏排列）。

---

## 7. 条件无阻塞 (Conditionally Nonblocking)

**定义**（Lee, 1990s）：一类交换网络，只在满足特定条件的排列子集上保证无阻塞。

例子：
- **CU（Circular-Unimodal）无阻塞**：排列矩阵的行索引和列索引满足 circular unimodal 条件
- **UC（Unimodal-Circular）无阻塞**
- **Rotator / Reflector**：特定结构的排列（位移、翻转等）

**两级互连网络**（X2/2X 结构）可以保持这些条件无阻塞性质，支持分布式自路由。

**与我们的关系**：条件无阻塞暗示了一个方向——如果真实流量不覆盖所有 $N!$ 排列，而是集中在某个子集上，无阻塞条件可以放松。我们的排列流量是最坏情况的（全集），但如果工程上能论证真实流量达不到最坏排列，条件可以进一步放松。

---

## 8. Ngo et al. (2010/2012) LP 对偶统一框架

### 8.1 核心方法

1. 将"阻塞条件"表示为**primal LP**（最大化不可用中间模块数）
2. 取**dual LP**
3. **手构造**一个 dual feasible 解（只含网络参数）
4. **弱对偶**给出 universal upper bound
5. bound < m → 非阻塞

### 8.2 关键洞察

**LP 在 Ngo 的方法中是证明工具，不是运行时求解器。** 对每个网络架构（Clos、Banyan、multilog），一次性推导出非阻塞的充分条件（$m \ge f(n,r)$ 形式的不等式），之后只需要检查参数。

### 8.3 与我们的关系

Ngo 的方法适用于**经典交换网络**（Clos/Banyan 及其变体），其中"非阻塞"是二元的（路径存在/不存在）。

我们的问题不同：我们有**物理约束**（bump、功耗、热）耦合，而且"非阻塞"变成了"能否同时满足所有物理约束"。Ngo 的方法处理的是纯拓扑非阻塞，我们需要把物理维度加进去。

**我们的统一 LP 框架在精神上延续了 Ngo 的方向——但统一的维度从"不同类型交换网络的非阻塞条件"扩展到了"性能 + 几何 + 功耗三类物理约束"。**

---

## 9. 综合：我们在谱系中的位置

| 维度 | 经典交换理论 | 多速率交换 | HPC 互连 | **我们** |
|------|------------|-----------|---------|---------|
| 非阻塞定义 | 路径存在性 | 带宽保证 | 仿真吞吐 | **最坏排列下的带宽保证** |
| 确定性/概率 | 确定性 | 确定性 | 概率/经验 | **确定性（最坏排列）** |
| 松弛方式 | SNB→WSNB→RNB | 多速率 WSNB | oversubscription | **允许链路共享，降速后仍 ≥ 目标** |
| 物理约束 | 无 | 无 | 无 | **bump + 功耗 + 热（我们独有的）** |

**我们的"广义无阻塞"定义在已有文献中找不到完全匹配的模板**，但其构成要素都有先例：
- 最坏排列分析 → 经典交换理论（排列矩阵 → BvN 松弛）
- 带宽保证而非路径存在性 → 多速率交换（Melen & Turner 1993）
- 路由策略作为分析工具（松弛 LP 中的 Valiant 候选路径集）→ WSNB 的精神（"存在某个路由策略可实现无阻塞"）
- 物理约束耦合 → **我们的独特贡献**

---

## 10. 对论文的建议

### 10.1 不要叫"广义无阻塞"

这个术语在多速率交换文献中已有特定含义（不同速率连接共享网络）。我们的定义不同（同构速率 + 路由分流 + 物理约束）。

**建议术语**：**"确定性带宽可保证性"（Deterministic Bandwidth Guarantee）** 或 **"最坏排列下的无阻塞带宽"（Worst-Case Permutation Nonblocking Bandwidth）**。

### 10.2 在 Related Work 中的定位

```
§2.1 经典交换网络的无阻塞理论 (Clos 1953, Benes 1965, Hwang 1998)
§2.2 多速率与广义无阻塞 (Melen & Turner 1993, Ngo & Vu 2004)
§2.3 HPC 互连中的非阻塞概念 (Kim ISCA 2008, Dragonfly 平衡条件)
§2.4 本文定位：物理约束感知的确定性带宽保证
```

### 10.3 关键引用

| 引用 | 用于 |
|------|------|
| Clos 1953 | 严格无阻塞条件 ($K \ge 2M-1$) |
| Slepian-Duguid 1959 | 可重排条件 ($K \ge M$) |
| Benes 1965 | WSNB 定义（路由算法依赖的无阻塞） |
| Pippenger 1978 | 图论形式化（安全状态定义） |
| Melen & Turner 1993 | 多速率无阻塞（带宽保证的数学先例） |
| Hwang 1998 | 非阻塞交换网络数学理论（标准参考书） |
| Ngo et al. 2010/2012 | LP 对偶统一分析交换网络（方法论先例） |
| Kim ISCA 2008 | Dragonfly 拓扑 + Valiant 路由 |
| Zheng 2005 | VNB/ANB（冗余路径 + 快速切换） |

---

## 参考文献

1. C. Clos, "A Study of Non-Blocking Switching Networks," *Bell System Technical Journal*, vol. 32, no. 2, pp. 406-424, 1953.
2. V.E. Benes, *Mathematical Theory of Connecting Networks and Telephone Traffic*. Academic Press, 1965.
3. F.K. Hwang, *The Mathematical Theory of Nonblocking Switching Networks*. World Scientific, 1998 (2nd ed. 2004).
4. W. Kabacinski, *Nonblocking Electronic and Photonic Switching Fabrics*. Springer, 2005.
5. N. Pippenger, "Generalized Connectors," *SIAM J. Computing*, vol. 7, no. 4, pp. 510-514, 1978.
6. P. Feldman, J. Friedman, and N. Pippenger, "Wide-Sense Nonblocking Networks," *SIAM J. Discrete Mathematics*, vol. 1, no. 2, pp. 158-173, 1988.
7. R. Melen and J.S. Turner, "Nonblocking Multirate Distribution Networks," *IEEE Trans. Communications*, vol. 41, no. 2, pp. 362-369, 1993.
8. H.Q. Ngo, A. Rudra, A.N. Le, and T.-N. Nguyen, "Analyzing Nonblocking Switching Networks using Linear Programming (Duality)," *IEEE INFOCOM*, 2010. (arXiv:1204.3180, 2012).
9. C.P. Shao and A.Y. Oruç, "Efficient Nonblocking Switching Networks for Interprocessor Communications in Multiprocessor Systems," *IEEE Trans. Parallel and Distributed Systems*, vol. 6, no. 2, pp. 132-141, 1995.
10. S.Q. Zheng and A. Gumaste, "Scalable and Practical Nonblocking Switching Networks," *PDCAT*, 2005.
11. J. Kim, W.J. Dally, S. Scott, and D. Abts, "Technology-Driven, Highly-Scalable Dragonfly Topology," *ISCA*, 2008.
12. Dally & Towles, *Principles and Practices of Interconnection Networks*. Morgan Kaufmann, 2004.
13. H.Q. Ngo and V. Vu, "Multirate Nonblocking Switching Networks," *IEEE Trans. Information Theory*, 2004.
