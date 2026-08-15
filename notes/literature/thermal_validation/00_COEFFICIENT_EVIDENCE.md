# 00 热模型系数 → 权威原文证据链

> 用途：把 LP 热模型里每个**实际生效的物理系数**，逐条锚定到一手权威文献（原始论文 / 官方标准 / 官方 datasheet），做到「下载原文后能按页码/图表号直接对照」。
> 检索时间：2026-08-15。家法：`notes/literature/RENT_RULE_AND_IO_DENSITY.md`（[可靠]/[中等]/[待确认]）。
>
> **与 01–05 的关系**：01–05 是主题卡片（材料、ASIC、冷却），本文件是「系数」维度的对账表——每行回答一个问题：**代码里这个数，最权威的原文是哪个？原文怎么说的？我们取的是保守还是乐观？**

---

## 0. 系数总览（代码 → 权威锚 → 判定）

| # | 系数 | 代码位置 | 代码值 | 权威锚 | 判定 |
|---|------|---------|--------|--------|------|
| 1 | `R_vert` | `ThermalParams.r_vert_k_per_w` | 1.0(TOY)/1.5(UCIE)/2.0(默认) | TH5 液冷论文全堆叠 ~0.09 K/W；HIR 高效风冷 0.8°C·cm²/W | 保守 ~4× |
| 2 | `k_interposer` | `ThermalParams.k_interposer` | 100(TOY)/150(UCIE) | Glassbrenner & Slack 1964 室温 130 W/m·K | 吻合（略偏乐观，非主导项） |
| 3 | `t_interposer` | `ThermalParams.t_interposer_mm` | 0.1 mm | TSMC/ECTC 2011 官方 100 μm | 完全吻合 |
| 4 | `T_ambient` | `ThermalParams.t_ambient_k` | 300 K = 27°C | ASHRAE TC9.9 推荐 18–27°C / A4 允许 45°C | 推荐上沿；**唯一不保守输入** |
| 5 | `T_max` | `ThermalParams.t_max_k` | 400(TOY)/358.15K=85°C | TH5 真实 Tj_max 105°C；TI 105°C=10年寿命 | 保守 20°C |
| 6 | 冷却四档 | `CoolingSolution` | 0.5/2.0/5.0/10.0 W/mm² | HIR 风冷 40–53 W/cm²；微通道演示 400–700 W/cm² | Air 贴边；其余=演示上限 |
| 7 | `ΔT_max` | `WarpModel.delta_T_max` | 10 K | 无直接权威数字（翘曲已移出主约束） | 缺口，见 §7 |

---

## 1. R_vert（单 die 垂直热阻，K/W）

**代码**：`src/physical/params.py` 的 `ThermalParams.r_vert_k_per_w`；`src/lp/models/phys/therm/network/_mfit_system.py` 默认 2.0（注释 1.5–3.0）。

**权威锚 A — TH5 液冷论文（最强锚）**
- 出处：Fan, Xiao, Liu. "The Study of Liquid Cooling Solution on 51.2T Switch." *2024 23rd IEEE Intersociety Conference on Thermal and Thermomechanical Phenomena in Electronic Systems (ITherm)*, DOI: [10.1109/ITherm55375.2024.10709537](https://doi.org/10.1109/ITherm55375.2024.10709537)
- 原文摘要原句（可对照）：
  > "Thermal design power of the latest generation 51.2T ASIC called Tomahawk 5 (TH5) from Broadcom is up to **763W**. The required thermal performance for air-cooled heat sink represented by Rca should be within **0.05°C/W** to maintain **105°C** of maximum junction limit..."
- 反推（论文内对账用）：结→环境总热阻 ≈ (105 − 35)/763 ≈ **0.09 K/W**（设进风 35°C，TH5 die ~800mm²）。
- 状态：**摘要级已确认**（Semantic Scholar + IEEE 双源一致）。页码/图表号需下载原文核对。

**权威锚 B — HIR 2021 高效风冷模块**
- 出处：HIR 2021, Chapter 20 Thermal Management, IEEE EPS.
- 数值：高效风冷模块单位面积热阻基准 **0.8 °C·cm²/W**（结→环境）→ 144mm² die 换算 ≈ **0.56 K/W**。
- 状态：[待确认] 原文 PDF 被网络策略拦截，需下载核对页码。

**判定**：默认 2.0 K/W vs 实测 ~0.5–0.56 K/W → **保守 ~4×**，温度是真实芯片的稳定上界。

---

## 2. k_interposer（interposer 面内热导率，W/(m·K)）

**代码**：`ThermalParams.k_interposer`（TOY=100，UCIE=150）。

**权威锚 — 硅热导率原始实测文献**
- 出处：Glassbrenner, C. J.; Slack, G. A. "Thermal Conductivity of Silicon and Germanium from 3K to the Melting Point." *Physical Review* **134**, A1058–A1069 (1964), DOI: [10.1103/PhysRev.134.A1058](https://doi.org/10.1103/PhysRev.134.A1058)
- 权威数值（Ioffe NSM 数据库 `ioffe.ru/SVA/NSM/Semicond/Si/thermal.html` 引用 G&S 1964 的温度依赖曲线）：
  > "Thermal conductivity | **1.3 W cm⁻¹ °C⁻¹**"（= **130 W/(m·K)**，室温）
- 交叉印证：MIT *Phys. Rev. B* 93, 035408 (2016) 给 bulk Si 室温 ≈ **143 W/(m·K)**；HotSpot 源码默认 **130 W/(m·K)**。
- 状态：[可靠]（原始文献 + 权威数据库 + 仿真工具默认值三方一致）。

**判定**：150 与权威 130–143 同量级，**吻合**。横向路径在热网络里非主导（interposer 仅 0.1mm 厚），此值略偏乐观不影响主结论。

---

## 3. t_interposer（interposer 厚度，mm）

**代码**：`ThermalParams.t_interposer_mm`（所有参数组 = 0.1）。

**权威锚 — TSMC 官方一手来源**
- 出处：Banijamali, Ramalingam, Nagarajan, Chaware. "Advanced Reliability Study of TSV Interposers and Interconnects for the 28nm Technology FPGA." *IEEE ECTC 2011*.（TSMC 官方研究页 `research.tsmc.com` 收录）
- 原文摘要原句（可对照）：
  > "The silicon interposer is **100um thick**, and is mounted on a 42.5mm×42.5mm substrate through **180um pitch C4 bumps**... micro-bumps at **45um pitch**."
- 补充：TSMC VLSI 2012《An ultra-thin interposer utilizing 3D TSV technology》另演示了 50 μm 超薄 interposer（极限值，非主流）。
- 状态：[可靠]（TSMC 官方收录 + IEEE 原文摘要）。

**判定**：0.1 mm = 100 μm 与 TSMC 官方 100 μm **完全吻合**；顺带印证了 `UBUMP_45UM`（45 μm μbump）与 C4 pitch 的物理合理性。

---

## 4. T_ambient（环境温度，K）

**代码**：`ThermalParams.t_ambient_k`（所有参数组 = 300 K = 27°C）。

**权威锚 — ASHRAE TC 9.9 官方热指南**
- 出处：ASHRAE TC 9.9, *Thermal Guidelines for Data Processing Environments*, 第 5 版 (2021)。（白皮书 PDF：`ashrae.org/File Library/Technical Resources/Bookstore/ASHRAE_TC0909_Power_White_Paper_22_June_2016_REVISED.pdf`）
- 权威数值（多源一致）：
  - **推荐范围 18–27°C**（A1–A4 全部等级一致，长期运行目标）
  - **允许范围**：A1 15–32°C … A4 **5–45°C**（短期容忍）
- 状态：[可靠]（官方标准，第 5 版 2021）。

**判定**：27°C = 推荐范围上沿。但 A4 允许到 45°C —— **这是全热模型唯一不保守的输入**。论文里应报 27°C 与 45°C 两档，让「稳定上界」无懈可击。

---

## 5. T_max（结温上限，K）

**代码**：`ThermalParams.t_max_k`（TOY=400，UCIE=358.15 K = 85°C）；`_config.py` 的 `T_JUNCTION_MAX_K = 273.15 + 85.0`，注释「结温上限 85°C (翘曲约束)」。

**权威锚 — 真实交换 ASIC 结温上限**
- 出处 A（TH5）：同上 §1 的 ITherm 2024 论文——「...to maintain **105°C** of maximum junction limit」。
- 出处 B（EM 寿命，TI 官方）：TI app note `sprabx4a`（`ti.com/lit/an/sprabx4a/sprabx4a.pdf`）——105°C 结温 = 10 年寿命设计基准；加速因子表 110°C→0.50、115°C→0.40、120°C→0.30、125°C→0.20。
- 出处 C（器件规范典型）：Microchip SAM9X75 datasheet Table 10-1——`T_J_MPU` 上限 **125°C**（工业级器件 Tj_max 规范的代表值）。
- 物理定律：Black 方程 `MTTF ∝ exp(Ea/kTj)`，每 +10°C 寿命约减半。

**判定**：85°C 比真实 Tj_max 105°C **保守 20°C**（比器件规范 125°C 保守 40°C）。**诚实注记**：代码里「85°C = 翘曲约束」这个数字本身没有直接的一手权威出处——它是建模者的保守设定；翘曲文献（§7）只给应力/变形趋势、不给「允许温差/允许温度」规范值。对标链应为「真实 Tj_max=105°C → 我们取 85°C 更紧」，而非「85°C 是翘曲硬阈值」。

---

## 6. 冷却四档（散热密度上限，W/mm²）

**代码**：`src/physical/thermal/_cooling.py` —— Air 0.5 / Liquid 2.0 / Immersion 5.0 / Microfluidic 10.0（单位 W/mm²）。

| 档位 | 代码值 W/mm² | = W/cm² | 权威边界 | 出处 | 判定 |
|------|-------------|---------|---------|------|------|
| Air | 0.5 | 50 | 风冷实际极限 40–53 W/cm² | HIR 2021 Ch20 [待确认] | 贴边（=实际极限上沿） |
| Liquid | 2.0 | 200 | 冷板典型 50–150；微通道演示 400 | ITherm/综述 [中等] | 偏乐观（演示上限） |
| Immersion | 5.0 | 500 | 嵌入式微通道演示 400–700 | pEMMC/ECS [可靠] | 研究级演示，非量产浸没 |
| Microfluidic | 10.0 | 1000 | AI 热点投影 >1000 | MDPI 综述 [中等] | 前沿研究值 |

**关键出处**：HIR 2021 Ch20 Thermal Management（`eps.ieee.org/images/files/HIR_2021/ch20_thermal1.pdf`）——风冷 40–53 W/cm² 是**待下载原文核对页码**的核心数字。

**判定**：Air 档（0.5 W/mm² = 50 W/cm²）与 HIR 实际风冷极限上沿对齐，是论文「风冷可实现性」的最硬论据；Liquid/Immersion/Microfluidic 三档名字与实际能力错位，论文中须明示「取该技术文献演示上限」。

---

## 7. ΔT_max（邻接 die 温差，K）——缺口

**代码**：`src/lp/models/phys/therm/_warp_limit.py` 的 `delta_T_max = 10.0`（默认参数）。

**状态**：翘曲约束已在 V4 移出主约束集（见 `README.md`「约束集」与 `archive/MATH_MODEL_COMPLETE_V3.md` §3.5），代码保留作技术记录。

**缺口**：搜索未找到「允许 die 间温差」的一手规范值。现有翘曲文献（Li et al. *ACES-China 2024*, DOI 10.1109/ACES-China62474.2024.10699555；Liu et al. *ECTC 2015*, DOI 10.1109/ECTC.2015.7159797）均把翘曲当**优化目标**（厚度/钝化膜/应力调谐），不给「允许温差」规范数字。若要补，候选方向：JEDEC 或封装厂翘曲规范（warpage spec ≤50–100 μm 级，有逆推空间）。

---

## 8. 待下载清单（请按需下载后回填页码）

> 排序 = 对论文结论的杠杆作用。下载后把「页码/图表号」回填进本表，即升级为可引用。

| 优先级 | 完整原文题名（可直接搜索下载） | 出处 | 需要核对的数字 | 当前缺口 |
|--------|------|---------|---------------|---------|
| ★★★ | **Heterogeneous Integration Roadmap, 2021 Edition — Chapter 20: Thermal Management** | IEEE Electronics Packaging Society | 40–53 W/cm²（风冷实际极限）、0.8 °C·cm²/W（高效风冷模块热阻） | 页码/图表号 |
| ★★★ | **The Study of Liquid Cooling Solution on 51.2T Switch** | Fan, Xiao, Liu, ITherm 2024, DOI 10.1109/ITherm55375.2024.10709537 | 763W / 105°C / Rca 0.05°C/W 的确切页与图 | 页码（当前只有摘要） |
| ★★ | **Thermal Conductivity of Silicon and Germanium from 3°K to the Melting Point** | Glassbrenner & Slack, Phys. Rev. 134, A1058, 1964, DOI 10.1103/PhysRev.134.A1058 | 室温 130 W/m·K 的温度曲线 | 曲线图号（数值已由 Ioffe NSM 转引确认） |
| ★★ | **Advanced Reliability Study of TSV Interposers and Interconnects for the 28nm Technology FPGA** | Banijamali et al., ECTC 2011, IEEE doc 5898527 | 100 μm interposer + 45 μm μbump + 180 μm C4 | 图号（摘要已确认） |
| ★ | TI Application Report **sprabx4a**（无正式标题，按编号下载） | Texas Instruments | 105°C=10年 + 加速因子表 | 页码（数值已有） |
| ★ | **Data Center Power Equipment Thermal Guidelines and Best Practices** | ASHRAE TC 9.9 Whitepaper, 2016 | 18–27°C 推荐 / A4 45°C | 页码（数值已确认） |

---

## 9. 引用纪律

1. 进论文前，所有 [待确认]/[待下载] 数字必须下载原文、核对页码后升级为 [可靠]。
2. 「负面 claim」（如 T_max=85°C 无直接翘曲出处、Liquid 档偏乐观）须如实声明，不得包装成权威。
3. 数字一律带单位 + DOI + 可定位页码/图表号；原始论文 > 官方 datasheet > 权威数据库 > 综述 > 媒体。
