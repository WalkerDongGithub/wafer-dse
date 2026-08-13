# 命名规范

## 风格

- **类名**：大驼峰（`CapWords`），例 `EnvelopeModel`、`TrafficMatrixPattern`
- **方法/函数/变量**：下划线（`snake_case`），例 `cache_key()`、`as_flow_matrix()`
- **私有模块/类/函数**：单下划线前缀，例 `_envelope.py`、`_bump.py`、`_partitions()`
- **常量**：全大写，例 `__all__`
- **临时变量**：尽可能不要使用缩写，而是使用全称，例如`pattern` 而不是`pat`。
## 核心规则：子类携带父类名后缀

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

### 多级继承

携带**根父类**后缀即可，不需要叠床架屋。

```python
class Model(ABC):                        # 根
class PerformanceModel(Model):           # ✓  一级，带 Model
class EnvelopeModel(PerformanceModel):   # ✓  二级，带 Model 即可（不需要 EnvelopePerformanceModel）
class ThermalModel(Model):               # ✓
class SteadyStateModel(ThermalModel):    # ✓  SteadyStateThermalModel 是过度工程
```

### 为什么

读到 `class AllDerangements(Selector)`，类名不告诉你它是个 Selector——你得往回翻 import 或继承声明。读到 `class DerangementSelector(Selector)` 则没有这个问题。不依赖 IDE、LSP、grep。名字本身就说明了一切。

## 已识别的不规范命名

| 当前 | 父类 | 应改为 | 说明 |
|------|------|--------|------|
| `TrafficMatrix` | `Pattern` | `TrafficMatrixPattern` | 是一种流量模式，名字要体现 |
| `SConjugacyReps` | `Selector` | `ConjugacySelector` | S 前缀 + Reps 后缀都不表达 Selector |
| `AllDerangements` | `Selector` | `DerangementSelector` | 暴力枚举"全部 derangement"的 Selector |

这三个连起来读：`ConjugacySelector`、`DerangementSelector`、`ManualSelector`——全是 Selector，一眼就知道可互换。`SConjugacyReps`、`AllDerangements`、`ManualSelector` 放在一起看不出是同一族。

## 不需要改的

以下类不参与继承体系或属于基础设施，不受后缀规则约束：

- `Ctx`、`LinExpr`、`Var`、`VarSpec`、`Term`、`LinearC`、`Sense` — 数据契约 / 符号表达式 / 枚举
- `TopoStructure`、`ThermalNetwork`、`RoutingGrid`、`DiePlacement`、`MfitStackConfig` — frozen dataclass，值对象
- `Result`、`FeasibilityResult`、`BmaxResult`、`Runner`、`ResultStore` — 引擎基础设施
- `_Backend`、`_DirBackend` — 私有实现类

## 检查清单

新加一个类时：

1. **它继承了什么？** → 类名包含父类名作为后缀
2. **它放在哪个模块？** → 文件名能猜到类名
3. **它会被导出吗？** → 名字在 `__all__` 里

三条都过 → 合规。
