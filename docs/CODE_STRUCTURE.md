# 新 DSE 代码结构说明

## 目标

本目录是一个独立完整的晶圆级交换机 DSE 小项目，不依赖旧 Titan 命名，也不依赖外部 NormNet 目录。它按职责拆成三层：

```text
wafer_dse/
  src/wafer_dse/
    user_interface/       用户指令级模块
    architecture_model/   体系结构级初筛模块
    packaging_model/      封装级初筛模块
    reporting/            运行结果报告模块
```

## 1. 用户指令级模块

路径：

```text
src/wafer_dse/user_interface/
```

输入：

- 目标无阻塞带宽；
- 峰值功耗上限；
- 严格程度；
- 封装工艺配置文件；
- 待考查拓扑结构。

输出：

- 每个 topology 的 `FeasibilityReport`。

职责：

```text
读用户需求 -> 调 architecture model -> 调 packaging model -> 做耦合判断 -> 写报告
```

## 2. 体系结构级初筛模块

路径：

```text
src/wafer_dse/architecture_model/
```

输入：

- Requirement；
- TopologySpec，例如 mesh/torus/dragonfly。

说明：拓扑结构由用户指令级模块传入；进入 architecture model 后，它只是纯体系结构输入。

输出：

- NetworkPotential。

职责：

```text
拓扑 + route -> 独立 worst-case 求解器 -> nonblocking bandwidth -> required internal speedup
```

## 3. 封装级初筛模块

路径：

```text
src/wafer_dse/packaging_model/
```

输入：

- Requirement；
- NetworkPotential；
- packaging config。

输出：

- PackagingEstimate。

职责：

```text
网络需求 -> lane 数/面积/功耗估计 -> external/internal budget 判断
```

## 4. 报告模块

路径：

```text
src/wafer_dse/reporting/
```

输出：

```text
results.json
results.csv
report.md
```

`report.md` 包含 Mermaid 可视化图和候选结果表。
