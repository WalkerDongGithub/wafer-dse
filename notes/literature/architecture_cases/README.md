# 既有架构参数还原卡片（research agenda 2.3）

> 用途：把既有晶圆级 / chiplet 交换机与互连架构论文还原成"参数级配置卡片"，直接喂我们 LP 模型做对照实验——还原论文架构 → 跑我们的五族约束 → 看论文结论能不能被我们的模型复现/解释。
> 调研时间：2026-08-15。在 notes/LITERATURE_SURVEY.md B 节概览基础上加深，不重复劳动。
> 质量标注：[可靠] = 原文/官方发布；[中等] = 综述/幻灯/新闻/评审摘要；[待确认] = 需下载原文核对。

## 模型输入对照（每张卡片都要回答的问题）

我们的模型（MATH_MODEL_COMPLETE_V4.md）需要：

| 模型输入 | 对应卡片字段 |
|---|---|
| 拓扑族 + 参数 | dragonfly (a,p,h,g)；mesh (维度, 边长)；torus；fullmesh；kary-ncube |
| die 数 / 尺寸 | 每 wafer die 数、die 尺寸 mm² |
| lane 速率 | Gbps/lane |
| pJ/bit（动态功耗） | 由 power/lane ÷ rate 折算 |
| bump 密度 | μbump pitch / lanes-per-mm / bump 供给 |
| 功耗预算 | 每 die W、总 W |
| 散热预算 | 冷却方式、每 tile/wafer 散热上限、T_max |

五族约束：性能包络（路由层 L）、μbump（die↔interposer）、布线（interposer 层容量）、C4（interposer↔substrate）、热（G·T = P + b）。

## 卡片索引与汇总表

| # | 架构 | 出处 | 拓扑 | 规模 | 文件 |
|---|---|---|---|---|---|
| 1 | Waferscale Network Switches | ISCA 2024 / IEEE Micro 2025 | 单 switch（die 级集成） | radix 32× | 01 |
| 2 | Switch-Less Dragonfly on Wafers | SC 2024 | dragonfly（chiplet=终端） | N=279,040 chiplets | 01 |
| 3 | Waferscale Switching System（BFT on mesh） | IEEE TVLSI 2024 | 2D mesh 物理 + 5 级 BFT 逻辑 | 392 dies / 896×10G | 01 |
| 4 | TickTock（NoW 物理/逻辑拓扑 co-design） | ISCA 2025 | mesh-switch 混合 | 50,000 mm² 级 | 01 |
| 5 | Tesla Dojo | Hot Chips 34 / 2024 | 2D mesh + Z-plane | 25×D1 / tile | 02 |
| 6 | Cerebras WSE-2 / WSE-3 | IEEE Micro / Hot Chips | 2D mesh（toroidal） | 46,225 mm²，~900K cores | 02 |
| 7 | TSMC InFO-SoW / SoW-X | TSMC 技术论文 / ECTC 2025 | 平台（RDL / LSI / SerDes） | 25+ die；16 ASIC+80 HBM4 | 02 |
| 8 | Si-IF（UCLA 硅互连织物） | UCLA CHIPS 2024 | 平台（dielet TCB 到硅 wafer） | ≤10µm pitch，≥8 Tbps/mm | 03 |
| 9 | Simba | MICRO 2019（注意不是 ISCA） | 36 chiplet 2D mesh NoP | 128 TOPS | 03 |
| 10 | WaferLLM | OSDI 2025 | Cerebras WSE 上的软件层 | 百万核并行 | 03 |
| 11 | Cramming a Data Center into One Cabinet | ISCA 2025 | 晶圆级 chip（计算+硬件 co-explore） | 单 wafer | 02 |
| 12 | 多 die 交换机（Multi-Die Optimization） | Electronics 2024 | chiplet 交换机内部互连 | die 间连接 -25% | 03 |

## 用法建议

1. **对照实验顺序**：2（dragonfly 参数最全）→ 3（die 级参数最全）→ 4（约束最接近我们）→ 1（radix 上限对标）。
2. 每张卡片的"还原难点"列了缺的参数；补齐顺序建议见"缺口与下一步"。
3. 所有 [待确认] 数字在进论文引用前必须核对原文页码。

---

## 缺口与下一步

1. **最大缺口：Chen ISCA 2024 的完整参数表**（内部/外部带宽 Tbps、功率密度 W/mm²、baseline radix 值）只有摘要级信息；它是我们"性能包络 vs 面积"叙事的直接对标，应尽快下载 IEEE Micro 45(4):37-43 全文。
2. **Feng & Ma 的物理层参数**（chiplet 尺寸、工艺、lane 速率、功耗、散热）摘要里没有——需下 arXiv:2407.10290 原文；这是唯一一篇"dragonfly 参数完整进我们 dragonfly 模型"的卡。
3. **TickTock 的 50,000 mm² / BER 108× / 210ns** 三数字只来自旧 survey，本次核实到 50mm D2D 与 <3 路由层，其余需核对 ISCA 2025 原文（DOI 10.1145/3695053.3731045）。
4. **Dojo 的 112 Gbps/lane 是推算值**（2 TB/s 每边 ÷ 144 lane/边），Hot Chips 原文只给每边 2 TB/s；引用时写"每边 2 TB/s（≈144×112G）"或核对 Hot Chips 34 幻灯。
5. **SoW-X 的 LSI 6.5mm/400G 与 SerDes 50mm/100G** 来自 2025 技术研讨会幻灯（[中等]）；ECTC 2025 测试载具已升级到 224G XSR SerDes + UCIe Gen6，引用时注意版本差异。
6. **Stanford "PRIZE" chiplet 交换机**检索未果（可能是名字记错或未公开发表），暂不建档；chiplet 交换机另找到 Luo et al. (Electronics 2024) 作为唯一近期公开条目，质量中等。
7. **Si-IF 原始论文**（Jangam/Iyer 系列，IEEE T-CPMT/EDL 2018-2021）未下载原文，现卡片基于 UCLA CHIPS 官方页与 2024 IEEE 论文摘要（[中等]），引用前补原文。
8. **Cerebras WSE-2/3 的 per-link 17.6-32 GB/s 与 per-hop ~1ns** 仍只有旧 survey 来源（[待确认]），WSE-3 fabric 数字以 Hot Chips 2024 官方 PDF 为准（214 Pbit/s）。
9. **下一步动作**：按 DOWNLOAD_LIST.md 的优先级把本目录标 [待确认] 的论文原文补齐；补完后每个数字回填出处页码，再把卡 2/3/4 的参数直接落成 exp 配置文件（exp/run_ledger.py、run_matrix.py 的案例族）。
