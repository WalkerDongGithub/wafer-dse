# μbump 与 C4 Bump 模型

## 物理位置

```
Layer 2:  Die ──μbump──→ Interposer  (上界面, die→interposer)
Layer 1:  Interposer ──C4──→ Substrate  (下界面, interposer→substrate)
Layer 0:  Substrate ──BGA──→ PCB
```

μbump 和 C4 是两种独立的 bump 工艺，密度不同、用途不同。

## 核心公式

### μbump (die 边沿，按周长计算)

| 量 | 公式 | 单位 |
|---|---|---|
| 总 bump 数 | `N_total = 2(w + h) / pitch` | 个 |
| 信号 bump 数 | `N_sig = N_total × η` | 个 |

其中 `η` = 信号 bump 占比 (扣除电源/地/测试):
- 交换芯片: `η ≈ 0.55`
- 逻辑芯片: `η ≈ 0.50`
- 内存芯片: `η ≈ 0.65`

**示例**: 12×12mm die, μbump 45μm, η=0.55:
```
N_total = 2(12+12) / 0.045 = 1067
N_sig   = 1067 × 0.55   = 586
```

### C4 (interposer 底面，按面积计算)

| 量 | 公式 | 单位 |
|---|---|---|
| 总 bump 数 | `N_total = A / pitch²` | 个 |
| 信号 bump 数 | `N_sig = N_total × η` | 个 |

**示例**: 858mm² interposer, C4 130μm, η=0.40:
```
N_total = 858 / 0.13² = 50710
N_sig   = 50710 × 0.40 = 20284
```

## 常用规格

| 名称 | pitch | η | 密度 (边沿) | 密度 (面积) |
|---|---|---|---|---|
| C4 | 130μm | 0.40 | 3.1/mm | 24/mm² |
| μbump-45μm | 45μm | 0.55 | 12.2/mm | — |
| μbump-25μm | 25μm | 0.60 | 24.0/mm | — |
| Hybrid-9μm | 9μm | 0.90 | 100/mm | — |
| Hybrid-5μm | 5μm | 0.90 | 180/mm | — |
| Hybrid-1μm | 1μm | 0.90 | 900/mm | — |

## μbump 预算约束

每个 die 的 μbump 池是**所有互联共享的硬上限**。一个 die 上需同时承载：

```
N_total_lanes = N_terminal + N_intra_D2D + N_global

其中:
  N_terminal = p × ⌈BW_target / lane_rate⌉           (外部端口)
  N_intra    = (a-1) × ⌈BW_target / lane_rate⌉       (组内 D2D)
  N_global   = h × ⌈BW_target / lane_rate_global⌉    (组间 global link)

约束: N_total_lanes ≤ N_sig
```

## C4 预算约束

所有 interposer 的总 C4 池，用于 global link (interposer 间) 和外部 I/O：

```
N_c4_needed = N_global_links × 2 × lanes_per_global_link

约束: N_c4_needed ≤ N_sig_C4_total
```

C4 也供电，但电源 bump 已在 η 中扣除，不计入信号池。
