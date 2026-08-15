# B 组：真实 Chiplet 产品数据卡

> 用途：Chiplet 集成产品的 D2D 带宽 / bump 密度 / 功耗实证，验证 BumpModel、C4Model 与热预算参数。
> 质量标注：[可靠] 官方 datasheet/新闻稿；[中等] 行业媒体/会议论文；[待确认] 需核对。

---

## B1. AMD Instinct MI250X（Aldebaran）[中等]

| 字段 | 值 | 出处 |
|------|----|----|
| 集成方式 | 2 GCD + 8 HBM2e，2.5D EFB（Elevated Fanout Bridge） | [中等] AMD/媒体拆解 |
| D2D 带宽 | xGMI（in-package Infinity Fabric）400 GB/s 双向 | [中等] AMD 文档/媒体 |
| 内存 | 128GB HBM2e（2×64GB），3.2TB/s，8192-bit | [可靠] AMD docs |
| 晶体管/工艺 | 58B / TSMC 6nm（双 die，各 110 CU） | [中等] TweakTown 图示 |
| TDP | 560W（OAM） | [可靠] AMD docs |
| 定位 | 首个量产多 die GPU（2021） | [中等] |

**换算进我们框架**：die↔die 的 xGMI 400GB/s = 3.2Tbps 走 EFB 桥（≈EMIB 类），是"组内 UCIe 桥接"的现实带宽锚点；560W OAM 空冷极限 = 我们热约束 T_max 在空冷场景的散热预算实证（~0.75W/mm² 量级 @ 750mm² die [待确认]）。

---

## B2. AMD Instinct MI300A [中等] ⭐ 3D 堆叠代表

| 字段 | 值 | 出处 |
|------|----|----|
| 集成方式 | 13 chiplets：9 个 5nm 计算 die（6 XCD + 3 CCD）+ 4 个 6nm AID 基底 die，SoIC 3D 混合键合（Cu TSV）堆叠 | [中等] AMD 技术发布/媒体 |
| D2D 带宽 | AID 间互联 >4.3TB/s；compute↔AID 3D 键合（TSV） | [中等] 媒体报道 |
| AID die | "Elk Range" ~370mm²，N6，含 64MB MALL cache/die | [中等] |
| 内存 | 128GB HBM3（8×16GB），5.2TB/s | [中等] |
| 晶体管 | 146B（5nm 计算 + 6nm I/O） | [中等] |
| TDP | 550W [待确认]（搜索未命中官方值；AMD 官方 OAM 档位） | [待确认] |
| 定位 | 世界首个 CPU+GPU 融合 APU（El Capitan 用） | [中等] |

**换算进我们框架**：这是商用硅片上最接近我们"3D 集成 wafer 场景"的产品——SoIC 混合键合 + 4 个基底 die 提供 >4.3TB/s 平面互连：4 AID 构成"主动 interposer"，正对应我们 interposer 布线/热网格的角色；146B 晶体管堆在 ~5000mm² 级封装面积上，功耗密度 ~0.1W/mm² 量级——热墙在 3D 场景的实证。

---

## B3. AMD Instinct MI300X [中等] ⭐ 2.5D 大 interposer 代表

| 字段 | 值 | 出处 |
|------|----|----|
| 集成方式 | 8 XCD（各 40 CU 设计/38 量产）+ 4 个 6nm I/O die（被动/主动基底）+ 8 HBM3 | [中等] AMD 发布/媒体 |
| D2D | Infinity Fabric 896 GB/s（die 间聚合） | [中等] |
| 内存 | 192GB HBM3（8×24GB 12-hi），5.3TB/s | [中等] |
| 晶体管 | 153B | [中等] |
| TDP | 750W TBP | [中等] Wikipedia/ROCm 文档 |
| 封装 | 2.5D 大 interposer（业界一致认为是 CoWoS 类，AMD 未点名） | [待确认] |
| 定位 | 对标 H100/H200 的 AI 训练/推理加速器（2023-12 发布） | [中等] |

**换算进我们框架**：8 计算 die + 4 I/O die + 8 HBM = 20 个 die 拼一个大 interposer——是我们 interposer 布线约束（R·x ≤ C）与 C4 池约束的真实 stress case；750W 整卡散热是当前商用最高功耗密度之一，直接对照我们散热预算的 rhs。

---

## B4. Apple M1 Ultra（UltraFusion）[可靠] ⭐ bump 供给实证

| 字段 | 值 | 出处 |
|------|----|----|
| 集成方式 | 2 × M1 Max die，硅 interposer 互联 | [可靠] Apple 官方新闻稿 |
| D2D | UltraFusion：**>10,000 信号，2.5TB/s** 低延迟 D2D | [可靠] Apple |
| 信号速率 | 推算 ~1Gbps/信号/方向（2.5TB/s ÷ 10k 信号 ÷ 2 方向） | [待确认]（自己推导） |
| 晶体管/工艺 | 114B / TSMC 5nm | [可靠] |
| 内存带宽 | 800GB/s（统一内存，128GB） | [可靠] |
| TDP | 缺（Mac Studio 系统级 ~60W [中等]，芯片级未公开） | [中等] |
| 封装技术争议 | InFO_LI（Tom Wassick 分析）vs CoWoS-S/L（IFTLE 分析） | [待确认] |

**换算进我们框架**：10k 信号就撑起 2.5TB/s（20Tbps 双向）——对照我们 12×12mm die @ 45µm ≈ 6.4 万 bump 的供给，信号 bump 需求只有供给的 ~1/6 量级：**bump 结构性过剩的直接工业证据**（支持 RENT_RULE_AND_IO_DENSITY.md 论断）。每信号 ~1Gbps 的并口 lane 速率对应框架 S_bw 的低端取值。

---

## B5. Apple M2 Ultra（UltraFusion 二代）[可靠]

| 字段 | 值 | 出处 |
|------|----|----|
| 集成方式 | 2 × M2 Max die，UltraFusion 硅 interposer | [可靠] Apple 官方新闻稿 |
| D2D | >10,000 信号，2.5TB/s（与 M1 Ultra 相同结构） | [可靠] |
| 晶体管/工艺 | 134B / 第二代 5nm | [可靠] |
| 内存 | 192GB 统一内存，800GB/s | [可靠] |
| TDP | 缺 | — |

**换算进我们框架**：两代 UltraFusion 参数一致 → D2D 互联技术 2.5TB/s/2-die 是稳定的工业锚点；带宽没随晶体管涨，说明 D2D 带宽受 interposer 面积/信号数约束而非晶体管数——框架里 N_total 与带宽解耦的建模方向正确。

---

## B6. Intel Ponte Vecchio [中等] ⭐ 混合封装极限案例

| 字段 | 值 | 出处 |
|------|----|----|
| 集成方式 | 47 功能 tile（+16 热 tile = 63 tile 总）：16 compute（TSMC N5）+ 8 RAMBO（Intel 7）+ 2 Foveros base（Intel 7，646mm²×2）+ 8 HBM2e + 2 XeLink SerDes tile（N7） | [中等] ISSCC 2022 / TechPowerUp |
| 封装 | EMIB（11 桥）+ Foveros 3D；compute tile 与 base die 间 **36µm pitch μbump** face-to-face | [中等] |
| D2D 带宽 | compute↔fabric 2.6TB/s；RAMBO cache 1.3TB/s | [中等] |
| 晶体管 | >100B，跨 5 个工艺节点 | [中等] |
| 硅面积 | 活性硅 2,330mm²（含热 tile 3,100mm²）；封装 77.5×62.5mm，4,468 脚 | [中等] |
| TDP | 600W OAM（液冷）；空冷上限 450W | [中等] |
| 发布 | 2022（Aurora 超算），现已退市 | [中等] |

**换算进我们框架**：36µm μbump → 密度 ~771/mm²（1/0.036²），介于我们 bump.py 的 45µm（494/mm²）与 25µm（1600/mm²）预设之间——参数选择合理。600W 需液冷：热约束在 >0.4W/mm²（600W/2330mm²≈0.26W/mm² 活性硅，但 tile 局部密度更高）后就必须水冷，是我们热模型"冷却方式 → q_max"分层的实证。47 tile 是最接近 wafer 级规模的商用集成。

---

## B7. Intel Sapphire Rapids [中等]

| 字段 | 值 | 出处 |
|------|----|----|
| 集成方式 | 4 tile（XCC），每 die 间 5 个 EMIB 桥，55µm bump pitch | [中等] Intel 架构日 2021 |
| D2D | 缺具体数字（MDF modular die fabric 承载 mesh 带宽） | — |
| 晶体管/工艺 | 缺 / Intel 7（10nm ESF） | [中等] |
| 内存 | 8 通道 DDR5；HBM 版（Xeon Max）64GB HBM2e，>1TB/s | [中等] |
| TDP | 350W（Platinum 旗舰，PL1） | [中等] WCCFTech |
| 封装面积 | 标准包 4,446mm²；HBM2e 包 5,700mm² | [中等] |

**换算进我们框架**：55µm EMIB bump 是"die 间桥接"密度下限的工业样本；D2D 带宽未公开 → 无法直接换算，但 SPR 证明 4-die EMIB 拼接在 350W 内可行——多 die 平面拼接的功耗预算锚点（我们组内 UCIe 场景可对照）。

---

## B8. NVIDIA GB200 NVL72 [可靠/中等] ⭐ 机架级铜缆

| 字段 | 值 | 出处 |
|------|----|----|
| 系统 | 72 × B200 GPU + 36 × Grace CPU，48U 液冷机架 | [可靠] NVIDIA 官方页 |
| NVLink 域 | 单域 72 GPU，聚合 **130TB/s**（1,296 端口 = 72 GPU × 18 链路） | [可靠/中等] NVIDIA + 拆解分析 |
| 每 GPU D2D | 1.8TB/s 双向（NVLink5，18 × 100GB/s 铜缆链路） | [可靠] |
| 背板 | 被动铜缆 twinax ~5,000 根手排；选铜缆省 ~20kW 光模块+SerDes 功耗 | [中等] nextpcb/分析 |
| NVSwitch | 18 颗（9 tray × 2），每颗 7.2TB/s / 144 端口 @ 50GB/s | [中等] |
| 机架功耗 | ~120–130kW（液冷强制） | [中等] |
| B200 die | 2 die 拼接（TSMC 4NP，共 208B 晶体管） | [中等] |

**换算进我们框架**：**铜缆 vs 光学省 20kW/机架** 是"SerDes/光学 pJ/bit 系数选择"的最强工业论据（~0.15 pJ/bit 量级差异 [待确认]）；机架 130TB/s ÷ 120kW ≈ 1.1 pJ/bit 全系统——比单芯片高 1 个数量级，因为含 PCB/背板/重驱动。它的 18 链路 × 100GB/s/GPU 结构对应我们 D 矩阵 + 组间 SerDes 通道的分层：GPU=组内 die，机架铜缆=组间链路。

---

## B9. HBM3 / HBM3E / HBM4 [中等] ⭐ 垂直 bump 供给

| 字段 | HBM3 | HBM3E | HBM4 | 出处 |
|------|------|-------|------|------|
| 每 stack 带宽 | 819 GB/s（6.4Gbps/pin，JEDEC 初版 665GB/s） | ~1.2TB/s（8–9.8Gbps/pin） | ~2.0TB/s（8Gbps/pin JEDEC 基线，2048-bit） | [中等] Wikipedia/业界 |
| 位宽 | 1024-bit（16 ch × 64） | 1024-bit | **2048-bit**（带宽靠加倍总线而非提速） | [中等] |
| 密度/堆高 | 16GB 8-hi / 24GB 12-hi（16Gb die） | 24GB 8-hi / 36GB 12-hi / 48GB 16-hi | 48GB 16-hi，后续 64GB | [中等] |
| 逻辑 base die | 无（JEDEC 标准） | 无 | **有**（5/3nm，SK hynix+TSMC，SoIC/混合键合集成） | [中等] |
| 量产 | 2022-06（SK hynix，H100 用） | 2024-03（SK hynix 首发） | 2025-12 送样（SK hynix，Rubin 用） | [中等] |
| 每 stack 功耗 | 缺（无统一官方值） | 缺 | 宣传比 HBM3E 低 20–30% | [中等] |

**换算进我们框架**：HBM 是"垂直 bump 供给"的极端案例——每 stack 1024–2048 数据通道 + 大量电源 bump 穿过 interposer，8 个 stack 在 MI300X/GB200 上占据 interposer 布线通道的很大份额；框架目前对 HBM 只隐含在 die 功耗里，**没有显式建模 HBM 通道的 bump/布线占用**——这是新约束候选（B* 可能被 HBM 布线反向挤压），列入缺口。

---

## 来源清单（B 组）

| 标题 | 来源 | 年份 | URL |
|------|------|------|-----|
| AMD Instinct MI250/MI250X 系统验收文档 | AMD 官方 docs [可靠] | 2023 | https://instinct.docs.amd.com/projects/system-acceptance/en/latest/gpus/mi250.html |
| AMD unveils MI250X MCM GPU diagram: 58B transistors, 6nm | TweakTown [中等] | 2023 | https://www.tweaktown.com/news/88075/amd-unveils-mi250x-mcm-gpu-diagram-58-billion-transistors-6nm-tsmc/index.html |
| AMD MI300X：192GB HBM3 @ 5.3TB/s | TweakTown / ServeTheHome / ROCm 博客 [中等] | 2023 | https://www.tweaktown.com/news/94795/... https://www.servethehome.com/amd-instinct-mi300x-gpu-and-mi300a-apus-launched-for-ai-era/ |
| AMD Instinct 维基（153B、750W、8 XCD） | Wikipedia [中等] | 2024 | https://en.wikipedia.org/wiki/AMD_Instinct |
| Apple unveils M1 Ultra | Apple 官方新闻稿 [可靠] | 2022 | https://www.apple.com/newsroom/2022/03/apple-unveils-m1-ultra/ |
| Apple introduces M2 Ultra | Apple 官方新闻稿 [可靠] | 2023 | https://www.apple.com/newsroom/2023/06/apple-introduces-m2-ultra/ |
| IFTLE 518: Apple M1 UltraFusion Technology | IMAPS 3D InCites [中等] | 2022 | https://www.3dincites.com/2022/04/iftle-518-apple-m1-ultrafusion-technology/ |
| M1 Ultra 用 InFO_LI 而非 CoWoS（Tom Wassick 分析） | 网易转载 [中等] | 2022 | https://www.163.com/dy/article/H64DNSD305118EDB.html |
| Intel Details Ponte Vecchio: 63 Tiles, 600W（ISSCC 2022） | TechPowerUp [中等] | 2022 | https://www.techpowerup.com/292250/intel-details-ponte-vecchio-accelerator-63-tiles-600-watt-tdp-and-lots-of-bandwidth |
| Ponte Vecchio 使用五个工艺节点 | EENews Europe [中等] | 2022 | https://www.eenewseurope.com/en/ponte-vecchio-3d-supercomputer-processor-uses-five-process-nodes/ |
| Sapphire Rapids 四 tile MCM 标注图 | TechPowerUp [中等] | 2022 | https://www.techpowerup.com/292204/intel-sapphire-rapids-xeon-4-tile-mcm-annotated |
| Sapphire Rapids-SP 规格（350W、HBM 版 5700mm²） | WCCFTech [中等] | 2022 | https://wccftech.com/intel-sapphire-rapids-sp-xeon-cpu-lineup-detailed-platinum-hbm-variants-over-350w-tdp-c740-chipset/ |
| Intel Details Sapphire Rapids（架构日 2021） | ServeTheHome [中等] | 2021 | https://www.servethehome.com/intel-details-sapphire-rapids-xeon-at-architecture-day-2021/ |
| NVIDIA GB200 NVL72 | NVIDIA 官方页 [可靠] | 2024 | https://www.nvidia.com/zh-tw/data-center/gb200-nvl72/ |
| GB200 NVL72: PCB & System Architecture Explained（铜缆 5000 根、省 20kW） | nextpcb [中等] | 2024 | https://jp.nextpcb.com/blog/nvidia-gb200-nvl72-architecture |
| High Bandwidth Memory（HBM3/4 规格） | Wikipedia [中等] | 2025 | https://en.wikipedia.org/wiki/High_Bandwidth_Memory |
| HBM Pricing & Specifications | SiliconAnalysts [中等] | 2026 | https://siliconanalysts.com/data/hbm-pricing |
| HBM 三厂进展对比 | PConline [中等] | 2024 | https://g.pconline.com.cn/x/1754/17548488.html |
