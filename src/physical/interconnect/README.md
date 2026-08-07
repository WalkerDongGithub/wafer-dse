# 互连标准模型

## 核心公式

每种互连标准 `s` 由一组物理参数定义。给定走线长度 L [mm] 和需求带宽 B [Gbps]：

### 基本换算

| 量 | 公式 | 单位 |
|---|---|---|
| 所需 lane 数 | `N_lane = ⌈B / s.lane_rate⌉` | — |
| 总损耗 | `loss = L × s.loss_db_per_mm` | dB |
| die 边沿占用宽度 | `width = N_lane / s.lane_density_per_mm` | mm |
| 总功耗 | `P = N_lane × s.power_per_lane + s.distance_power(L, N_lane)` | W |
| 物理占位层数 | `layers = s._footprint(L, N_lane).total_layers` | — |

### 距离可行性

```
feasible ⇔ L ≤ s.max_reach_mm
```

不可行时，`LinkBudget.feasible = False`，其余字段为占位值。

### 距离相关功耗

| 标准族 | distance_power |
|---|---|
| UCIe, TSV, Ethernet | 0 (已含在 per_lane 中) |
| SerDes MR | `N_lane × 0.05 × L/100` |
| SerDes LR | `N_lane × 0.10 × L/100` |
| Optical | 0 (CPO 固定开销 0.8W 在 _footprint 中另加) |

### 物理占位模型

| 标准 | 端点类型 | 中间介质 | 层数 | 备注 |
|---|---|---|---|---|
| UCIe-Advanced | ENDPOINT ×2 | COPPER_TRACE × ⌈L/12⌉ | 1 | interposer 单层走线 |
| UCIe-Standard | ENDPOINT ×2 | COPPER_TRACE × ⌈L/12⌉ | 2 | substrate 差分对 |
| SerDes | SERDES_PHY ×2 | COPPER_TRACE × ⌈L/12⌉ | 2 | 长距可能含 SERDES_PHY 中继 |
| Optical | ENDPOINT + WAVEGUIDE×2 | WAVEGUIDE + COPPER_TRACE | 2 | CPO 固定开销 0.8W |
| Ethernet | SERDES_PHY ×2 | — | 0 | 不在晶圆上 |
| TSV | ENDPOINT ×1 | — | 0 | 垂直，同分区 |

## 注册标准

17 个已注册标准，按距离区间分布：

```
<1mm:    TSV-3D-{1,5,9}μm                   (垂直)
<2mm:    UCIe-{12,16,24,32}G-Advanced         (interposer 内)
2-25mm:  UCIe-{8,16}G-Standard                (substrate 短距)
25-500mm: SerDes-112G-{VSR,MR,LR}, 224G-VSR  (substrate 长距)
>500mm:  Optical-{1.6T-8λ, 3.2T-16λ}         (晶圆间)
>1000mm: Ethernet-{800G, 1.6T}                (跨机柜)
```

## 数据来源

- UCIe: UCIe 1.1/2.0 Specification Tables 1-1, 1-2, 1-3
- SerDes: OIF-CEI-112G/224G, IEEE 802.3ck/802.3dj
- Optical: JLT 2025, COL 2024, Optica 2025
- TSV: Intel Nature Electronics 2024 (UCIe-3D)
- Ethernet: IEEE 802.3df-2024
