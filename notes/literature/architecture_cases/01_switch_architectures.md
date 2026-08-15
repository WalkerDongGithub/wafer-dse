# 01 — 晶圆级交换机架构卡片（4 张）

> 对应 LITERATURE_SURVEY.md B1-B4，加深到参数级。

---

## 卡片 1：Waferscale Network Switches ⭐（我们的直接对标）

- **架构名**：Waferscale Network Switch（WSI 交换机）
- **作者**：Shuangliang David Chen（UIUC）、Saptadeep Pal（Etched AI）、Rakesh Kumar（UIUC）
- **出处**：ISCA 2024（2024-06-29 ~ 07-03，Buenos Aires）→ IEEE Micro Top Pick，Vol. 45, Issue 4, pp. 37-43（2025）。[可靠]

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| 仅考虑面积约束时的 radix 提升 | 最高 **32×**（vs 现有最先进交换机） | [可靠] IEEE Micro 摘要 |
| 实际瓶颈（radix 不涨的原因） | 内部带宽、外部带宽、功率密度 三者共同限制 | [可靠] 同上 |
| 异构 subswitch 设计（heterogeneous） | 交换功耗降 **30.8%–33.5%**，换来的功耗余量可让 radix 再升 **4×**（靠牺牲能效增加内部 I/O 带宽） | [可靠] 同上 |
| Subswitch deradixing（降 subswitch radix） | 缓解内部 I/O 瓶颈，整体 radix **×2** | [可靠] 同上 |
| 外部带宽解法 | Area I/O（面阵列 I/O）+ Optical I/O 替代传统 SerDes | [可靠] 同上 |
| 时延优化 | low-latency buffering + proprietary routing | [可靠] 同上 |
| 系统配套 | 支撑端口数/供电/冷却的紧凑机箱系统架构 | [可靠] 同上 |

### 配置参数表（我们模型输入视角）

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| 拓扑族 | 单级 switch（die 内 crossbar 族），无显式拓扑参数 | — | — |
| baseline radix 具体值 | 未在摘要给出（疑对标 512 端口级商用交换机） | — | [待确认] 需全文 |
| 内部 I/O 带宽上限（Tbps） | 未给出 | — | [待确认] 需全文 |
| 外部 SerDes 带宽上限 | 未给出 | — | [待确认] 需全文 |
| 功率密度上限（W/mm²） | 未给出 | — | [待确认] 需全文 |
| die/封装工艺 | 未在摘要给出 | — | [待确认] |

### 还原难点

- 这是**分析型上限研究**（自顶向下估计 radix 天花板），论文给的是一族"约束→radix 损失"的斜率关系，不是单一配置点。进我们模型需要把它的瓶颈分成我们五族约束的对应项：内部带宽≈路由层性能包络（L1），外部带宽≈C4/SerDes 约束，功率密度≈热约束。
- 缺 baseline radix、I/O 带宽绝对值的三个关键数——它们决定"32×"从什么基数出发。

### 与我们的关系

- 最直接的对标：他们问"晶圆级交换机上限多大"，我们问"给定配置 feasible 吗、哪个约束先顶到"。**对照实验设计**：取他们描述的异构设计（heterogeneous subswitch）做参数族，用我们的 LP 重算 B*，看功率约束在多大 radix 上开始支配——预期能复现"面积不是瓶颈、功率密度先到"的结论，并补上他们没给的"精确交界点"。
- 论文叙事价值：他们用自顶向下、我们用自底向上耦合 LP，两条路线交叉验证。

### 来源

- IEEE Micro 2025 摘要（ieeexplore.ieee.org/document/10609578）
- IDEALS 条目（ideals.illinois.edu/items/136269）
- sciprofiles 摘要页

---

## 卡片 2：Switch-Less Dragonfly on Wafers ⭐（唯一一篇 dragonfly 参数完整可还原的卡）

- **架构名**：Switch-Less Dragonfly（SL-DF）——晶圆上直接实现 dragonfly，去掉高 radix 物理交换机
- **作者**：Yinxiao Feng, Kaisheng Ma（清华 IIIS）
- **出处**：SC 2024（Atlanta，2024-11-17~22），IEEE Xplore 10793167，DOI 10.1109/SC41406.2024.00102；arXiv:2407.10290。[可靠]

### 拓扑分层与参数（与 Kim et al. ISCA 2008 dragonfly 参数一一对应）

5 级物理层级：**chiplet → C-group → wafer → W-group → system**。chiplet = dragonfly 终端（terminal），C-group = dragonfly 交换机（router），W-group = dragonfly 路由器组。

| 符号 | 定义 | 论文建议/案例值 | 状态 |
|---|---|---|---|
| n | 每 chiplet 的互连接口（IO 端口）数 | 12 | [可靠] |
| m | C-group 内 2D mesh 的规模（m×m chiplets） | 4（4×4=16 chiplets/C-group） | [可靠] |
| k = n·m | 每 C-group 的外部（长距）接口数 | 48 | [可靠]（推导） |
| a | 每 wafer 的 C-group 数 | 4（64 chiplets/wafer） | [可靠] |
| b | 每 W-group 的 wafer 数 | 8（512 chiplets/W-group，组内全连接） | [可靠] |
| h | 每 C-group 连向其他 W-group 的全局端口数 | 544 端口/W-group（离 W-group 口） | [可靠] |
| g | W-group 总数（全连接） | 545 | [可靠] |
| N | 总 chiplet 数 = a·b·m²·g | **279,040** | [可靠] |
| 均衡条件 | n = 3m 且 ab = 2m² → h/t ≈ 1/2（全局:本地口比） | 满足 | [可靠] |

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| 全局吞吐 | 与 switch-based dragonfly 理论持平（global-local 比调平） | [可靠] |
| 本地（injection）吞吐 | ~2 flits/cycle/chip——**2×** switch-based dragonfly | [可靠] |
| C-group 内吞吐 | ~3 flits/cycle/chip | [可靠] |
| 交换机数量 | **0**（vs HPE Slingshot 同级系统 17,440 台交换机） | [可靠] |
| 死锁自由路由（最小+非最小） | 只需**额外 1 个 VC**（baseline 与改进两版算法，靠连接标号 + 优先级排序实现） | [可靠] |
| 可推广 | 同一无交换机法可用于 Slim Fly / PolarFly / HyperX；C-group 内 mesh 可换 HexaMesh 或加宽链路 | [可靠] |

### 配置参数表（物理层）

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| chiplet 尺寸 / 工艺 | 未在摘要给出 | — | [待确认] 需原文 |
| wafer 直径 | 300mm（隐含） | — | [待确认] |
| lane 速率（Gbps） | 未给出（以 flits/cycle 度量吞吐） | — | [待确认] 需原文 |
| 功耗 / 散热 | 未在摘要给出 | — | [待确认] 需原文 |

### 还原难点

- 拓扑参数 **n, m, a, b, h, g 全齐**，直接映射我们 dragonfly 模型的 a/p/h/g——这是最干净的一张卡。难点全在物理层：原文吞吐用 flits/cycle 度量，需要 lane 速率假设（如 112G 或 224G SerDes）和 chiplet 尺寸假设才能换算成 B*。
- 它的"C-group 内 2D mesh"与"组间全连接"是两层混合物理实现，我们模型需要把 dragonfly 的 group 内全连接映射到 wafer 级 mesh 物理结构（M 矩阵按物理位置取）。

### 与我们的关系

- **预期最紧约束**：W-group 全连接意味着组间长距链路很多，C4 + SerDes 布线约束很可能先到；chiplet 间 mesh 的 μbump 供给次之。他们的 h=544/W-group 是外部 I/O 密度的硬数字，可直接进 C4 约束验算。
- **对照实验设计**：用 (n=12, m=4, a=4, b=8, g=545) 还原，扫 B* 与 radix——预期我们模型会指出"组间全连接在 C4/pad 容量上不可行或极紧"（论文未讨论 pad 供给），这正是我们的增量贡献点。

### 来源

- arXiv:2407.10290（摘要 + ar5iv 全文片段）
- SC24 官方程序页（sc24.supercomputing.org/.../pap220.html）
- IEEE Xplore 10793167

---

## 卡片 3：Architectural Exploration for Waferscale Switching System（BFT on 2D mesh，之江实验室）

- **架构名**：晶圆级交换系统——物理 2D mesh + 逻辑 5 级 BFT（butterfly fat-tree）
- **作者**：Zhiquan Wan, Zhipeng Cao, Shunbin Li, Peijie Li, Qingwen Deng, Weihao Wang, Kun Zhang, Guandong Liu, Ruyun Zhang, Qinrang Liu（之江实验室）
- **出处**：IEEE TVLSI Vol. 33, Issue 2, pp. 512-524（2025-02），在线 2024-09；DOI 10.1109/TVLSI.2024.3455332。[可靠]

### 配置参数表

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| 每 wafer die 数 | **392** 个交换机 die（300mm wafer） | [可靠] | |
| 可用布局面积 | 282mm 直径（边缘留 9mm 给 yield/测试） | [可靠] | |
| die 间距 | 100µm（die-to-wafer 键合） | [可靠] | |
| die 工艺 / 尺寸 | 自研 40nm，**12×12 mm** | [可靠] | |
| A die（外部） | 16×10G 长距 SerDes（外）+ 16×10G 短距并口（内）= **320 Gb/s** | [可靠] | |
| B die（内部） | 4 边 × 16×10G 短距并口 = **640 Gb/s** | [可靠] | |
| 端口模式 | 每端口可配 packet-switching / circuit-switching / 关闭 | [可靠] | |
| 物理拓扑 | 2D mesh（仅邻接 die 互连） | [可靠] | |
| 逻辑拓扑 | 5 级 BFT（端口级软件配置实现） | [可靠] | |
| 系统容量 | **896 端口 × 10 Gbps = 8.96 Tb/s** | [可靠] | |
| 集群数 | 28 clusters | [中等] 来自旧 survey，原文摘要未复现 | [待确认] |
| 路由算法 | BFS 流量均衡、确定性、死锁自由（配 VC） | [可靠] | |

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| 跳数 | vs 2D mesh 物理拓扑 **-55.6%** | [可靠] |
| 传输延迟 | **-41.4%** | [可靠] |
| 吞吐 | **+24.2%** | [可靠] |
| 封装对比 | 晶圆级 vs 单 chip 封装：短距 I/O 带来功耗与延迟优势（数值分析） | [可靠] |
| yield | KGD 选择；被动 wafer 互连 yield ~99%；flip-die 键合 yield 实测 100% | [可靠] |

### 还原难点

- die 级参数**最全的一张卡**（尺寸、速率、端口数、yield 都有），但缺：功耗/散热数字（40nm 的功耗预算未给出）、bump 密度、热预算。40nm 工艺意味着动态功耗系数需要工艺换算假设。
- 逻辑 BFT 是"端口级重配置"实现——我们模型目前把拓扑当静态图，需要把"物理 mesh + 逻辑 BFT 的映射"当成 M 矩阵的两种取法来处理。

### 与我们的关系

- **预期最紧约束**：B die 640 Gb/s 并口从四边进出 → μbump 供给约束最可能先到；8.96 Tb/s 总容量在 392 die 上的分布决定热墙位置。12×12mm/40nm 是很好的"低工艺"对照点（我们的默认 12×12mm 直接可用）。
- **对照实验设计**：还原 392 dies + 896×10G，分别按 2D mesh 和 BFT 两种逻辑拓扑跑，看我们模型给出的 B* 差是否与论文的 24.2% 吞吐差同向；若同向，等于用第三方系统验证了我们的性能包络约束。

### 来源

- IEEE TVLSI 2024/2025（ieeexplore.ieee.org/document/10682064；DOI 10.1109/TVLSI.2024.3455332）

---

## 卡片 4：TickTock——PD Constraint-aware Physical/Logical Topology Co-Design for NoW ⭐（最接近的 DSE 同行）

- **架构名**：TickTock——物理拓扑 ↔ 逻辑拓扑 ↔ 并行策略迭代 co-design；hybrid "mesh-switch" 拓扑
- **作者**：Qize Yang, Taiquan Wei, Sihan Guan, Chengran Li, Haoran Shang, Jinyi Deng, Huizheng Wang, Chao Li, Lei Wang, Yan Zhang, Shouyi Yin, Yang Hu（清华大学）
- **出处**：ISCA 2025（Tokyo，2025-06-21~25），pp. 49-64；DOI 10.1145/3695053.3731045。[可靠]

### 配置参数表 / 物理约束

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| 最大 D2D 链路长度 | **50 mm**（超出则链路劣化） | [可靠] 评审摘要 §2.2 | |
| 超出 50mm 的代价 | BER 108×、延迟 210ns | [中等] 旧 survey 数字，本次未独立复现 | [待确认] |
| interposer 路由层数 | **< 3 层** | [可靠] 评审摘要 | |
| 可用 wafer 面积 | 50,000 mm² | [中等] 旧 survey，评审摘要未复现 | [待确认] |
| 未来目标面积 | 300,000 mm² 玻璃面板 | [可靠] 评审摘要 §5.6 | |
| 拓扑结论 | pure mesh 通信受限；pure fat-tree（FRED）计算受限；hybrid mesh-switch 最优；DSE 得 2×2 mesh group 最优 | [可靠] | |

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| LLM 训练吞吐 | **2.39×** | [可靠] 评审摘要 |
| 对比基线 | **Tesla Dojo**（⚠️ 修正旧 survey 的"vs SOTA mesh-based NoW"表述） | [可靠] 评审摘要 |
| 覆盖范围 | 物理拓扑 + 逻辑拓扑 + 集合通信算法 + 并行/sharding 策略全栈 | [可靠] |
| 已知批评 | 无故障容忍/yield 考虑；集中式 switch 单点故障；面向 LLM 训练局限 | [可靠] 评审 |

### 还原难点

- 论文给的是"约束发现 + DSE 方法"，不是单一落点配置；die 数、lane 速率、功耗预算等绝对参数未在公开摘要出现，需全文。
- 它的物理约束集（面积、<3 路由层、50mm D2D）与我们五族约束高度重叠，但**没有 μbump 供给和 C4 约束**——这是我们可以补的洞。

### 与我们的关系

- 最接近的 DSE 同行：同为"物理/逻辑联合可行性判断"，但他们 compute-centric（LLM 训练），我们 communication-centric（交换机）。**对照实验设计**：把 50mm D2D 与 <3 路由层作为我们布线约束的参数实例，跑他们 2×2 mesh-switch 配置，比较我们给 B* 时哪个约束先顶到——预期我们的 μbump/C4 约束在他们认为可行的点上给出新收紧，正好是"TickTock 缺的那一环"。
- 论文叙事价值：他们是 ISCA 2025 清华三篇晶圆级论文之一（另两篇含 02 文件卡 11），证明"PD 约束感知"是当下热点，我们的五族联立是更全面的框架。

### 来源

- ACM DOI 10.1145/3695053.3731045（ISCA 2025 Proceedings）
- archprisms 评审摘要（archprisms.talkyard.net）
- researchr 书目页（YangWGLSDWLWZYH25）
