# Interposer 物理模型

## 物理约束

```
单个 interposer = 1 个 reticle 曝光区
  ～26×33mm ≈ 858mm²
  容纳 ~6 个 die (12×12mm, 含 5mm 间距)

Die 间连接: μbump → interposer 铜线 → μbump
  - 线宽 0.4μm, 2-4 层金属
  - 最远 die 间距 ≈ √2 × 12 ≈ 17mm (2×2 紧凑排列对角)
  - 加 routing detour × 1.2 → ~20mm
  - 考虑安全余量 → 保守取 2mm (最近邻) 用于 UCIe-Advanced
```

## 核心公式

### 最多容纳 die 数

```
N_max = ⌊A_interposer × 0.7 / A_die⌋
```

其中 0.7 = 面积利用率 (扣除 interposer 上走线/间距)。

**示例**: 858mm² interposer, 12×12mm die:
```
N_max = ⌊858 × 0.7 / 144⌋ = ⌊4.17⌋ = 4
```

严格 2×2 排列最多 4 个 die。若 die 更小 (8×8mm) 可容纳更多。

### 组内布线距离约束

对每条 D2D 边，需满足:

```
d(die_i, die_j) ≤ max_reach(std)   ∀ edge ∈ intra_group_edges
```

当前模型简化: 假设 die 紧密排列 (2×2)，最大邻近距离 ~2mm。因此只有 UCIe-Advanced (max_reach ≥ 2mm) 可用。

### UCIe 标准选择优先级

```
1. UCIe-32G-Advanced (max_reach=1mm) — 最快但距离最短
2. UCIe-24G-Advanced (max_reach=1.5mm)
3. UCIe-16G-Advanced (max_reach=2mm)
4. UCIe-12G-Advanced (max_reach=2mm) — 最慢但最省 bump

选择策略: 按 lane_rate 降序遍历，取第一个满足距离+bump预算的方案。
```

### μbump 消耗

每个 die 的组内 D2D 消耗:

```
N_intra_per_die = (a - 1) × ⌈BW_target / lane_rate⌉
```

其中 `a-1` = 每个 die 在组内连接的其他 die 数 (全互联)。

## 输出

`IntraRouteResult`:
- `chosen_standard`: 选中的 UCIe 标准名
- `feasible`: 是否存在可行的 UCIe 标准
- `lanes_per_edge`: 每条 D2D 链路消耗的 lane 数
- `total_power_w`: 组内所有 D2D 链路的总功耗
