# A 组：真实交换 ASIC 数据卡

> 用途：真实交换芯片硬参数，验证全部落在可行域内（在域外 = 模型 bug 或新约束）。
> 质量标注：[可靠] 官方 datasheet/新闻稿；[中等] 行业媒体/会议论文；[待确认] 需核对。
> 卡片字段：端口×速率=总容量 / SerDes / TDP / die 面积与工艺 / 封装 / 换算进我们框架。

---

## A1. Broadcom Tomahawk 3（BCM56980）[可靠]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 12.8 Tbps 全双工 | [可靠] Broadcom 2018 新闻稿 |
| 端口×速率 | 32×400G / 64×200G / 128×100G | [可靠] 同上 |
| SerDes | 256 × 50G PAM4（32 个 Blackhawk 核 × 8） | [可靠] 同上 |
| TDP | 缺（整机 32×400G 1RU ≈ 1300W 典型 [中等]，芯片级未公开） | [中等] Edgecore 整机规格 |
| die 面积/工艺 | 缺 / TSMC 16nm | [可靠] IP Infusion 硅片清单 |
| 封装 | monolithic FC-BGA | [可靠] |
| 发布 | 2018（首款 12.8T 量产交换芯片） | [可靠] |

**换算进我们框架**：256×50G 串行链路即 SerDes 族（S_bw=50G/lane）；12.8T 满配在传统 SerDes 场景（~4 pJ/bit）下动态功耗 ~50W 量级，但整机 1.3kW 说明系统级热预算大头在 SerDes+光学模组——对照我们 C4/组间约束的场景划分，TH3 这类传统封装交换机的 B* 会被功耗先压住，落在可行域内但靠近功耗面。

---

## A2. Broadcom Tomahawk 4（BCM56990）[可靠]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 25.6 Tbps | [可靠] Broadcom 2019-12 新闻稿 |
| 端口×速率 | 64×400G / 256×100G | [可靠] 同上 |
| SerDes | 512 × 50G PAM4（400G 端口 8×50G） | [可靠] 同上 |
| TDP | 缺（新闻稿只给"比替代方案低 75%"） | — |
| die 面积/工艺 | 缺 / 7nm monolithic | [可靠] |
| 封装 | monolithic BGA | [可靠] |
| 发布 | 2019-12（TH3 后 2 年内） | [可靠] |

**换算进我们框架**：512 lane 是单 die SerDes 供给的上限实证；按 4 pJ/bit 系数，25.6T 链路功耗 ~102W，加上逻辑 TDP 估计 ~350–450W [待确认]。在框架里做"die 内 + UCIe 组内"混合场景时，TH4 是 400G 端口时代端口带宽（B*）的锚点。

---

## A3. Broadcom Tomahawk 5（BCM78900）[中等] ⭐ 最硬的一张卡

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 51.2 Tbps | [中等] ISSCC 2025 论文 |
| 端口×速率 | 64×800G / 128×400G / 256×200G | [中等] 同上 |
| SerDes | 512 × 112G PAM4 Peregrine（102.5G ADC/DAC+DSP） | [中等] ISSCC 2025 |
| TDP | 450W 典型（EE Times 估 ~500W） | [中等] ISSCC 2025 / EE Times |
| die 面积/工艺 | **750 mm² / TSMC 5nm，60B 晶体管**，核时钟 1.325GHz | [中等] ISSCC 2025 |
| 封装 | monolithic BGA 87.5×77.5mm，无盖（lidless），空冷 | [中等] ISSCC 2025 |
| 其他 | 160M shared buffer；DAC/LPO/CPO 原生支持；Bailly CPO 变体省电 ~50% | [中等] |

**换算进我们框架**：整芯片能耗 450W/51.2T ≈ **8.8 pJ/bit**（含逻辑+SerDes），SerDes 部分 ~2–4 pJ/bit 量级 [待确认]——我们的传统 SerDes 系数 4 pJ/bit 取的是长距上限，偏保守；先进封装 UCIe 0.5 pJ/bit 与之差 ~1 个数量级，正好是"先进 vs 传统"场景 B* 差 ~8× 的来源（22k vs 2.8k，单位待核）。750mm² 单 die 装下 512 lane = 面积约束在 reticle 内（858mm²）被用到 87%——这是"为什么单 die 到 51.2T 就是极限"的实证，也是我们 wafer 级（多 die）设计空间存在的理由。

---

## A4. Broadcom Jericho2（BCM88690）[中等]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 10 Tbps（首款 10T 单芯片路由器） | [中等] 行业综述（CSDN 对比表） |
| 端口×速率 | 48×200G / 96×100G | [中等] 同上 |
| TDP | <300W | [中等] 同上 |
| die 面积/工艺 | 缺 / 16nm | [中等] |
| 封装 | monolithic | [中等] |
| 特色 | 深度缓冲 + 多 chip 扩展（Q2Q），路由导向 | [中等] |

**换算进我们框架**：Jericho 系列是"路由/缓冲导向"而非"线速交换"——大缓冲 + 多 die 级联，对应我们框架里缓存的模型化缺失（当前无缓冲约束）；它的多芯片扩展接口（Q2Q）是 chiplet 化交换机的前身。

---

## A5. Broadcom Jericho3 / Jericho3-AI（BCM88890）[中等]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 21.6T（Jericho3）/ 28.8T（Jericho3-AI 全交换带宽） | [中等] Broadcom 产品页 + 综述 |
| 端口×速率 | 48×400G；AI 版 144 lane 网络侧 = 18×800G / 36×400G / 72×200G | [中等] Broadcom 产品页 |
| SerDes | 144 × 106G PAM4（网络侧）+ 160 × 100G（fabric 侧） | [中等] Broadcom 产品页 |
| TDP | 缺（宣传"比 IB 方案低 40% 功耗/bit"） | — |
| die 面积/工艺 | 缺 / 7nm | [中等] |
| 定位 | AI/ML 集群以太网（RoCEv2），最多互联 32,000 GPU | [中等] |

**换算进我们框架**：Jericho3-AI 的 144 网络 + 160 fabric SerDes 是"组间/组内分离"的现实原型——网络侧端口进 EnvelopeModel，fabric 侧走框架的 SerDes/C4 通道；其 14.4T "GPU 连接带宽/每片"对应我们组间 B* 的口径，值得对齐单位后再引用。

---

## A6. NVIDIA Spectrum-1 [待确认]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 12.8 Tbps | [待确认]（NVIDIA 官方页未检索到，需 datasheet 核对） |
| 端口×速率 | 128×100G / 64×200G（SN3700 为 32×200G 整机） | [待确认] |
| SerDes | 128 × 100G 量级 | [待确认] |
| TDP | 缺 | — |
| die 面积/工艺 | 缺 / 7nm | [待确认] |
| 发布 | 2019-02 | [待确认] |

**换算进我们框架**：Spectrum-1 是 12.8T 时代 Mellanox 单 die 方案，与 TH3 同代同量级；卡片整体 [待确认]，引用前必须补官方 datasheet。

---

## A7. NVIDIA Spectrum-2 [待确认]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 25.6 Tbps | [待确认] |
| 端口×速率 | 64×400G（SN4600 整机 32×400G） | [待确认] |
| TDP | 缺 | — |
| die 面积/工艺 | 缺 / 7nm | [待确认] |
| 发布 | 2020 | [待确认] |

**换算进我们框架**：与 TH4 同代对标（25.6T/400G 端口时代）；无官方规格支撑，暂只做定性引用。

---

## A8. NVIDIA Spectrum-3 [待确认]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 25.6 Tbps | [中等] NVIDIA SN4000 产品页 |
| 端口×速率 | 64×400G（SN4700 整机 32×400G QSFP-DD） | [中等] NVIDIA SN4000 产品页 |
| 转发速率 | 8.4 Bpps | [中等] 同上 |
| TDP | 缺 | — |
| die 面积/工艺 | 缺 / 7nm | [待确认] |
| 发布 | 2021 | [待确认] |

**换算进我们框架**：Spectrum-3 与 TH4/Teralynx 8 同为 25.6T 第三梯队竞争；对框架的意义主要是确认"每代交换容量 ×2、端口速率 ×2"的节奏，用作 D 矩阵规模标度。

---

## A9. NVIDIA Spectrum-4 [可靠/中等] ⭐

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 51.2 Tbps 双向 | [可靠] NVIDIA Spectrum-4 datasheet |
| 端口×速率 | 64×800G / 128×400G / 256×200G（ASIC 本身 128×400G） | [可靠] 同上 |
| SerDes | 512 × 100G PAM4（8×100G/800G 端口） | [可靠] datasheet / GTC 2022 |
| TDP | ~500W | [中等] ZDNet GTC 报道 / 知乎拆解文 |
| die 面积/工艺 | 缺（**100B 晶体管**，TSMC 4N；封装 ~88–90×88–90mm） | [中等] GTC 2022 / 知乎（die 面积未公开，90×90mm 是封装） |
| 封装 | BGA（~7739 脚 @ 1.0mm pitch [待确认]） | [中等] 知乎拆解文 |
| 发布 | 2022-03 GTC（"最大的交换 ASIC"） | [可靠] |

**换算进我们框架**：整芯片 ~9.8 pJ/bit（500W/51.2T），与 TH5 同量级；Spectrum-4 的加密引擎（12.8T MACsec）说明真实交换机还有框架未建模的加密功耗项；BGA ~7700 脚对应 C4 信号池上限的实证量级（我们 C4Model 的 N_C4 应与它同量级才可信）。128×400G 是"组内 UCIe 化"时的 D 矩阵候选行。

---

## A10. Cisco Silicon One G100 [可靠]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 25.6 Tbps 全双工（可配成 fabric element） | [可靠] Cisco G100 datasheet |
| 端口×速率 | 支持 10/25/40/50/100/200/400/800/1600G 灵活端口（32×800G 整机） | [可靠] 同上 |
| SerDes | 256 × 112G（每 lane 独立可配 NRZ/PAM4） | [可靠] 同上 |
| TDP | 缺（datasheet 无绝对值；宣传"比 12.8T 方案省电至多 77%"） | [中等] Cisco 博客/Telecom Review |
| die 面积/工艺 | 缺 / 7nm | [可靠] datasheet |
| 架构 | P4 可编程 run-to-completion NPU，大共享包缓冲 | [可靠] |

**换算进我们框架**：G100 证明 25.6T 可以由 256 条 112G lane 实现（lane 数减半、速率翻倍 vs TH4 的 512×50G）——框架里 S_bw 的取值直接决定 lane 数与 bump 占用，这是"lane 速率 ↑ → bump 压力 ↓"链路的工业证据。

---

## A11. Cisco Silicon One Q200 / Q200L [待确认]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 25.6T（Q200）/ 12.8T（Q200L） | [待确认]（G100 datasheet 提到 Q200L 为前代，未给明细） |
| 端口×速率 | 32×800G / 64×400G | [待确认] |
| SerDes | 256 × 112G | [待确认] |
| TDP | 缺 | — |
| die 面积/工艺 | 缺 / 7nm | [待确认] |
| 发布 | Q200L 2020-02，Q200 2020-06 | [待确认] |

**换算进我们框架**：Q200 与 G100 同为 25.6T 但面向 DCI 路由；卡片数据薄弱，作为"25.6T 时代还有第三家供应商"的引用即可。

---

## A12. Marvell Teralynx 7（IVM77700）[中等]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 12.8 Tbps（6.4–12.8T 变体） | [中等] Marvell 产品页/媒体 |
| 端口×速率 | 32×400G 等 | [中等] |
| SerDes | 256 × 50G 量级 | [待确认] |
| TDP | 缺 | — |
| die 面积/工艺 | 缺 / 7nm | [待确认] |
| 出货 | >500 万 400G 端口（Cisco Nexus 3400-S 等） | [中等] Marvell |

**换算进我们框架**：Teralynx 7 以"最低确定性延迟 + P4 可编程"差异化——可编程管线对应框架里包处理延迟/缓冲建模的缺口（目前无缓冲约束）。

---

## A13. Marvell Teralynx 8（Innovium 时代）[中等]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 25.6 Tbps | [可靠] Innovium 2020-05 BusinessWire 新闻稿 |
| 端口×速率 | 32×800G / 64×400G / 128×200G / 256×100G | [可靠] 同上 |
| SerDes | 256 × 112G PAM4（首个 25.6T 用 112G 的芯片） | [可靠] 同上 |
| 片上缓冲 | 170MB（两最高 SKU） | [可靠] 同上 |
| die 面积/工艺 | 缺 / 7nm 单 die | [可靠] 新闻稿 |
| 收购 | 2021-08 Marvell 11 亿美元收购 Innovium | [可靠] NetworkWorld |

**换算进我们框架**：Teralynx 8 用 256×112G 而非 512×50G 达成 25.6T——lane 减半 → bump 占用减半，是我们"S_bw 与 bump 零和竞争"约束的直接工业佐证。

---

## A14. Marvell Teralynx 10（TX9180）[可靠/中等] ⭐

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 51.2 Tbps | [可靠] Marvell 官方博客（OFC 2025） |
| 端口×速率 | 32×1.6T / 64×800G / 128×400G | [可靠] 同上 |
| SerDes | 512 × 112G 长距（LR，最低 BER） | [可靠] 同上 |
| TDP | ~500W | [中等] TechInsights 拆解（64×800G 整机拆解） |
| 延迟 | ~500ns 端口间（可编程交换机最低） | [可靠] Marvell |
| die 面积/工艺 | 缺 / 5nm monolithic | [可靠] |
| 发布 | 2023-06 送样（"比 TL7 带宽 ×4"） | [可靠] |

**换算进我们框架**：与 TH5/Spectrum-4 并列 51.2T 三强——三家同容量但实现不同（512 lane 全部），说明 SerDes 供给在 51.2T 时代已标准化为 512×112G；框架里 51.2T 对应的 ℓ 向量（512 lane/64 端口 = 8 lane/端口）可直接作为 D 矩阵默认配置。

---

## A15. Intel Tofino 2 [中等]

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 12.8 Tbps（8.0/6.4T 变体） | [中等] Intel 产品页/DirectIndustry |
| 端口×速率 | 32×400G / 128×100G / 256×50G | [中等] 同上 |
| 转发速率 | 6 Bpps，64MB 包存储 | [中等] Intel |
| TDP | 缺（Intel 称与同速固定功能 ASIC 相同功耗） | [中等] |
| die 面积/工艺 | 缺 / 7nm；封装 71.5×66mm | [中等] |
| 架构 | **交换芯片首个 chiplet 设计**：模拟 SerDes chiplet + 逻辑 chiplet 分制（U/M/H 三 SKU） | [中等] Intel 架构资料 |

**换算进我们框架**：Tofino 2 是"交换芯片 chiplet 化"的首例——模拟/逻辑分 die 对应我们 die 级混合集成场景；其"分 die 无功耗/面积代价"的结论支持 wafer 级多 die 集成的可行性论证。

---

## A16. Intel Tofino 3 [待确认] ⚠️

| 字段 | 值 | 出处 |
|------|----|----|
| 总容量 | 25.6 Tbps | [待确认]（媒体转述） |
| 端口×速率 | 64×400G | [待确认] |
| TDP | 缺 | — |
| die 面积/工艺 | 缺 / 7nm | [待确认] |
| 状态 | **Intel 已退出 P4 交换机路线**（2023-01 停产公告），Tofino 3 未成主流 | [中等] 行业报道 |

**换算进我们框架**：作为"可编程交换机路线终结"的案例引用；数字可靠性低，不宜进定量对照表。

---

## 来源清单（A 组）

| 标题 | 来源 | 年份 | URL |
|------|------|------|-----|
| Broadcom Ships Tomahawk 3（12.8T） | Broadcom 官方新闻稿 [可靠] | 2018 | https://investors.broadcom.com/news-releases/news-release-details/broadcom-ships-tomahawkr-3-industrys-highest-bandwidth-0 |
| Broadcom Ships Tomahawk 4（25.6T） | Broadcom 官方新闻稿 [可靠] | 2019 | https://investors.broadcom.com/news-releases/news-release-details/broadcom-ships-tomahawk-4-industrys-highest-bandwidth-ethernet |
| Tomahawk5: 51.2Tb/s 5nm Monolithic Switch Chip（ISSCC 2025, pp.282–284） | IEEE 会议论文 [中等] | 2025 | https://ieeexplore.ieee.org/document/10904728 |
| Tomahawk 5 功耗讨论（EE Times） | EE Times Asia [中等] | 2022 | https://www.eetasia.com/express/tomahawk-5-switches-at-51-2tbps/ |
| Jericho3-AI（BCM88890）产品页 | Broadcom 官方 [可靠] | 2024 | https://www.broadcom.com/products/ethernet-connectivity/switching/stratadnx/bcm88890 |
| Jericho 系列对比表 | CSDN 博客（引用时降级为[中等]） | 2025 | https://blog.csdn.net/yelzinc/article/details/152799397 |
| NVIDIA Spectrum-4 ASIC datasheet | NVIDIA 官方 PDF [可靠] | 2023 | https://images.nvidia.cn/cn/networking/ethernet-switching/ethernet-switches-spectrum-4-asic-datasheet-CN.pdf |
| NVIDIA SN5600（Spectrum-4）datasheet | Dell 转 NVIDIA [可靠] | 2024 | https://www.delltechnologies.com/asset/de-de/products/networking/technical-support/nvidia-spectrum-sn5600-datasheet.pdf |
| Nvidia Debuts Spectrum-4（100B 晶体管、500W） | HPCwire / ZDNet [中等] | 2022 | https://www.hpcwire.com/2022/03/22/nvidia-debuts-spectrum-4-ethernet-platform-with-eyes-on-the-enterprise/ |
| Mellanox 51.2T Switch ASIC（88×88mm、7739 BGA） | 知乎专栏 [中等] | 2022 | https://zhuanlan.zhihu.com/p/616920053 |
| Cisco Silicon One G100 datasheet | Cisco 官方 [可靠] | 2021 | https://ciscolivewem.cisco.com/c/en/us/solutions/collateral/silicon-one/datasheet-c78-744833.html |
| Cisco Silicon One Easily Shatters the 25.6T Barrier | Cisco 官方博客 [可靠] | 2021 | https://blogs.cisco.com/sp/ciscociscosilicononeg100announcement |
| Innovium Teralynx 8（25.6T, 256×112G）新闻稿 | BusinessWire [可靠] | 2020 | https://www.businesswire.com/news/home/20200511005048/en/ |
| Marvell Switches On Teralynx 10 | TechInsights 拆解 [中等] | 2024 | https://www.techinsights.com/blog/marvell-switches-teralynx-10 |
| Introducing the 51.2T Teralynx 10 | Marvell 官方博客 [可靠] | 2025 | https://jp.marvell.com/blogs/51-2t-teralynx-10-industrys-lowest-latency-programmable-switch.html |
| Tofino 2 规格 | Intel / DirectIndustry [中等] | 2019 | https://www.directindustry.com/prod/intel/product-33710-2693388.html |
| NVIDIA Spectrum-3 SN4000 | NVIDIA 官方 [可靠] | 2022 | https://www.nvidia.com/en-eu/networking/sn4000/ |
