# YAML schema v1 核对报告（schema-review）

> DomainExpert 核对，2026-08-21。依据 `thermal-module-catalog.md`（传热模块全景）逐项对照 CodeEngineer 交付的 YAML schema v1（config/thermal/ 三件 + `_yaml.py` 组装器）。
> 结论先行：**schema v1 结构正确、散热逻辑可读、3D/2.5D 同构、M-矩阵校验满足；模块覆盖 v1 覆盖核心 7/12，缺 5 个模块的显式字段（v1.1 建议）**——见下。

---

## 1. 模块覆盖核对（vs thermal-module-catalog §1 目录 A-E）

| 目录模块 | schema v1 表达 | 状态 |
|---|---|---|
| A1 die 纵向 R_vert（die→环境） | `vertical_chain`（from die → to ambient，r_vert_k_per_w） | ✅ 显式 |
| A2 散热板/heat sink | heatsink 变体：`vertical_chain` to 边界节点 heatsink（R_vert 0.8 更小） | ✅ 显式（boundary 节点即散热声明，路径变化可见） |
| A3 TIM/lid（FCBGA 链） | —（并入 vertical_chain 的 R_vert，未拆 TIM/lid 独立段） | ⚠️ 隐性（R_vert 可含，无独立字段） |
| A4 背面冷却 h（晶圆级） | —（无 `backside`/`h_cooling` 字段） | ❌ 缺（v1.1：建议） |
| B1 面邻接（半单元串联） | `face_adjacency`（k_interposer_w_mk、t_interposer_mm；geometry 提供 d/gap） | ✅ 显式 |
| B2 underfill 系数 | —（face_adjacency 无 underfill 修正系数） | ❌ 缺（v1.1：建议） |
| C1 μbump 热阻 | —（并入 vertical_chain R_vert，无独立 μbump 字段） | ⚠️ 隐性（R_vert 可含） |
| C2 C4 热阻 | —（同 C1） | ⚠️ 隐性 |
| C3 interposer 横向扩散 | face_adjacency 的 k_interposer（即横向扩散） | ✅ 显式 |
| D1 TSV 垂直线链 | `tsv` 边类型已定义（组装器支持，v1 无示例 YAML） | ✅ 类型有，示例缺 |
| D2 hybrid bonding | `hybrid` 边类型已定义 | ✅ 类型有，示例缺 |
| D3 层间横向 | 3D 集总：face_adjacency 层聚合；完整多层形态（K×N + 层间支路）v1 未做 | ⚠️ 集总有，显式层间缺（扩展方向） |
| E1 substrate/PCB 平面扩散 | —（无 substrate 平面扩散模块） | ❌ 缺（v1.1：建议/后置） |
| E2 环境边界 ambient | `boundary` 节点（temperature_k）+ vertical_chain 到 boundary | ✅ 显式 |

**覆盖统计**：显式 7/12（A1/A2/B1/C3/D1/D2/E2）、隐性 3/12（A3/C1/C2——并入 R_vert，可接受但不可独立配置）、缺 2/12（A4 背面冷却 h、B2 underfill——v1.1 建议）、扩展 1（D3 完整多层、E1 substrate——后置）。

---

## 2. 散热逻辑可读性核对

**✅ 通过（v1 已达成作者"一眼看懂"目标）**：
- 2p5d-two-die.yaml 头部注释："die0 ──face_adjacency── die1 / die0 ──vertical_chain── ambient"——传热路径一目了然；
- heatsink 变体注释："vertical_chain 改走 heatsink 中间边界……R_vert 更小 = 强散热……这是散热逻辑可见的演示"——**加散热板 → 传热路径变化**的用户读法成立；
- boundary 节点（ambient/heatsink）即散热声明（温度 + 到边），每 die 散热路径可见。

**可读性建议（v1.1，非阻塞）**：
- A4 背面冷却若加，用 `backside: {h_w_per_m2k, t_coldplate_k}` 块（每节点或全局）——保持"每节点散热方式可见"；
- 建议 YAML 顶部加"冷却摘要"注释（如 "die0: vertical_chain→ambient (R=1.5)"），让"每个 die 怎么散热"更显式。

---

## 3. 3D/2.5D 同 schema 核对

**✅ 满足**：3d-stack-two-lumped.yaml 与 2.5D 完全同构——nodes 用 `type: stack`（含 layers）+ edges 结构不变（face_adjacency + vertical_chain）；组装器 node 类型统一处理（die/stack 均为自由节点，stack 记 layers）。**节点/边类型不同、结构同一**——作者"3D/2.5D 共享同一 schema"达成。
- 3D 集总：stack 节点 + vertical_chain R_vert=2.4（=1.2+1.2 串联，注释说明）——与 thermal-g-construction §2 集总近似一致（纵向热主导）；
- 完整多层形态（K×N 节点 + tsv/hybrid 边）v1 未做——**tsv/hybrid 边类型已定义**（组装器支持），扩展只需 YAML 示例。

---

## 4. M-矩阵条件可表达

**✅ 满足**：组装器 `_yaml.py` 行 113-116——每节点必须 ≥1 散热路径（vertical_chain/ground），G 对角元 ≤ 0 则 `ValueError`（"节点 X 无散热路径（G 对角非正）"）；`ThermalNetworkBuilder.precompute/_make_network` 保留 M-矩阵不变量校验（G⁻¹≥0）。**"无散热路径被拒绝"成立**。

---

## 5. 缺什么字段/参数 → v1.1 建议（必须/建议/后置）

| # | 项 | 目录模块 | 优先级 | v1.1 建议 |
|---|---|---|---|---|
| 1 | **背面冷却 h + 冷板温度**（晶圆级） | A4 | **建议**（晶圆级是验证建议构型，survey §4） | `cooling` 块或节点级 `backside: {h_w_per_m2k: <float>, t_coldplate_k: <float>}`（或复用 vertical_chain to boundary 但 h·A 形式） |
| 2 | **underfill 修正系数** | B2 | 建议 | `face_adjacency` 加 `k_underfill_w_mk` 或 `alpha_underfill`（默认 1.0 = 无修正） |
| 3 | **μbump/C4 独立段** | C1/C2 | 建议（可配置性；当前并入 R_vert 可接受） | `vertical_chain` 可选子段 `segments: [{type: ubump|c4|tim|lid, ...}]`（显式链）或保留 R_vert 集总 |
| 4 | **TIM/lid 段** | A3 | 后置（FCBGA 非当前验证目标） | 同 #3 segments |
| 5 | **substrate/PCB 平面扩散** | E1 | 后置 | `substrate` 平面扩散块（多跳横向）——当前无 |
| 6 | **TSV/HB 示例 YAML** | D1/D2 | 建议（类型已定义，缺示例） | 补 `3d-stack-two-explicit.yaml`（K×N + tsv/hybrid 边）演示完整多层 |
| 7 | **多温度边界** | E2 | 建议 | 已支持（每 boundary 独立 temperature_k）；如需分层 T_max 见 t_max_k 扩展 |
| 8 | **TSV 并联数** | D1 | 建议 | `tsv` 边加 `n_vias`/`r_via` 或直接 r_tsv_k_per_w（当前类型定义未见字段细节） |
| 9 | **h·A 面积字段** | A4 | 必须（若加 A4） | 节点 geometry 已含 w/h → 面积可由组装器计算（h·A_node），无需重复字段 |

**必须项**：无（v1 核心 7 模块 + 校验 + 可读性已满足作者目标）。
**建议项（v1.1）**：#1 背面冷却 h（晶圆级验证需要）、#2 underfill、#6 TSV/HB 示例、#8 TSV 并联数。
**后置项**：#3/#4 segments（可配置性增强）、#5 substrate 扩散。

---

## 6. 总结（给 master）

- **schema v1 不缺核心**：传热路径可读、3D/2.5D 同构、M-矩阵校验、加散热板路径变化可见——作者指令达成；
- **缺**：晶圆级背面冷却 h（A4，验证建议构型）、underfill 系数（B2）、TSV/HB 示例 YAML（类型已定义）——均**建议级**非必须；
- **隐性**：μbump/C4/TIM/lid 并入 R_vert（可接受，v1.1 可加 segments 显式化）；
- **后置**：substrate 平面扩散、3D 完整多层显式、分层 T_max。
- v1.1 建议清单见 §5（必须 0 / 建议 4 / 后置 3）。
