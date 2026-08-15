# 03 — Chiplet 互连架构与平台卡片（新增发现，4 张）

> 2023-2025 新增检索的产出：Si-IF（UCLA）、Simba（MICRO 2019，纠正 venue）、WaferLLM（OSDI 2025）、多 die 交换机（Electronics 2024）。Si-IF 与 Simba 是任务点名的 chiplet 互连/交换案例；WaferLLM 是晶圆级互连的软件层证据。

---

## 卡片 8：Si-IF——Silicon Interconnect Fabric（UCLA，chiplet 互连密度上限）

- **架构名**：Si-IF（silicon interconnect fabric）；配套 SuperCHIPS 协议
- **作者**：UCLA CHIPS（Subramanian Iyer 团队；Jangam 等）
- **出处**：UCLA 技术公开页 + CHIPS 中心新闻 + 2024 IEEE 论文（GaN/Si-IF 供电，IEEE 10413759）。[中等]（官方页与会议摘要；原始系列论文待补）

### 配置参数表

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| 键合方式 | 裸 dielet 热压键合（TCB）到硅 wafer | [中等] | |
| 键合 pitch | **≤10 µm**（metal-metal；演示到 10µm，2024 供电论文 sub-10µm） | [中等] | |
| dielet 间距 | ≤100 µm | [中等] | |
| 短链路（≤500µm） | 延迟 ≤35 ps；插损 ≤2 dB @ 30 GHz | [中等] | |
| 协议 | SuperCHIPS：≥10 Gbps/link，**≤0.04 pJ/bit** | [中等] | |
| 聚合带宽 | **≥8 Tbps/mm**（每 mm dielet 边缘） | [中等] | |
| vs 传统封装 | 120–300× 带宽/mm；100–500× 每 bit 能耗改善；寄生 L 低 10–40×、C 低 7–35× | [中等] | |

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| 平台定位 | 面向 wafer-scale 超大规模异构集成（HPC/AI/LLM 训练） | [中等] |
| 扩展 | cryogenic/superconducting 版本（Superconducting-IF） | [中等] |

### 还原难点

- Si-IF 是**平台**不是具体配置：dielet 尺寸/数量由用户决定，无端到端系统配置可还原；≤10µm pitch 与我们 bump.py 最细的 20-25µm hybrid bonding 还细一档——进模型需要新增 bump 档位或按比例外推。
- 原始论文（IEEE T-CPMT / EDL 系列 2018-2021）未下载，数字以官方页为准（[中等]）。

### 与我们的关系

- **预期最紧约束**：≤10µm pitch 意味着 μbump 供给暴涨（密度 ~10k/mm² 量级），"bump 供给不足"约束被推开，瓶颈会转移到布线与热——它是我们"bump 结构性过剩"论点的**最强平台证据**（与 Rent's rule 卡呼应）。
- **对照实验设计**：把 Si-IF 的 8 Tbps/mm 作为 lane 密度上限输入（等价于 lanes_per_mm 拉到物理极限），重跑布线约束实验——预期 B* 从 bump 墙翻到布线/热墙，直接支撑"瓶颈转移"叙事。

### 来源

- UCLA 技术公开页（ucla.technologypublisher.com/technology/48108）
- UCLA CHIPS 新闻（chips.ucla.edu/news/media/13，Siva Jangam，≤10µm 表征）
- IEEE 10413759（2024，GaN/Si-IF 异构供电，sub-10µm）

---

## 卡片 9：Simba（chiplet 计算阵列——"chiplet 交换机"的对立面，但互连数据直接可用）

- **架构名**：Simba——36-chiplet MCM 深度学习推理加速器
- **作者**：Yakun Sophia Shao 等（Berkeley/NVIDIA/Toronto 合作）
- **出处**：**MICRO 2019**（⚠️ 旧 survey 记为 ISCA 2019 有误，实为 MICRO-52），DOI 10.1145/3352460.3358302；CACM 2021 跟进。[可靠]

### 配置参数表

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| chiplet 数/阵列 | 36 个（6×6），评估用 32 个（2 的幂分片） | [可靠] | |
| chiplet 尺寸/工艺 | **6 mm²**，16nm FinFET | [可靠] | |
| 每 chiplet 算力 | 4 TOPS（8b 权重/24b 累加） | [可靠] | |
| 每 chiplet 存储 | 752 KiB | [可靠] | |
| 频率 | 161 MHz – 1.8 GHz | [可靠] | |
| 互连拓扑 | 2D mesh NoP（network-on-package），XY 路由 | [可靠] | |
| 每 chiplet 带宽 | **100 GB/s**（GRS 地参考信号有线 mesh） | [可靠] | |
| GRS 典型速率 | 11 Gbps/lane（0.72V 评估点） | [可靠] | |
| 系统峰值 | 128 TOPS（1.1V/1.8GHz）；能效 0.2–6.1 TOPS/W | [可靠] | |
| 每 chiplet 功耗（推算） | ~0.6 W（峰值能效点，0.16 pJ/op @0.52V） | [中等] 推导 | |

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| ResNet-50 | 1,988 img/s（batch 1，0.50 ms 延迟） | [可靠] |
| 关键发现 | 通信开销限制扩展：部分层高 chiplet 数时效率掉近一个数量级；mapping 差异最高 2.5×——通信感知 tiling 必要 | [可靠] |

### 还原难点

- Simba 是**计算阵列**不是交换机：无 port/radix 概念，互连是纯 2D mesh；chiplet 6mm² 是我们 12×12mm 假设的 1/24，bump/布线按比例缩放有代表性风险。
- 100 GB/s/chiplet 的 GRS mesh 是 on-package 有线——可类比我们的"die 内/近距"档位，但无 SerDes 外部口，C4 约束不适用。

### 与我们的关系

- **预期最紧约束**：若把它当"chiplet 密度极限"样本，6mm²/16nm 小 die 的 bump 供给远大于 100 GB/s 需求——它是"die 越小 I/O 越富"（Rent 规则 + area-array）的实证；反过来，128 TOPS 的通信受限结论支持我们"性能包络约束在 chiplet 阵列里主导"的判断。
- **对照实验设计**：6×6 mesh、100 GB/s/chiplet、GRS 11 Gbps/lane 进我们的 mesh 模型——lane 数 = 100GB/s ÷ 11Gbps ≈ 73 lane/chiplet，在 6mm² 上的 bump 占用率极低，验证"小 die 场景 bump 供给不是约束"。

### 来源

- ACM DOI 10.1145/3352460.3358302（MICRO-52）
- 作者版 PDF（people.eecs.berkeley.edu/~ysshao/assets/papers/shao2019-micro.pdf）

---

## 卡片 10：WaferLLM（OSDI 2025——晶圆级互连约束的软件层实测证据）

- **架构名**：WaferLLM——晶圆级 LLM 推理系统（跑在 Cerebras WSE 上）
- **作者**：Congjie He, Yeqi Huang, Pei Mu, Ziming Miao, Jilong Xue, Lingxiao Ma, Fan Yang, Luo Mai（爱丁堡大学 + Microsoft Research）
- **出处**：OSDI 2025；arXiv:2502.04563。[可靠]

### 关键参数（PLMR 模型——晶圆级互连的四个硬件属性）

| 属性 | 值 | 出处 | 状态 |
|---|---|---|---|
| P：并行度 | 百万级核/wafer | [可靠] | |
| L：延迟不均匀 | 核间延迟差异最高 **1000×**（mesh 中心 vs 边） | [可靠] | |
| M：本地存储 | 每核 tens of KB – few MB | [可靠] | |
| R：硬件路由能力 | 只支持小消息、少量路由路径（**WSE-2 上 <2⁵ 条路径**） | [可靠] | |

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| GEMV vs A100（同为 7nm） | **606× 更快**，能效 16–22× | [可靠] |
| 推理加速 vs GPU 集群 | decode 10–20×（论文版 38–39×） | [可靠] |
| vs SOTA 系统 | 100–200×（T10）、200–400×（Ladder） | [可靠] |
| 算法 | MeshGEMM（prefill，cyclic shifting + interleaving）；MeshGEMV（decode，two-way K-tree allreduce） | [可靠] |

### 还原难点

- 纯软件论文：不做硬件配置，但 PLMR 的 R 属性（<2⁵ 路由路径）是对 Cerebras mesh 路由供给的**实测约束**，比任何架构幻灯都具体。

### 与我们的关系

- **预期最紧约束**：R 属性直接对应我们的"路由层性能包络"约束——WSE-2 上硬件只支持 32 条路径/核，说明真实 wafer mesh 的路由供给远小于我们模型假设的自由路由；这是"性能包络约束需要按硬件路径数收紧"的实证。
- **对照实验设计**：把"路径数 ≤32/核"作为我们路由层约束的附加限制（等价于限制路径 incidence 矩阵行数），看 B* 的损失——预期量化"硬件路由供给"这一我们目前未建模的约束项。

### 来源

- arXiv:2502.04563（abstract + GitHub MeshInfra/WaferLLM）

---

## 卡片 12：多 die 交换机（Multi-Die Optimization with Efficient Connections，chiplet 交换机稀缺条目）

- **架构名**：多 die 交换机的统一互连架构（数据队列映射 + 统一接口）
- **作者**：Jifeng Luo, Feng Yu, Weijun Li, Qianjian Xing
- **出处**：Electronics 2024, 13(16): 3205；DOI 10.3390/electronics13163205。[中等]（MDPI 期刊，质量一般，仅作 chiplet 交换机近期公开条目）

### 已知参数

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| 动机 | 多 die 封装下 die 间连接有限，交换机内部互连受限 | [中等] | |
| 声称结果 | die 间互连占用 **-25%**，同时支持 unicast+multicast | [中等] | |
| 具体规模 | 未公开（无 die 数/端口数） | — | [待确认] |

### 与我们的关系

- 与我们卡 3（Wan TVLSI）同一问题域（chiplet 交换机的 die 间互连），但深度差很多。用途仅是"chiplet 交换机研究存量稀少"的现状佐证——它 + 卡 1 + 卡 3 就是"把交换机搬到多 die/晶圆级"的全部主要公开工作，支撑我们的 gap claim。

### 来源

- MDPI Electronics 13(16):3205（ouci.dntb.gov.ua 收录页交叉确认）

---

## 搜索未果记录（供后续）

- **Stanford "PRIZE" chiplet 交换机**（或类似名的开源 chiplet 交换 fabric）：多次检索无结果——可能名字记错或未公开发表，未建档。
- **Decimo**（ETH wafer-scale LLM inference）：检索无结果，未建档。
- **Optimus high-radix switch**：检索无结果，未建档。
- **Coyote**（2018 Cisco/Stanford chiplet 交换机）：检索无结果，未建档——属窗口外（<2023）且需原文，暂缓。
