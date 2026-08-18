# AGENTS.md — wafer-dse 编码规则

面向 AI 编码助手与协作者的编码规则。架构设计原则（分层解耦、薄 facade、ABC+注册表、frozen dataclass、算法纯函数化等）已在 [CONTRIBUTING.md](CONTRIBUTING.md) 详述，本文件聚焦**具体可执行的编码规则**，不重复架构原则。改代码前请先读 CONTRIBUTING.md。

---

## 1. 项目概述

晶圆级交换机（Wafer-Scale Switch）设计空间探索工具，个人论文项目。在架构设计早期，快速判断「网络拓扑 + 路由策略 + 封装工艺」组合能否达到目标无阻塞带宽和功耗要求。

## 2. 技术栈与依赖管理

| 层 | 内容 |
|---|---|
| 语言 | Python ≥ 3.9 |
| 核心依赖 | **零外部依赖**（仅标准库）；配置走自研极简 YAML 解析器（`config.py`），不引入 PyYAML |
| 测试 | pytest ≥ 7（`pip install -e ".[test]"`） |
| Lint | flake8 ≥ 5，`max-line-length = 120` |
| 构建 | setuptools + src layout（`pyproject.toml`，`packages.find where=["src"]`） |
| Rust 加速（可选） | `rust-solvers/`（Cargo workspace），经 `rust_backend.py` 透明调用，不可用静默回退纯 Python |
| 拥塞仿真（可选） | `vendor/congestion`（git submodule，branch v2） |
| CLI 入口 | `wafer-dse` = `wafer_dse.__main__:main` |

**依赖原则**：核心代码不引入第三方包；新增依赖需充分论证，优先用标准库实现。

常用命令：

```bash
make run                 # PYTHONPATH=src python -m wafer_dse --config configs/example_user_request.yaml
make test                # 全部测试
make lint                # flake8 src/wafer_dse/ --max-line-length=120
make rust-build          # 编译 Rust 后端（可选）
make ci                  # 构建 + 测试
```

## 3. 目录结构与模块组织

```
wafer-dse/
├── src/wafer_dse/            主包
│   ├── models.py             跨模块数据契约（frozen dataclass）
│   ├── config.py             配置读取（JSON / 极简 YAML）
│   ├── __main__.py           CLI 入口
│   ├── architecture_model/   体系结构级初筛
│   │   ├── topology/         拓扑定义（base.py + 每拓扑一文件）
│   │   └── solver/           interface.py + algorithm/ + fixed_route.py + rust_backend.py
│   ├── packaging_model/      封装级初筛（checks/ 一 check 一文件）
│   ├── die_model/            单 die 物理模型
│   ├── group_dse/            Group 级 DSE
│   ├── wafer_dse/            晶圆级 DSE
│   ├── user_interface/       指令解析 + 驱动
│   └── reporting/            报告生成（JSON / CSV / Markdown）
├── tests/                    单元测试（与 src 平级）
├── configs/                  YAML 配置示例
├── docs/                     设计文档（CODE_STRUCTURE / ARCHITECTURE_MODEL / FORMULA_LOGIC）
├── rust-solvers/             Rust 加速后端（wafer-core / hungarian / derangement / solve）
└── vendor/congestion         拥塞仿真子模块
```

组织约定（详见 CONTRIBUTING.md §1–§4）：

- **一个模块一个文件**，每个文件能用一句话描述唯一职责；描述出现「和/以及」就考虑拆分。
- **接口 > 算法 > 实现**三层分离：`interface.py`/`base.py` 定义 ABC，`algorithm/` 放纯函数，具体实现独立文件。
- **编排层 `model.py` 是薄 facade**（构建对象 → 委托执行 → 聚合结果），不含算法细节。
- 每个包的 `__init__.py` 用 `__all__` 显式导出公开 API。

## 4. 命名规范

| 对象 | 风格 | 示例 |
|---|---|---|
| 文件 | snake_case | `mesh.py`、`kary_ncube.py`、`fixed_route.py`、`die_area.py` |
| 类 | PascalCase | `FixedRouteSolver`、`DieAreaCheck`、`NetworkPotential` |
| 函数 / 变量 | snake_case | `hungarian_min_cost`、`link_capacity_gbps` |
| 私有 | `_` 前缀 | `_parse_scalar`、`_build_link_weights`、`_unique_paths` |
| 常量 | UPPER_CASE | `ALL_CHECKS`、`_SOLVER_CLASSES` |
| 测试文件 | `test_<被测>.py` | `test_hungarian.py`、`test_topology_mesh.py`、`test_solver_fixed_route.py` |
| 测试类 | `TestXxx` | `TestHungarianExhaustive` |
| 测试方法 | `test_<场景>` | `test_n4_exhaustive` |
| 拓扑类 | 拓扑名 | `Mesh`、`Torus`、`KaryNCube`、`Dragonfly` |
| 检查类 | `XxxCheck` | `DieAreaCheck`、`PowerCheck` |

## 5. 代码风格

- 每个文件首行 `from __future__ import annotations`，用 PEP 604 联合类型（`int | None`、`list[int]`、`tuple[str, ...]`）。
- 行宽 **120**（`pyproject.toml` `[tool.flake8] max-line-length = 120`）。
- import 顺序：标准库 → 本项目模块，组内字母序；**显式导入，禁止 `*`**。
- 类型标注全覆盖（参数、返回值、关键变量）。
- 数据契约用 `@dataclass(frozen=True)`，**禁止裸 dict 跨模块**（CONTRIBUTING.md §5）。
- 接口用 `ABC` + `@abstractmethod`；多策略用 ABC + 注册表，**不写 if-else 分支**（§3）。
- **禁止循环导入**（说明分层方向错误）；**禁止 `type: ignore`**（修正而非抑制）。
- 工艺参数从 YAML 配置读取，**禁止硬编码**。
- Lint：`make lint`。

## 6. 注释与文档约定

- **模块 docstring**（中文）：每个文件顶部说明职责、输入/输出、目的。
- **公开类/方法必须有 docstring**（中文），含一句话概述 + 关键公式/算法引用。
- 纯算法/复杂函数用 Google 风格 docstring：`Args` / `Returns` / `Raises` / `复杂度` / `Example`。
- dataclass 字段说明用字段后紧跟 `"""docstring"""`。
- 分块注释：`# ------`（类内分节）、`# ============`（大块分隔）、`# —— 阶段 N ——`（流程阶段）。
- 注释解释「为什么」而非「是什么」；禁止无意义注释（如 `# 初始化变量`）。

## 7. 测试约定

- 框架：pytest（`pyproject.toml`：`testpaths=["tests"]`、`pythonpath=["src"]`）；测试类继承 `unittest.TestCase`，pytest 兼容运行。
- 命名：`tests/test_<被测>.py`。
- 策略（详见 README 测试策略表与 CONTRIBUTING.md §8）：

  | 被测模块 | 最低要求 |
  |---|---|
  | 纯算法 `algorithm/` | 穷举验证（小 N 枚举所有解）+ 数学性质不变式 |
  | 拓扑 `topology/` | 全节点坐标往返 + 全对路由收敛 + 结构性约束 |
  | 求解器 `solver/` | 已知基准值回归 + witness 自洽性 |
  | 检查单元 `checks/` | 手工验算公式 + 通过/失败/边界 |

- 断言：`assertEqual` / `assertAlmostEqual`（`places=9`）。
- 涉及随机数（如 `random.uniform` 生成测试矩阵）时，**建议固定 `random.seed`** 以保证可复现（当前测试未统一固定，属待补强项）。
- 命令：`make test` / `test-hungarian` / `test-topology` / `test-solver` / `test-quiet` / `test-slow` / `test-rust-backend` / `test-all` / `ci`。

## 8. Git 提交约定

基于 GitHub 提交历史提炼：

- **Conventional Commits 前缀**：`feat:` / `fix:` / `docs:` / `refactor:` / `build:` / `test:`；大重构可用组合（`refactor+feat:`）。
- **标题**：简短一句话，中文为主，概述核心变更。
- **body**：用 `-` 列表罗列具体变更点（新增/删除/重构/测试情况），每点一句话。
- AI 协作提交带 `Co-Authored-By: Claude <noreply@anthropic.com>`。

示例：

```
feat: ResultStore 磁盘缓存接入 main 与 ledger/matrix 实验入口

- scripts/import_cache.sh：合并式导入外部缓存（key 无路径依赖）
- ResultStore 接入 main.py / run_matrix / run_ledger
- 验证：toy 问题两遍运行，第二遍零新增
```

## 9. 项目特有注意事项（DSE）

- **零依赖原则**：核心求解器仅用标准库；配置走自研 YAML 解析器，不引入 PyYAML。新增第三方依赖前先论证。
- **实验输出不入库**：DSE 运行结果写入 `outputs/`（已 `.gitignore`）；`*.pdf` 同样忽略（论文 PDF 不入库）。
- **Rust 后端透明回退**：`rust_backend.py` 自动探测 `wafer-solve` 二进制，不可用时静默回退纯 Python，调用方无感知——不要在调用方写 `try/except` 处理 Rust 缺失。
- **算法层必须纯函数**：`algorithm/` 内函数不访问文件/网络，不 import 本项目其他模块，相同输入永远相同输出。
- **求解器只依赖 `Topology` ABC** 的公开方法（`terminals()`/`det()`/`valiant()`），不依赖具体拓扑实现——新拓扑实现接口后所有求解器自动兼容。
- **配置统一入口**：用户指令和封装工艺文件都走 `config.load_config`。
- **测试基准值是 ground truth**：solver 对各拓扑的 `nonblocking` / `worst_load` 固定值，任何改动必须保持不变。
- **随机性**：实验/测试中涉及随机数应可复现（固定种子）；论文实验结果需可重放。

---

## 版本说明

本规则基于本地代码（commit `898f5601`，2026-06-09，hierarchical DSE 架构）提炼。本地已演进至 LP engine 架构（引入 numpy / pyyaml / cvxpy，`src` 结构扁平化为 `problem/` + `physical/` + `topology/`，`lp/` 已按"数学/物理/几何各归各管"原则改名为 `problem/`）。编码风格、命名、注释、测试、Git 约定跨版本一致；若要对齐最新版的「目录结构」与「依赖」部分，`git pull` 后重新审视第 2、3 节。
