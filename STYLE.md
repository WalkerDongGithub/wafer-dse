# 代码风格规范（统一版 — 全项目唯一权威）

> **适用范围**：`src/` 下**所有**代码，包括但不限于 `problem/`、`topology/`、`physical/`、编排入口 `main.py`、`config.py`。
> **已合并的旧文档**（不再单独存在）：
> - 原 `src/lp/STYLE.md` — 内容已并入本文件第 4、7、8 节
> - 原 `NAME.md` — 命名详则已并入本文件第 2 节

最核心原则：**代码清晰、易于验证、可读性好、逻辑扫一眼就能看懂**，比代码是否高效、是否鲁棒重要一万倍。代码的清晰整洁永远是编码的第一原则。只有在不牺牲清晰整洁性的前提下，才考虑高效和鲁棒。

> **代码服务于论文**（最高原则，来自旧 lp/STYLE.md §0）：
> - 代码与论文冲突 → 改代码
> - 论文产生变化 → 代码做对应调整
> - 论文没提到的（产品级校验、异常处理、边界检查）→ 可以删
> - 论文需要的（运行结果、日志、实验数据）→ 必须做好
> **这不是一个产品，这是一篇论文的配套代码。**

---

## 1. Model 结构（三段式 — 硬性）

每个 `Model` 子类（`src/problem/models/` 下所有模型）必须严格遵循三段式：

```python
class XxxModel(Model):
    """一句话——这个模型对应论文哪条约束."""

    def __init__(self, ...):
        """预计算全部系数。不做 B 相关的事。"""
        self._coeff = ...    # 系数 (float, np.ndarray, 或 dict)
        self._rhs = ...      # RHS  (float 或 np.ndarray)
        self._rate = ...     # lane_rate (若需要 B 缩放)

    def build(self, ctx: Ctx, B: float) -> None:
        """只做 B 缩放 + 写约束。不超过 30 行。"""
        L = ctx["L"]
        scale = B / self._rate
        for i in range(...):
            (scale * sum(coeff * L[e] for e in ...)) <= self._rhs[i]

    def cache_key(self) -> tuple:
        """返回可哈希元组。Runner 用它做 L1/L2 缓存。"""
        return ("model_name", self._rate,
                self._coeff.tobytes(), self._rhs.tobytes())
```

规则：
- `__init__` 不调用 `ctx`，不声明变量，不写约束。只做数学运算。
- `build()` 不 `import`，不做复杂循环。系数全在 `__init__` 算好了。
- `cache_key()` 不能返回 `None`。如果模型参数可变，把参数编码进去。

---

## 2. 命名（含原 NAME.md 全部规则）

### 2.1 风格

| 元素 | 规范 | 示例 |
|------|------|------|
| 模块 (`.py`) | 私有实现 `_` 前缀，小写+下划线；公开实现无前缀，小写+下划线 | `_network.py`, `_bump.py`, `builder.py` |
| 类 | 大驼峰，**子类名必须以直接父类名结尾**（硬规则，见 §2.2） | `SteadyStateModel`, `BumpModel`, `DragonflyTopology` |
| 函数 | 小写+下划线 | `build_thermal_network` |
| 私有方法/属性 | `_` 前缀 | `self._coeff`, `self._rhs` |
| 变量名 | 简短、数学符号优先（文档有明确定义的符号优先复用） | `L`, `B`, `G`, `b` |
| 常量 | 全大写+下划线 | `RC_POWER_BUDGET_W`, `__all__` |
| 临时变量 | 尽可能不要使用缩写，而是使用全称 | `pattern` 而不是 `pat` |

### 2.2 核心规则：子类携带父类名后缀（硬规则）

**子类名必须以直接父类名结尾。** 这是硬规则。

```
class XxxParent(Parent):     ✓  子类名以 "Parent" 结尾
class XxxModel(Model):       ✓
class XxxSelector(Selector): ✓
class XxxPattern(Pattern):   ✓
class XxxSolver(Solver):     ✓

class XxxFoo(Parent):        ✗  子类名不以 "Parent" 结尾 —— 一眼看不出继承关系
```

后缀 = 直接父类的类名（不含模块前缀）。

#### 多级继承

携带**根父类**后缀即可，不需要叠床架屋。

```python
class Model(ABC):                        # 根
class PerformanceModel(Model):           # ✓  一级，带 Model
class EnvelopeModel(PerformanceModel):   # ✓  二级，带 Model 即可（不需要 EnvelopePerformanceModel）
class ThermalModel(Model):               # ✓
class SteadyStateModel(ThermalModel):    # ✓  SteadyStateThermalModel 是过度工程
```

#### 为什么

读到 `class AllDerangements(Selector)`，类名不告诉你它是个 Selector——你得往回翻 import 或继承声明。读到 `class DerangementSelector(Selector)` 则没有这个问题。不依赖 IDE、LSP、grep。名字本身就说明了一切。

### 2.3 已识别的不规范命名

| 当前 | 父类 | 应改为 | 说明 |
|------|------|--------|------|
| `TrafficMatrix` | `Pattern` | `TrafficMatrixPattern` | 是一种流量模式，名字要体现 |
| `SConjugacyReps` | `Selector` | `ConjugacySelector` | S 前缀 + Reps 后缀都不表达 Selector |
| `AllDerangements` | `Selector` | `DerangementSelector` | 暴力枚举"全部 derangement"的 Selector |

这三个连起来读：`ConjugacySelector`、`DerangementSelector`、`ManualSelector`——全是 Selector，一眼就知道可互换。`SConjugacyReps`、`AllDerangements`、`ManualSelector` 放在一起看不出是同一族。

### 2.4 不需要改的（豁免清单）

以下类不参与继承体系或属于基础设施，不受后缀规则约束：

- `Ctx`、`LinExpr`、`Var`、`VarSpec`、`Term`、`LinearC`、`Sense` — 数据契约 / 符号表达式 / 枚举
- `TopoStructure`、`ThermalNetwork`、`RoutingGrid`、`DiePlacement`、`MfitStackConfig` — frozen dataclass，值对象
- `Result`、`FeasibilityResult`、`BmaxResult`、`Runner`、`ResultStore` — 引擎基础设施
- `_Backend`、`_DirBackend` — 私有实现类

### 2.5 命名检查清单

新加一个类时：

1. **它继承了什么？** → 类名包含父类名作为后缀
2. **它放在哪个模块？** → 文件名能猜到类名
3. **它会被导出吗？** → 名字在 `__all__` 里

三条都过 → 合规。

> **本节为命名最高权威**。本节未提到的命名争议一律按 §2.2 核心规则裁决。

---

## 3. 函数/方法内编码规则

- 尽可能使用文档中有明确定义的变量名（例如 `D`、`B` 都是文档中明确约定用途的符号）。
- 如无必要，不要定义文档中没有定义过的变量。
- 产生了新的局部变量 → **必须写注释说明定义缘由**（方法内 `#` 注释 → 英文，见 §4.2）。

---

## 4. 注释（两类注释，语言不同 — 解决了之前双标准的冲突）

### 4.1 文档型注释（模块/类/方法前的 docstring + 分段注释块）— 允许中文

**模块 docstring**（每个 `.py` 文件前 3 行三引号）：中文，必须回答三个问题（来自旧 lp/STYLE.md）：
1. 这个文件解决什么问题？（存在意义）
2. 怎么用？（一行示例，若适用）
3. 读者应该读哪里、可以跳过哪里？（读者指南）

**类 docstring**：中文，一句话——这个类做什么、对应论文哪条约束（如果是 Model 子类）。

**方法 docstring**：中文，关键参数说明（`Args`/`Returns`/`Raises`/`复杂度`/`Example`，纯算法/复杂函数要求 Google 风格）。

**分段注释块**（类之前、方法之间、模块内部的大段结构说明）— **允许中文**。格式建议：

```python
# ========================================================================
# 这部分是什么？
#   变量声明——ctx.vector / scalar / var 三个方法。
#   读者：需要知道怎么声明变量 → 读这里。内部实现 → 可以跳过。
# ========================================================================
```

或更小粒度：

```python
# -- 内部（读代码时可跳过）----------------------------------------------
```

> **重要 — 澄清判定边界（解决原 B3 伪冲突）**：
> 上述「分段注释块」和类/方法 docstring 同属**文档型注释**，允许中文。
> 判断它是不是文档型注释的标准：
> （1）它出现在**缩进级别 0**（不在任何 `def`/函数体的内部），或
> （2）它出现在 `class Xxx:` 的缩进级、但**不在任何 `def xxx:` 的方法体内部**。
> 满足（1）或（2）→ 文档型注释，允许中文。

### 4.2 代码内注释（函数/方法体内部的零散 `#` 注释）— 必须英文

```python
def some_method(self, x: float) -> float:
    """方法 docstring（中文）。"""
    # 好：解释为什么，英文，非显而易见处才写
    d = x * self._beta  # scale to per-bandwidth cost (§2.4 formula 11)
    # 坏：出现中文 —— "乘以缩放系数 β" → 一律打回
    return d
```

一句话记忆：**方法体内的 `#` = 英文；方法体外的 `#` = 中文（分段注释块）或英文都允许。**

---

## 5. 导入

```python
# 标准顺序:  future → stdlib → numpy → problem → 其他
from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from problem.ctx import Model
# 延迟导入 ctx 用 TYPE_CHECKING
if TYPE_CHECKING:
    from problem.ctx import Ctx
```

顺序错误（例如把 `from problem...` 放在 `import numpy` 前面）→ 打回。

---

## 6. 数据类

- 纯数据容器（跨模块传递的值对象）→ **必须**用 `@dataclass(frozen=True)`。
- 有行为的类（尤其是 `Model` 子类）→ 用普通 class，手写 `__init__`。
- 禁止裸 `dict` 跨模块（见 `AGENTS.md` §5）：模块边界上（入参/返回值）传的是 frozen dataclass，`dict` 仅限模块内部临时数据结构。

---

## 7. 纯面向对象设计（不要裸露模块级函数）

**纯面向对象设计：尽可能不要裸露的模块级函数。** 能放进类的逻辑和方法，统一放类里：

- 算法本体挂在类上（例如 `AnalyticNetworkBuilder.system_of()` 是解析 G/b 的唯一真相，`ThermalNetworkBuilder.precompute()` 是预计算的唯一真相）。
- 多态设计的意义在于"调用方只认抽象类"——函数壳会让多态形同虚设。
- **模块级只允许**：
  - 包 `__init__.py` 的 re-export
  - 与类无关的**纯工具**（几何判定等极少数）
- 反例（2026-08-13 已整改）：热网络的 `build_thermal_system` / `build_thermal_network` 裸露模块函数全部删除，收编进 builder 类。

---

## 8. 文件组织（一个文件只解释一件事 — 来自旧 lp/STYLE.md §1）

文件目录结构反映概念之间的层级关系：
- 每个文件开头的**模块 docstring**（三行中文）要能让读者在**不理解其他模块**的情况下，读懂当前模块的逻辑。
- 如果一个文件里同时出现了两个独立概念（比如 engine 里既做 store 又做 solver）→ **拆**。

### 文件内部结构顺序

```
1. 顶层 docstring（中文，三问）
2. from __future__ → stdlib → numpy → problem → 其他
3. 数据类（frozen dataclass 值对象，如有）
4. ABC 抽象类（如有）
5. 默认 / 具体实现类
6. 内部辅助（标 `# -- 内部（读代码时可跳过）--` 分隔块）
```

---

## 9. ABC 抽象（抽象做 ABC，实现可替换 — 来自旧 lp/STYLE.md §2）

如果一个概念的实现工具与概念本身无关 → 抽 ABC。

| 概念 | 无关工具 | 抽象形式 |
|------|---------|---------|
| `Model` | 用什么求解器（cvxpy/自研…） | `class Model(ABC)` |
| `Solver` | 不一定永远是 cvxpy | `Solver` ABC + `CvxSolver` 默认 |
| `ResultStore` | 存储不一定永远是目录文件 | `_Backend(ABC)` + `_DirBackend` 默认 |

**我们关心的是接口，不是具体实现。** 具体实现可以随时换。

---

## 10. 日志与结果保留（论文原材料必须妥善保管 — 来自旧 lp/STYLE.md §4）

- 运行结果 = 实验数据 → 论文的原材料。
- `ResultStore`：每次求解落盘，`meta.json` 记录完整性。
- `Runner`：缓存透明，同参数不解两次。
- 日志：帮助调试 + 作为实验记录的一部分。
- 日志和存储同样要遵守 ABC 原则——`ResultStore` 有 `_Backend`，未来可以换存储介质。

---

## 11. 审查清单（每次提 PR / 交付前勾）

- [ ] Model 子类：`__init__` 预计算了全部系数？
- [ ] Model 子类：`build()` ≤ 30 行、无 import、无复杂循环？
- [ ] Model 子类：`cache_key()` 返回可哈希元组（非 `None`）？
- [ ] 类命名是否符合 §2.2（子类带直接父类后缀）？
- [ ] 方法体内部的零散 `#` 注释全部是英文？（文档型分段注释、类前/方法前注释允许中文）
- [ ] 导入顺序 correct（future → stdlib → numpy → problem → other）？
- [ ] 跨模块传递的值对象全部是 `@dataclass(frozen=True)`，没有裸 `dict`？
- [ ] 没有不必要的模块级裸函数（算法本体都在类上）？
- [ ] 每个 `.py` 文件顶部有三行中文模块 docstring？
