# 卡片 05：DSENT + McPAT —— 功耗/面积建模工具，模型焊死在代码里

> 对应必做清单 #5。两者是"模型硬编码"的典型代表。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## DSENT

### 出处
- **Chen Sun, Chia-Hsin Owen Chen, George Kurian, Lan Wei, Jason Miller, Anant Agarwal, Li-Shiuan Peh, Vladimir Stojanović**, "DSENT – A Tool Connecting Emerging Photonics with Electronics for Opto-Electronic Networks-on-Chip Modeling," *IEEE/ACM NoCS 2012*, pp. 201–210. DOI: 10.1109/NOCS.2012.31 [可靠]
- 开源 v0.91（2012-06），已集成进 gem5 (`ext/dsent`)，MIT 已停维护 [可靠]

### 建模维度清单
| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | — | 无流量/延迟仿真；仅有 timing optimizer（不收敛时会把所有单元 size 到最大，功耗/面积偏高）[可靠] |
| 功耗 | ● | 核心能力：电学+光学 NoC 功耗，分解为电学（router/link/interface/tuning）+ 光学（laser 墙插功耗）；关键发现：laser 与热调谐是 non-data-dependent 功耗，低利用率时光网络低效 [可靠] |
| 热 | — | 无热网络（只有 ring 热调谐功耗项） |
| bump | — | 无 |
| 布线 | ○ | 链路长度是输入参数（默认 1mm，不区分实际长度）[中等] |
| 成本 | — | 无 |

### 模型是否硬编码、是否可替换
- C++ 面向对象，building-block 层次化建模，**参数可配但模型固定**：工艺节点（45/32/22/11nm）、router 流水线（3 级 VC router）、crossbar（MULTREE）等全部写死在代码里。换一种 router 微架构 = 改代码 [可靠]
- 已知限制：VC 控制/credit buffer 未建模；22nm 及以下低估本地互连功耗/时序 [可靠]

### 搜索方法与单次评估代价
- 无搜索：文本配置 + 手动参数扫描；单次评估秒级 [可靠]

### 在我们框架里的位置
- **对应环节：功耗系数（进 §2.3 电源 bump、§2.5 热源的 P 项）的"一种取值来源"。**
- 缺：性能、热、bump 预算、布线、成本全无。它是单点评估器，不是 DSE 框架。
- 子集论证价值：**功耗建模工具只建模功耗**——它的存在正是"每个环节都有工具、但没有联立"图景的组成块；且模型硬编码说明"可替换模型接口"本身是稀缺设计。

## McPAT

### 出处
- **Sheng Li et al.**, "McPAT: An Integrated Power, Area, and Timing Modeling Framework for Multicore and Manycore Architectures," *IEEE/ACM MICRO 2009*（HPCA/MICRO 系经典，引用数千）[可靠]
- 开源，BSD 许可

### 建模维度清单
| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ○ | 输出 cycle time（延迟路径） |
| 功耗 | ● | 动态+静态，处理器微架构组件级 |
| 热 | — | 无 |
| bump | — | 无 |
| 布线 | — | 无 |
| 成本 | — | 无 |

### 模型是否硬编码、是否可替换
- 同为参数化 XML 配置 + 固定实现模型；工艺仅到 22nm；**NoC 面积估算有 bug（ring 与 mesh 返回相同面积）**[中等：来自现有调研笔记，需在原文/issue 中核对]

### 在我们框架里的位置
- 同 DSENT：功耗/面积系数的取值来源之一；与 DSENT 合起来是"功耗环节的单维度工具对"。

## 缺口与下一步
1. DSENT 的 22nm 限制是"分析模型保质期"的证据——物理模型需要随工艺替换，这正是我们 Model 接口的动机
2. McPAT NoC 面积 bug 若需引用，找原始 issue 或复现实验

## 来源
- [DSENT MIT DSpace](https://dspace.mit.edu/handle/1721.1/69050)
- [DSENT gem5 集成 README](https://gem5.googlesource.com/public/gem5/+/3cf4a04fceef321b5cd6ece9a4ff1814787a236d/ext/dsent/README)
- [McPAT 主页](https://www.hpl.hp.com/research/mcpat/)（HP Labs 存档）
