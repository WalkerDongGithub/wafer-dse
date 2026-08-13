# 组内 / 组间双模型实验计划

> 2026-08-13。旧 pipeline（exp/lib/_pipeline.py 等）已删除——它诞生于 builder/query/参数组合重构之前，六成内容与现架构重叠。本计划是重做版。
> 图景依据：三个设计决策（记忆 inter-group-blueprint）。

## 1. 目标

**两个完整子模型各自算，再对照**：

- **组内模型**：FullMesh 拓扑 + UCIe + μbump，全套约束（placement / perf / therm / wiring / bump）
- **组间模型**：Dragonfly 全局链路 + SerDes + C4，全套约束，**热用套娃近似**
- 对照输出：两个 B* + 两个约束账本并排——瓶颈归属一目了然

## 2. 现状盘点

| 组件 | 状态 |
|------|------|
| 参数组合（ExpParams，含 global_link=SerDes-112G-VSR） | ✓ 就位 |
| 布局（src/layout.py：place + node_die_map） | ✓ 就位 |
| 场景组装（lp/builder.py：perf / perf+bump / perf+bump+therm） | ✓ 组内主体就位 |
| 热网络（ThermalNetworkBuilder 多态） | ✓ 就位，套娃可直接复用 |
| 查询（BmaxQuery + FeasibilityQuery + 缓存） | ✓ 就位 |
| 账本（src/diagnostics.py） | ✓ 就位 |
| **链路分类（intra/inter/ondie 按 reach）** | ✗ 旧 _pipeline 里，已删，需重写进 src |
| **SerDes + C4 场景（组间模型）** | ✗ 未建 |
| **套娃热（interposer 聚合 die）** | ✗ 未建 |
| 布线进场景（WiringModel） | ✗ 未接（组内、组间都要） |
| 布线溢流（外部交换机逃生） | ✗ 后置 |

## 3. 步骤

### S1. 链路分类进 src

`categorize_links(topo, layout, reach_mm)` → intra / inter / ondie 三堆。核心判据：die 间曼哈顿距离 ≤ UCIe max_reach（Advanced 2mm/1.5mm/1mm 按档）→ intra，否则 inter；同 die → ondie。放 `src/layout.py`（与 place 同层）。测试：test02 补分类契约（网格布局下手算 intra/inter）。

### S2. builder 加组间场景

`build_scenario` 扩展两个场景：

- `perf+bump+therm+wiring`（组内完整）：现有场景 + WiringModel（link_specs 从 layout + intra 链路生成）
- `inter-serdes-c4`（组间）：perf（Dragonfly 全局拓扑）+ C4Model（SerDes lane 数 ≤ C4 预算）+ 套娃热 + 布线（可后置）

SerDes 参数用 `P.global_link`（ExpParams 已有字段）。

### S3. 套娃热

组间场景的热网络：每个 group 一个"聚合 die"（位置 = group 内 die 的几何中心，功耗 = 组内全元件功耗之和），喂 `AnalyticNetworkBuilder`——代码零改动，换 `R_vert` 为 interposer 级等效热阻。近似代价（丢失组内温度梯度）在论文一句交代。测试：toy 参数下套娃热的手算断言。

### S4. 对照实验脚本

`exp/run_compare.py`：同一参数组下跑两个模型，输出并排表（B*、绑定物理约束、账本最紧项）。CSV 进 exp/output/。

### S5. 布线溢流（后置，先硬约束）

远走线 SerDes 布不下 → 外部交换机绕行 = 布线约束的松弛变量（外部端口 + 延迟/功耗惩罚）。等 S1–S4 跑通、有真实 infeasible 案例后再设计。

## 4. 验证约定

- 每步先改/写测试（.md + 手算锚点），再实现
- toy 参数组先行（toy 的 SerDes 档已定义：100G/1W → 10 pJ/bit）
- 旧 dragonfly 数据（exp/output 里的历史 log/png）不再作为参考——旧架构数字已过时
