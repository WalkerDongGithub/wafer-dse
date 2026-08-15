# 04 Chiplet/2.5D 热仿真工具、热感知放置、晶圆级系统热数据

## 1. 热仿真工具与精度锚（我们的网络模型属于哪一类）

### 1.1 MFIT（我们代码直接借鉴的组装方法）

| 项 | 值 | 出处 |
|---|---|---|
| 论文 | "MFIT: Multi-FIdelity Thermal Modeling for 2.5D and 3D Multi-Chiplet Architectures" | ACM TODAES 31(1), 2025, doi:10.1145/3765905；arXiv:2410.09188 |
| 四层模型 | 细粒度 FEM → 抽象 FEM（误差 <0.5°C）→ **热 RC 网络（秒级，误差 <1.7°C，~1–3.5% @ ~100°C）** → 离散状态空间 DSS（毫秒级） | 同上 |
| 评估对象 | 16/36/64 个 2.5D chiplet、16×3 3D chiplet、AMD MI300A（500 节点） | 同上 |
| 相对 HotSpot/PACT/3D-ICE 的差异 | 支持非均匀网格、各向异性材料、非均匀层、两侧散热 | 同上 |
| 开源 | github.com/AlishKanani/MFIT | [可靠] |

**与我们的关系**：`_mfit_system.py` 的 nodal analysis 组装（G = diag(rowsum) − off_diag）正是 MFIT 方法。MFIT 的验证结论——**集总 RC 网络 vs FEM 误差 <1.7°C（~2%）**——是我们模型方法可信性的直接背书：误差远小于我们 R_vert/T_max 的保守裕量（4×/20°C）。引用时可写："同类集总网络工具（MFIT）对标 FEM 误差 <2%，而我们参数的保守裕量远大于该误差"。

### 1.2 HotSpot（UVa，行业最常用开源热仿真器）

| 参数 | 默认值 | 出处 |
|---|---|---|
| 硅热导率 k_chip | 130 W/(m·K) | HotSpot 源码/配置（IFTE-EDA/HotSpot） |
| die 厚度 | 0.15 mm（4.0 版起；早期 0.5mm） | 同上 |
| TIM 厚度/热阻 | 20μm / 0.25 mK/W | 同上 |
| grid 模型默认分辨率 | 64×64 网格 | 同上 |

**与我们的关系**：HotSpot 是"die 级热网络"的工业基准，其默认硅 k=130 与我们 150 同量级（差 15%，不改变结论）；其网格模型 64×64 的分辨率量级说明 die 内热点建模需要 ~百 μm 网格——我们 lumped 到 die 级节点，热点由 T_max 裕量覆盖（见 §3）。

## 2. 热感知 chiplet 放置（横向热耦合的学术证据）

| 工作 | 方法 | 关键数字 | 出处 |
|---|---|---|---|
| TAP-2.5D | SA 放置 + MILP 布线，开源 | 多 GPU 峰值降 4°C（10% 线长代价）；CPU-DRAM 系统从不满足的 113.54°C 降到可行（150W TDP 余量）；复现华为 Ascend 910 设计 | DATE 2021, Ma et al. [可靠] |
| Dark Silicon（Eris） | 多起点贪心：chiplet 数×功率密度×interposer 尺寸 | 85°C 阈值下性能 +41%（平均）；105°C 阈值下 +16%；等价性能下成本 −36% | DATE 2018 [可靠] |
| TACPlace | 可行性寻找 superiorization，1760× 提速 | 峰值再降 6.1°C、线长 −11.9%；多功率模式下 46°C 峰值（Samsung 2.5D） | GLSVLSI 2025, doi:10.1145/3716368.3735185 [可靠] |
| ATPlace2.5D | 解析式放置，大规模 | 比 SA/枚举/RL 方法可扩展性更好 | ICCAD 2024 [可靠] |
| RL 放置 | 强化学习状态=位置/旋转 | 优于 SA（多 GPU、CPU-DRAM 验证） | IEEE EPTC 2024 [可靠] |
| 两阶段放置+TSV 优化 | PSO 放置 + GPR 代理 FEM | TSV 插入后峰值再降 ~10°C；"TSV 空间分布比材料热导率更重要"；2.7s/次评估 | J. Comput. Electronics 2026 [中等] |
| REMOTE | 无线 SoP 任务映射去热点 | 峰值降 ~24% | IEEE 2023 [可靠] |

**共同结论**：die 间距（spacing）是横向热耦合的第一杠杆；高功率密度 chiplet 之间的热串扰可达使邻 die 升温数 °C 到十几 °C（从"4–24°C 的峰值降幅"反推）。这直接验证了我们 `g_lat`（die 间横向耦合）建模的必要性——若忽略横向耦合，低估邻 die 温度。

**与我们的关系**：TAP-2.5D 的"113.54°C 不可行 → 放置优化后可行"和 Dark Silicon 的"85°C vs 105°C 阈值"说明：**业界热感知放置把 85°C/105°C 当标准温度阈值用**——与我们 T_max=85°C（翘曲）不谋而合，105°C 即 EM 上限。我们 LP 的 `ΔT_max=10 K` 邻接温差约束没有直接工业规范可引用（缺口），但"热感知放置可降 4–24°C 峰值"暗示 die 间温差扰动就在这个量级，10 K 是合理的量级选择。

## 3. die 内热点幅度（lumped 模型误差的上界估计）

- 文献中"热感知放置降峰值 4–24°C"、MFIT 对 MI300A 500 节点建模、AI 加速器热点热流密度 >1000 W/cm² 的投影——热点与 die 平均的温差通常在 **10–20°C** 量级（综述级结论，精确数字待 MDPI 综述原文 [待确认]）。
- **与我们的关系**：我们 lumped die 为单节点，低估 die 内峰值。T_max 用 85°C 而工业上限 105°C——**20°C 裕量 ≥ 热点幅度**，这正是"lumped 误差被保守阈值吸收"的定量论证。建议在论文里显式写出这个不等式：20°C（T_max 裕量）> 10–20°C（热点幅度）。

## 4. 晶圆级系统热数据（Cerebras / Dojo）

| 系统 | 功耗 | 面积 | 功率密度（换算） | 散热方案 | 出处 | 状态 |
|---|---|---|---|---|---|---|
| **Cerebras WSE-2** | 芯片 14kW typical / **23kW peak**（AnandTech）；~15kW 为广泛引用口径 | 46,225 mm²（300mm 晶圆） | **0.30–0.50 W/mm²**（30–50 W/cm²） | 直接贴板 + flexible membrane + 水冷冷板铜换热器，垂直供电 | AnandTech 报道；Hot Chips 2021（Sean Lie） | [可靠]/[中等] |
| **Cerebras CS-2 整机** | 28 kW max（PSC Neocortex 文档） | — | — | 闭环水冷（冗余泵） | PSC 文档 | [可靠] |
| **Cerebras WSE-3 / CS-3** | 晶圆功耗与 WSE-2 持平（~15kW）；整机 ~120kW 级（架构研究）；HotCarbon 实测训练时高于 idle ~4.3 kW | ~46,000 mm² | ~0.32 W/mm² | 同上 + 全系统水冷 | HotCarbon 2025 paper-160；Kundu et al. 2025 | [可靠]/[待确认] |
| **Tesla Dojo Training Tile** | **15 kW/tile**（~10kW 归 25×D1 die，400W/die TDP；~5kW 归供电/IO/互连） | 300mm wafer（70,686 mm²） | **~0.21 W/mm²** | 液冷层 + 铜 tray 把散热从 7kW 抬到 15kW；18,000A 垂直供电；MEMS 应变感知闭环调压 | Hot Chips 34（2022）+ 新智元等 | [可靠]/[中等] |

**三个关键观察**：
1. **晶圆级系统的功率密度只有 0.2–0.5 W/mm²**——比交换 ASIC 单 die 的 ~0.95 W/mm²（TH5，见 03）低 2–4 倍。原因：计算 die 的晶体管密度虽高，但晶圆面积里大量区域（IO、互连、dummy、空白）不产热；而交换机 die 里全是 SerDes 和 crossbar，功耗密度天然更高。**这正是"交换机比计算芯片更撞热墙"的物理直觉来源**。
2. 晶圆级系统**必须液冷**（Dojo 铜 tray 是专门把散热 7→15kW 的手段）——风冷连 15kW/wafer 都压不住。
3. 120kW 的 CS-3 整机口径 vs 15kW 晶圆口径差 8 倍——**引用时必须分清"晶圆功率"和"系统功率"**，我们论文里对标的是晶圆侧。

**与我们的关系**：
- 我们的 B* 实验（热墙主导）与"晶圆级系统必须上液冷、密度被散热锁死"的工业现实互相印证。
- 若我们的散热预算模型允许 ~0.2–0.5 W/mm²（晶圆级系统现实密度），那 12×12mm die 每 die ~30–70W——与 R_vert=2.0 K/W、T_max=85°C 给出的 29W/die（见 README §2 换算）同量级，**说明现有参数组合产出的 B* 数字（不是绝对量）是自洽的**；而若用真实 R_vert=0.5 K/W 会得到 ~116W/die，超出晶圆级现实——这提示 85°C/2.0 组合其实同时吸收了"die 级冷却能力现实"和"热点 lumping 误差"，是工程上聪明的保守化，值得写进论文方法学。

## 5. 来源清单

1. MFIT: ACM TODAES 2025, doi:10.1145/3765905；arXiv:2410.09188；https://github.com/AlishKanani/MFIT —— [可靠]
2. HotSpot: Huang et al., UVa；https://www.cs.virginia.edu/~skadron/lava/HotSpot/；https://github.com/IFTE-EDA/HotSpot —— [可靠]
3. Ma et al., "TAP-2.5D: A Thermally-Aware Chiplet Placement..." DATE 2021 —— [可靠]
4. Eris et al., "Leveraging Thermally-Aware Chiplet Organization in 2.5D Systems to Reclaim Dark Silicon", DATE 2018 —— [可靠]
5. TACPlace, GLSVLSI 2025, doi:10.1145/3716368.3735185 —— [可靠]
6. ATPlace2.5D, IEEE 11126201（ICCAD 2024）—— [可靠]
7. "Optimizing Chiplet Placement in Thermally Aware Heterogeneous 2.5D Systems Using Reinforcement Learning", IEEE EPTC 2024, 10909800 —— [可靠]
8. "A two-stage thermal-aware design strategy for chiplet placement and TSV optimization in 2.5D integrated systems", J. Comput. Electronics, doi:10.1007/s10825-026-02545-0 —— [中等]
9. Cerebras WSE-2: AnandTech（14/23kW）；Hot Chips 2021（Sean Lie, HC33）；PSC Neocortex 文档 —— [可靠]/[中等]
10. Cerebras CS-3: HotCarbon 2025（https://hotcarbon.org/assets/2025/paper-160.pdf）；Kundu et al. 2025 —— [可靠]/[待确认]
11. Tesla Dojo: Hot Chips 34（Talpes et al. 2022）；新智元/十方 报道（15kW、铜 tray、18000A）—— [可靠]/[中等]
