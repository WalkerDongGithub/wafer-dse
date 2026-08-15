# 01 封装热阻标准（JESD51）与典型 θjc/θja 数值

> 断言：JEDEC JESD51 系列定义了热阻的测量口径；真实 flip-chip BGA / 2.5D interposer 封装的 θjc 落在 0.1–1 K/W 量级（取决于 die 大小、mold 与否），我们的 R_vert 必须与之同量级才有物理意义。

## 1. JESD51 定义口径（引用时务必区分）

| 符号 | 定义 | 标准 | 备注 |
|---|---|---|---|
| θJA | (Tj − Ta)/P，结到环境 | JESD51-2（自然对流静止空气）、JESD51-7（2s2p 四层测试板）、JESD51-9（单层板） | 只用于**封装间对比**，JESD51-3 明确警告不能直接预测具体系统性能 |
| θJC | 结到 case（顶/底面） | JESD51-14（TDI 瞬态双界面法） | 现代口径区分 θJC-TOP / θJC-BOT，测量时其余表面绝热 |
| ΨJT | (Tj − TT)/P，结到封装顶面中心（表征参数，非热阻） | — | BGA 类封装顶面测的"θjc"实际是 Ψjt，**不能**用来算功率上限，只能由实测 case 温度反推 Tj |

**与我们的关系**：我们热约束 rhs 用的是"温度上限折算功率预算"，等价于 θJA 口径（全堆叠）而非 θJC（半程）。引用真实芯片数据时只能引 θJA 或完整堆叠 R（Rjc+Rca），不能直接拿 θjc 当 R_vert——这是对标时最容易犯的口径错误。

## 2. 典型数值（小/中 die，JEDEC 测试板口径）

| 封装 | θJA（静止空气） | θJC/Ψjt | 出处 | 状态 |
|---|---|---|---|---|
| CSBGA（Maxim DS21Q48） | 24 °C/W | 4.1 °C/W（Ψjt） | Maxim datasheet | [可靠] |
| 256 MAPBGA（NXP K70） | 28（四层）/43（单层）°C/W | θJB≈17 | Freescale datasheet | [可靠] |
| 64-LFCSP（ADI AD9516） | 22.0 °C/W | — | ADI datasheet | [可靠] |
| Microchip 器件群 | 17.3–21.5 °C/W | 9–12.2 °C/W | Microchip 文档 | [可靠] |
| 风的影响 | θJA 随 2–2.5 m/s 气流降 15–25% | — | JESD51-6 系数据 | [可靠] |

**为什么可信**：datasheet 数值按 JEDEC 标准测试板（2s2p）产出，同一标准下可比。注意这些是小功率芯片，θ 值偏大，不能直接当大 die 交换 ASIC 用。

## 3. 大 die / 2.5D 封装（与我们的场景同族）

| 封装形态 | 数值 | 出处 | 状态 |
|---|---|---|---|
| **裸 die 2.5D TSI（硅 interposer）**，5.08×5.08mm die | θjc = **0.82 K/W**（= 0.21 K·cm²/W，文献中"最低之一"） | IEEE TCPMT 2014, doi:10.1109/TCPMT.2014.2311587（实测+仿真） | [可靠] |
| 同封装 + 0.6mm overmold | θjc = **11.76 K/W**（mold 主导热阻） | 同上 | [可靠] |
| 同封装 + 0.1mm 薄 mold | θjc ≈ 1 K/W 量级 | 同上（内插结论） | [可靠] |
| FCBGA 20mm die，平盖，TIM k=2.0 W/mK，BLT 50μm | θjc = **0.17 K/W** | Kandasamy, Appl. Thermal Eng. 2009（数值研究） | [可靠] |
| 同上但 TIM k=10 W/mK | θjc < **0.1 K/W** | 同上 | [可靠] |
| 同上但 die 从 5mm 增到 20mm | 面积 16×，θjc 降 9–12× | 同上 | [可靠] |
| 大容量交换芯片 FCBGA 封装 | >60 cm²，8000+ LGA 引脚（封装级，非 die 级） | SunshinePCB 行业文章 | [待确认] |

**关键规律**：
1. **mold 与否差 10×+**——molded 2.5D（如 overmolded CoWoS）θjc 比裸 die 高一个数量级。我们要"稳定上界"，对 molded 封装应取高值。
2. **die 面积是 θjc 的第一杠杆**（面积 16× → 热阻降 9–12×）——单位面积热阻 θjc·A 相对稳定在 0.2 K·cm²/W（裸 die）~ 0.4 K·cm²/W（含盖）。
3. **TIM 热导率第二杠杆**——k=2→10 可把 θjc 减半以上；TIM 占全堆叠热预算 20–50%（Kandasamy 结论）。

## 4. 为什么可信

- TCPMT 2014 是 IEEE 正式期刊的实测+仿真交叉验证工作，给出"文献最低之一"的 0.21 K·cm²/W，且 mold 厚度敏感性是逐点测量的。
- Kandasamy 2009 是同行评审数值研究，其 0.17 K/W（20mm die, k=2）与行业共识（大 die 带盖 FCBGA θjc 0.1–0.3 K/W）一致。
- JESD51 定义部分来自多家原厂技术文档（ROHM/Analog/Maxim），口径一致。

## 5. 与我们的关系

- **口径警示**：真实芯片的 θjc（0.1–0.3 K/W）只是半程热阻；我们 R_vert 对应全堆叠（θJA 口径，含 heatsink/对流）。换算：TH5 全堆叠 R≈0.09 K/W（见 03），其中 Rca≈0.05、Rjc≈0.04——θjc 占约一半。
- **R_vert 的标定锚**：用"单位面积热阻 R·A"跨 die 尺寸换算（θjc·A≈0.2–0.4 K·cm²/W，全堆叠 R·A≈0.5–0.8 K·cm²/W）。12×12mm die：全堆叠 R·A≈0.72 K·cm²/W → R_vert≈0.5 K/W。**我们默认 2.0 K/W 是其 4 倍**——保守（上界）方向，见 README §2。
- **molded 场景**：若我们支持 overmolded 2.5D profile，R_vert 应乘 ~10（θjc 0.8→11.8 的教训）——这是灵敏度分析里"R_vert 涨 10 倍"的物理依据。
- **T_max 的独立证据**：JESD51 标准本身不管 Tj_max——那是 EM 可靠性的事（见 03 §3）。

## 6. 来源清单

1. JEDEC JESD51 series：https://www.jedec.org —— [可靠]
2. ROHM, "Thermal Resistance Data: Definitions of Thermal Resistance, Thermal Characterization Parameters"：https://techweb.rohm.com/product/circuit-design/thermal-design/9678/ —— [可靠]
3. Maxim DS21Q48 / ADI AD9516 datasheet（θja/Ψjt 数值）—— [可靠]
4. "Thermal Characterization of Both Bare Die and Overmolded 2.5-D Packages on Through Silicon Interposers", IEEE Trans. CPMT, 2014, doi:10.1109/TCPMT.2014.2311587 —— [可靠]
5. Kandasamy & Subramanyam, "Interface thermal characteristics of flip chip packages – A numerical study", Applied Thermal Engineering 29 (2009) 822–829, doi:10.1016/j.applthermaleng.2008.04.002 —— [可靠]
6. 大容量交换芯片封装尺寸（>60cm²）：https://www.sunshinepcb.com/news/Industry/120.html —— [待确认]
