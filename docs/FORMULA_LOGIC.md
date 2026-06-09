# 公式计算逻辑文档

## 1. 体系结构级公式

目标：判断一个 topology 是否有达到无阻塞带宽目标的网络潜能。

### 1.1 无阻塞带宽

体系结构模块内部的固定路由求解器得到：

```text
nonblocking_gbps_per_port
```

含义：在 worst-case traffic 下，每个端口能保证的无阻塞注入带宽。当前求解器对 `det/val` 固定路由做精确 assignment worst-case 求解，不依赖外部项目。

### 1.2 所需内部 speedup

```text
required_speedup = ceil(target_nonblocking_gbps_per_port / nonblocking_gbps_per_port)
```

解释：如果拓扑原始无阻塞能力低于目标，则需要把内部链路容量放大若干倍。

### 1.3 所需内部链路预算

```text
required_internal_800g_links = directed_link_count × required_speedup
```

解释：拓扑有多少有向内部链路，每条链路需要多少倍 800G-equivalent 资源。

### 1.4 fixed-route worst-case 的含义

对每条物理有向链路 `e`，体系结构模块会计算每个 `src -> dst` demand 对该链路造成的负载系数：

```text
weight_e[src,dst] = 该 demand 在 route 分流后经过 e 的比例
```

然后在所有 permutation/derangement traffic 中找最坏情况：

```text
worst_load_e = max_permutation Σ_src weight_e[src, permutation(src)]
```

全网 worst-case load 是：

```text
worst_load = max_e worst_load_e
```

若单条基础链路容量等于目标端口带宽 `target`，则：

```text
nonblocking_gbps_per_port = target / worst_load
```

这个求解用 assignment/derangement 完成，因此对当前 fixed route 模型是精确的。

## 2. 封装级公式

目标：判断 required internal/external links 是否能被单 die/package 承载。

### 2.1 每个目标端口所需 lane 数

```text
lanes_per_target_port = ceil(target_gbps_per_port / lane_rate_gbps)
```

例如 800G 目标、100G/lane：

```text
lanes_per_target_port = 8
```

### 2.2 外部 lane 需求

```text
required_external_lanes = port_count × lanes_per_target_port
```

### 2.3 内部 lane 需求

```text
required_internal_lanes = required_internal_800g_links × lanes_per_target_port
```

### 2.4 封装预算换算

```text
external_800g_port_budget = max_external_lanes / lanes_per_target_port
internal_800g_link_budget = max_internal_lanes / lanes_per_target_port
```

### 2.5 面积早筛

```text
die_area = base_die_area
         + terminal_count × router_area
         + required_external_lanes × area_per_external_lane
         + required_internal_lanes × area_per_internal_lane
```

这是 early-stage linear accounting，不是 layout sign-off。

### 2.6 功耗早筛

```text
power = base_power
      + terminal_count × router_power
      + required_external_lanes × power_per_external_lane
      + required_internal_lanes × power_per_internal_lane
```

这是峰值功耗/TDP 早筛。

## 3. 耦合判断

```text
feasible_potential =
    terminal_count matches port_count
    AND certificate is usable
    AND external ports fit budget
    AND internal links fit budget
    AND die area <= area limit
    AND power <= power limit
```

只有网络潜能和封装能力同时通过，才认为 topology 具有落地潜力。

## 4. 单 die 物理公式（DieEstimator）

这些公式位于 `wafer_dse.die_model.estimator`，用于层次化 DSE 中评估单个物理 die。

### 4.1 crossbar 面积（O(N²)）

```text
crossbar_area = crossbar_ports² × crossbar_cell_mm2
```

交叉开关矩阵有 N² 个交叉点，每个交叉点占用固定的单元面积。

### 4.2 buffer 面积（O(N)）

```text
total_buffer_bits = crossbar_ports × vc_count × vc_depth × flit_width
buffer_area = total_buffer_bits / (sram_density_mbit_per_mm2 × 1e6 × buffer_area_efficiency)
```

每端口有 vc_count 个 VC，每个 VC 深度 vc_depth，每条 flit 宽 flit_width bit。面积效率系数考虑 SRAM 外围电路开销。

### 4.3 外部 SerDes

```text
ext_lanes_per_port = ceil(target_gbps / ext_lane_rate_gbps)
ext_lanes = ext_port_count × ext_lanes_per_port
ext_area = ext_lanes × area_per_external_lane_mm2
ext_power = ext_lanes × power_per_external_lane_w
```

### 4.4 D2D PHY

```text
int_lanes_per_port = ceil(target_gbps / int_lane_rate_gbps)
d2d_lanes = d2d_link_count × int_lanes_per_port
d2d_area = d2d_lanes × area_per_internal_lane_mm2
d2d_power = d2d_lanes × power_per_internal_lane_w
```

### 4.5 总面积与约束

```text
die_area = base_die_area + router_area + ext_area + d2d_area
die_power = base_power + ext_power + d2d_power

area_ok = die_area ≤ max_die_area（reticle limit）
perimeter = 4 × sqrt(die_area)            # 正方形近似
d2d_lane_budget = perimeter × d2d_lanes_per_mm_edge
d2d_edge_ok = d2d_lanes ≤ d2d_lane_budget
```

## 5. Group 枚举公式（GroupExplorer）

对 Dragonfly (a, p, h) 群体，按 K 个 die 均匀分割：

```text
K = 1 .. a, a % K == 0
r = a / K   （每个 die 上的 router 数）

crossbar_ports = r×p + (r-1) + (K-1) + r×h
ext_ports = r×p
d2d_links = (K-1)                    # 当 speedup=1
d2d_links = (K-1) × required_speedup  # 当 speedup>1
```

解释：
- `r×p`：本 die 上所有 terminal 端口
- `(r-1)`：本 die 上多个 router 间全互联端口
- `(K-1)`：连接到同 group 其他 die 的端口
- `r×h`：本 die 的全局出口端口

## 6. Wafer 级汇总公式（WaferAssembler）

```text
枚举 (a, p, h, g) 使 a × p × g = total_ports
对每个 group 跑 GroupExplorer

inter_group_links = g × (g - 1)        # g 个 group 全互联
inter_group_lanes = inter_group_links × int_lanes_per_port
inter_group_ok = inter_group_lanes ≤ max_internal_lanes（package 基板预算）

total_dies = g × group.best_partition.die_count
total_area = g × group.best_partition.total_area
total_power = g × group.best_partition.total_power
```
