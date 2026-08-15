# Wafer-Scale / 晶圆级芯片 @ 体系结构顶会 (2021–2026)

> 覆盖 ISCA / HPCA / ASPLOS / DAC / IEEE Micro，共 **17 篇**。

---

## ISCA (International Symposium on Computer Architecture)

### ISCA 2026（录用率 ~19%）

| # | 论文 | 团队 |
|---|------|------|
| 1 | **ConBin: A Performance-Convergence Framework for Wafer-Scale Chip Binning** | 中科院计算所 SKLP（许慧卿 / 王颖 / 韩银和） |
| 2 | **Unlocking Pipeline Parallelism for Bootstrapping: A Pipelined Multi-Chiplet TFHE Accelerator** | 中科院计算所 SKLP（杜一博 / 王颖 / 韩银和） |
| 3 | **AutoFHE: An Automatic Hardware Generation Framework for Domain-Specific FHE Accelerators** | 中科院计算所 SKLP（杜一博 / 王颖 / 韩银和） |

### ISCA 2025（东京）

| # | 论文 | 团队 |
|---|------|------|
| 4 | **PD Constraint-aware Physical/Logical Topology Co-Design for Network on Wafer** | 清华大学（杨启泽 / 胡杨 / 尹首一） |
| 5 | **Cramming a Data Center into One Cabinet: A Co-Exploration of Computing and Hardware Architecture of Waferscale Chip** | 清华大学（余幸懋 / 尹首一 / 胡杨） |
| 6 | **WSC-LLM: Efficient LLM Service and Architecture Co-Exploration for Wafer-Scale Chips** | 清华大学（徐铮 / 胡杨 / 尹首一） |
| 7 | **FRED: A Wafer-Scale Fabric for 3D Parallel DNN Training** | Georgia Tech / UIUC (Rashidi, Won, Srinivasan, Gupta, Krishna) |

### ISCA 2024（布宜诺斯艾利斯）

| # | 论文 | 团队 |
|---|------|------|
| 8 | **Waferscale Network Switches** | UIUC (Shuangliang Chen, Saptadeep Pal, Rakesh Kumar) |

---

## HPCA (International Symposium on High-Performance Computer Architecture)

### HPCA 2025（→ HPCA 2026 会议）

| # | 论文 | 团队 |
|---|------|------|
| 9 | **MoEntwine: Unleashing the Potential of Wafer-Scale Chips for Large-Scale Expert Parallel Inference** | 清华 / 中科院 (Tang, Hou, Jiang 等) |
| 10 | **TEMP: A Memory Efficient Physical-Aware Tensor Partition-Mapping Framework on Wafer-Scale Chips** | 清华 / 中科院 (Wang, Wei, Wang 等) |
| 11 | **WATOS: Efficient LLM Training Strategies and Architecture Co-Exploration for Wafer-Scale Chip** | 清华 / 中科院 (Wang, Wang, Wang 等) |
| 12 | **HDPAT: Hierarchical Distributed Page Address Translation for Wafer-Scale GPUs** | 清华 / 中科院 (Xu, Li, Sun 等) |

### HPCA 2024

| # | 论文 | 团队 |
|---|------|------|
| 13 | **Gemini: Mapping and Architecture Co-Exploration for Large-Scale DNN Chiplet Accelerators** | 清华（尹首一 / 胡杨组） |

---

## ASPLOS (Architectural Support for Programming Languages and Operating Systems)

### ASPLOS 2026

| # | 论文 | 团队 |
|---|------|------|
| 14 | **Ouroboros: Wafer-Scale SRAM CIM with Token-Grained Pipelining for Large Language Model Inference** | Shixin Zhao 等 |
| 15 | **An MLIR Lowering Pipeline for Stencils at Wafer-Scale** | Edinburgh / Cambridge (Stawinoga, Katz, Lydike 等) |

---

## 其他体系结构/半导体顶会 & 期刊

### DAC 2021

| # | 论文 | 团队 |
|---|------|------|
| 16 | **Designing a 2048-Chiplet, 14336-Core Waferscale Processor** | UCLA + UIUC (Saptadeep Pal, Rakesh Kumar, Subramanian Iyer 等) |

### IEEE Micro 2023

| # | 论文 | 团队 |
|---|------|------|
| 17 | **The Microarchitecture of DOJO, Tesla's Exa-Scale Computer** | Tesla (Talpes, Sarma, Williams 等) |

---

## 统计总览

| 维度 | 情况 |
|------|------|
| **时间跨度** | 2021 – 2026 |
| **覆盖会议** | ISCA / HPCA / ASPLOS / DAC / IEEE Micro |
| **论文总数** | **17 篇** |
| **主力团队** | 清华大学（尹首一/胡杨组）> 中科院计算所 SKLP > UIUC > UCLA |
| **热点方向** | LLM 训练/推理映射、Network-on-Wafer 拓扑、芯粒 FHE 加速、晶圆级交换机、SRAM 存内计算 |
| **对标系统** | Tesla Dojo、Cerebras WSE、GPU 集群 |
| **趋势** | 2025–2026 年论文数量井喷，晶圆级芯片从工业探索进入学术界主流议程 |

---

## PDF 获取状态

| # | 论文 | 来源 | 状态 |
|---|------|------|:--:|
| 1 | ConBin (ISCA'26) | — | ❌ 太新，无预印本 |
| 2 | CASCADE FHE (ISCA'26) | — | ❌ 太新，无预印本 |
| 3 | AutoFHE (ISCA'26) | — | ❌ 太新，无预印本 |
| 4 | NoW Co-Design (ISCA'25) | ACM 付费墙 | ❌ 无开放获取版本 |
| 5 | Cramming Data Center (ISCA'25) | ACM 付费墙 | ❌ 无开放获取版本 |
| 6 | WSC-LLM (ISCA'25) | ACM 付费墙 | ❌ 无开放获取版本 |
| 7 | **FRED** (ISCA'25) | arXiv `2406.19580` | ✅ 已下载 |
| 8 | Waferscale Network Switches (ISCA'24) | IEEE 付费墙 | ❌ 无开放获取版本 |
| 9 | **MoEntwine** (HPCA'26) | arXiv `2510.25258` | ✅ 已下载 |
| 10 | **TEMP** (HPCA'26) | arXiv `2512.14256` | ✅ 已下载 |
| 11 | **WATOS** (HPCA'26) | arXiv `2512.12279` | ✅ 已下载 |
| 12 | HDPAT (HPCA'26) | IEEE 付费墙 | ❌ 无开放获取版本 |
| 13 | **Gemini** (HPCA'24) | arXiv `2312.16436` | ✅ 已下载 |
| 14 | **Ouroboros** (ASPLOS'26) | arXiv `2603.02737` | ✅ 已下载 |
| 15 | **MLIR Stencils** (ASPLOS'26) | arXiv `2601.17754` | ✅ 已下载 |
| 16 | **2048-Chiplet Processor** (DAC'21) | UCLA NanoCAD Lab | ✅ 已下载 |
| 17 | Tesla Dojo (IEEE Micro'23) | IEEE 付费墙 | ❌ 无开放获取版本 |

> **总计: 8/17 ✅ | 9/17 ❌**

所有 PDF 文件位于 `wafer-scale-pdfs/` 目录下。
