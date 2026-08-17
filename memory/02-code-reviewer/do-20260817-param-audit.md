# Do 报告 — 代码审查员（02）

日期：2026-08-17
任务：src/physical/ 物理参数对标 + 三层热阻参考值

## 一、参数对标结论（摘要）

- **完全对标规范**：lane rate（UCIe 16/24/32 GT/s、SerDes 106.25/212.5 Gbps）、bump pitch（μbump 45μm、C4 130μm、hybrid 1/5/9μm）、供电电压 0.8V（规范 <0.85V）。
- **功耗档位**：UCIe 5/9/16 mW 是「官方 0.25 pJ/bit 能效指标的工程裕量版」（0.31/0.38/0.50 pJ/bit），方向偏保守，但不能挂「UCIe 规定」。
- **SerDes-224G = 1.062W（5 pJ/bit）可能偏乐观**（早期演示 5–8 pJ/bit），宜标「早期演示值」。
- **冷却档名字错位**：Liquid 2.0 W/mm² 是微通道冷板演示上限（典型冷板 50–150 W/cm²）；Immersion/Microfluidic 是研究级演示值。
- **bump 载流 75mA/300mA 追不到单一权威 datasheet**（EM 限制工程典型值），量级正确、对模型结论不敏感（电源 bump 占比 <1%）。

## 二、🔴 硬错误（必须改）

**`ucie.py` 全部 UCIe 实例 `ber=1e-27` 是错的**。UCIe 2.0 Spec：Advanced ≤12GT/s=1e-27、≥16GT/s=1e-15；Standard ≤8GT/s=1e-27、≥12GT/s=1e-15。
应改：UCIe-16G/24G/32G-Advanced 与 UCIe-16G-Standard → 1e-15；仅 UCIe-12G-Advanced、UCIe-8G-Standard 保留 1e-27。
（BER 不参与 LP 可行性计算，只进 LinkBudget.ber 报告字段，不影响 B* 数值，但作论文「实验设置」必须正确。）

## 三、★★ 三层垂直热阻参考值（最重要产出）

统一给**面积归一热阻 R·A [K·mm²/W]**：

| 层 | R·A (K·mm²/W) | 12×12mm die 场景 R (K/W) | 出处 |
|---|---|---|---|
| R_die→interposer（μbump+underfill） | **8.0**（50μm pitch 实测） | 0.056 | Colgan & Wakil (IBM) Electronics Cooling 2013；Maria et al. ECTC 2011（50μm=8.0/71μm=15.5/100μm=19.0 °C·mm²/W） |
| R_interposer→substrate（C4 焊球） | **75**（k⊥=8, t=0.6mm） | 0.52（按 die 面积）/0.087（按 interposer 858mm²） | 封装建模专著（Beyond Moore/Elsevier） |
| R_substrate→ambient（TIM+HS+对流） | **50–80** | 0.35–0.56 | Fan et al. ITherm 2024（72）；HIR 2021 Ch20（80）；IEEE TCPMT 2014 θjc |

**量级关系**：8 : 75 : 50–80 ≈ **1 : 9 : 7–10**。
**关键物理结论**：垂直主导是 C4 焊球层 + TIM/散热器，μbump 层仅 ~10%；三层加总（按 die 面积）≈1.1 K/W，当前集总 R_vert=1.5 是分层加总保守上界。
**建议定案值**：μbump 8.0、C4 75、TIM+HS+对流 60 K·mm²/W（液冷/风冷折中）。

## 四、需改正参数清单（完整）

1. 🔴 BER 1e-27 → 分档 1e-15/1e-27（见上）。
2. 🟡 UCIe 功耗档位论文声明口径：改「基于官方 0.25 pJ/bit 能效指标的工程裕量」。
3. 🟡 SerDes-224G 标「早期演示值」+ 做灵敏度。
4. 🟡 冷却档 Liquid/Immersion/Microfluidic 改名或明示「文献演示上限」。
5. 🟡 bump 载流标「工程典型值，待核实」。
6. 🟡 loss_db_per_mm 与按速率细分 max_reach 是自拟工程值，论文不必展开（只进报告字段）。
7. 🟢 供电 0.8V、interposer 0.1mm、硅 k=150、T_ambient 27°C、T_max 85°C 已对标通过（T_max 比真实 105°C 保守 20°C，「85°C=翘曲约束」无直接出处，笔记已声明）。
