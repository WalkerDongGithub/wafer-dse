# Substrate 互联模型

## 物理约束

```
16 个 interposer × 4×4 网格, 贴在有机基板上

Interposer 间距:
  水平: 26mm + 5mm gap = 31mm
  垂直: 33mm + 5mm gap = 38mm

最远对角距离:
  dx = 3 × 31 = 93mm
  dy = 3 × 38 = 114mm
  euclidean = √(93² + 114²) = 147mm
  × routing detour 1.3 = 191mm

Substrate 布线能力:
  面积: ~50000mm² (整板), 层数: 20+
  → 视为充裕, 不建模局部瓶颈
```

## 核心公式

### Global Link 标准选择

Substrate 布线走 SerDes-112G-MR (唯一覆盖 ~190mm 且功耗可接受的标准):

| 标准 | max_reach | 可行性 |
|---|---|---|
| UCIe-Standard | 25mm | ✗ |
| SerDes-112G-VSR | 150mm | ✗ (擦边) |
| SerDes-112G-MR | 500mm | ✓ |
| SerDes-112G-LR | 1000mm | ✓ (但功耗更高) |

选择 SerDes-112G-MR: `lane_rate = 106.25 Gbps, power = 0.637W/lane`

### 每条 Global Link 的物理账单

```
lanes_per_edge = ⌈800 / 106.25⌉ = 8
power_per_edge = 8 × 0.637 + distance_power(191mm, 8)
              ≈ 5.1 + 0.8 = 5.9W
```

### C4 消耗

每条 global link 使用两端 C4 (发送端 + 接收端):

```
N_C4_per_link = 2 × lanes_per_edge = 2 × 8 = 16
total_C4 = N_global_links × 16
```

### 总 Global Link 数

Dragonfly (a,p,h) 的组间全互联:

```
g = a × h + 1  (总 group 数)
global_edges_per_group = h × a  (每 group 的全局端口数)
total_global_edges = g × h × a / 2  (双向, 除以 2)
```

**约束**:

```
total_C4 ≤ C4_pool.available
```

## 输出

`GlobalRouteResult`:
- `chosen_standard`: 固定为 "SerDes-112G-MR"
- `feasible`: C4 预算是否够
- `total_c4_needed`: 消耗的 C4 信号 bump 数
- `total_power_w`: 所有 global link 的总功耗
