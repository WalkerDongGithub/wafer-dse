# 组内/组间联合优化模型设计（草案 v0）

> 目标：基于 V4 总纲，设计一个「基础 model + 组内/组间/联合三种实例」的分层模型架构。
> 状态：草案待 review。
> 前置：`MATH_MODEL_COMPLETE_V4.md`、`plan_inter_group.md`。

## 1. 基础模型（Base Model）= V4 §3 骨架

变量（通用）：`f, L, ℓ, P, N_sig, N_pwr, T, x` + 标量 B。
约束模板（通用）：路由（2.1）、`ℓ = B·S_bw^{-1}·L`、`P = P0 + M·S_dyn·ℓ`、bump（`N_sig+N_pwr ≤ N_total`）、布线（`Ax=ℓ, Rx≤C`）、热（`GT=P+b, T≤T_max`）、C4（`1^T·ℓ_SerDes ≤ N_C4`）。

**总模型不变**：联合求解不改变约束形式——仍是线性 LP，变的只是系数矩阵（尤其热 G/b）的物理数值关系。

## 2. 实例化 = 三张表

| 表 | 内容 |
|----|------|
| 链路分类表 | 每条链路 e → on-die / intra(UCIe) / inter(SerDes)，决定 S_bw,e、S_dyn,e |
| 资源归属表 | 每个 lane → 哪个物理资源：die 侧信号 μbump ↔ substrate 侧 C4 焊球（一一对应） |
| 热层表 | 热节点属于哪层：die / interposer / substrate，及各层热阻 |

三种实例 = 三张表的不同填充：

| 实例 | 链路范围 | S_bw/S_dyn | bump/C4 | 热 |
|------|---------|-----------|---------|-----|
| 组内 | E_UCIe ∪ E_ondie | UCIe + on-die 零代价 | μbump | 单层：die→ambient（集总 R_vert） |
| 组间 | E_SerDes | SerDes | 信号 μbump ↔ C4 一一对应 | substrate 层 |
| 联合 | 全部 | 混合 | μbump ↔ C4 一一对应 | 三层垂直热网络（见 §3） |

## 3. 联合模型的核心：垂直热耦合（功耗），而非 bump

**bump 是简单对应**：组间 SerDes 每个 lane，die 侧一个信号 μbump、经 interposer 走线后对应 substrate 侧一个 C4 焊球——一一映射，不构成联合建模难点。

**真正的难点在功耗/热的垂直耦合**。组内模型的 interposer 底面温度不是固定 T_ambient，而是 = substrate 顶面温度；substrate 温度取决于组间 SerDes PHY 功耗。耦合链：

```
组间 SerDes 功耗 P_substrate
  → substrate 温度 T_substrate
  → interposer 底面温度 T_bottom
  → 组内 die 温度 T_die
```

三层垂直热网络（die → interposer → substrate → ambient），每层线性：

- 组内：T_die = G_intra^{-1}·(P_die + b_intra(T_bottom))
- 组间：T_substrate = G_inter^{-1}·(P_substrate + b_inter(T_ambient))
- 耦合：T_bottom = T_substrate（interposer 底面 = substrate 顶面）

联合后 T_die 仍线性于 (P_die, P_substrate)——**约束形式不变（线性 LP），只是 G/b 的物理数值关系变了**。对应 V4 §5「集总 R_vert」假设的升级：单一 die→ambient 热阻 → die→interposer→substrate→ambient 分层热阻。

**联合模型的贡献**：独立算 intra/inter 时，组内用固定 T_ambient 作底面边界，漏掉组间 SerDes 功耗对 interposer 底面温度的抬升——分离求解低估组内 die 温度（偏乐观）。

注：垂直热耦合 ≠ 套娃热（plan_inter_group S3 的套娃是组间模型里对 interposer 的横向粗粒度聚合；此处是组内/组间之间的纵向温度传递，正交的另一维度）。

## 4. 代码分层映射（engineer 的"叠层"）

- 基础 model = 现有 `lp.models` 骨架（`Model`/`PerfModel`/`PhysModel` + 各约束模型）。
- 实例化 = `build_scenario` 按三张表装配；热模型从单层 AnalyticNetworkBuilder 升级为可分层（三层垂直热网络）。
- 联合场景 = 新增 scenario（如 `joint`），同时挂组内 + 组间约束，热用三层网络。

## 5. 待定案 / 待核实

- [x] 三层热阻数值（已对标，02 提供）：R_die→interposer≈8、R_interposer→substrate≈75、R_substrate→ambient≈50-80 K·mm²/W（≈1:9:7-10）；垂直主导是 C4 层 + TIM/散热器，μbump 仅 ~10%；集总 R_vert=1.5 是分层加总保守上界
- [ ] interposer 底面温度随 substrate 温度的传递（简单 T_bottom=T_substrate，还是衰减系数）
- [ ] 组间 SerDes 功耗落点：substrate 侧 C4？die 侧 PHY 也发热？决定垂直耦合的输入位置
- [ ] B*_joint 语义：min(intra, inter) 作下界、联合作精确值？论文如何陈述
