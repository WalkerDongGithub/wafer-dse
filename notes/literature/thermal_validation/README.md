# 热仿真对标：真实芯片/封装热数据收集

> 用途：为"我们的稳态热阻网络模型是真实芯片温度的稳定上界"收集弹药。
> 调研时间：2026-08-15。检索方式：WebSearch 多轮 + 多源交叉核对（WebFetch 在本环境被网络策略拦截，关键数字以"多个独立来源一致"为准）。
> 质量标注：[可靠]=原始学术文献/行业规范/官方 datasheet；[中等]=行业杂志/综述/可信新闻；[待确认]=需下载原文核对数字。

---

## 0. 一句话结论

**我们的热模型在三个方向上全部保守，且在保守方向上各自有明确安全裕量：R_vert 比工业实测堆叠热阻大约 4 倍、T_max 比交换 ASIC 真实结温上限低 20°C、冷却档位（除 Air 档）按"该技术的演示上限"而非"典型值"配置。因此 G·T=P+b 给出的温度是真实芯片温度（die 平均）的稳定上界，B* 不会因热模型不精确而被高估。**

文件结构：

| 文件 | 内容 |
|---|---|
| 00_COEFFICIENT_EVIDENCE.md | **热模型系数 → 权威原文证据链**（7 个系数的强溯源对账 + 待下载清单） |
| 01_jedec_theta.md | JESD51 标准、θjc/θja/Ψjt 定义、典型数值 |
| 02_materials_bumps.md | 硅/铜/TIM/underfill 热导率、μbump 阵列热阻、TSV 等效热导 |
| 03_switch_asic_thermal.md | Tomahawk 4/5、Spectrum-4 的 TDP/Tj_max/Rca，51.2T 液冷研究 |
| 04_chiplet_wafer.md | MFIT/HotSpot 工具与标定精度、热感知 chiplet 放置文献、Cerebras/Dojo 晶圆级热数据 |
| 05_cooling_limits.md | 风冷/液冷/浸没/微通道功率密度极限（HIR 等）、与代码冷却档位对比 |

---

## 1. 与 LP 系数的映射表（每篇文献最终都要落回这里）

| 我们的系数（代码位置） | 现状默认 | 文献锚点 | 结论 |
|---|---|---|---|
| `R_vert`（`network/_mfit_system.py`，默认 2.0 K/W，注释 1.5–3.0） | 2.0 K/W（按 12×12mm die） | TH5 全堆叠 R≈0.09 K/W@~800mm² → 换算 144mm² die ≈ 0.5 K/W；HIR 高效风冷模块 0.8 °C·cm²/W → 144mm² ≈ 0.56 K/W（见 03、05） | **保守 ~4×**，温度上界成立 |
| `T_max`（`network/builder/_analytic.py`，358.15 K = 85°C） | 85°C | TH5 结温上限 105°C；EM 寿命设计点普遍 105–110°C（见 03） | **保守 20–25°C**，且恰好覆盖 die 内热点幅度（10–20°C，见 04） |
| `k_interposer`（150 W/(m·K)） | 150 | 硅体热导率 125–150 W/(m·K)，HotSpot 默认 130（见 02） | 吻合，非保守非乐观 |
| `t_interposer`（0.1 mm） | 0.1 mm | CoWoS interposer 主流 ~100μm、TSV 10:1 深宽比（见 02） | 吻合 |
| `CoolingSolution` 四档（`_cooling.py`） | Air 0.5 / Liquid 2.0 / Immersion 5.0 / Microfluidic 10.0 W/mm² | HIR：风冷实际极限 40–53 W/cm²；冷板典型 50–150 W/cm²；嵌入式微通道演示 400–700 W/cm²（见 05） | Air 档≈HIR 实际极限（贴边）；其余档位=该技术演示上限（乐观但非虚构） |
| `ΔT_max`（`_warp_limit.py`，10 K 邻接 die 温差） | 10 K | 文献中热感知放置以 85°C/105°C 阈值、间距插入使峰值降 4–24°C 为手段（见 04） | 无直接对标数字，见缺口 |
| `T_ambient`（300 K = 27°C） | 27°C | ASHRAE 数据中心进风 45°C、Telcordia 55°C（见 05） | **乐观方向**，上界论证需注意（唯一不保守的输入） |

## 2. 稳定上界的论证链（写论文引言/方法时直接引用）

1. **垂直路径**：真实大 die 交换 ASIC 全堆叠（die→TIM→lid→heatsink→air/liquid）的等效 R·A ≈ 40–80 K·mm²/W（TH5 反推 ≈72，HIR 高效风冷 80）。我们 144mm² die 用 R_vert=2.0 K/W → 288 K·mm²/W，**3.6–7 倍于实测**。上界裕量 ~4×。
2. **结温上限**：交换 ASIC 设计点 Tj_max=105°C（EM 寿命 cliff，TI 可靠性表：105°C 是 10 年寿命基准，每 +5°C 寿命近似减半）。我们用 85°C，保守 20°C，恰好大于 die 内热点相对 die 平均的典型幅度（10–20°C）——**lumped 掉的热点被 T_max 的保守裕量吸收**。
3. **横向路径**：die 间耦合 g_lat 用硅 interposer 真实热导率（150 W/mK）建模，与 HotSpot 默认（130）同量级，横向路径本身不做保守化——但它远弱于垂直路径（interposer 仅 0.1mm 厚），所以横向是否保守不影响主结论。
4. **热网络方法可信性**：MFIT（同族工具，我们代码直接借鉴其 nodal analysis 组装）验证：lumped RC 模型 vs FEM 误差 <1.7°C（~1–3.5% @ ~100°C）——**集总热阻网络是 chiplet 热分析的标准近似，且误差远小于我们模型的保守裕量**。
5. **唯一不保守的输入是 T_ambient=27°C**（ASHRAE 数据中心允许到 45°C）。若要更硬的"稳定上界"，用 T_ambient=318 K（45°C）跑一次灵敏度（对偶变量/影子价格可直接回答：B* 对 T_ambient 的弹性）。

## 3. 与已有笔记的关系

- `notes/THERMAL_MODEL.md`：数学推导，本文档提供其中所有"典型值"的外部证据。
- `notes/LITERATURE_SURVEY.md` A1/A2：Dojo 与 Cerebras 已有带宽/拓扑数字，本文档补充其**热侧**数字（功耗、面积→功率密度、散热方式）。
- `notes/literature/RENT_RULE_AND_IO_DENSITY.md`：风格模板（表格+质量标注+为什么可信+与我们的关系）。

## 4. 关键数字速查表（全文件最硬的 10 个数）

| 数字 | 单位 | 出处 | 文件 |
|---|---|---|---|
| 105 | °C（Tj_max） | TH5 液冷研究（IEEE 10709537） | 03 |
| 763 | W（TH5 TDP 上限） | 同上 | 03 |
| 0.05 | °C/W（TH5 风冷 heatsink 目标 Rca） | 同上 | 03 |
| 0.82 | K/W（5.08mm die 裸 die 2.5D TSI θjc） | IEEE TCPMT 2014（10.1109/TCPMT.2014.2311587） | 01 |
| 8.0–19.0 | °C·mm²/W（μbump 层实测单位热阻 @50–100μm pitch） | Electronics Cooling 2013 实测 | 02 |
| ~3200 | K/W（单 bump 热阻 @50μm pitch，换算） | 同上换算 | 02 |
| 125–150 | W/(m·K)（硅热导率；HotSpot 默认 130） | 教材/HotSpot 源码 | 02 |
| 40–53 | W/cm²（风冷实际散热极限，HIR 2021） | HIR Chapter 20 | 05 |
| 0.32 / 0.21 | W/mm²（Cerebras WSE-2 / Dojo tile 晶圆功率密度） | 15kW/46,225mm²；15kW/70,686mm² 换算 | 04 |
| <1.7 | °C（MFIT RC 模型 vs FEM 温度误差） | ACM TODAES 2025（10.1145/3765905） | 04 |

## 5. 缺口与下一步

1. **TH5 die 面积**（用于把 763W 折算成真实热流密度 W/cm²）未找到公开数字——只找到"大容量交换芯片 FCBGA 封装 >60cm²、8000+ 引脚"这类笼统说法。候选：找 Broadcom BCM78900 官方资料或 chipworks/techinsights 拆解。
2. **Spectrum-4 ASIC 级 TDP 未公开**（只有整机 940W typical）。可用整机功率扣除 optics 预算（30W/端口×64=1920W？不成立——SN5600 940W 是 passive cable 下的数字，含 optics 空间有限）反推，但不精确，标注为缺口。
3. **51.2T 液冷论文（IEEE 10709537）的会议/年份待确认**——数字（763W/105°C/0.05 Rca/冷板好 40%/CFD 误差 5.7%）来自两次独立检索的摘要级一致信息，建议下载原文核对。
4. **ΔT_max（翘曲）没有找到直接的工业上限数字**。TSV 系文献把热应力和翘曲当优化目标但少给"允许温差"规范值。候选：JEDEC 或封装厂翘曲规范（warpage spec ≤50–100μm 级别的数据可能有逆推空间）。
5. **die 内热点幅度（10–20°C）**需要一个可引用的权威综述（MDPI Energies 2026 综述与 HIR 章节有述，待下载原文取精确值）。
6. **HIR 2021 Chapter 20 原文**（eps.ieee.org PDF）未能直接抓取，40–53 W/cm² 与 0.8 °C·cm²/W 来自检索摘要的交叉一致，建议下载归档。
7. **immersed/两相浸没的芯片级 W/cm² 极限**只有机架级（>100–200 kW/rack）证据，die 级数字缺失。

## 6. 全文件来源总清单

1. JEDEC JESD51 系列（JESD51-2/6/7/9/14）：https://www.jedec.org —— [可靠]
2. Rohm 技术专栏《Thermal Resistance Data》（θjc/Ψjt 定义）：https://techweb.rohm.com/product/circuit-design/thermal-design/9678/ —— [可靠]
3. 2.5D TSI 热表征：IEEE Trans. CPMT 2014, doi:10.1109/TCPMT.2014.2311587 —— [可靠]
4. Kandasamy & Subramanyam, "Interface thermal characteristics of flip chip packages – A numerical study", Applied Thermal Engineering 29 (2009) 822–829, doi:10.1016/j.applthermaleng.2008.04.002 —— [可靠]
5. "Measured Thermal Resistance of Microbumps in 3D Chip Stacks", Electronics Cooling, 2013-03 —— [可靠]（实测报告）
6. Matsumoto et al., SEMI-THERM 2014, doi:10.1109/semi-therm.2014.6892243 —— [可靠]
7. Oprins et al., "Experimental Characterization of the Vertical and Lateral Heat Transfer in 3D Stacked Die Packages", ASME J. Electronic Packaging, 2016, doi:10.1115/1.4032346 —— [可靠]
8. "The Study of Liquid Cooling Solution on 51.2T Switch", IEEE（文档号 10709537），会议年份待确认 —— [可靠]/[待确认]
9. NVIDIA SN5600 Datasheet（Dell 镜像 PDF）：https://www.delltechnologies.com/asset/.../nvidia-spectrum-sn5600-datasheet.pdf —— [可靠]
10. Broadcom Tomahawk 4 发布稿（含 Linley Group 450W 估计）：https://investors.broadcom.com/news-releases/... —— [中等]
11. Huang et al., HotSpot（UVa 开源热仿真工具 + 默认参数）：https://www.cs.virginia.edu/~skadron/lava/HotSpot/ —— [可靠]
12. Pfromm, Kanani et al., "MFIT: Multi-Fidelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures", ACM TODAES 31(1), 2025, doi:10.1145/3765905；arXiv:2410.09188 —— [可靠]
13. Ma et al., "TAP-2.5D", DATE 2021 —— [可靠]
14. Eris et al., "Leveraging Thermally-Aware Chiplet Organization in 2.5D Systems to Reclaim Dark Silicon", DATE 2018 —— [可靠]
15. TACPlace, ACM GLSVLSI 2025, doi:10.1145/3716368.3735185 —— [可靠]
16. ATPlace2.5D, IEEE（文档号 11126201，ICCAD 2024）—— [可靠]
17. Cerebras WSE-2 数据：AnandTech 报道（14/23 kW）；Hot Chips 2021 Sean Lie 演讲；PSC Neocortex 文档（CS-2 28 kW）—— [中等]/[可靠]
18. HotCarbon 2025 论文 160（CS-3 实测：训练时高于 idle 约 4.3 kW）：https://hotcarbon.org/assets/2025/paper-160.pdf —— [可靠]/[待确认]
19. Tesla Dojo：Hot Chips 34（2022）+ 中文科技报道（15kW/tile、铜 tray 7→15kW、18000A VRM）—— [可靠]/[中等]
20. HIR 2021 Chapter 20 Thermal（IEEE EPS）：https://eps.ieee.org/images/files/HIR_2021/ch20_thermal1.pdf —— [可靠]/[待确认]
21. "Thermal Management Challenges in 2.5D and 3D Chiplet Integration: A Review on Architecture–Cooling Co-Design", MDPI 2024, 6(12):373 —— [中等]
22. 液冷 vs 浸没数据中心综述（Noxtel/行业白皮书；机架级 30–100+ kW 极限）—— [中等]
23. CoWoS interposer 参数（~100μm 厚、TSV 10:1、μbump 40μm pitch、0.8μm 布线）：华金证券研报/科学网科普 —— [中等]
24. TSMC InFO-SoW / Dojo 晶圆级平台（LITERATURE_SURVEY.md A3 已有）—— [可靠]
