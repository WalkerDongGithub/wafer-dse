# 体系结构级初筛模块说明

对应代码：

```text
wafer_dse/src/wafer_dse/architecture_model/model.py
```

## 1. 独立性

该模块是 `wafer_dse` 项目内部的独立实现，不依赖外部 `normnet` 目录。

它内部包含：

```text
1. Topology 定义
   - Mesh
   - Torus
   - Dragonfly

2. Route 生成
   - deterministic route
   - fixed-splitting Valiant route

3. Worst-case nonblocking 求解
   - 对每条 link 构造 src-dst 权重矩阵
   - 用 assignment/derangement 精确求最坏 traffic
   - 输出 nonblocking bandwidth 和 worst link
```

## 2. 输入

来自用户指令级模块的 `TopologySpec`：

```text
kind: mesh / torus / dragonfly
size: mesh/torus 边长
route: det / val
a, p, h: dragonfly 参数
```

以及 `Requirement`：

```text
target_nonblocking_gbps_per_port
strictness
```

## 3. 输出

`NetworkPotential`：

```text
topology_name
route
terminal_count
directed_link_count
nonblocking_gbps_per_port
required_internal_speedup
required_internal_800g_links
certificate_status
worst_link
notes
```

## 4. 为什么这样实现

体系结构级初筛只回答网络问题：

```text
给定 topology 和 route，在 worst-case traffic 下，每个端口能保证多少无阻塞带宽？
如果目标是 800G/port，需要多少 internal speedup？
```

它不关心封装、面积和功耗。封装级模块会在下一关判断这些 speedup 和 link 需求能否真实承载。

## 5. 当前求解器边界

当前独立求解器支持：

```text
route = det
route = val
strictness = full 时的 worst-case exact fixed-route 求解
```

暂不支持：

```text
adaptive opt route
benchmark traffic
benchmark x% traffic
大规模 cutting-plane certificate
```

这些后续应继续放在 architecture model 内部实现，而不是依赖外部项目。
