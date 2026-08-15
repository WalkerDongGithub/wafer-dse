# C 组：平台与标准数据卡

> 用途：封装平台/互联标准的工艺边界参数——直接对应我们 `tsmc_profiles.py`、bump.py、C4Model 与布线容量 C 的参数来源。
> 质量标注：[可靠] 官方规范/datasheet；[中等] 行业综述/会议；[待确认] 需核对。
> 已有概览见 `notes/LITERATURE_SURVEY.md` A3（InFO-SoW）与 `notes/literature/RENT_RULE_AND_IO_DENSITY.md`（bump pitch 阶梯）——本文件只加深、不重复。

---

## C1. TSMC CoWoS-S（全硅 interposer）[中等] ⭐

| 字段 | 值 | 出处 |
|------|----|----|
| 结构 | monolithic 硅 interposer（最高布线密度） | [中等] TSMC 3DFabric 页 |
| reticle 基准 | 单掩膜 ~26×33mm ≈ 830–858mm² | [中等] 行业综述 |
| 尺寸代际 | 1× (~775mm²) → 2× (~1150mm²，4 HBM) → 3× (~2500mm²，双 GPU+8 HBM) | [中等] 开源证券 2.5D 报告 |
| **上限** | **3.3× reticle ≈ 2700–2831mm²**（再大 stitching 成本/良率不可行） | [中等] |
| 互联栈 | die μbump → interposer → C4 → substrate | [可靠] 封装常识 |

**换算进我们框架**：CoWoS-S 的 3.3× ≈ 2700mm² 是"单一硅 interposer 能给出的 N_total 与布线容量上限"——我们 interposer 网格的 C（边/点容量）应按此标定；超出即需 CoWoS-L 的桥接方案或 InFO-SoW 的 RDL 方案。这也是"为什么 51.2T 单 die 后必须走向 wafer 级/多 die"的供给侧理由。

---

## C2. TSMC CoWoS-L（LSI 桥 + RDL）[中等] ⭐ 突破 reticle 的路线

| 字段 | 值 | 出处 |
|------|----|----|
| 结构 | RDL interposer + 嵌入式局部硅互连（LSI 桥），只在需要高密度 D2D 处放硅 | [中等] |
| 代际 | 3.5× reticle（**2024 量产，NVIDIA Blackwell 用**）→ 5.5× ≈ **4719mm²**（~100×100mm substrate，12 HBM，Rubin 用，验证中）→ **9.5× ≈ 7885mm²**（2027 规划，120×150mm substrate，12+ HBM4E） | [中等] 开源证券 2026 报告/行业综述 |
| 与 CoWoS-S 关系 | >3.3× 后 TSMC 强制转 L 或 R | [中等] |

**换算进我们框架**：CoWoS-L 3.5×→5.5×→9.5× 的节奏就是"面积约束边界逐年外推"的工业路线图——我们的 wafer 级可行域比它大一个量级（300mm wafer ≈ 7 万 mm²），说明 wafer 级集成面对的不是面积墙而是 I/O/热墙（与 UIUC ISCA 2024 结论一致）；L 桥的"只在高密度处用硅"正是我们布线约束中路径候选集分层的物理根据。

---

## C3. TSMC CoWoS-R（纯 RDL interposer）[中等]

| 字段 | 值 | 出处 |
|------|----|----|
| 结构 | 多层聚合物 RDL，无硅 interposer/桥 | [中等] |
| 适用 | >3.3× reticle、对布线密度要求低的场景，更便宜、机械顺应性好 | [中等] |
| 路线图 | 同 L：至 9×（2027） | [中等] |

**换算进我们框架**：CoWoS-R 是 CoWoS-L 的低密度廉价替代——对应我们布线容量 C 的"低密度档位"；RDL L/S ~5µm 与 RENT_RULE 笔记 §4 的 RDL 密度数据交叉一致。

---

## C4. TSMC InFO-SoW / SoW-X（晶圆级平台）[中等]

| 字段 | 值 | 出处 |
|------|----|----|
| InFO-SoW | 300mm 晶圆上集成 25+ die，RDL（2µm L/S 量级），molding compound 上直接布线（无硅 interposer） | [中等] LITERATURE_SURVEY A3 |
| SoW-X LSI | 短距（≤6.5mm）极密并口，400Gbps/lane | [中等] TSMC 公开资料 |
| SoW-X SerDes | 中距（≤50mm）串行化，100Gbps/lane | [中等] |
| 工业落地 | Tesla Dojo Training Tile：25 × D1（7nm，645mm²/die），576×112G SerDes/die，tile 功耗 ~15kW（≈600W/die），on-tile bisection 10TB/s、off-tile 36TB/s | [中等] Hot Chips 34 (2022) + Hot Chips 2024（见 LITERATURE_SURVEY A1） |

**换算进我们框架**：Dojo 是唯一量产晶圆级系统，直接校验我们 InFO-SoW profile：576 lane × 112G ≈ 64.5T/die 的 SerDes 供给、600W/die 的散热（15kW/25 die）——在框架里对应 S_bw 与 P_peak 的取值；其 2D mesh + Z-plane 拓扑即我们 EnvelopeModel 的候选拓扑之一。SoW-X 的 LSI/SerDes 两档互连 = tsmc_profiles.py 三个 profile 的直接来源。

---

## C5. UCIe 1.0 / 1.1（die-to-die 标准）[中等] ⭐

| 字段 | 标准封装（Standard） | 先进封装（Advanced） | 出处 |
|------|---------------------|---------------------|------|
| lane 速率 | 4–32 GT/s（1.1 增 24GT/s） | 32 GT/s | [中等] IBM 幻灯引规范 KPI |
| bump pitch | 100–130µm（标称 130µm） | 25–55µm（标称 45µm） | [中等] 同上 |
| shoreline 带宽密度 | 28–224 GB/s/mm | 165–1317 GB/s/mm | [中等] 同上 |
| 功耗目标 | 0.5 pJ/bit | 0.25 pJ/bit | [中等] 同上 |
| 模块 | x16/x32（shoreline 0.6mm/1.2mm 量级） | x64（面积 <0.7mm²） | [中等] 同上 |
| 发布 | 1.0: 2022-03；1.1: 2023-08 | 同左 | [中等] UCIe 联盟 |

**换算进我们框架**：0.25–0.5 pJ/bit 正是"先进封装场景 B*≈22k"的 S_dyn 系数来源；shoreline 密度（28–1317 GB/s/mm）是布线约束容量 C 的标定依据——lane 沿 die 边界的 shoreline 占用 = 我们 edge 容量 R_edge·x ≤ C_edge 的物理含义。

---

## C6. UCIe 2.0 / 3.0（3D 与 64GT/s）[中等]

| 字段 | 值 | 出处 |
|------|----|----|
| UCIe 2.0（2024-08-06 发布） | 新增 **UCIe-3D**：混合键合，bump pitch 10–25µm（直至 <1µm 展望）；新增 DFx/可管理性架构（UDA）；向后兼容 1.0/1.1 | [中等] UCIe 联盟 + TechPowerUp 报道 |
| UCIe 3.0 | lane 速率提至 **64 GT/s**（PHY IP datasheet 佐证：S 包 64GT/s @130µm pitch，shoreline 448 GB/s/mm；A 包 64GT/s @45µm，shoreline 2632 GB/s/mm，0.2–0.4 pJ/bit） | [中等] InPsy PHY IP datasheet |
| 功耗下限 | 3D 混合键合 ~0.2 pJ/bit（对比 2.5D μbump ~3.5 pJ/bit 的说法 [待确认]） | [中等] |

**换算进我们框架**：UCIe-3D 的 10–25µm 混合键合 = 我们 bump.py 的 UBUMP_25UM 档（1600/mm²）的规范出处；64GT/s 时代 S_bw 上行扩展，lane 数需求减半——3D 与 lane 速率是缓解 bump 压力的两个自由度，框架里由 S_bw 与 N_total 参数化。

---

## C7. Dojo / Cerebras 补充锚点（概览已有，此处只记换算）[中等]

| 系统 | 关键参数 | 换算 |
|------|----------|------|
| Tesla Dojo Tile | 25×645mm² die、576×112G/die、15kW/tile、bisection 10TB/s | 600W/die → 框架热预算上界；576 lane/die → S_bw 供给锚点；见 C4 |
| Cerebras WSE-3 | 单晶圆 ~46,225mm²、~900K PE、2D toroidal mesh | 单 die 面积远超市面上任何封装——"wafer 即封装"的极端供给侧案例，bump 概念被晶圆级布线与 RDL 替代；其 ~1ns/hop 与 50mm 最大 D2D 距离（TickTock ISCA 2025）对应我们链路 reach 约束 |

---

## 来源清单（C 组）

| 标题 | 来源 | 年份 | URL |
|------|------|------|-----|
| TSMC CoWoS 官方技术页 | TSMC 3DFabric [可靠] | 2025 | https://3dfabric.tsmc.com/schinese/dedicatedFoundry/technology/cowos.htm |
| CoWoS Packaging Guide（S/R/L 结构与 HBM 集成） | Digi-Electronics [中等] | 2025 | https://www.digi-electronics.com/en/blogs/cowos-packaging-guide-cowos-s-cowos-r-cowos-l-hbm-integration-and-ai-gpu-design/715.html |
| 2026 年 2.5D 封装技术：CoWoS 硅中介层从 1× 向 9.5× 演进 | 开源证券（经 sgpjbg 转载）[中等] | 2026 | https://www.sgpjbg.com/labelsyh/2.5dfengzhuangjishu/1/6544924.html |
| TSMC unveils plans for giant AI chips（CoWoS 路线） | TechSpot [中等] | 2025 | https://www.techspot.com/news/107695-tsmc-unveils-plans-giant-ai-chips-meet-surging.html |
| UCIe Consortium Specifications 页 | UCIe 联盟 [可靠] | 2024 | https://www.uciexpress.org/specifications |
| UCIe Consortium Releases UCIe 2.0 Specification | TechPowerUp [中等] | 2024 | https://www.techpowerup.com/325309/ucie-consortium-releases-ucie-2-0-specification |
| Design and technology spaces for heterogeneous chiplet integration（UCIe 1.0 时代 KPI 表） | IBM GI-WS-2023 幻灯 [中等] | 2023 | http://designthesolution.org/wp-content/uploads/2022/09/Design-and-technology-spaces-for-heterogeneous-chiplet-integration.pdf |
| UCIe-S/UCIe-A 64GT/s PHY IP datasheet | InPsy [中等] | 2025 | https://inpsytech.ai/en/product/4/11/26 |
| Tesla Dojo（Hot Chips 34） | Hot Chips 会议 [中等] | 2022 | （项目内已有，见 notes/LITERATURE_SURVEY.md A1） |
| Waferscale Network Switches | UIUC, ISCA 2024 [中等] | 2024 | https://www.ideals.illinois.edu/items/136269 |
| TickTock: PD Constraint-aware Co-Design for NoW | ISCA 2025 [中等] | 2025 | （项目内已有，见 LITERATURE_SURVEY B4） |
| 项目内部实现：tsmc_profiles.py / bump.py / C4Model | 本仓库 | 2026 | /home/walker/wafer-dse/src/physical/interconnect/tsmc_profiles.py |
