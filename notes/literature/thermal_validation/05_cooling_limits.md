# 05 散热能力上限：风冷 / 液冷 / 浸没 / 微通道

> 断言：散热手段的功率密度极限有明确的物理与标准边界（HIR 2021 量化了风冷极限），我们的四档冷却预算必须逐档与这些边界对齐——每档都应理解为"该技术的实测/演示上限"，而非"典型值"。

## 1. HIR 2021 Chapter 20（IEEE Heterogeneous Integration Roadmap）量化极限

| 项 | 数值 | 备注 |
|---|---|---|
| 风冷理想上限（均匀热流假设） | ~84 W/cm² | 纯物理推演 |
| **风冷实际极限**（Telcordia GR63 进风 55°C / ASHRAE 45°C 约束 + 热扩展假设，1U–4U 服务器） | **40–53 W/cm²** | 热预算 ~45–50°C |
| 高效风冷模块单位面积热阻基准 | **0.8 °C·cm²/W**（结→环境） | 高导热 TIM + 薄 BLT + 均温板 + 热管 |
| 拟合公式 | R_JA = 192.8·(V_HS/A_af)^−1.258·F^−0.30 | 风量/翅片面积的工程拟合 |

**为什么可信**：[可靠]/[待确认]——IEEE HIR 官方路线图章节（eps.ieee.org PDF），但本环境未能抓取原文，数字来自检索摘要的两次独立交叉（一次直接命中该章节数值，一次经综述转引）。写论文引用前建议下载归档原文。

## 2. 各散热技术极限总表（die 级与机架级）

| 技术 | die/模块级能力 | 机架级（数据中心实践） | 出处 |
|---|---|---|---|
| 自然对流/风冷 | 40–53 W/cm²（HIR 实际极限）；TH5 靠 2U 巨型均温板做到 ~95 W/cm² die 热流（见 03） | 常规设计 30–40 kW/rack；>30–50 kW 风冷"不再合理" | HIR 2021；Noxtel 行业综述 [中等] |
| 冷板液冷（DLC） | 典型 50–150 W/cm²（直接 die 冷板）；TH5 液冷冷板实测优于 0.05°C/W 目标 40%（→约 0.03 K/W） | 50–100 kW/rack，渐次改造 | IEEE 10709537；Noxtel [中等] |
| 浸没（单相/两相） | die 级公开数字少（缺口）；CPU 温度可比风冷低 13°C（CFD 对比） | >100 kW/rack，量产部署达 200+ kW/rack | Purdue ITHERM 论文；Noxtel [中等] |
| 嵌入式微通道/歧管 | **400 W/cm²**（pEMMC 2.5D 原型：948W、温升 <80K）；**700+ W/cm²**（歧管微通道演示，65K 温差） | — | 西安交大学者 pEMMC；ECS 论文 [可靠] |
| AI 加速器需求投影 | 热点 >1000 W/cm²；系统功率密度 >500 W/cm² | — | MDPI 综述 2024 [中等] |

**为什么可信**：die 级数字来自 IEEE/期刊论文（含实测）；机架级来自行业综述（多个独立来源一致）。浸没 die 级数字缺失是公开缺口。

## 3. 与我们代码冷却档位的逐档对标（核心结论）

代码 `_cooling.py`：Air 0.5 W/mm²（=50 W/cm²）、Liquid 2.0（=200）、Immersion 5.0（=500）、Microfluidic 10.0（=1000）。

| 代码档位 | W/cm² | 文献边界 | 判定 |
|---|---|---|---|
| **Air 0.5 W/mm²** | 50 | HIR 实际极限 40–53 W/cm²；TH5 巨型均温板 ~95 | **贴边合理**（=HIR 实际极限上沿）——但注意 TH5 是在 2U 全机箱均温板+105°C 结温下才到 95，我们用 85°C 结温时应更紧 |
| **Liquid 2.0 W/mm²** | 200 | 典型冷板 50–150；pEMMC 歧管 400 | **偏乐观**：该数字属于"微通道冷板演示上限"而非普通冷板典型值；建议标为"Liquid（microchannel cold plate）"或降到 ~1.0–1.5 W/mm² |
| **Immersion 5.0 W/mm²** | 500 | 嵌入式微通道演示 400–700 | 处于研究级演示区间，非量产浸没（量产浸没 die 级数字缺失） |
| **Microfluidic 10.0 W/mm²** | 1000 | AI 热点投影 >1000 | 前沿研究值，作为"物理极限档"可以，但不能当"可实现量产" |

**与我们的关系**：
- **Air 档直接进散热预算 rhs**：50 W/cm² ≈ HIR 实际极限 → 我们 Air 档产出的 B* 不会被指责为"风冷做不到"。这是论文里最有价值的一个对齐。
- **Liquid/Immersion/Microfluidic 三档的名字与实际能力错位**：要么改名（如 "Liquid-VC"、"Microchannel"、"Research-Limit"），要么在论文中明示"本档取该技术文献演示上限"。改不改名字由建模者定，但**对标结论必须先写进文档**。
- **T_ambient 警示**：HIR 风冷极限是在 ASHRAE 45°C 进风约束下推的；我们 T_ambient=300K（27°C）比之宽松 18°C——若把 T_ambient 提到 318K（45°C）重跑，热约束 rhs 收窄（每 die 少 (318−300)×g_vert 的预算），B* 下降。**论文里建议报 27°C 与 45°C 两档**，让上界论证无懈可击。

## 4. 来源清单

1. HIR 2021, Chapter 20: Thermal Management（IEEE EPS）：https://eps.ieee.org/images/files/HIR_2021/ch20_thermal1.pdf —— [可靠]/[待确认]
2. HIR Thermal TWG 2024 更新（eps.ieee.org HIR_Presentations）：https://eps.ieee.org/images/files/HIR_Presentations/HIR_Thermal_TWG_Update_at_Annual_Workshop_-_Feb_20_2024.pdf —— [可靠]
3. "The Study of Liquid Cooling Solution on 51.2T Switch", IEEE 10709537 —— [可靠]/[待确认]
4. pEMMC 2.5D 嵌入式歧管微通道（西安交大学者成果页）：https://scholar.xjtu.edu.cn/zh/publications/synergistic-thermal-management-of-heterogeneous-25d-integration-e/ —— [可靠]
5. "Wafer-Level Integration of Embedded Cooling Approaches", ECS Trans.（歧管微通道 700+ W/cm²）：doi:10.1149/06405.0253ecst —— [可靠]
6. "Thermal Management Challenges in 2.5D and 3D Chiplet Integration: A Review on Architecture–Cooling Co-Design", MDPI 2024, 6(12):373：https://www.mdpi.com/2673-4117/6/12/373 —— [中等]
7. 液冷 vs 浸没行业综述（机架级极限）：Noxtel —— [中等]
8. Purdue 会议论文（浸没 vs 风冷 CFD，CPU 温度低 13°C）：docs.lib.purdue.edu（article 3600）—— [中等]
9. 我们的冷却档位定义：`src/physical/thermal/_cooling.py` —— [内部]
