# 02 — 已知晶圆级系统与封装平台卡片（3 张 + 1 张相关）

> 对应 LITERATURE_SURVEY.md A1-A3，加深到参数级。这些不是交换机，但提供 wafer 物理边界（bump、功率密度、散热）的实测数据点。

---

## 卡片 5：Tesla Dojo（2D mesh + Z-plane on InFO-SoW）

- **架构名**：Dojo——AI 训练超算；Training Tile = 25×D1 晶圆级集成
- **作者**：Emil Talpes 等（Tesla）
- **出处**：Hot Chips 34（2022）；Hot Chips 2024 更新。[可靠]

### 配置参数表

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| D1 die 尺寸 | **645 mm²**，TSMC 7nm，~50B 晶体管 | [可靠] | |
| D1 核心 | 354 可用训练核（5×5 cluster 排布），1.25 MB SRAM/核，440 MB 总 SRAM | [可靠] | |
| D1 算力 | 362 TFLOPS BF16/CFP8；22.6 TFLOPS FP32；TDP ≤ 400 W | [可靠] | |
| D1 SerDes | **576 双向通道/die**（每边 144 × 112 Gbps → 每边 2 TB/s） | [可靠] 576 与 2 TB/s/边；112G 为推算 | [待确认] 112G 细节 |
| 封装 | InFO_SoW：300mm 重建 wafer + 铜托盘；无基板，RDL fan-out | [可靠] | |
| Training Tile | 25×D1（5×5）+ 40 个 I/O die | [可靠] | |
| Tile 功耗/散热 | **15 kW**（液冷；D1 约占 10 kW；总电流 ~18,000 A；散热能力从 7 kW 提到 15 kW） | [可靠] | |
| Tile 带宽 | on-tile bisection ~10 TB/s；off-tile 36 TB/s；tile 间 9 TB/s；每边 4.5 TB/s | [可靠] | |
| 拓扑 | 2D mesh + **Z-plane**（跨 mesh 快速通道，30 跳 → 4 跳） | [可靠] | |
| 路由/容错 | flat addressing、compiler-driven、可绕坏核 | [可靠] | |
| 系统规模 | 2 box = 1 cabinet（4,248 核）；10 cabinet = ExaPOD（3,000 D1，120 tile，1.1 EFLOPS BF16/CFP8） | [可靠] | |

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| 单 tile 算力 | ~9 PFLOPS BF16/CFP8（约等于 6 台 8-GPU A100 服务器） | [可靠] |
| Z-plane 收益 | 跨 mesh 通信 30 跳 → 4 跳 | [可靠] |

### 还原难点

- die 级参数全，但**缺 lane 速率绝对值**（2 TB/s/边 ÷ 144 lane/边 = 112 Gbps 是推算）；**缺 bump 密度/pitch**（InFO 平台按 RDL 处理，无公开 μbump 数）；功耗有 TDP（400W/die）但热模型需要冷却侧参数（液冷 15kW/tile 可作为散热预算输入）。
- 拓扑是 mesh + 少量长距 Z-plane 链路——我们模型可表达为"mesh 基础 + 稀疏长距边"，Z-plane 的带宽分配需假设。

### 与我们的关系

- **预期最紧约束**：15 kW/tile 里 10 kW 是计算（D1），SerDes 动态功耗只是小头——若用我们的模型还原 tile，热约束先到，且结论会是"计算功率密度决定 tile 面积"，与 Dojo 实际（计算墙）一致；做交换机版对照时把计算功耗换成交换功耗即可。
- **对照实验设计**：还原 5×5 mesh + 4.5 TB/s/边，跑 μbump 约束看 576 lane/die 在 45µm pitch 下占用多少供给——这是"bump 供给 vs Dojo 实际"的实测锚点。

### 来源

- Hot Chips 34 报道（notateslaapp.com/news/935，Talpes 演讲要点）
- 行业深度拆解（iczoom.com，D1 规格交叉确认）

---

## 卡片 6：Cerebras WSE-2 / WSE-3（单晶圆计算芯片，mesh fabric 实测）

- **架构名**：Wafer-Scale Engine 2 / 3
- **作者**：Cerebras（Sean Lie 等）
- **出处**：Hot Chips 2021-2024；IEEE Micro；官方发布。[可靠]（发布数字）

### 配置参数表

| 参数 | WSE-2 | WSE-3 | 出处 | 状态 |
|---|---|---|---|---|
| 硅面积 | 46,225 mm² | 46,225 mm²（同 wafer 尺寸） | [可靠] | |
| 工艺 | TSMC 7nm | TSMC 5nm | [可靠] | |
| 晶体管 | 2.6T | 4.0T | [可靠] | |
| 核心数 | ~850,000 | ~900,000 | [可靠] | |
| 片上 SRAM | 40 GB | 44 GB（48 kB/核 + 512B 本地） | [可靠] | |
| 存储带宽 | 20 PB/s | 21 PB/s | [可靠] | |
| fabric 带宽 | 220 Pbit/s | 214 Pbit/s | [可靠]（Argonne/Hot Chips 幻灯） | |
| 峰值算力 | 62.5 FP16 PFLOPS（官网口径） | 125 FP16 PFLOPS | [可靠] | |
| 拓扑 | 2D mesh（逻辑 2D 阵列，跨 reticle 边界满速；HW 冗余重连绕坏点） | 同左 | [可靠] | |
| per-link 带宽 | 17.6–32 GB/s；per-hop ~1ns | — | [中等] 旧 survey | [待确认] |
| vs H100 | 57× 面积 / 52× 核 / 880× SRAM / ~7,000× 存储带宽 | 同左 | [可靠] | |

### 论文声称结果

| 结果 | 值 | 出处 |
|---|---|---|
| 缺陷容忍 | HW 重映射绕坏核，软件始终见均匀 2D mesh | [可靠] |
| 模型规模 | 44 GB SRAM 原生支撑 ~70B 参数模型 | [中等] 分析 |

### 还原难点

- 单晶圆单 die，**没有 die 间互连**——μbump/C4 约束对它不适用（等价于我们的"die 内零代价"假设）；它的价值在 mesh fabric 的实测带宽/跳延迟数据点。
- per-link 17.6-32 GB/s 与 per-hop ~1ns 未在官方发布中复现，[待确认]。

### 与我们的关系

- **预期最紧约束**：WSE-3 的 214 Pbit/s fabric 若按 2D mesh 边带宽折算，单边带宽高达 ~50 Tb/s 量级——远超我们交换机场景的 lane 供给假设；它证明的是"on-die fabric 可以做到多快"，与我们的 on-die 零代价假设一致，反衬 die 间互连才是瓶颈。可作为论文里"die 内 fabric 供给充足"的实测引用。
- **对照实验设计**：WSE-3 尺寸 × 2D torus 参数进我们的几何约束，算纯面积/热上限，验证我们的 wafer 面积与功率密度常数与 Cerebras 实测（21 PB/s、~100 kW 级整机液冷）同一量级。

### 来源

- Argonne LCF Accelerators4HPC 幻灯（argonne-lcf.github.io/.../2_Cerebras.pdf）
- Hot Chips 2024 官方 PDF（hc2024.hotchips.org/assets/.../72_HC2024.Cerebras.Sean.v03.final.pdf）
- WSE-2 发布报道（wccftech / extremetech，交叉核对）

---

## 卡片 7：TSMC InFO-SoW / SoW-X 平台（我们 tsmc_profiles.py 的出处）

- **架构名**：InFO-SoW（System-on-Wafer，现称 SoW-P）与 SoW-X（eXtended）
- **作者**：TSMC（3DFabric）
- **出处**：TSMC 技术研讨会（2024/2025）；IEEE OJSSCS 2024（Li et al.）；ECTC 2025。[中等]（厂商口径为主）

### 配置参数表

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| InFO-SoW | 300mm wafer 上集成 25+ die；RDL fan-out（~2µm L/S）；无硅中介层、无基板 | [中等] | |
| InFO-SoW 单级互连 | die → μbump → RDL → μbump → die（我们代码 lane_rate 200G、0.15 pJ/bit、reach 50mm） | [中等] 与代码一致 | |
| SoW-X 架构 | Chip-Last：wafer 级 RDL + **LSI（local silicon interconnect）** + IVR/PMIC/eDTC；最多 **40× reticle 面积**、200+ chiplet；2027 量产 | [中等] 2025 研讨会 | |
| LSI 短距 | **6.5mm reach、400 Gbps/lane**（我们代码 0.10 pJ/bit） | [中等] 研讨会幻灯 | [待确认] 版本细节 |
| SerDes 中距 | **50mm reach、100 Gbps/lane**（我们代码 0.25 pJ/bit） | [中等] 研讨会幻灯 | [待确认] |
| ECTC 2025 测试载具 | 4×4 ASIC（16 个全 reticle ASIC）+ 5×16 HBM4（80 颗）+ 16 IO die | [可靠] | |
| 载具互连 | **2,800 × 224G XSR SerDes 通道；总片间带宽 260 TB/s；外部 80 TB/s** | [可靠] ECTC 2025 | |
| LSI 通道（载具） | ASIC↔ASIC 5 TB/s（XSR 224G）；ASIC↔ASIC/内存 10 TB/s（LSI UCIe Gen6） | [可靠] | |
| 载具声称收益 | +46% 性能、-17% 功耗、1.76× 能效（vs 同规模分布式集群） | [可靠] | |

### 还原难点

- 厂商口径与论文口径有代差：研讨会幻灯的 LSI 400G/6.5mm、SerDes 100G/50mm（我们代码用的）已被 ECTC 2025 的 224G XSR + UCIe Gen6 升级。引用时注明版本。
- 260 TB/s 片间带宽的分摊方式（多少走 LSI、多少走 SerDes、HBM4 接口占多少）未公开，进模型需要假设。
- 无公开功耗/散热预算数字（只说 IVR/eDTC 优化供电）。

### 与我们的关系

- 这是我们**互连参数的直接出处**（tsmc_profiles.py 三个 profile：InFO-SoW / SoW-X-LSI / SoW-X-SerDes 全来自这张卡）。LSI 400G/lane 与 SerDes 100G/lane 的"距离-速率-能效"三档是我们"距离决定选型"叙事的物理依据。
- **对照实验设计**：用 SoW-X 载具拓扑（16 ASIC + 80 HBM4）做 2.5D 对照——把 260 TB/s 需求落到 μbump/布线约束，看 TSMC 声称的可行性在我们模型里是不是真的 feasible，以及哪个约束余量最小。

### 来源

- ECTC 2025 测试载具报道（腾讯云开发者社区转载 + 百度百科 SoW-X 条目，交叉核对）
- TSMC 2025 技术研讨会公开报道
- IEEE OJSSCS 2024（Li et al.，我们代码已引用）

---

## 卡片 11：Cramming a Data Center into One Cabinet（清华 ISCA 2025 三件套之一）

- **架构名**：单柜数据中心——晶圆级芯片的计算+硬件架构 co-exploration
- **作者**：Xingmao Yu, Dingcheng Jiang, Jinyi Deng, Jingyao Liu, Chao Li, Shouyi Yin, Yang Hu（清华）
- **出处**：ISCA 2025，pp. 631-645。[中等]（只有书目与新闻级信息，无公开摘要细节）

### 已知信息

| 参数 | 值 | 出处 | 状态 |
|---|---|---|---|
| 路线 | "One Wafer One Chip"：整 wafer 高密度硅互连基板 + 数十计算 chiplet 集成 | [中等] | |
| 验证 | 与上海 AI Lab 合作建成国内首个 12 英寸晶圆级芯片验证原型（可重构 AI chiplet） | [中等] | |
| 定位 | 与 TickTock（卡 4）构成"计算架构—集成架构—映射"三件套 | [中等] | |

### 与我们的关系

- 清华团队把"计算架构 + 集成架构"分开成两篇 co-explore，正是我们"五族约束联立"想合并的东西；引用其作为"行业在做 wafer-scale chiplet 集成"的最新佐证。细节不足，暂不做参数还原。

### 来源

- dblp（Yang Hu 0001 条目）；researchr ISCA 2025 目录；行业报道（drcnet 转载）
