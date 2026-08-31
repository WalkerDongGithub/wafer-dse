# G 构建逻辑总结（thermal-g-construction）

> DomainExpert 主持产出，2026-08-21。作者概念定案：$\mathbf{G}\mathbf{T} = \mathbf{P} + \mathbf{b}$ 是**抽象形式**——T 未必是每 die 温度，P 是 die 功耗向量，总形式；热模型本质 = **输入功耗 P → 输出温度凸函数**。
> **硬要求**：本位置无明确积累——所有实现必须忠实反映调研材料 `thermal-network-survey.md`（LiteratureSearcher 产出，2026-08-21），物理量要准，不得让人觉得明显有毛病。
> 权威层级：经书（V5 §2.6 符号/旋钮）> IMPLEMENTATION_MAP.md（实现对应）> 本文件（G 构建逻辑，派生）。

---

## 0. 统一抽象视角（作者概念定案）

$$
\mathbf{G}\mathbf{T} = \mathbf{P} + \mathbf{b}, \qquad T_i(\mathbf{P}) = \left(\mathbf{G}^{-1}(\mathbf{P}+\mathbf{b})\right)_i, \qquad T(\mathbf{P}) = \max_i T_i(\mathbf{P})
$$

- $\mathbf{G}$ 为 **M-矩阵**（对角占优，$\mathbf{G}^{-1} \ge 0$）⟹ 每个 $T_i$ 是 $\mathbf{P}$ 的**仿射函数**（系数 = $\mathbf{G}^{-1}$ 行，非负）⟹ $T(\mathbf{P}) = \max_i$ 是 $\mathbf{P}$ 的**凸函数**（仿射的逐点最大 = 凸）。
- **封装差异全部收进 $\mathbf{G}$、$\mathbf{b}$ 的参数化**——经书 §2.6 两旋钮：网格粒度（决定 G 维度）× 封装方式（决定 G 元素值）。
- 四种封装构型的网络都是**无源电阻网络**（节点间电导 + 节点对地电导）→ 导纳矩阵 = 图拉普拉斯 + 对角阵，严格对角占优 → M-矩阵 → **形式总可映射**（survey §0）——问题只在节点/参数保真度。

---

## 1. 2.5D interposer 的 G 构建（现状，MFIT 式）

**节点**：die（N 个 die 节点）。
**支路**：
- **die 间横向面邻接**（经 interposer + underfill）：半单元串联热导
  $$
  G_{\text{lateral},ij} = \frac{k_{\text{inter}} \cdot \text{overlap}_{ij} \cdot t_{\text{inter}}}{\frac{d_i}{2} + \frac{d_j}{2} + \text{gap}_{ij}}
  \quad [\text{W/K}]
  $$
  其中 $k_{\text{inter}}$ = interposer 有效热导率 [W/(m·K)]（硅 ~130–150，underfill 复合修正），$\text{overlap}_{ij}$ = die i,j 共享边长 [m]，$t_{\text{inter}}$ = interposer 厚度 [m]，$d_i/2$ = die i 半宽 [m]，$\text{gap}_{ij}$ = die 间距 [m]（半单元串联：die 中心到边 + gap 半宽）。【标准物理：k·A/L 形式；MFIT 精确式**待全文核实**（arXiv:2410.09188）】underfill 横向弱耦合（k_underfill ≈ 0.2–0.5 W/mK，远小于硅）【待核实数值】。
- **每 die 纵向集总**（die → μbump → interposer → C4 → substrate → ambient）：$g_{\text{vert},i} = 1/R_{\text{vert},i}$ [W/K]，纵向链串联
  $$
  R_{\text{vert},i} = R_{\mu\text{bump},i} + R_{\text{inter},i} + R_{C4,i} + R_{\text{sub},i}, \quad \text{各段 } R_k = \frac{t_k}{k_k A_k} \text{（或 per-area 集总）}
  $$
  【标准物理：Fourier 串联；μbump/C4/interposer 厚度与 k 以 config/params/*.yaml 为准（UCIe spec 对齐）】
**边界条件**：$\mathbf{b}_{\text{die}} = g_{\text{vert}} \cdot T_{\text{amb}}$（die 向散热板/环境）；$\mathbf{b}_{\text{inter}}$ 变量（§4 C4，Substrate 温度反馈为 Interposer Ambient）。
**G 形态**：$N \times N$ 对称，对角元 $G_{ii} = \sum_j G_{\text{lateral},ij} + g_{\text{vert},i}$，非对角元 $-G_{\text{lateral},ij}$——M-矩阵（对角占优）。

**对照 survey §2/§3（2.5D 行）**：✅ 即 `AnalyticNetworkBuilder` 现状（MFIT 式面邻接 + 集总 $R_{\text{vert}}$，die 级粒度，$b = g_{\text{vert}}T_{\text{amb}}$，无显式 T_inter/T_sub 回路 = L1 稳态约化）。待补参数（survey）：interposer 横向 R、μbump/C4 纵向 R、underfill 耦合系数（config YAML 对齐，不硬编码）。
**单位核对**：$k$ [W/(m·K)] × 面积 [m²] ÷ 长度 [m] = [W/K] ✅；$R_{\text{vert}}$ [K/W] → $g_{\text{vert}}$ [W/K] ✅；$g_{\text{vert}} \cdot T_{\text{amb}}$ [W/K·K = W] ✅（与 P 同单位，b 为常数项）。

---

## 2. 3D 堆叠的 G 构建（survey 分档 ⚠️ 需改造）

**完整多层节点形态**（精确）：
- 每层 die 一个节点集 $\mathbf{T}_{\text{die}}^{(1..K)}$；层间纵向支路 = TSV/hybrid bonding 热阻（$\mu$m 间距 HB 低 R、TSV 阵列 R）；每层独立横向面邻接。
- TSV 阵列纵向（并联）：$R_{\text{TSV,array}} = R_{\text{via}} / N_{\text{vias}}$，$R_{\text{via}} \approx \frac{t_{\text{via}}}{k_{Cu} \cdot A_{\text{via}}}$，$k_{Cu} \approx 400$ W/mK【标准物理 + 3D-ICE 形态；公式细节待 3D-ICE 全文核对】；HB $R$ 极低（µm 间距 Cu-Cu 大面积并联）【数值待核实】。
- G 扩维为 $KN \times KN$（K 层 × N die/层）：纵向链 $G_{\text{vert,TSV/HB}}$ 连接相邻层同位置 die，横向 $G_{\text{lateral}}^{(l)}$ 连接同层邻接 die。
- **适用条件**：层间横向耦合不可忽略、需逐层结温解析（每层 $T_{\max}$ 独立约束）。

**集总近似（每堆叠一条垂直线链）**：
- 把 TSV/HB 链压成单 $R_{\text{vert}}$（$R_{\text{vert}} = \sum_l R_{\text{vert}}^{(l)}$ 串联），每堆叠一个节点，横向按层聚合（跨层横向弱耦合时忽略或聚合）。
- G 形态回到 $N \times N$（N = 堆叠数），每节点 $g_{\text{vert}} = 1/\sum_l R_{\text{vert}}^{(l)}$。
- **适用条件（survey §4）**：**纵向热主导、层间横向弱耦合**——此时垂直线链近似成立；精确多层需 G 扩维（后期，需求明确再动）。

**G 形态对照**：完整 = 多层块结构（每层块 + 层间耦合块，仍 M-矩阵）；集总 = 同 2.5D 单层形态（仅 $R_{\text{vert}}$ 换为串联和）。

---

## 3. 晶圆级（wafer-level）的 G 构建（survey 分档 ✅ 可直接采用）

**节点**：大面积 die 网格（成百上千 die 节点）。
**支路**：
- **面内横向扩散** $R_{\text{lateral}}$：die 网格相邻节点横向热导（大面积面内扩散，同 2.5D 横向公式但网格更大）；
- **背面整体冷却**：每 die 节点 $g_{\text{vert},i} = h_{\text{cooling}} \cdot A_{\text{node}}$ [W/K]（背面水冷/风冷冷板；$h$ 数量级：自然对流 5–25、强制风冷 25–250、**水冷板 10³–10⁴** W/(m²·K)）【标准数量级；Cerebras/Dojo 具体冷却参数**待核实**（白皮书级，白名单外）】。
**边界条件**：$\mathbf{b} = g_{\text{vert}} \cdot T_{\text{coldplate}}$（均匀常数，ambient = 冷板温度）；**功率密度上限**为额外约束（Chen ISCA'24：radix 受 power density 限制——$\sum P_i / A_{\text{wafer}} \le \text{PD}_{\max}$，非热网络本身但常与热联合绑定）。
**G 形态**：$N \times N$ 稀疏网格拉普拉斯 + 均匀对角 $g_{\text{vert}}$——M-矩阵（对角占优，每行和 ≥ $g_{\text{vert}} > 0$）。

**对照 survey §3（晶圆级行）/§4**：✅ 大 die 网格 + 每节点 $g_{\text{vert}}$（背面水冷/风冷）+ 面内横向扩散——正是 G 的 die 级网格形式。**验证阶段建议首试此构型对照**（survey §4，与 2.5D 一起覆盖"大面积平面散热"与"interposer 横向耦合"两种网络形态）。

---

## 4. 统一抽象视角：三者收敛到同一凸函数形式

$$
T(\mathbf{P}) = \max_i \left(\mathbf{G}^{-1}(\mathbf{P}+\mathbf{b})\right)_i, \quad \mathbf{G} \text{ M-矩阵}, \quad T \text{ 是 } \mathbf{P} \text{ 的凸函数}
$$

**G 结构差异表**（节点/支路/热阻公式/参数来源）：

| 构型 | 节点 | 支路 | 热阻公式 | 参数来源 |
|---|---|---|---|---|
| **2.5D interposer** | N die | die 间横向面邻接 + 每 die 纵向集总 | $G_{\text{lateral}} = k\cdot\text{overlap}\cdot t / (\frac{d_i}{2}+\frac{d_j}{2}+\text{gap})$；$R_{\text{vert}} = R_{\mu\text{bump}}+R_{\text{inter}}+R_{C4}+R_{\text{sub}}$（串联），$g_{\text{vert}} = 1/R_{\text{vert}}$ | MFIT 式（mfit2025，精确式待全文核实）；underfill 弱耦合 k≈0.2–0.5 待核实；YAML（μbump/C4/interposer） |
| **3D 堆叠（完整）** | K×N（K 层 × N die/层） | 层间 TSV/HB 纵向 + 各层横向 | $R_{\text{TSV,array}} = R_{\text{via}}/N_{\text{vias}}$，$R_{\text{via}} \approx t_{\text{via}}/(k_{Cu}A_{\text{via}})$，$k_{Cu}\approx 400$；HB 极低 R | 3D-ICE（3dice2010，公式细节待核对）；后期 |
| **3D 堆叠（集总近似）** | N 堆叠 | 每堆叠一条垂直线链 | $g_{\text{vert}} = 1/\sum_l R_{\text{vert}}^{(l)}$；横向按层聚合 | 同上；**条件：纵向热主导、层间横向弱耦合** |
| **晶圆级** | 大面积 die 网格 | 面内横向扩散 + 均匀背面 $g_{\text{vert}}$ | $G_{\text{lateral}}$（网格）；$g_{\text{vert},i} = h_{\text{cooling}} \cdot A_{\text{node}}$（$h$ 水冷 10³–10⁴）；PD 上限额外约束 | Cerebras/Dojo（lie2023hcs/dojo*，冷却参数待核实）+ Chen ISCA'24（PD 限制）；YAML |

**共同点**：全部为无源电阻网络 → M-矩阵 → $T(\mathbf{P})$ 凸函数；差异只在节点粒度、层数、支路参数——**封装差异全部收进 G、b 参数化**（作者定案）。

---

## 5. 物理量核对（逐项，与 thermal-network-survey.md 一致）

| 量 | 公式 | 单位 | 核对 |
|---|---|---|---|
| $G_{\text{lateral},ij}$ | $k\cdot\text{overlap}\cdot t / (\frac{d_i}{2}+\frac{d_j}{2}+\text{gap})$ | W/K | [W/(m·K)]·[m]·[m]/[m] = W/K ✅ |
| $g_{\text{vert}}$ | $1/R_{\text{vert}}$ | W/K | 1/(K/W) = W/K ✅ |
| $b_{\text{die}}$ | $g_{\text{vert}} \cdot T_{\text{amb}}$ | W | (W/K)·K = W ✅（与 P 同单位） |
| $G_{ii}$ | $\sum_j G_{\text{lateral},ij} + g_{\text{vert},i}$ | W/K | 对角占优 ⟹ M-矩阵 ✅ |
| $T_i$ | $(G^{-1}(P+b))_i$ | K | (K/W)·W = K ✅ |
| $T(\mathbf{P})$ | $\max_i T_i$ | K | 仿射的 max = 凸 ✅ |
| $R_{\text{vert}}$（2.5D） | $R_{\mu\text{bump}}+R_{\text{inter}}+R_{C4}+R_{\text{sub}}$（串联，各段 $t/(kA)$） | K/W | 串联求和 ✅ |
| $R_{\text{TSV,array}}$（3D） | $R_{\text{via}}/N_{\text{vias}}$（并联），$R_{\text{via}} \approx t_{\text{via}}/(k_{Cu}A_{\text{via}})$ | K/W | 并联分压 ✅ |
| $g_{\text{vert}}$（晶圆级） | $h_{\text{cooling}} \cdot A_{\text{node}}$ | W/K | (W/(m²·K))·m² = W/K ✅ |
| 3D 集总 $g_{\text{vert}}$ | $1/\sum_l R_{\text{vert}}^{(l)}$ | W/K | 串联热阻求和 ✅ |
| 晶圆级 PD 上限 | $\sum P_i / A \le \text{PD}_{\max}$ | W/m² | Chen ISCA'24 radix/power-density ✅ |

**参数来源纪律**：全部来自 config YAML（`src/physical/config/`）或文献（mfit2025 / 3dice2010 / hotspot2006 / lie2023hcs / dojo* / chen2024waferscale，paper.bib 核验版）；**禁止硬编码**（STYLE.md）。MFIT 为热网络构建依据（IMPLEMENTATION_MAP.md 已标），传热学细节不展开（经书纪律：热只引 MFIT）。

---

## 6. 与经书/实现的对齐

- **经书 §2.6**：两旋钮（网格粒度 × 封装方式）⟹ 本文件三构型 G 构建就是"封装方式旋钮"的具体化；$b_{\text{die}}$ 常数、$b_{\text{inter}}$ 变量（§4 C4）与 2.5D 对应。
- **IMPLEMENTATION_MAP.md**：`AnalyticNetworkBuilder` = MFIT 式面邻接 + 集总 R_vert（2.5D 现状）；3D 完整/晶圆级为扩展方向（survey §4 分档）。
- **验证阶段建议（survey §4）**：2.5D（现状）+ 晶圆级背面冷却（大网格 + 均匀 g_vert）两种直接跑现有 `SteadyStateModel`（换 YAML 参数组，不改造求解器）；3D 集总近似条件（纵向热主导）明确后可试；3D 完整扩维留后期。

### 6.1 heatsink 节点化（作者纠正 2026-08-21：heatsink ≠ ambient）

**heatsink 是有自身热阻与温升的实体节点，不是固定温度边界**——建模三件套（依据 thermal-modeling-dimensions.md §4/§5）：

- **依据（理论）**：$R_{\text{hs}} = R_{\text{spread}} + R_{\text{conv}} = R_{\text{spread}} + 1/(h \cdot A_{\text{fin}} \cdot \eta_{\text{fin}})$——扩散热阻（Lee 模型，lee1995spreading/lee2008spread）+ 对流热阻（incropera 翅片理论）；翅片效率 $\eta_{\text{fin}} = \tanh(mL)/(mL)$，$m = \sqrt{2h/(k_{\text{fin}} t_{\text{fin}})}$；
- **逻辑（近似）**：heatsink 单节点（紧凑 CTM 标准，HotSpot spreader/sink 层同类；JEDEC Rθja 双热阻体系）——节点温升 $T_{\text{hs}} - T_{\text{amb}} = R_{\text{hs}} \cdot Q$ 显式建模；加散热板 = 新增显式环节 die→TIM/lid→heatsink→ambient（非"边界换 R"）；
- **局限（不成立时）**：自然对流（η_fin 显著 <1、非均匀）、大翅片/多热源、强梯度 → 多节点/翅片级或 CFD；仅 Q 小或 R_hs 极小时可并入 b 作固定边界近似（须说明条件）。

**G 落点（修正原"边界换 R"）**：heatsink 为节点进 G——$G_{\text{hs,hs}} += g_{\text{hs} \to \text{amb}}$（$g_{\text{hs} \to \text{amb}} = 1/R_{\text{hs}}$），$b_{\text{hs}} += g_{\text{hs} \to \text{amb}} T_{\text{amb}}$；die→heatsink 经 TIM/lid 边（非对角）。**不消元进 b**（有自身温升）。

### 6.2 3D 集总 vs 展开的建模依据（三件套）

- **依据**：纵向热主导时层链串联（Fourier）；TSV 阵列并联（$R_{\text{TSV,array}} = R_{\text{via}}/N_{\text{vias}}$）；
- **逻辑**：集总快速估计（每堆叠一条垂直线链，避免 K×N 扩维）；展开精确（K×N + tsv/hybrid 边 + 层间横向）；
- **局限**：集总不成立条件 = 层内温度不均 / TSV 密度低 / 层间横向耦合强 / 需逐层结温；实现侧留"层间横向/纵向电导比值阈值"判据。

---

## 版本记录

- v0.1（2026-08-21）：G 构建逻辑总结（作者概念定案 + survey 对照 + 三构型 + 物理量核对）。
- v0.2（2026-08-21）：heatsink 节点化纠正（§6.1，三件套）+ 3D 集总/展开建模依据（§6.2）——依据 thermal-modeling-dimensions.md（Searcher 调研 v2）。
