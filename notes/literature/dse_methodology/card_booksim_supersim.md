# 卡片 06：BookSim/BookSim2 + SuperSim —— cycle 级仿真，单次评估分钟~天级

> 对应必做清单 #6，另补 SuperSim（开源 flit 级仿真器）。
> 家法：[可靠]=原文；[中等]=综述/幻灯/新闻；[待确认]=需核对。

---

## BookSim / BookSim2

### 出处
- **William J. Dally, Brian Towles**, *Principles and Practices of Interconnection Networks*, Morgan Kaufmann, 2004（BookSim 1 出处）；**Nan Jiang, Daniel U. Becker, George Michelogiannakis, et al.**, "A Detailed and Flexible Cycle-Accurate Network-on-Chip Simulator," *ISPASS 2013*（BookSim2.0 出处）[可靠]
- 开源，斯坦福/UC Davis 维护，支持 15+ 拓扑，学界事实标准

### 建模维度清单
| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ● | cycle-accurate：延迟/吞吐/排队，流量驱动 |
| 功耗 | — | 无（功耗交给 DSENT/McPAT/Orion 配套） |
| 热 | — | 无 |
| bump | — | 无 |
| 布线 | — | 无 |
| 成本 | — | 无 |

### 模型是否硬编码、是否可替换
- 拓扑/路由/选择策略以代码扩展为主（编译期），无运行时模型替换接口；配置参数多但**模型结构需写 C++** [可靠]

### 搜索方法与单次评估代价（关键证据）
- 无内置搜索：**单点评估器**，每次运行一个流量场景
- 单点代价随规模爆炸：4×4 mesh 约 6 秒，54×54 mesh 约 **10 天**；某研究累计评估 3D mesh 全部流量场景 1.14×10⁷ 秒（~132 天）；注入率 >0.01 或拓扑 >8×8 后性能明显劣化；单线程无原生并行 [中等：来自后续 ML 代理论文的测量，需定位原始测量论文]
- 在我们论文语境：1000 个设计点 × 分钟级 = 数天，DSE 不可行——我们的 ms 级 LP 快 3–6 个数量级

### 在我们框架里的位置
- **对应环节：性能（§2.1）的"精仿验证层"。** 我们的 B* 是保守可行判定（假阴性不可接受、假阳性留给仿真），BookSim 正是处理假阳性的 ground truth。
- 子集论证价值：**性能环节的仿真实现**——只覆盖性能，且单次评估慢到无法支撑 DSE。

## SuperSim

### 出处
- **Noel M. McDonald et al.**, "SuperSim: Extensible Flit-Level Simulation of Large-Scale Interconnection Networks," *ISPASS 2018*. DOI: 10.1109/ISPASS.2018.00017 [可靠]
- 开源，C++（30,000+ 行），源于斯坦福高 radix router（SuperSwitch）DSE 项目，用于斯坦福互连网络课程

### 建模维度清单
| 维度 | 有无 | 细节 |
|---|---|---|
| 性能 | ● | flit-level 离散事件，支持大规模（远超 gem5/Garnet 的 256 endpoint 限制）；tick/epsilon 两级时间抽象 [可靠] |
| 功耗 | — | 无 |
| 热/bump/布线/成本 | — | 全无 |

### 模型是否硬编码、是否可替换
- **插件式架构**：abstract class 工厂，加新组件模型（Router/Allocator/Arbiter/Workload）只需加源文件不改主代码——这是"可替换模型接口"在仿真界的对应物 [可靠]

### 在我们框架里的位置
- 同 BookSim：性能环节精仿；它的插件架构值得在论文里引为"接口可替换"在仿真领域的先例（证明接口抽象不是我们独创，但我们把它用在了约束族层面）。

## 缺口与下一步
1. BookSim 单点代价的测量数字来自二手（ML 代理论文），引用时定位原测量或自己复跑小规模标定
2. 我们的论文需要"BookSim 验证 LP"的实验设计：抽 N 个 B* 边界点 → BookSim 跑 → 确认无阻塞与假阳性率

## 来源
- [BookSim2 (GitHub: booksim2)](https://github.com/booksim/booksim2)
- [Jiang et al. ISPASS 2013 (Semantic Scholar)](https://www.semanticscholar.org/search?q=BookSim2.0%20cycle-accurate%20network-on-chip)
- [SuperSim ISPASS 2018 (KAIST OA 存档)](https://koasas.kaist.ac.kr/handle/10203/247529)
