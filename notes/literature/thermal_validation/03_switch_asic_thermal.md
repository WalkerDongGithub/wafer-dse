# 03 交换 ASIC 热数据（Tomahawk 4/5、Spectrum-4）

> 断言：现代 51.2T 交换 ASIC 是热设计最激进的量产硅片——单 die 数百瓦、Tj_max=105°C、风冷靠巨型均温板才能压住。这是我们"热是晶圆级交换机瓶颈"论断的最强工业证据。

## 1. 数字总表

| 芯片 | 工艺 | 容量 | TDP | 热设计要点 | 出处 | 状态 |
|---|---|---|---|---|---|---|
| **Tomahawk 5**（BCM78900） | TSMC N5 单片 | 51.2T（512×100G SerDes） | **最高 763W**；Broadcom 口径 <1W/100G（即 <512W）；第三方电源规划按 ~450W/ASIC | Tj_max **105°C**；风冷（2U 均温板 VC heatsink）需 Rca ≤ **0.05°C/W**；液冷冷板比目标好 ~40%（≈0.03°C/W） | Fan et al., ITherm 2024, DOI 10.1109/ITherm55375.2024.10709537 | [可靠]（摘要级已确认，页码待核对） |
| **Tomahawk 4**（BCM56990） | TSMC N7 单片 | 25.6T（512×50G SerDes） | ~350–515W（Linley Group 估计 **450W typical**；另源 515W/350W） | 换算能效 14–20 pJ/bit（450W 口径 17.6） | Broadcom 发布稿（引 Linley）；行业文章 | [中等] |
| **Spectrum-4**（SN5600 整机） | — | 51.2T | 整机 **940W typical**（passive cable，ATIS 口径）；ASIC 级 TDP **未公开** | 风冷 C2P，0–35°C 工作温度，64 端口 × 18W optics 预算 | NVIDIA SN5600 datasheet（Dell 镜像） | [可靠]（整机）；ASIC 级为缺口 |
| 前代参考：Tomahawk 3 | TSMC 16FFC | 12.8T | ~300W（Linley） | — | Broadcom 文档 | [中等] |

## 2. 51.2T 液冷研究（Fan et al., ITherm 2024）——最有价值的一篇

论文背景与研究内容：AI 流量驱动 51.2T 交换 ASIC 热挑战；TH5 TDP 最高 **763W**；为维持 **105°C 结温上限**，风冷 heatsink 必须做到 Rca ≤ **0.05°C/W**（2U 机箱内大型均温板可实现，但占空间、风机功耗大）；论文做了 3 种液冷冷板设计（CFD 仿真 + 实测），最优冷板比目标热性能好 **~40%**，CFD 与实验误差 **5.7%** 以内。

**反推全堆叠热阻**（写论文时可直接用的数字）：
- 结到环境总 R ≈ (105 − 35)/763 ≈ **0.09 K/W**（设进风 35°C）。
- 单位面积 R·A ≈ 0.09 × ~800mm² ≈ **72 K·mm²/W**（die 面积 ~800mm² 是假设，见缺口）。
- 该口径下 12×12mm die 的全堆叠 R_vert ≈ 72/144 ≈ **0.5 K/W**——我们默认 2.0 K/W 的 **4 倍保守**。

**为什么可信**：IEEE 正式论文（ITherm 2024，Fan/Xiao/Liu，物理实验 + CFD 交叉验证）；与 Broadcom"<1W/100G"口径（≤512W）一致地"最坏 763W"。会议/年份已确认，页码/图表号需下载原文核对。

## 3. Tj_max 为什么是 105–110°C（EM 可靠性锚）

| 事实 | 数字 | 出处 | 状态 |
|---|---|---|---|
| TI datasheet 可靠性口径 | "硅片工作寿命设计目标 = 105°C 结温下 10 年"，主导失效机制是 EM | TI SN65HVD11-HT / CDCLVP111 datasheet | [可靠] |
| 加速因子表（以 105°C 为 1.0） | 110°C→0.50；115°C→0.40；120°C→0.30；125°C→0.20 | TI app note sprabx4a | [可靠] |
| 直观后果 | 105°C 设计寿命 10 年 → 长期跑 125°C 只剩 ~2 年 | 同上换算 | [可靠] |
| EM 签核温度 | 多数芯片在 ~110–115°C 做 EM signoff（"cliff"之上再加 2–3× 裕量） | SemiEngineering《Thermally Challenged》 | [中等] |
| 消费级 CPU 参考 | Intel 3rd gen Core TJmax=105°C | AnandTech 论坛/Intel 资料 | [中等] |

**与我们的关系**：我们 T_max=85°C（358.15 K）比 EM 寿命设计点低 **20–25°C**——这不是随便选的，恰好能把 die 内热点幅度（10–20°C，见 04）吸收进去，同时离翘曲风险（85°C 阈值）还有 0。即：**85°C 是"翘曲阈值"，105°C 是"可靠性上限"，我们取的是更紧的那个，符合"稳定上界"叙事**。

## 4. 与我们的关系

- **热墙主导的直接证据**：单 die 763W @ ~800mm² = **~0.95 W/mm²** 的 die 热流密度，风冷必须巨型均温板、液冷才从容——说明"交换机密度极限由热定"是工业界正在面对的活问题，我们论文的热墙结论不是纸面推演。
- **R_vert 标定**：以 0.09 K/W @ 763W 全堆叠为锚，12×12mm die 的物理合理 R_vert ≈ 0.5 K/W（液冷）~0.56 K/W（高效风冷，见 05 的 HIR 0.8 °C·cm²/W）。我们默认 2.0 K/W → 上界成立；灵敏度实验建议扫 R_vert ∈ {0.5, 1.0, 2.0, 3.0}。
- **T_max 对标**：论文里 TH5 用 105°C，我们 85°C——引用该论文时说明"我们的 T_max 更紧"是加分项（保守侧）而非缺陷。
- **能效锚**：TH4 14–20 pJ/bit、TH5 <1W/100G 是全 chip 口径；我们的 lane 功耗系数（SerDes ~几 pJ/bit）是链路侧，两者口径不同，不能直接比——但"全 chip 功耗 ÷ 总带宽"可作为我们 LP 里 P0（静态功耗基线）的上界校验：51.2T 交换机 P0 不应低于 ~500W 量级。

## 5. 来源清单

1. "The Study of Liquid Cooling Solution on 51.2T Switch", IEEE（文档号 10709537）—— [可靠]/[待确认]
2. Broadcom, "Broadcom Ships Tomahawk 4 ... 25.6 Tbps"（发布稿，含 Linley Group 功耗估计）：https://investors.broadcom.com/news-releases/ —— [中等]
3. IP Infusion Tomahawk 4/5 产品页（工艺/SerDes 配置）：https://www.ipinfusion.com/technology/tomahawk-5/ —— [中等]
4. NVIDIA SN5600 Datasheet：https://www.delltechnologies.com/asset/.../nvidia-spectrum-sn5600-datasheet.pdf —— [可靠]
5. TI datasheet 可靠性段落（SN65HVD11-HT, CDCLVP111-SP）+ app note sprabx4a：http://www.ti.com/lit/an/sprabx4a/sprabx4a.pdf —— [可靠]
6. SemiEngineering, "Thermally Challenged"：https://semiengineering.com/thermally-challenged/ —— [中等]
7. ServeTheHome 对 TH5 平台/CPO 报道（Bailly 5.5W/800G 等）：https://www.servethehome.com/ —— [中等]
