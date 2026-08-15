# 00 交换 die 带宽–面积–功耗 scaling 证据链

> 用途：回答「交换 die 的带宽 B、面积 A、功耗 P 之间是什么关系？线性还是超线性？能否写成表达式？」
> 检索时间：2026-08-15。质量家法：`notes/literature/RENT_RULE_AND_IO_DENSITY.md`。

---

## 0. 一句话结论

**分层，不是单一幂律：**

- **I/O / SerDes 部分：严格线性** —— `P_IO = p_IO · B`（p_IO ≈ 2 pJ/bit），`A_IO ∝ B`。
- **交换核心（crossbar / 调度器）部分：超线性（平方）** —— 面积与功耗都 `∝ N²`（N = radix/端口数），等价于 `∝ B²`（同速率下）。
- **总功耗/总面积 = 线性项 + 二次项**；radix 小时线性项主导，radix 大时二次项主导——这就是「功耗随 radix 超线性」的物理根源。

---

## 1. 权威论断

### 1.1 功耗随 radix 超线性（直接命中）

- 出处：Chen, Pal, Kumar. "Waferscale Network Switches." *ISCA 2024*, DOI [10.1109/ISCA59077.2024.00025](https://doi.org/10.1109/ISCA59077.2024.00025)；扩展版 UIUC MS thesis 2025（[ideals PDF](https://www.ideals.illinois.edu/items/136269/bitstreams/445395/data.pdf)）；IEEE Micro 45(4), 2025, pp. 37–43（Top Picks），DOI [10.1109/MM.2025.3589927](https://doi.org/10.1109/MM.2025.3589927)。
- 原文（thesis §1，可对照）：
  > "we replace some of the SSCs in the Clos with lower-radix SSCs. This can lead to significant power reduction since **the power of an SSC decreases superlinearly with its radix**."
- 原文（thesis §1，面积/radix 增长受限）：
  > "network switch radix has not seen much growth ... the maximum radix has increased only by 8x over the last 12 years ... due to poor scaling of off-chip IO pitches ... as well as poor scaling of switch die sizes. Switch die sizes scale even slower, since the maximum chip size is dictated by reticle limits ... does not exceed 858 mm² [at 5nm]."
- **决定性量化证据**（ISCA 2024 论文 §V-B，Figure 15）：
  > "We observed that various commodity high-radix switches show **super-linear (near quadratic) scaling of normalized power consumption with respect to the switch radix**. Figure 15 shows the normalized reported consumption of various radix switches from Broadcom Tomahawk series [13] and Marvell TeraLynx series [1] ... The scaling **tracks well the quadratic scaling suggested by Ahn et al. [19]** for both monolithic crossbars and hierarchical crossbars."
  - Figure 15 题注：「Reported power consumption of Tomahawk series (TH-1, TH-3, TH-4, TH-5) and TeraLynx series (TeraLynx-7, 8, 10), **normalized to 5nm process node (only non-IO power is shown)**. Theoretical quadratic power scaling models for both series are shown as well.」
  - 关键推论（原文）：「the total power consumption of **two radix-k/2 switches will be lower than a single radix-k switch**」——这是超线性的直接推论，也是 heterogeneous switch 省电 30.8% 的根据。
- 状态：[可靠]（ISCA 2024 + IEEE Micro Top Picks 双背书；PDF 已归档 `architecture_cases/Chen_Pal_Kumar_ISCA2024_Waferscale_Network_Switches.pdf`）。

### 1.2 crossbar 面积/复杂度 ∝ N²（平方）

| 出处 | 原文 | 状态 |
|------|------|------|
| EDN (Arteris), de Lescure 2021 | "the crossbar architecture, which **scales in a quadratic way**, would become impractical and overdesigned" | [中等] 行业技术文 |
| TeraNoC, arXiv:2508.02446 (ETH Zürich, 2025) | "crossbars ... their **routing complexity grows quadratically with the number of I/Os**" | [可靠] 学术论文 |
| Rent's rule 笔记 §1 | "crossbar 复杂度 ~O(N²)（内部逻辑），I/O 需求 ~O(N)（端口数）" | [可靠] 见 RENT_RULE_AND_IO_DENSITY.md |

### 1.3 现代交换机用 shared-buffer 缓解平方项

Broadcom TH3/TH4/TH5 官方口径均为「shared-buffer architecture」（64MB/160MB on-chip buffer）——这不是纯 crossbar，面积/功耗的二次项被 shared-buffer + 多 pipeline 摊薄，但仍未消除（否则 Chen 不会观察到 superlinear）。

### 1.4 quadratic scaling 的理论出处（两篇均已下载核对）

**Ahn, Choo, Kim. "Network within a network approach to create a scalable high-radix router microarchitecture." HPCA 2012, pp. 1–12** —— quadratic 的物理根源：
- 单 crossbar 有 **k² 个 crosspoint**，只有 k 个 active，其余 k²−k 个只耗静态功耗：
  > "in a canonical crossbar, only k out of k² crosspoints are active and the remaining k²−k ones consume static power only ... static power consumption is more important for high-radix routers"
- allocation 复杂度 ∝ k²：
  > "the canonical router microarchitecture ... scales poorly with the router radix (k) as the complexity of the allocation is proportional to k²"
- 面积 / crosspoints ∝ k²（folded-Clos / torus / HyperX 均如此）：
  > "both switch area and the number of crosspoints are proportional to k²"
- PDF：`architecture_cases/Ahn_Choo_Kim_HPCA2012_Network_within_a_network.pdf`

**Stillmaker & Baas. "Scaling equations for the accurate prediction of CMOS device performance from 180 nm to 7 nm." Integration, vol. 58, pp. 74–81, 2017** —— 跨工艺节点归一化：
- 用 HSpice（PTM + ITRS 模型）对 delay/energy/power 拟合二阶/三阶多项式，R² > 0.95；修正 Dennard scaling 在深亚微米的失效。
- Chen Figure 15 用它把 TH-1→TH-5、TeraLynx-7→10 的功耗统一归一化到 5nm，才得到可比的 quadratic 曲线。
- PDF：`textbooks/Stillmaker_Baas_Integration2017_CMOS_Scaling_Equations.pdf`

---

## 2. 表达式（α=2，有权威数据背书）

设 N = radix（双向端口数），r = 每端口速率（Gbps），总带宽 `B = N·r`。

### 功耗

```
P(B) = p_IO · B  +  p_core · (B/r)²
       └─ 线性项 ─┘   └── 超线性(平方)项 ──┘
```

- `p_IO`：I/O 能耗，≈ **2 pJ/bit**（Chen thesis 对 TH5 的假设，见 §3）
- `p_core`：核心调度/缓冲功耗系数（W/port²），需数据拟合

### 面积

```
A(B) = a_IO · (B/r)  +  a_core · (B/r)²
       └─ SerDes+bump ─┘  └─ crossbar/缓冲 ─┘
```

- 受硬上限：`A ≤ 858 mm²`（5nm reticle，Chen thesis 引 [53]）

### 等价形式（radix 视角，Chen 论文的口径）

```
P(N) = p_IO·r·N  +  p_core·N²
A(N) = a_IO·N   +  a_core·N²
```

---

## 3. 数据锚点（TH5，唯一面积+功耗都齐全的点）

Chen thesis Table 1.2（TH5 参数）：

| 量 | 值 |
|----|----|
| 总带宽 B | 51.2 Tbps（256×200G / 128×400G / 64×800G） |
| 总功耗 P | **500 W** |
| 非 I/O 功耗（核心） | **400 W** |
| I/O 功耗 | **100 W**（= 2 pJ/bit × 51.2T） |
| 面积 A | **800 mm²** |

由 TH5 反推系数：

```
p_IO  = 100 W / 51.2 Tbps = 1.95 pJ/bit ≈ 2 pJ/bit
p_core = 400 W / 256² = 0.0061 W/port²   (N=256, r=200G)
```

> 注：ISSCC 2025 口径 TH5 为 450W/750mm²，Chen 口径 500W/800mm²——差异在 I/O 能耗假设与面积口径，引用时标注来源。

### 超线性的自洽验证（用 TH5 系数外推）

- radix 减半（256→128，B 减半到 25.6T，同 r）：
  `P = 2pJ/bit·25.6T + 0.0061·128² = 50W + 100W = 150W` → 带宽减半，功耗降到 **30%**（<50%，超线性下降）
- radix 翻倍（256→512，B 翻倍到 102.4T）：
  `P = 2pJ/bit·102.4T + 0.0061·512² = 200W + 1600W = 1800W` → 带宽翻倍，功耗 **×3.6**（超线性增长，功耗墙）

这正是 Chen 论文「radix 受功耗密度限制」的量化来源，也是本项目「单 die 交换机有功耗墙，需 wafer-scale」的核心论据。

---

## 4. 超线性的意义：LP → 凸优化（论文卖点，非缺陷）

代码 [params.py](file:///home/walker/wafer-dse/src/physical/params.py) 当前功耗模型是纯线性（`P0 + Σ lane·power_per_lane`），对应**线性规划（LP）**。

但 §1–§3 的证据表明真实关系是 quadratic（超线性）：`P_core ∝ N²`。

**含义**：要把二次项纳入模型，问题就从 LP 升级为**凸二次规划 / 凸优化**——这**不是**模型的缺陷，恰恰是**优化模型必要性的论据**：

- 若功耗对带宽是纯线性，LP 是平凡的（trivial），没有「瓶颈演化」「约束交换率」这些非平凡结构可讨论。
- 超线性（凸）让「radix 越大、单位带宽的功耗代价越陡」成为模型的**内生权衡**——正是研究议程 `plan_research_agenda.md` §3.2「线性化放宽的凸性讨论」要抓的点：牺牲线性性换更准的物理，且仍在凸优化范畴内。

**结论**：`p_core·N²` 项不应视为「代码缺失」，而应视为「论文要论证的凸性来源」。数据侧的任务是把 `p_IO`/`p_core`/α 校准出来（见 §3、§5），而非急着改求解器。

---

## 5. 缺口与下一步

1. **面积系数 `a_core` 无法拟合**：TH3/TH4 die 面积官方未公开（TechInsights 有 BCM56980 floorplan 报告 DFR-1907-803，付费），只有 TH5 一个点。候选：找 ISSCC/HotChips 论文的 die shot 尺寸，或 TechInsights 拆解报告。
2. **`p_core` 系数需 2 个以上 radix 点校准**：TH5（256, 400W core）是唯一锚点；若拿到 TH4（128, 核心功耗）或 TH3（64）即可拟合 `p_core·N²` 的指数（α 是否真等于 2，还是 1.5 之类）。
3. **是否真的 α=2 待验证**：shared-buffer 架构可能把二次降为 `N^1.5` 或 `N·logN`。需要 ≥3 个不同 radix 的（B, P, A）三元组才能判 α。
4. **校准数据是当前主线**：把 §3 的系数锚点扩展到多 radix 数据点（见 §6 待下载），确定 α 与 `p_core` 的可信区间；求解器是否凸化是后置议题（见 §4）。

## 6. 待下载（用户可帮忙）

> ✅ 已下载归档：Chen ISCA 2024（`architecture_cases/Chen_Pal_Kumar_ISCA2024_Waferscale_Network_Switches.pdf`）、Ahn HPCA 2012（`architecture_cases/Ahn_Choo_Kim_HPCA2012_Network_within_a_network.pdf`）、Stillmaker & Baas 2017（`textbooks/Stillmaker_Baas_Integration2017_CMOS_Scaling_Equations.pdf`）。

| 完整原文题名（可直接搜索下载） | 出处 | 需要核对 | 说明 |
|------|------|---------|------|
| **Waferscale Network Switches**（UIUC MS Thesis 2025 扩展版） | Shuangliang (David) Chen, University of Illinois Urbana-Champaign, 2025 | Figure 15 的具体数据点坐标（7 个芯片的 radix/功耗数值） | UIUC ideals 开放 PDF 可下；比论文版多 power model 推导 |
| **Broadcom BCM56980 StrataXGS Tomahawk 3 TSMC 16FFC FinFET Process Digital Floorplan Analysis** | TechInsights, report DFR-1907-803 | TH3 die 面积 | 付费，唯一已知 TH3 面积来源 |
