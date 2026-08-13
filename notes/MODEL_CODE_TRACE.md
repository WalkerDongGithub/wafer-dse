# 模型 ↔ 代码对照表

论文 MATH_MODEL_COMPLETE_V2.md §5 完整 LP 的每一条约束 → 代码实现位置。

---

## 性能约束 (§5 第 1-3 行)

| 约束 | 代码 | 说明 |
|------|------|------|
| $\sum_k f_{ij}^{k,(r)} = D_{ij}^{(r)}$ | `src/lp/models/perf/traffic_based/_envelope.py:53-66` | `EnvelopeModel.build()` 中声明分流变量 + 流量守恒 |
| $L_e^{(r)} = \sum f$ | `_envelope.py:69-75` | 链路负载 = 经过该链路的分流之和 |
| $L_e \ge L_e^{(r)}$ | `_envelope.py:77-78` | 包络不等式 |

## 物理 lane 数 (§5 第 4 行)

| 约束 | 代码 | 说明 |
|------|------|------|
| $\ell_e = B \cdot L_e / S_{\text{bw},e}$ | **不在独立文件中** | 消去 $\ell$，直接代入后续约束。`BumpModel` 用 `coeff = 1/lane_rate`；`SteadyStateModel` 用 `ppl/lane_rate` 进 M 矩阵 |

## 功耗模型 (§5 第 5 行)

| 约束 | 代码 | 说明 |
|------|------|------|
| $P_v = P_{0,v} + \sum_{e \in \delta(v)} S_{\text{dyn},e} \cdot \ell_e$ | **消去** | $P$ 不在 LP 中显式出现。在 `BumpModel` 中代入 bump 约束系数；在 `SteadyStateModel` 中通过 `M[i,e] = ppl[e]/lane_rate[e]` 编码进 `link_coeff` |

## μbump 约束 (§5 第 6-8 行)

| 约束 | 代码 | 说明 |
|------|------|------|
| $\mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell}$ | `src/lp/models/phys/bumps/_bump.py:58-64` | `BumpModel.__init__` 预计算系数 |
| $\mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}}^{-1} \cdot \mathbf{P}$ | `_bump.py:62-63` | `pwr_P0` 和 per-lane 系数中编码 |
| $\mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}$ | `_bump.py:71-73` | `build()` 中 `B * expr <= rhs` |

## 热约束 (§5 第 9-11 行)

| 约束 | 代码 | 说明 |
|------|------|------|
| $\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}$ | `src/lp/models/phys/therm/_network.py:36-55` | `build_thermal_network()` 预计算 $G^{-1}$ |
| $\mathbf{T} \le T_{\max} \cdot \mathbf{1}$ | `_network.py:75-80` | `SteadyStateModel.build()` 中 per-die 不等式 |
| $\mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max}$ | `src/lp/models/phys/therm/_warp_limit.py` | **未实现**，占位 |

## 布线约束 (§5 第 12-15 行)

| 约束 | 代码 | 说明 |
|------|------|------|
| $\sum_{q} x_{e,q} = \ell_e$ | `src/lp/models/phys/routing/__init__.py:70-74` | `RoutingModel.build()` 需求等式 |
| $\sum_{e,q: g \in q} x_{e,q} \le C_g$ | `routing/__init__.py:77-80` | 边容量不等式 |
| $\sum_{e,q: v \in q} x_{e,q} \le C_v$ | `routing/__init__.py:83-86` | 点容量不等式 |

## C4 约束 (组间 §5.2)

| 约束 | 代码 | 说明 |
|------|------|------|
| $\sum_{e \in \mathcal{E}_{\text{inter}}} \ell_e \le \eta N^{\text{signal}}$ | `src/lp/models/phys/bumps/_c4.py:41-44` | `C4Model.build()` 全局 C4 池不等式 |

## 变量声明 & 求解

| 概念 | 代码 |
|------|------|
| 变量声明 (L, f, x) | `src/lp/ctx/__init__.py` — `Ctx.vector()`, `Ctx.scalar()` |
| 约束注册 (≤, =) | `src/lp/ctx/_expr.py` — `LinExpr.__le__()`, `ctx.constrain()` |
| 编译求解 | `src/lp/engine/solution/_cvx.py` — `CvxSolver._compile_and_solve()` |
| 二分搜索 $B^*$ | `exp/lib/_pipeline.py:_run_bmax()` — 对可行性 LP 做二分 |

## 布局 & 前处理

| 概念 | 代码 |
|------|------|
| die 布局 | `src/physical/placement/_solver.py` — `solve_grid_placement()` |
| 链路分类 (距离 → UCIe/SerDes) | `exp/lib/_pipeline.py:categorize_links()` |
| G 矩阵构建 | `src/lp/models/phys/therm/_mfit.py` — `build_thermal_system()` |
| 布线网格构建 | `src/lp/models/phys/routing/_grid.py` — `build_routing_grid()` |

## 模型 ↔ 代码 差异

| 论文有，代码缺 | 说明 |
|---------------|------|
| $\mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max}$ (翘曲) | `_warp_limit.py` 占位，未实现 |
| C4 per-pad 约束 (§3.3 L1) | `C4Model` 只有全局池 L0，per-pad 待扩展 |
| 组内布线模型集成 | `intra_group_bmax` 当前未调用 `make_routing_model` |

| 代码有，论文不需写 | 说明 |
|-------------------|------|
| 消去 $P$, $T$, $\ell$, $\mathbf{N}^{\text{sig}}$, $\mathbf{N}^{\text{pwr}}$ | 求解策略——`__init__` 预计算系数使 `build()` 成为纯 L 上线性不等式 |
| $\min \sum L_e$ 目标 | 求解策略——确保 feasibility LP 中 L 不被放大 |
| `cache_key()` | Runner 持久化缓存，纯工程 |
