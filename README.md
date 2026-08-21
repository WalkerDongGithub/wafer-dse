# Wafer DSE

晶圆级交换机设计空间探索——用线性规划判定"给定拓扑、布局和物理参数，最大可承诺的额定出入口带宽 B* 是多少？"

## 快速开始

```bash
make test          # 全部测试（tests/ 下 17 个 .md，14 通过 + 3 待修）
make run           # CLI：读 YAML 配置求解（默认 toy 示例）
make run PROBLEM=config/problems/ucie32g_mesh3.yaml
make matrix        # 实验矩阵：拓扑 × 约束场景 → B* 表 + CSV
make ledger TOPOS="Mesh(2)"   # 约束账本：沿 B 轴看每约束关键值演化
```

CLI 一次输出：B*、求解统计、约束账本（每约束利用率/余量）、CSV。

## 配置文件

```
config/
├── params/          物理参数 = 论文"实验设置"（可复用）
│   ├── toy.yaml         手算友好参数组（B* 锚点 4500）
│   └── ucie-32g.yaml    UCIe 1.1/2.0 Spec 典型值
└── problems/        问题定义 = 论文"实验实例"
    ├── toy_fullmesh2.yaml
    └── ucie32g_mesh3.yaml
```

问题定义引用 params 文件 + 拓扑 + 约束场景 + query。改物理参数编辑 params yaml，换实验写一个 problem yaml。

## 架构

```
src/
├── main.py           CLI 入口：YAML → 组装 → 求解 → 结果文档
├── layout.py         布局设计（拓扑分片 + die 摆放）
├── diagnostics.py    约束账本（每约束利用率/余量、绑定诊断）
├── config.py         YAML 配置读取
├── topology/         拓扑定义，Topology ABC（MeshTopology/TorusTopology/KaryNCubeTopology/FullMeshTopology/DragonflyTopology）
├── physical/
│   ├── params.py     参数组合结构体（ExpParams：TOY + UCIE 三档）
│   ├── config/       物理规格（spec_bump / spec_interconnect / spec_thermal / validator）
│   ├── placement/    网格布局（PlacementSolver ABC + GridFillSolver）
│   └── layout/       几何实体（Layout / Interposer / Substrate）
│       ├── thermal_network/   布局 → 预计算热网络（G⁻¹/rhs/link_coeff）
│       └── thermal_solver/    工厂驱动的热求解器多态（simple/mfit/hierarchical）
└── problem/          LP 引擎（纯数学层，不 import physical）
    ├── builder/      编排：拓扑 + 参数 + Layout → 模型列表
    ├── ctx/          变量声明 + 约束注册（constrain(name, lhs, sense, rhs, meaning)）
    ├── models/
    │   ├── perf/     性能包络（ObliviousValiantModel）
    │   └── phys/
    │       ├── bumps/ μbump + C4
    │       ├── therm/ 热约束族（L0 全局 / L1 稳态 / L2 翘曲 — LP 模板）
    │       └── wiring/ 布线网格 + 多商品流
    ├── engine/       求解器（CvxSolver）+ 缓存（Runner）
    └── queries/      查询（FeasibilityQuery / BmaxQuery，共享缓存）

exp/                实验编排（只做选参数、跑查询、收集结果）
├── run_matrix.py    拓扑 × 场景矩阵
├── run_ledger.py    约束账本扫描
└── smoke_*.py       冒烟测试

tests/              测试即文档（.md 叙述 + 可运行代码块，17 个 .md（14 通过 + 3 待修））
config/             物理参数 + 问题定义
notes/              论文文档（见下表）
```

### Python 编程入口

```python
from problem import Ctx, CvxSolver, Runner, BmaxQuery
from problem.builder import build_scenario
from layout import place
from physical.params import TOY
from topology import FullMeshTopology

topo = FullMeshTopology(2, 1)
layout = place(topo, TOY)                       # 更高层：布局设计
models, meta = build_scenario(topo, "perf+bump+therm", TOY, layout)

r = BmaxQuery().solve(Runner(CvxSolver(), log=False),
                      lambda b: (Ctx(), models), lo=100, hi=20000, step=100)
print(f"B* = {r.B_star:.0f} Gbps")             # toy: 4453（手算锚点 4500）
```

## 约束集

论文约束集（MATH_MODEL_V5_JOINT_SENSITIVITY）：性能包络、μbump、C4、温度极限、布线。
翘曲已移出（die 间温差代理撑不起真实物理；V5 无翘曲约束，实现保留作技术记录）。

## 文档

| 文档 | 内容 |
|------|------|
| [MATH_MODEL_V5_JOINT_SENSITIVITY.md](notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md) | 唯一权威模型文档（V5，符号表自包含；代码对齐目标） |
| [insight.md](insight.md) | 7 条 critical insight（字节级不变）——全项目核心意图，V5 为其完整形式化 |
| [STYLE.md](STYLE.md) | 代码风格规范（含纯 OO 规矩） |
| [notes/literature/](notes/literature/) | 文献知识库（Rent's rule / 非阻塞定义调研 / 系数证据等） |

## 测试

```bash
make test
# tests/ 下 17 个 .md：叙述 + 可运行代码块（run_all.py 提取执行，14 通过 + 3 待修）
# toy 参数组的手算锚点写死在 test09/test10——模型输出与手算不一致当场变红
```
