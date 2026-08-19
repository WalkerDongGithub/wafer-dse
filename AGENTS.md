# AGENTS.md — wafer-dse 编码规则（agent 自用）

## 三份灵魂文档（唯一准绳）

改代码前先对齐这三份；其他所有文档与代码都是工具，可改可删，缺失内容用户会再填。

| 文档 | 作用 |
|---|---|
| `notes/MATH_MODEL_V5_JOINT_SENSITIVITY.md` | V5 数理模型，代码语义唯一权威 |
| `insight.md` | 7 条 critical insight，字节级不变 |
| `STYLE.md` | 代码风格唯一权威 |

## 项目概述

晶圆级交换机设计空间探索工具。LP 引擎求解「拓扑 + 路由 + 封装工艺」组合的无阻塞带宽 B* 与功耗/热可行性。

## 技术栈与命令

- Python ≥ 3.9；依赖 `numpy`、`pyyaml`；可选 `cvxpy`（LP 求解）。
- `make run`（读 YAML 求解）、`make test`（全测）、`make lint`、`make matrix`、`make ledger`、`make smoke`。
- 测试框架：`cd tests && PYTHONPATH=../src python run_all.py`，驱动各 `.md` 测试（叙述 + 可运行代码块），非 pytest。

## 目录结构

```
src/
├── problem/           LP 引擎（纯数学层，不 import physical）
│   ├── ctx/           变量声明 + 约束注册
│   ├── models/        约束模型（perf: ObliviousValiantModel；phys: bump/c4/therm/wiring）
│   ├── engine/        Solver + Runner + ResultStore
│   ├── queries/       feasibility / bmax
│   └── builder/       拓扑 + 参数 + Layout → 模型列表
├── physical/          物理层（config / layout / placement / params）
├── topology/          拓扑（Mesh / Torus / KaryNCube / FullMesh / Dragonfly）
├── main.py            CLI 入口
├── layout.py          布局设计
└── diagnostics.py     约束账本诊断
config/                物理参数 + 问题定义 YAML
tests/                 测试（.md 驱动）
exp/                   实验编排
notes/                 V5 + V4 符号表 + literature
docs/paper/            LaTeX（下游产物）
benchmark/             对标复现
```

## 编码约定（要点，完整见 STYLE.md）

- 每文件首行 `from __future__ import annotations`；PEP 604 联合类型（`int | None`）。
- 行宽 120；import 显式，禁止 `*`；类型标注全覆盖。
- 数据契约用 `@dataclass(frozen=True)`；接口用 ABC + `@abstractmethod`。
- 禁止循环导入、禁止 `type: ignore`；工艺参数从 YAML 读取，禁止硬编码。

## 测试约定

- 命名：`tests/<领域>/test<序号>_<被测>.md`。
- 测试先行：先写 `.md` 测试 → 确认 → 再写实现。

## Git 约定

- Conventional Commits 前缀：`feat:` / `fix:` / `docs:` / `refactor:` / `build:` / `test:`。
- 标题简短中文；body 用 `-` 列表。
- 实验输出（`exp/output/`）与 `*.pdf` 不入库。

## 关键注意

- 代码服务 V5，非 `docs/paper/` LaTeX（下游产物）；冲突 → 改代码。
- 求解器只依赖 `Topology` ABC 公开方法，不依赖具体拓扑实现。
- 实验/测试随机性需可复现（固定种子）。
