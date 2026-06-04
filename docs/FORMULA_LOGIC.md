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
