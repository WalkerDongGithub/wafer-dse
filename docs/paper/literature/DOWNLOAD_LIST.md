# 待下载文献清单

> 以下论文无法自动下载（付费墙/机构访问/网络限制），需要手动获取后放入对应目录。

---

## 1. 晶圆级平台 (wafer_platforms/)

| 论文 | 来源 | 用途 |
|---|---|---|
| TSMC InFO-SoW技术论文 | IEEE / TSMC website | 引言L6: 晶圆级集成工业量产 |
| TSMC CoW-SoW (2024 announcement) | TSMC / latitudeDS | 引言L6: 3D晶圆级集成进展 |
| Hot Chips 34: Tesla Dojo (Talpes et al.) | IEEE Xplore | 已引用 cite:tesla2022dojo |
| Cerebras WSE-2 paper | IEEE Micro / Hot Chips | 已引用 cite:cerebras2022wse2 |

---

## 2. 晶圆级交换机 (wafer_switches/)

| 论文 | 来源 | 用途 |
|---|---|---|
| Chen, Pal, Kumar. "Waferscale Network Switches." ISCA 2024, pp. 215-229 | ACM DL | 已引用 cite:chen2024waferscale |
| Feng & Ma. "Switch-Less Dragonfly on Wafer." ATC 2024 (USENIX) | USENIX | 已引用 cite:feng2024switchless |
| Wan et al. "Architectural Exploration for Waferscale Switching System." IEEE TVLSI 2025 | IEEE Xplore | 引言: Wan的NoW架构 → cite:wan2024architectural |
| Yang et al. "PD Constraint-aware Physical/Logical Topology Co-Design for Network on Wafer" (TickTock). ISCA 2025 | ACM DL | 已有 cite:yang2025pd |

---

## 3. 互联标准 (interconnect_standards/)

| 论文 | 来源 | 用途 |
|---|---|---|
| **UCIe 2.0 Specification** (Aug 2024) | uciexpress.org | **核心引用**: bump power 0.25-0.6 pJ/bit, lane速率, Advanced/Standard区分 |
| UCIe 3.0 (Aug 2025) 64 GT/s | uciexpress.org | 最新标准速率 |
| OIF-CEI-112G/224G VSR/MR/LR standards | oiforum.com | SerDes reach和速率等级 |
| Cadence 112G ELR SerDes on TSMC N4P (2023 press release) | cadence.com | SerDes功耗参考 |
| **Ayar Labs TeraPHY**: 8 Tbps optical chiplet, <5 pJ/bit | ayarlabs.com | 光学互联带宽+功耗 |
| TSMC 3nm UCIe: 0.52 pJ/bit @16G (2025) | IEEE Xplore | UCIe最新硅验证数据 |
| TSMC 3nm UCIe: 0.6 pJ/bit @32G (2025) | research.tsmc.com | UCIe实际硅功耗 |

---

## 4. 网络拓扑与性能 (network_topology/)

| 论文 | 来源 | 用途 |
|---|---|---|
| **Kim et al. "Technology-Driven, Highly-Scalable Dragonfly Topology." ISCA 2008** | ACM DL | Dragonfly参数空间(a,p,h,g)，拓扑基础 |
| Benito et al. "Analysis and Improvement of Valiant Routing in Low-Diameter Networks." HiPINEB 2018 | IEEE Xplore | Valiant路由在Dragonfly上的分析 |
| Navaridas & Pascual. "Improving Dragonfly via Restrictive Proxy Routing." 2025 | ScienceDirect | Dragonfly+Valiant最新改进 |
| "Analyzing Nonblocking Switching Networks using Linear Programming (Duality)" | arXiv:1204.3180 | **核心引用**: LP在交换网络非阻塞分析中的应用先例 |
| Birkhoff 1946 / von Neumann 1953 | 数学经典 | 已有 cite:birkhoff1946tres |
| BookSim 2.0 simulator paper | 学术引用 | BookSim仿真速度 |

---

## 5. Chiplet DSE (chiplet_dse/)

| 论文 | 来源 | 用途 |
|---|---|---|
| **RapidChiplet** (Iff et al., CF'25): arXiv:2311.06081 | arxiv.org | chiplet DSE, 427×-137k× speedup, 覆盖latency/throughput/cost/thermal |
| **FireLink** (Li et al., JCRD 2025) | crad.ict.ac.cn | chiplet DSE + PPAC + ID3剪枝 |
| CHARIOT (DTIC, 2024) | dtic.dimensions.ai | 2.5D/3D interposer DSE, Bayesian optimization |
| FPIA (Jiao et al.) | 已有 | 已有 cite:jiao2024fpia |

---

## 6. 物理约束 (physical_constraints/)

| 论文 | 来源 | 用途 |
|---|---|---|
| **2.5D/3D Thermal-Warpage reliability survey** | ScienceDirect / IEEE | **核心引用**: 温度→翘曲→bump失效的物理链条 |
| MFIT paper: Berman 1994 "Nonnegative Matrices" | 已有 | 已有 cite:berman1994nonnegative |
| HotSpot thermal modeling tool | 学术引用 | 热分析工具的存在证明 |
| 3D-ICE thermal simulator | 学术引用 | 热分析工具 |
| Synopsys RedHawk-SC Electrothermal | synopsys.com | 工业热分析工具 |
| Li et al. "Thermal Cycling Reliability Analysis of 2.5D Chiplet Based on Silicon Interposer" | Semantic Scholar | bump失效与温差关系 |

---

## 7. LP/优化方法论 (lp_optimization/)

| 论文 | 来源 | 用途 |
|---|---|---|
| Bertsekas "Nonlinear Programming" | 已有 | 已有 cite:bertsekas1997nonlinear |
| Diamond & Boyd "CVXPY" | 已有 | 已有 cite:diamond2016cvxpy |
| Goulart et al. "CLARABEL" | 已有 | 已有 cite:goulart2024clarabel |
| LP-duality for nonblocking networks | arXiv:1204.3180 | 同目录4 |

---

## 优先下载 Top 5

1. **UCIe 2.0 Specification** — 功耗/bump/lane的所有硬数据来源
2. **RapidChiplet (arXiv:2311.06081)** — chiplet DSE的定量对比基准
3. **Kim et al. ISCA 2008 (Dragonfly)** — 拓扑参数空间的原始定义
4. **2.5D Thermal-Warpage reliability survey** — 翘曲是L的线性函数的物理证据
5. **LP-duality for nonblocking networks (arXiv:1204.3180)** — LP方法在交换网络中的先例
