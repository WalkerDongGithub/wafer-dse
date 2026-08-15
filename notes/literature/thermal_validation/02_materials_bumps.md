# 02 材料热导率与 μbump/TSV 热阻

> 断言：热网络的垂直路径由 TIM/underfill/μbump 主导（材料热导率差硅两个数量级），横向路径由硅 interposer 主导。μbump 阵列是垂直路径的定量瓶颈，有实测数据。

## 1. 体材料热导率

| 材料 | k [W/(m·K)] | 出处 | 状态 |
|---|---|---|---|
| 硅（体） | 125–150 | 教材通用值；HotSpot 默认 **130** | [可靠] |
| 铜 | 390–400 | 教材通用值 | [可靠] |
| 银 | ~429 | 导热填料参考 | [可靠] |
| AlN（陶瓷） | ~170–321 | 刚性 TIM / 填料 | [可靠] |
| 焊料（SnPb 系） | 18–24 | Matsumoto SEMI-THERM 2014（实测，200μm pitch Pb97Sn3） | [可靠] |
| TIM 硅脂（常规） | 1–7 | 多源一致 | [可靠] |
| 液态金属 TIM（Cu 纳米簇增强） | ~65 | IEEE 9501784 | [中等] |
| 聚合物 thermal pad | 0.8–17 | 行业多源 | [中等] |
| underfill（环氧系常规） | **0.4–2** | 多源一致（含 SEMI-THERM 2014） | [可靠] |
| 高导热 underfill（BN 填充） | 2.6（演示） | Matsumoto SEMI-THERM 2014 | [可靠] |
| 空气 | 0.026 | 教材 | [可靠] |

**规律**：硅/铜差 2.5–3×；TIM/underfill 比硅低 **1–2 个数量级**——所以垂直堆叠里"界面层"（TIM、underfill+μbump）贡献大部分热阻，体硅/铜不是瓶颈。

**为什么可信**：硅/铜/焊料为教科书常数；underfill 0.4–2 W/mK 在 SEMI-THERM 2014 与综述文献中一致；液态金属 ~65 为 IEEE 论文演示值。

## 2. μbump 阵列热阻——垂直路径的实测瓶颈

### 2.1 实测（4-die 堆叠热测试芯片，含 BLM/IMC 界面贡献）

| pitch | 单位（面积归一）热阻 | 换算单 bump 热阻（R×pitch²） | 出处 |
|---|---|---|---|
| 50 μm | **8.0 °C·mm²/W** | ~3200 K/W | Electronics Cooling 2013 实测 |
| 71 μm | 15.5 °C·mm²/W | ~3100 K/W | 同上 |
| 100 μm | 19.0 °C·mm²/W | ~1900 K/W | 同上 |

- 25μm 无铅 μbump，误差 <5%（50μm）/ <10%（100μm）。
- 比用体热导率的并联估算（keff = k_solder·面积占比 + k_uf·占比）**高一截**——界面（BLM/IMC）和 void 不可忽略。
- 注：单 bump 数值大（K/W 级）不吓人——上万个 bump 并联后整体才几 °C·mm²/W；**我们 LP 里不需要每 bump 热阻，只需要单位面积值**。

### 2.2 等效集总层参数（建模用）

| 层 | 尺寸 | 面内 k∥ | 垂直 k⊥ | 出处 |
|---|---|---|---|---|
| die 下 μbump+underfill 集总层 | 5.08×5.08×0.15mm | 0.7 W/mK | 6.5（bump 区）/ 0.4（中心 underfill-only）W/mK | 封装建模专著章节（Elsevier, Beyond Moore） |
| interposer 下 bump+underfill 层 | 18×18×0.075mm | 0.6 | 4.9 | 同上 |
| 焊球层（C4） | 31×31×0.6mm | 0.054 | 8.0 | 同上 |
| 30μm/50μm pitch 满布 μbump | — | 0.8 | （Maxwell 均匀化） | 同上 |

### 2.3 设计杠杆（结论级）

- underfill k 从 0.4→2.0 W/mK：互连层+BEOL 热阻 86.2→41.9 K·mm²/W（减半），**>4 W/mK 后饱和**（BEOL 变瓶颈）——SEMI-THERM 2014。
- die-die 界面：降 standoff 高度最有效；die-package 界面：升 underfill k 最有效——Oprins 2016 标定 FEM 结论。

## 3. TSV 阵列等效热导（3D 垂直路径）

| 参数 | 值 | 出处 |
|---|---|---|
| TSV 阵列等效 k | 111–196 W/mK（Dv/P=0.1–0.5） | 封装建模专著章节 |
| CoWoS interposer | ~100μm 厚，TSV 深宽比 10:1（即 TSV Ø~10μm），μbump pitch 40μm，RDL 布线 0.8μm | 华金证券研报/行业科普 [中等] |
| CoWoS-S interposer 面积演进 | 1 代 775mm² → 4 掩模拼接 2500–2700mm² → 下一代 ~3400mm² | 同上 [中等] |

**为什么可信**：TSV 等效 k 是 Maxwell 均匀化标准算法输出，数值与"铜填充 TSV 占比"直觉一致；CoWoS 几何参数来自券商研报转引 TSMC 公开技术文献，属 [中等]，引用时需落到 TSMC 原文。

## 4. 与我们的关系

- **`g_lat`（横向）**：硅 interposer 面内热导率 130–150 W/mK 是共识值，我们用 150 没问题；interposer 0.1mm 厚度与 CoWoS ~100μm 一致——横向路径参数无需改动。
- **`R_vert`（垂直）**：垂直全路径 = die_z + μbump 层 + interposer_z + TIM + heatsink 对流。其中 μbump 层单位热阻 ~8 K·mm²/W（实测，见 §2.1）只是一环（约全路径的 10%）；C4/焊球层（k⊥=8 W/mK，0.6mm 厚 → R·A≈75 K·mm²/W）通常在热沉路径之外（C4 面朝基板，不参与向上散热），不计入 R_vert。**结论：μbump 不是 die→ambient 全路径主导项，TIM + 对流才是**——R_vert 标定应优先对 TIM 热导率与对流系数做灵敏度（见 05），μbump 用文献实测值（8 K·mm²/W）即可。
- **上界策略**：underfill k 取 0.4（下限）→ 层热阻取上限，是我们的保守方向；若做 molded 2.5D，额外 ×10（见 01）。

## 5. 来源清单

1. "Measured Thermal Resistance of Microbumps in 3D Chip Stacks", Electronics Cooling, 2013-03：https://www.electronics-cooling.com/2013/03/measured-thermal-resistance-of-microbumps-in-3d-chip-stacks/ —— [可靠]
2. Matsumoto et al., "High thermal conductivity underfill for the thermal management of 3D chip stacks", SEMI-THERM 2014, doi:10.1109/semi-therm.2014.6892243 —— [可靠]
3. Oprins et al., "Experimental Characterization of the Vertical and Lateral Heat Transfer in 3D Stacked Die Packages", ASME J. Electronic Packaging 138, 2016, doi:10.1115/1.4032346 —— [可靠]
4. 封装建模专著："Thermal modeling, analysis, and design"（Beyond Moore / Elsevier, doi:10.1016/B978-0-08-102532-1.00003-2）—— [可靠]（书籍章节）
5. HotSpot 默认参数（硅 130 W/mK）：https://github.com/IFTE-EDA/HotSpot 与 https://www.cs.virginia.edu/~skadron/lava/HotSpot/ —— [可靠]
6. CoWoS interposer 几何：华金证券 TSV 研报 / scienceinsights.org interposer 科普 —— [中等]
7. 液态金属 TIM：IEEE 9501784（Rapid Enhancement of Thermal Conductivity ... Liquid Metal-based TIM）—— [中等]
