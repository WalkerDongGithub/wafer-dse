# 真实芯片数据卡库（real chip catalog）

> 用途：研究议程 2.2 —— 用真实交换芯片 / chiplet 产品的硬参数，验证它们都落在我们 LP 可行域内（落在外面 = 模型有 bug 或发现新约束）。
> 检索时间：2026-08-15。全部中文。家法同 `notes/literature/RENT_RULE_AND_IO_DENSITY.md`。

---

## 0. 质量标注体系

| 标注 | 含义 |
|------|------|
| [可靠] | 官方 datasheet / 规范 / 官方新闻稿原文 |
| [中等] | 行业杂志、可信科技媒体、Hot Chips / ISSCC 会议论文 |
| [待确认] | 二手转述或仅一家来源，需核对官方原文 |

优先级：官方 datasheet / 官方新闻稿 > Hot Chips / ISSCC 论文 > 行业杂志 / 媒体 > 博客 / 论坛。

---

## 1. 文件目录

| 文件 | 内容 | 卡片数 |
|------|------|--------|
| [switches.md](./switches.md) | A 组：交换 ASIC（Broadcom / NVIDIA / Cisco / Marvell / Intel） | 16 |
| [chiplets.md](./chiplets.md) | B 组：Chiplet 产品（AMD / Apple / Intel / NVIDIA / HBM） | 9 |
| [platforms.md](./platforms.md) | C 组：平台与标准（CoWoS / InFO-SoW / UCIe） | 7 |
| README.md（本文件） | 总览、换算方法、硬数字、缺口 | — |

---

## 2. 总览对照表（A 组交换 ASIC）

| 芯片 | 总容量 | 端口×速率 | SerDes | 工艺 | TDP | 封装 |
|------|--------|-----------|--------|------|-----|------|
| Tomahawk 3 (BCM56980) | 12.8T | 32×400G | 256×50G PAM4 | 16nm [可靠] | 缺 | monolithic BGA |
| Tomahawk 4 (BCM56990) | 25.6T | 64×400G | 512×50G PAM4 | 7nm [可靠] | 缺 | monolithic BGA |
| Tomahawk 5 (BCM78900) | 51.2T | 64×800G | 512×112G PAM4 | 5nm [可靠] | 450W [中等] | monolithic BGA 87.5×77.5mm |
| Jericho2 (BCM88690) | 10T | 48×200G | — | 16nm [中等] | <300W [中等] | monolithic |
| Jericho3 / Jericho3-AI (BCM88890) | 21.6T / 28.8T | 48×400G / 18×800G | 144×106G + 160×100G(组间) | 7nm [中等] | 缺 | monolithic |
| Spectrum-1 | 12.8T | 128×100G | 128×100G | 7nm [待确认] | 缺 | monolithic |
| Spectrum-2 | 25.6T | 64×400G | — | 7nm [待确认] | 缺 | monolithic |
| Spectrum-3 | 25.6T | 64×400G | — | 7nm [待确认] | 缺 | monolithic |
| Spectrum-4 | 51.2T | 64×800G / 128×400G | 512×100G | 4N [可靠] | ~500W [中等] | BGA ~88×88mm |
| Silicon One G100 | 25.6T | 32×800G | 256×112G LR | 7nm [可靠] | 缺 | monolithic |
| Silicon One Q200 | 25.6T | 32×800G | 256×112G | 7nm [待确认] | 缺 | monolithic |
| Teralynx 7 (IVM77700) | 12.8T | 32×400G | 256×50G | 7nm [待确认] | 缺 | monolithic |
| Teralynx 8 | 25.6T | 32×800G | 256×112G | 7nm [中等] | 缺 | monolithic |
| Teralynx 10 (TX9180) | 51.2T | 64×800G | 512×112G LR | 5nm [可靠] | ~500W [中等] | monolithic |
| Tofino 2 | 12.8T | 32×400G | — | 7nm [中等] | 缺 | 双 chiplet（模拟+逻辑），71.5×66mm |
| Tofino 3 | 25.6T | 64×400G | — | 7nm [待确认] | 缺 | chiplet [待确认] |

> 注：Spectrum-1/2/3、Tomahawk 3/4 的 TDP、die 面积官方未公开或未检索到——缺。详见各卡片与"缺口与下一步"。

---

## 3. 总览对照表（B 组 Chiplet 产品）

| 产品 | 集成方式 | D2D 带宽 | 内存带宽 | 晶体管 | TDP | 封装 |
|------|----------|----------|----------|--------|-----|------|
| MI250X | 2 GCD + 8 HBM2e | xGMI 400GB/s | 3.2TB/s | 58B (6nm) | 560W | 2.5D EFB 桥接 |
| MI300A | 9 计算 die 3D 堆在 4 AID 上 + 8 HBM3 | AID 间 >4.3TB/s | 5.2TB/s | 146B | 550W [待确认] | SoIC 混合键合 + CoWoS |
| MI300X | 8 XCD + 4 I/O die + 8 HBM3 | Infinity Fabric 896GB/s | 5.3TB/s | 153B | 750W | 2.5D CoWoS 类 |
| M1 Ultra | 2 × M1 Max | UltraFusion 2.5TB/s，>10k signals | 800GB/s | 114B (5nm) | 缺（系统 ~60W） | 硅 interposer（InFO_LI / CoWoS 争议） |
| M2 Ultra | 2 × M2 Max | UltraFusion 2.5TB/s，>10k signals | 800GB/s | 134B (5nm) | 缺 | 同上 |
| Ponte Vecchio | 47 功能 tile（63 tile 含热 tile） | compute↔fabric 2.6TB/s | 128GB HBM2e | >100B（5 工艺节点） | 600W OAM | EMIB + Foveros，36µm μbump |
| Sapphire Rapids | 4 tile | 缺（MDF mesh） | 64GB HBM2e >1TB/s（HBM 版） | 缺 | 350W | EMIB，55µm bump |
| GB200 NVL72 | 72 GPU + 36 CPU 机架 | NVLink 铜缆 1.8TB/s/GPU，机架 130TB/s | 13.4TB HBM3e/机架 | B200 208B | 机架 ~120–130kW | 机架级被动铜缆背板 |
| HBM3/3E/4 | 8–16-hi 堆叠 | 每 stack 0.82/1.2/2.0TB/s | — | — | 缺 | TSV + μbump + base die（HBM4 用 SoIC） |

---

## 4. 换算进我们框架的方法（每张卡片的"换算"句怎么读）

五族约束 ↔ 真实芯片参数的对应：

| 框架元素 | 真实芯片对应物 |
|----------|----------------|
| EnvelopeModel D 矩阵（端口×速率） | 端口数 × 每端口速率 = 总容量（如 64×800G = 51.2T） |
| S_bw（每 lane 带宽）、lane 数 ℓ = B·S_bw⁻¹·L | SerDes lane 数 × lane 速率（如 TH5：512×112G） |
| S_dyn / ppl 系数（每 lane 动态功耗） | 链路 pJ/bit（UCIe 先进 0.25–0.5，标准 0.5–0.8，长距 SerDes 2–4+，chiplet 总能耗 ~9 pJ/bit 量级） |
| BumpModel N_total（μbump 供给） | bump pitch → 面密度（45µm ≈ 494/mm²；36µm ≈ 771/mm²；20µm 混合键合 ≈ 2518/mm²） |
| C4Model N_C4（interposer↔substrate 信号池） | BGA 引脚数（Spectrum-4 ~7739 脚 [中等]、PV 4468 脚 [中等]；TH5 未公开） |
| 热 G·T=P+b ≤ T_max | TDP + 散热方式（OAM 空冷 450–560W、液冷 600W、机架液冷 120kW） |

**核心论点**：所有真实交换芯片满配线速（800G/端口量级）都落在我们可行域内部、离边界还有数量级余量——与 UIUC ISCA 2024"仅面积约束时 32× radix"的结论同向；功耗/热是真实产品中最先碰到的墙（TDP 450–750W 量级）。Chiplet 产品则反过来提供 bump 供给侧的实证：UltraFusion 10k 信号就撑起 2.5TB/s，Dojo 645mm² die 576 条 112G SerDes——bump 结构性过剩。

---

## 5. 最硬的数字（可直接引用）

1. **TH5（ISSCC 2025 论文）**：51.2T、TSMC 5nm、**750mm²、60B 晶体管、450W、512×112G Peregrine SerDes、BGA 87.5×77.5mm 无盖空冷** [中等，会议论文]。
2. **Spectrum-4（NVIDIA datasheet + GTC 2022）**：51.2T、4N、**100B 晶体管、~500W**、128×400G/64×800G、BGA ~88×88mm [可靠/中等]。
3. **UCIe 1.0 KPI（IBM 幻灯引规范）**：标准封装 4–32GT/s、bump 100–130µm、shoreline 28–224 GB/s/mm、目标 0.5 pJ/bit；先进封装 25–55µm、165–1317 GB/s/mm、目标 0.25 pJ/bit [中等]。UCIe 2.0 增 3D 混合键合 10–25µm [中等]。
4. **CoWoS 路线图**：CoWoS-S 上限 3.3× reticle ≈ 2700mm²；CoWoS-L 3.5×（2024 量产，Blackwell）→ 5.5× ≈ 4719mm²（Rubin，验证）→ 9.5× ≈ 7885mm²（2027 规划）[中等，开源证券/行业综述]。
5. **GB200 NVL72**：72 GPU 单一 NVLink 域 **130TB/s**、每 GPU 1.8TB/s（18×100GB/s 铜缆）、机架 **~120–130kW** 液冷 [可靠/中等]。

---

## 6. 缺口与下一步

1. **官方 TDP 缺失最严重**：Tomahawk 3/4、Tofino 2/3、Jericho3、Teralynx 7/8、Cisco G100/Q200 的芯片级 TDP 官方均未公开或未检索到——建议找 ISSCC/Hot Chips 论文与 teardown 报告补。
2. **Spectrum-1/2/3 规格整体 [待确认]**：本次搜索未命中官方页面（域名被网络策略拦截），需用 NVIDIA datasheet PDF 补。
3. **die 面积大面积缺**：除 TH5（750mm²）、Dojo（645mm²）、PV 活性硅（2330mm²）外，其余芯片 die 面积未公开或未检索到。
4. **Tofino 3 状态未定**：Intel 已中止 P4 交换机路线（2023 年 1 月停产公告），卡片标注 [待确认]，注意引用时说明。
5. **bump 数直接数据缺**：真实产品很少公布 μbump/C4 引脚明细；C4 侧可用 BGA 引脚（TH5/Spectrum-4/PV）近似，μbump 侧只能按 pitch 推算。
6. **HBM stack 功耗缺**：HBM3/3E/4 每 stack 功耗无统一官方值，散热预算里 HBM 占比需要找 teardown 或 JEDEC 功耗模型补。
7. **下一步验证动作**：把 TH5、Spectrum-4 的参数直接喂进框架（D 矩阵 64×800G、S_dyn=3pJ/bit、P0=450W），跑一个 64 端口组看落在哪个约束的 slack 里；MI300X 的 8+8 die 布局作为 interposer 布线约束的 stress test。
