# 00 性能模型审视框架（读每篇 perf 论文的统一视角）

> 用途：用同一套问题去审视「性能评价模型」论文，判断它能给我们什么、缺什么、功耗建模在哪一层。
> 这是方法论对标（`plan_research_agenda.md` §2.4「论证同行是我们的子集」）的核心工具。
> 来源：与用户 2026-08-15 讨论定稿。

---

## 0. 六个审视问题（框架本体）

对任意一篇「性能模型」论文，逐条回答：

| # | 维度 | 问题 |
|---|------|------|
| Q1 | **输入** | 模型输入有哪些？依赖流量（traffic-dependent）还是纯拓扑性质（topology-only）？具体形态（流量矩阵 / 排列 / arrival curve / 拓扑参数）？ |
| Q2 | **性能定义** | 它评价的「性能」是什么？无阻塞带宽？空载延迟（zero-load latency）？带宽-延迟曲线？吞吐量？ |
| Q3 | **数学表示** | 用什么数学形式？（LP / queueing / network calculus / 组合-群论 / 仿真） |
| Q4 | **无阻塞判定能力** | 若我们需要无阻塞，它能给出严格无阻塞答案吗？放宽条件后，能给出「差不多无阻塞 / 近似」答案吗？ |
| Q5 | **功耗建模** | 有没有讨论功耗？功耗在它眼里是什么地位——链路线性项（per-lane pJ/bit）？超线性项（radix²）？还是一个静态常量 P0？或完全不建模？ |

> 这六个问题里，**Q5（功耗）是最能暴露空白的一维**：绝大多数性能模型论文根本不碰功耗。

---

## 1. 逐篇审视表

| 论文 | Q1 输入 | Q2 性能 | Q3 数学 | Q4 无阻塞 | Q5 功耗 |
|------|---------|---------|---------|-----------|---------|
| **我们（Birkhoff 排列 + LP 包络）** | 依赖流量：排列矩阵 + 拓扑对称性（群论归约） | 无阻塞带宽 B\*（二分搜索） | LP（纯线性） | 严格（对称假设下）；放宽→RNB | 线性 per-lane + 静态 P0；**无 radix² 项** |
| **Chang & Lee 2006（交换机专著）** | 依赖流量：双随机矩阵（admissible） | 100% throughput | Birkhoff 分解 + Lyapunov | 严格（调度层 100% throughput） | 不讨论 |
| **McKeown 1996（100% throughput）** | 依赖流量：i.i.d. arrival（admissible） | 100% throughput | LP + 二次 Lyapunov | 严格（最大权重匹配） | 不讨论 |
| **Chang 1999（Birkhoff service guarantees）** | 依赖流量：doubly substochastic（admissible） | 100% throughput + service guarantee | Birkhoff 分解 + 调度（offline O(N^4.5)） | 严格（对所有非均匀流量 uniform） | 不讨论 |
| **Le Boudec & Thiran（网络演算）** | 依赖流量：arrival curve α | **延迟上界 + 积压界**（非带宽） | min-plus 代数 | 不直接答无阻塞，答延迟界 | 不讨论 |
| **Harchol-Balter（queueing 教材）** | 依赖流量：arrival/service 分布 | **平均响应时间 / 延迟** | queueing（M/M/1、M/G/1、Little） | 不答无阻塞，答均值 | 不讨论 |
| **Kiasari 2013（NoC queueing）** | 依赖流量：任意 pattern + 拓扑 + mapping | **平均延迟** | G/G/1 queueing | 不答无阻塞，答平均延迟 | 不讨论 |
| **Fischer 2012（NoC queueing）** | 依赖流量：pattern + 拓扑 + routing | **平均延迟 + 稳态分布** | queueing（状态分布） | 不答无阻塞 | 不讨论 |
| **Mandal 2019（NoC 优先级）** | 依赖流量：input traffic + 微架构（priority class） | **端到端延迟** | queueing（优先级队列变换） | 不答无阻塞 | 不讨论 |
| **Yuan 2009（oblivious routing）** | 依赖流量但**不确定**（oblivious） | oblivious performance ratio（吞吐比值） | 组合 / LP | 间接（ratio=1 即任意流量最优） | 不讨论 |
| **Zhang-Shen & McKeown 2008（VLB 容错）** | 依赖流量：traffic matrix | congestion-free + 容错 | VLB（Valiant）分析 | 间接（任意流量矩阵可支持） | 不讨论 |
| **Chen ISCA 2024（waferscale switch）** | 依赖拓扑：Clos 映射 + radix | radix（受内带宽/外带宽/功耗密度限制） | 组合 + 启发式 | Clos 无阻塞 | **讨论：quadratic 超线性** |

---

## 2. 框架扫出来的三个结构洞见

### 2.1 功耗是最大的空白（Q5 几乎全空）

上表 Q5 列，12 篇里只有 **Chen ISCA 2024** 讨论了功耗（且明确是 quadratic 超线性），其余 11 篇全部「不讨论」——包括 Chang/McKeown 的 100% throughput、Le Boudec 的网络演算、Harchol-Balter 的 queueing 教材、以及全部 NoC queueing 模型。

- 这意味着「**无阻塞带宽 + 功耗联立建模**」在文献里是**真空**——我们（Birkhoff + LP + 热/bump/功耗约束）正好站在这个空位上。
- 这正是 `plan_research_agenda.md` §2.4「论证同行是我们的子集」的最强论据：同行要么做无阻塞（不碰功耗），要么做功耗（不碰无阻塞），**没人把两者放在同一个可求解模型里联立**。

### 2.2 「性能」分裂成两个正交轴

- **带宽轴**：无阻塞带宽 / 100% throughput / radix（Chang、McKeown、Yuan、Chen、我们）
- **延迟轴**：延迟界 / 平均延迟（网络演算、NoC queueing）

两轴几乎不相交。我们当前 perf 模型**只在带宽轴**；网络演算是把延迟轴并入的现成入口（arrival curve 输入 + service curve 输出延迟界）。

### 2.3 「输入」的 traffic-dependent vs topology-only 之别

- 大多数模型**依赖流量**（矩阵 / 排列 / arrival curve）——需要指定「最坏流量是什么」。
- 我们的群论归约属于「用拓扑对称性压缩流量枚举」——是 traffic-dependent 与 topology-only 的**混合**：流量假设是排列，但枚举量由 Aut(H) 决定。
- oblivious routing（Yuan）是「不确定流量」的一般化：不指定具体流量，给 ratio 保证。这比「排列 = 最坏流量」更宽松、更贴近真实数据中心流量的不确定性。

---

## 3. 结论：框架给我们的定位

用六个问题看，我们的性能模型在文献版图里的位置是：

> **「无阻塞带宽 + 功耗联立 + LP 可解」—— 三个标签的组合在现有文献里无人占据。**

- 无阻塞带宽：Chang/McKeown 有，但不碰功耗。
- 功耗联立：Chen 有（超线性），但做的是 radix 上限而非无阻塞带宽判定。
- LP 可解 + 群论归约：只有我们。

下一步（可选）：
1. 用 Q1–Q6 把 `perf_evaluation/README.md` 里列的四类文献（吞吐量理论 / 网络演算 / oblivious / NoC queueing）逐篇补齐审视表。
2. 把「Q4 放宽条件 → 差不多无阻塞」作为一个**独立子问题**，对应去看哪些模型能给出近似无阻塞（如 RNB、oblivious ratio、100% throughput 的 ε-松弛）。
