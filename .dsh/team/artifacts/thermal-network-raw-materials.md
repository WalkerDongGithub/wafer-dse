# 热阻网络原始材料（thermal-network-raw-materials）

> **产出**：LiteratureSearcher（master 分派支撑 ①：为 DomainExpert 构建 G 提供 2.5D/3D/晶圆级原始材料）
> **日期**：2026-08-21
> **配套**：`thermal-network-survey.md`（调研结论）；本文档是**原始材料**（公式/参数/引用），供 `thermal-g-construction.md` 构建对照。
> **来源标注**：【标准物理】= 传热学通识（可安全引用）；【论文】= 引文论文内容（已核验引用，公式细节以论文全文为准）；【待核实】= 参数/公式尚未全文核对，构建 G 时须标出或补数。
> **作者硬要求**：物理量一定要准；凡缺参数/来源不明处标出，不默认。

---

## 0. 总形式（作者概念定案，2026-08-21）

- G·T=P+b 是**抽象总形式**：T 未必是每 die 温度；P 是 die 功耗向量。
- 热模型本质 = 输入功耗 P → 输出温度凸函数：
  T(P) = max_i T_i(P)，T_i(P) = (G⁻¹(P+b))_i
  G 为 M-矩阵 ⇒ G⁻¹ ≥ 0 ⇒ 每个 T_i 是 P 的**仿射**函数 ⇒ max 是 P 的**凸**函数。
- 封装差异全部收进 G、b 的参数化（经书 §2.6 旋钮：网格粒度 × 封装方式）。

## 1. 通用热阻公式【标准物理】

| 项 | 公式 | 说明 |
|---|---|---|
| 串行传导（多层） | R = Σ_k t_k / (k_k · A) | Fourier 定律；各层厚度/导热率/面积 |
| 横向面内扩散（相邻节点） | R_lat ≈ L / (k · A_cross)，A_cross = t·W | L=间距，t=厚度，W=宽度（截面积） |
| 面邻接电导（die 间） | G_adj = k_eff · L_shared / d | L_shared=共享边长，d=间距，k_eff=有效导热率（interposer/underfill 复合）【论文 MFIT 式，精确式待核实】 |
| 对流边界 | g_conv = h · A | h 数量级：自然对流 5–25；强制风冷 25–250；水冷板 10³–10⁴ W/m²K |
| 稳态节点方程 | G T = P + b；b = g_vert · T_amb | 对地（环境/冷板）支路 |
| M-矩阵性 | G = 图拉普拉斯 + 对角对地支路 → 严格对角占优 → G⁻¹ ≥ 0 | 所有无源电阻网络成立【标准】 |

## 2. 2.5D interposer（MFIT 式，我们现状）【论文 mfit2025 + IMPLEMENTATION_MAP】

- **网络形态**：die 节点网格；die 间 **lateral 面邻接**（经 interposer RDL + underfill 横向耦合）；纵向链 die→μbump→interposer→C4→substrate→ambient。
- **公式**：
  - 纵向链（每 die i）：R_vert,i = R_μbump + R_inter,i + R_C4 + R_sub,i（串联，各段 t/(kA) 或 lumped per-area）【标准物理 + 论文形态】
  - 面邻接：G_adj,ij = k_eff,interposer · L_ij / d_ij【论文 MFIT 式，精确式**待核实**】
  - underfill：横向弱耦合（k_underfill ≈ 0.2–0.5 W/mK，远小于硅 ~130–150 W/mK）【待核实数值】
- **参数**：μbump pitch/高度（对齐 UCIe 45μm bump，config YAML）；C4 pitch；interposer 厚度 ~50–100μm 硅（k_Si ≈ 130–150 W/mK）；TSV 若存在 k_eff【参数数值以 config/params/*.yaml 为准】
- **边界**：b_die 常数（die 向散热板）；b_inter 变量（interposer→substrate，经书 §4 C4）；T_max die 结温。
- **与我们实现的对应**：`AnalyticNetworkBuilder` = 此形态的 die 级约化（面邻接 + 集总 R_vert；无显式 T_inter/T_sub 回路，L1 稳态）——一致性已在 survey 确认 ✅。

## 3. 3D 堆叠（TSV / hybrid bonding）【论文 3dice2010】

- **网络形态**：每层 die 为节点（多层 T_die）；纵向 TSV/HB 链 die₁→…→die_k→substrate；各层独立横向扩散。
- **公式**：
  - TSV 阵列纵向：R_TSV,array = R_via / N_vias（并联），R_via ≈ t_via/(k_Cu·A_via)，k_Cu ≈ 400 W/mK【标准物理 + 3D-ICE 形态】
  - hybrid bonding：R_HB 极低（µm 间距 Cu-Cu、大面积并联）【论文 3D-ICE 涵盖；数值待核实】
  - 每层横向同 §1【标准物理】
- **参数**：TSV 直径/高度/密度；HB pitch；层厚；各层功率分布【待核实/以论文全文为准】
- **边界**：每层 T_max；顶层主散热或双面散热。
- **早期集总近似（若采用）**：把每堆叠压成一条垂直线链 R_vert（TSV/HB 链 + 各层厚度），横向按层聚合——**成立条件**：纵向热主导、层间横向弱耦合（survey §4 已述）。

## 4. 晶圆级（Cerebras/Dojo 类）【论文 lie2023hcs + dojo2022hc/dojo2023micro + chen2024waferscale】

- **网络形态**：大面积 die 网格（N 大）；面内多跳横向扩散；**背面整体冷却**（每节点 g_vert 均匀或分片）。
- **公式**：
  - 面内扩散同 §1（大网格多跳）【标准物理】
  - 背面冷却：g_vert,i = h_cooling · A_node；水冷板 h ~ 10³–10⁴ W/m²K【标准数量级；Cerebras/Dojo 具体冷却参数**待核实**（白皮书级，白名单外）】
  - 功率密度：ΣP/A ≤ 上限——Chen ISCA'24 实证 radix 受 power density 限制【论文 chen2024waferscale】
- **参数**：die 网格数/尺寸；冷却 h；大面积横向扩散 k_eff【参数待核实/白名单外数据】
- **边界**：ambient = 冷板温度；T_max。
- **验证阶段建议**：大网格 + 均匀 g_vert 即现有 `SteadyStateModel` 可跑（只换 config YAML 参数组，不改求解器）。

## 5. 每构型 → G 构建速查（给 DomainExpert）

| 构型 | 节点集 | G 对角 | G 非对角 | b | M-矩阵 |
|---|---|---|---|---|---|
| 2.5D | die 集合 | Σ垂直支路电导 + Σ面邻接电导 | −面邻接电导 | b_die 常数 + b_inter 变量 | ✓（图拉普拉斯+对角） |
| 3D | die×层 | 同上（层内）+ 纵向链电导 | 同上（层内）+ 层间 TSV/HB | 顶层散热 b | ✓ |
| 晶圆级 | die 网格（大 N） | 同上 + g_vert（背面冷却） | −面邻接电导 | g_vert·T_coldplate 均匀 | ✓ |

## 6. 待核实清单（物理量准确性硬要求）

| 项 | 状态 | 影响 |
|---|---|---|
| MFIT 面邻接/纵向精确公式 | 待全文核对（arXiv:2410.09188） | G_adj 具体形式 |
| 3D-ICE TSV 模型公式细节 | 待全文核对（ICCAD'10） | 3D 纵向 R |
| underfill k 值（0.2–0.5 W/mK） | 待核实数值 | 横向弱耦合项 |
| 晶圆级冷却 h / Cerebras/Dojo 散热参数 | 待核实（白皮书级，白名单外） | g_vert 数量级 |
| μbump/C4/interposer 厚度与 k | 以 config/params/*.yaml 为准（UCIe spec 对齐） | 纵向链数值 |
