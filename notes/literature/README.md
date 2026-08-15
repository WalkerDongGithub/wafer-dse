# notes/literature/ 索引

> 对应研究议程（notes/plan_research_agenda.md）阶段二的文献库。2026-08-15 大规模扩充：按 2.1–2.4 四条脉络建了四个子目录。
> 质量标注家法见 RENT_RULE_AND_IO_DENSITY.md：[可靠]=原始文献/规范/datasheet；[中等]=行业杂志/综述/新闻；[待确认]=需下载原文核对。

## 四个主题子目录（2026-08-15 新建）

| 目录 | 对应议程 | 内容 | 最硬的结论 |
|---|---|---|---|
| [thermal_validation/](thermal_validation/) | 2.1 热仿真对标 | JESD51 热阻标准、材料/μbump 热导率、交换 ASIC 热数据、chiplet 热文献、散热极限（6 文件，24 来源） | 热模型三向保守：R_vert 保守 ~4×、T_max 85°C 比真实 105°C 低 20°C（恰好吸收 lumped 热点误差）、Air 档贴 HIR 风冷极限。唯一不保守输入：T_ambient=27°C（ASHRAE 允许 45°C） |
| [real_chip_catalog/](real_chip_catalog/) | 2.2 真实芯片数据 | 16 张交换 ASIC + 9 张 chiplet + 7 张平台卡片（4 文件） | TH5：51.2T/750mm²/450W/512×112G。UCIe 0.25–0.5 与 SerDes 2–4 pJ/bit 差 ~8× ≈ 实验 B* 比 7.9×。UltraFusion 10k 信号撑 2.5TB/s → bump 结构性过剩 |
| [architecture_cases/](architecture_cases/) | 2.3 既有架构还原 | 12 张参数级还原卡片（Chen ISCA'24 / Feng&Ma SC'24 / Wan TVLSI'24 / TickTock ISCA'25 / Dojo / Cerebras / InFO-SoW / Si-IF / Simba / WaferLLM 等，4 文件） | Feng&Ma 的 dragonfly 参数全齐（n=12,m=4,a=4,b=8,g=545），可直接落成 exp 配置。对照实验顺序建议：Feng&Ma → Wan → TickTock → Chen |
| [dse_methodology/](dse_methodology/) | 2.4 方法论对标 | 24 工具×6 维度对比矩阵 + 12 张方法论卡片 + 子集论证骨架（13 文件） | 无一行覆盖超三维、联立列全是 ○；C4 环节无人建模（真空）；"子集"论证需三级联立定义（独立评估/两两耦合/同变量统一求解） |

## 原始文献 / 规范 PDF 库（2026-08-15 从 wsl-docs 归入）

> 一手 PDF（规范 / 教材 / 专著 / 会议论文），本地归档，不进 git（`.gitignore` 忽略 `*.pdf`）。

| 目录 | 内容 |
|------|------|
| [interconnect/](interconnect/) | **UCIe 2.0 Spec 原文 PDF** + 12 份 UCIe 规范读书笔记（Ch1–5 讲义、通道/合规/VTF、Retimer、去加重）——页码级，UCIe 系数证据链的黄金素材 |
| [packaging/](packaging/) | John H. Lau 封装权威专著 3 本（chiplet 设计 / flipchip 混合键合 / 半导体先进封装） |
| [textbooks/](textbooks/) | 权威教材 PDF：Rabaey《数字集成电路》、Bogatin《信号与电源完整性》、Hennessy & Patterson《计算机体系结构》+ 附录 F 互连网络中文翻译 |
| [architecture_cases/](architecture_cases/) | 新增 9 篇 wafer-scale/chiplet 会议论文 PDF（ISCA/HPCA/ASPLOS/DAC，含 Wan《Architectural Exploration for Waferscale Switching》）+ `wafer-scale-papers.md` |

> SI 理论笔记（传输线/串扰/反射/S 参数/差分/均衡/弹性力学，44 份）放 `notes/si/`——是 UCIe 电气层参数的技术背景，非权威文献，不进本库。

## 旧文件（2026-08-06 及更早，部分已被新目录吸收）

| 文件 | 内容 | 去向 |
|---|---|---|
| [RENT_RULE_AND_IO_DENSITY.md](RENT_RULE_AND_IO_DENSITY.md) | Rent's rule、pad-limited→area-array、bump pitch 阶梯 | 家法模板；内容属于 2.2 佐证 |
| [LITERATURE_MAP.md](LITERATURE_MAP.md) | 论文引言逐句文献地图（19 条） | 引言写作素材 |
| [EVIDENCE_RATIONALE.md](EVIDENCE_RATIONALE.md) | 引言 10 条论断的证据链 | 与 LITERATURE_MAP 配套 |
| [NONBLOCKING_DEFINITIONS_SURVEY.md](NONBLOCKING_DEFINITIONS_SURVEY.md) | 无阻塞定义沿革（Clos/Beneš/RNB/SNB） | 论文 §4 搜索轴素材 |
| [DOWNLOAD_LIST.md](DOWNLOAD_LIST.md) | 优先下载论文清单（按主题分目录） | 各新目录"缺口与下一步"的待核对原文都指向它 |
| [textbooks/](textbooks/) | 教材资料 | — |

## 关联总表

- 论文框架总纲：notes/paper_outline_v0.md（旧）、memory 中 paper-outline
- 数理模型：notes/MATH_MODEL_COMPLETE_V4.md（§7 实现状态对照表）
- 研究议程：notes/plan_research_agenda.md（阶段二 = 本目录的任务来源）
- 架构对标综述（A–E 分类）：notes/LITERATURE_SURVEY.md —— 本目录四个子库是它的加深版，2026-08-15 修正其一（TickTock 基线实为 Tesla Dojo）

## 引用纪律（进论文前）

1. 所有 [待确认] 数字必须下载原文核对页码后升级为 [可靠]。
2. 负面 claim（"C4/热无人联立"）须声明检索边界，并引 EDA 综述佐证。
3. 数字一律带单位与出处；datasheet > 会议论文 > 媒体 > 博客。
