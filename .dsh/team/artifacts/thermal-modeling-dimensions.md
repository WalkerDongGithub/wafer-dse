# 热分析建模维度（散热模式全景 + 三个说服力论证）（thermal-modeling-dimensions）

> **产出**：LiteratureSearcher（master 调研任务 v2，2026-08-21 范围校准版）
> **校准**：不钻传热学牛角尖——服务论文故事"**不同散热模式 = 不同建模维度**"，覆盖到"讲得圆"即可（B 红线：简洁）。
> **用法**：为 G·T=P+b 的建模与论文论证提供"散热模式 → 建模维度"全景 + 三个"说服我"问题的论证。

---

## 1. 散热模式 → 建模维度全景（在 G·T=P+b 里怎么落）

| 散热模式 | 建模维度 | G·T=P+b 落点 | 关键参数 |
|---|---|---|---|
| **背面散热板/翅片（heatsink）** | **实体节点**（R_spread + R_conv 串联到 ambient，非边界消元）| heatsink 节点进 G；对地支路 g = 1/R_hs（R_hs = R_spread + 1/(h·A_fin·η_fin)）；b += g·T_amb | R_spread（Lee 模型：热源/基板面积比、厚度）；h；A_fin；η_fin |
| **冷板（cold plate，水冷）** | **实体节点/接地**（背面均匀 g）| 每节点 g_vert = h_cooling·A_node 对角；b = g_vert·T_coldplate | h ~ 10³–10⁴ W/(m²·K) |
| **微流道（microfluidic）** | **接地/链段**（内嵌冷却 = 高 h 对地支路）| 每节点 g_micro = h_eff·A（或并入 die 垂直链段）| h_eff 极高（10⁴–10⁵，对流增强/相变）；泵功耗（额外 P 项）|
| **浸没（immersion）** | **接地**（全暴露表面对地支路）| 每暴露节点 g = h_imm·A；b = g·T_fluid | h 中-高；沸腾时非线性（近似窗）|
| **TIM / lid** | **链段**（并入 die 垂直链，非节点）| R_TIM = t/(k·A) 串联进 R_vert；lid 视面内扩散决定是否节点 | t（25–100μm）、k（3–10 W/mK）|
| **heat spreader** | **实体节点**（面内扩散）或合并 | R_spread 节点化（扩散显著时）或并入 | k（铜/铝 200–400）、厚度 |
| **晶圆级背面整体冷却** | **接地**（大面积网格 + 均匀 g_vert）| 大 N 网格 + g_vert = h·A_node 对角；b = g_vert·T_coldplate | h（水冷/风冷）；A_node |

**一句话故事**：散热模式的差异 = 对地支路（g = h·A 或 1/R_hs）与链段（R_TIM、R_spread）的不同组合——全部收进 G、b 参数化，G 始终是"图拉普拉斯 + 对地支路"的 M-矩阵。

## 2. 三个"说服我"问题的论证

### a. 散热板为什么可建模成"一个节点 + R_spread+R_conv 到 ambient"？

**逻辑**：heatsink 是热流路径上的实体，热流 = die → 基板（扩散，R_spread）→ 翅片表面（对流，R_conv）→ 流体（ambient）。三段路径在热流方向上**串联**，总热阻 R_hs = R_spread + R_conv = R_spread + 1/(h·A_fin·η_fin)；节点温度 T_hs = T_amb + R_hs·Q（自身温升显式）。紧凑模型把整块散热板收进一个节点，前提是**基板近似等温**（高 k 铜/铝、薄 → 面内温度梯度小）。

**理论依据**：串联热阻（Fourier + Newton，incropera）；R_spread 由扩散热阻模型给出（lee1995spreading，验证版 lee2008spread）；翅片效率 η_fin = tanh(mL)/(mL)（incropera 标准式，m = √(2h/(k_fin·t_fin))）。

**失效条件（何时多节点/扩散修正）**：① 热源面积远小于基板面积 → R_spread 显著、基板温度场非均匀 → 需多节点或扩散修正；② 自然对流下 η_fin 显著 < 1 → 翅片自身温度梯度不可忽略 → 翅片级节点或解析翅片温度分布；③ 多热源分布 → 基板等温假设失效。

### b. 3D 堆叠主流是按 stack 建模吗？集总有什么问题？

**现状**：工程粗筛常按 **stack 集总**（每堆叠一条垂直线链，g_vert = 1/Σ_l R_vert^(l)）；精确分析按**每层节点**（3D-ICE 网格模型，层间 TSV/HB 支路 + 每层横向，3dice2010）。

**集总的问题**：
1. **层内不均被抹平**——各层功率密度不同（计算层 vs 存储层），集总用平均功率掩盖层内热点；
2. **TSV 密度被等效化**——TSV 纵向热导 ∝ 密度，集总用等效 R 掩盖 TSV 布局差异；
3. **层间横向耦合被忽略**——每层独立横向扩散，层间仅纵向相连（3D 堆叠中层间横向通过 TSV 阵列边缘/填料弱耦合）；
4. **每层 T_max 约束丢失**——上层结温 ≠ 下层结温，T_max 是逐层约束（完整形态 K×N 节点，thermal-g-construction §2）。

**何时集总可接受（适用条件判据）**：纵向热主导（TSV/HB 链 R 小）、层间横向弱耦合、每层功率相近——用**层间横向电导/纵向电导比值阈值**检查（与 thermal-g-construction §2 一致，3D 扩展期实现）。

### c. 每个传热图/模型的支路对应什么物理路径？

| 支路类型 | 物理路径 | 理论依据 | G·T=P+b 表示 |
|---|---|---|---|
| **传导支路** | 固体路径（die 内、interposer、TSV、基板、TIM/lid）| Fourier：G = k·A/L | G 非对角（横向）/ 对角链段（纵向）|
| **串联链** | 沿热流方向的多段固体（die→TIM→lid→heatsink 基板）| 串联热阻 R = Σ t_k/(k_k·A) | R_vert 链 → g = 1/R_vert |
| **对流支路** | 固-流界面（翅片表面、冷板、背面、浸没表面、微流道壁）| Newton：g = h·A | 对地支路（对角）+ b = g·T_fluid |
| **固定温度边界** | 无限大热库/恒温冷源近似 | Dirichlet 消元 | 节点从 T 消去，b_i += G_ij·T_fixed |
| **功耗源项** | die 发热（焦耳/动态功耗）| Neumann | P 向量 |

**一致性检查**：图上每个支路都能对应一条物理路径；G 的元素 = 电导 [W/K]，b = 边界温度贡献 [W]，P = 功耗 [W]——三者量纲闭合（thermal-g-construction §5 已核）。

## 3. 引用（服务于上述论证，简洁）

| 用途 | 引用 |
|---|---|
| heatsink 单节点（R_spread+R_conv）| lee1995spreading、lee2008spread、incropera、hotspot2006 |
| 3D 分层 vs 集总 | 3dice2010、thermal-g-construction（内部对齐）|
| 冷板/微流道/浸没（对流接地）| incropera（对流/翅片）、3dice2010（inter-tier liquid cooling 即微流道冷却形态）|
| 紧凑 CTM 方法论 | lasance2008ctm（BCI-CTM）|
| 2.5D/3D chiplet 热模型 | mfit2025、chen2025survey2p5d、lau2023chiplet |
| 解析扩散经典（可选背景）| carslaw1959 |
| 降阶（可选，进附录再引）| rogie2018mor |

> 说明：carslaw/rogie 为可选背景（进附录或 Discussion 时再引），正文论证不需要；对应 bib 条目保留备用。

## 4. 与已有调研的衔接

- thermal-network-survey.md：HotSpot/MFIT/FCBGA 对照（本文件是其"散热模式维度"的展开）；
- thermal-network-raw-materials.md：三构型公式/参数（本文件的支路物理路径与之一致）；
- thermal-g-construction.md：heatsink=节点修正框架（DomainExpert，与本节 a 的论证一致）。
