# 性能评价方法文献地图（perf 模型增强）

> 用途：为现有 perf 模型（Birkhoff 排列流量 + 群论归约 + LP 包络，见 `notes/NONBLOCKING_CONDITIONS.md`）找「更好的性能评价方法」。
> 检索时间：2026-08-15。质量家法：`RENT_RULE_AND_IO_DENSITY.md`。

---

## 0. 现有 perf 模型的三个缺口

| 缺口 | 现状 | 后果 |
|------|------|------|
| 只判带宽/无阻塞，**不评延迟** | LP 只求可行分流 + 负载包络 | 无法回答「B* 下延迟多少」 |
| 流量模型 = **排列矩阵**（最差情况） | Birkhoff-von Neumann，admissible traffic | 覆盖 permutation，但未显式处理一般可容许流量/不确定流量 |
| 无阻塞语义 = **潜能**（最优路由） | 文档自述「potential, not guarantee」 | 不是严格保证，需 RNB 兜底 |

---

## 1. 吞吐量理论（加固带宽判定，与现有 Birkhoff 同源）

| 文献 | 出处 | 补足什么 |
|------|------|---------|
| **Chang & Lee, "Principles, Architectures and Mathematical Theories of High Performance Packet Switches"** | Springer, 2006（专著，全书） | 交换机性能数学理论的权威总纲：Birkhoff-von Neumann switch、load-balanced switch、100% throughput 的统一框架 |
| **McKeown, Anantharam, Walrand, "Achieving 100% Throughput in an Input-Queued Switch"** | INFOCOM 1996 | 用 LP + 二次 Lyapunov 证明最大权重匹配可达 100% throughput；「100% throughput」这个概念的源头 |
| **Chang, Chen, Huang, "On service guarantees for input-buffered crossbar switches: a capacity decomposition approach by Birkhoff and von Neumann"** | IWQoS 1999, DOI 10.1109/IWQOS.1999.766481 | Birkhoff-von Neumann 分解直接用作调度，提供 uniform service guarantee + 100% throughput——现有方法的严格化版本 |

> 这三篇是现有 Birkhoff 方法的上游理论：把「排列 + 包络」从启发式升级为「有 100% throughput 保证的分解调度」。

---

## 2. 延迟 / 积压的确定性界（网络演算，补足延迟评价）

| 文献 | 出处 | 补足什么 |
|------|------|---------|
| **Le Boudec & Thiran, "Network Calculus: A Theory of Deterministic Queuing Systems for the Internet"** | Springer LNCS 2050, 2001（权威教材，中文版《网络演算》2022） | arrival curve + service curve → 端到端延迟上界 + 积压（buffer）界；min-plus 代数体系 |
| **RFC 9320, "Deterministic Networking (DetNet) Bounded Latency"** | IETF, 2022（Le Boudec 为作者之一） | 网络演算在确定性网络（TSN/DetNet）的落地：算排队延迟、积压、零拥塞丢失 |

> 网络演算给的是**确定性最坏情况界**（不是平均），跟现有「最差排列流量」的 worst-case 精神一致——适合把 perf 模型从「只判可行」扩展为「可行 + 延迟上界」。

---

## 3. 不确定流量下的性能保证（oblivious routing）

| 文献 | 出处 | 补足什么 |
|------|------|---------|
| **Yuan, Nienaber, Duan, Melhem, "Oblivious Routing in Fat-Tree Based System Area Networks with Uncertain Traffic Demands"** | IEEE/ACM Trans. Networking, 2009 | oblivious performance ratio（路由性能 vs 最优的比值）：单路径有下界，多路径可达 ratio=1（对任意流量最优） |
| **Zhang-Shen & McKeown, "Designing a Fault-Tolerant Network Using Valiant Load-Balancing"** | INFOCOM 2008 | VLB 支持任意流量矩阵 + 容错，过配比 ~k/N |

> 现有「排列 = 最差流量」是 traffic-oblivious 的特例；oblivious routing 给出「不确定流量下性能保证」的更一般框架。

---

## 4. NoC 分析延迟模型（queueing theory，快速延迟估计）

| 文献 | 出处 | 补足什么 |
|------|------|---------|
| **Kiasari, Lu, Jantsch, "An Analytical Latency Model for Networks-on-Chip"** | IEEE TVLSI 21(1), 2013 | G/G/1 queueing，任意拓扑 + 确定性路由 + 任意流量，平均延迟误差 <10%，比仿真快 4 个数量级 |
| **Fischer, Fehske, Fettweis, "A Flexible Analytic Model ... Queueing Theory"** | SIMUL 2012 | queueing theory，给路由器稳态分布，可推导 mean latency / buffer usage / blocking，误差 ~3% |
| **Mandal et al., "Analytical Performance Models for NoCs with Multiple Priority Traffic Classes"** | arXiv:1908.02408, 2019 | 优先级感知的 NoC 分析模型（工业 NoC 有 priority scheduler） |

> 这类是「平均延迟」的快速解析模型，与网络演算的「最坏延迟界」互补；可作为 LP 判可行之后的 second-pass 延迟估计。

---

## 5. 推荐路径

1. **先加固吞吐量理论**（§1 Chang/McKeown）：现有 Birkhoff 方法的最直接上游，能让「排列 + 包络」的可行性判定有「100% throughput」理论背书。
2. **再加延迟界**（§2 网络演算）：把 perf 模型从「判带宽」升级为「带宽 + 延迟上界」，是论文最自然的增量贡献。
3. **oblivious routing**（§3）作为「不确定流量」的一般化叙述，NoC queueing（§4）作为实验对照。

## 6. 归档状态

> ✅ 已下载归档（2026-08-15）：
> - 教材 → `textbooks/`：`Le_Boudec_Thiran_Network_Calculus_LNCS2050.pdf`、`Harchol_Balter_Performance_Modeling_Queueing_Theory.pdf`
> - 论文 → `perf_evaluation/papers/`：McKeown 1996、Chang 1999、Kiasari 2013、Fischer 2012、Mandal 2019、Yuan 2009、ZhangShen & McKeown 2008（7 篇）

| 完整原文题名（仍可补） | 出处 | 说明 |
|------|------|------|
| **Principles, Architectures and Mathematical Theories of High Performance Packet Switches** | Cheng-Shang Chang, Duan-Shin Lee, Springer 2006 | 专著；在线版 `ee.nthu.edu.tw/cschang/switchbook.pdf` |
