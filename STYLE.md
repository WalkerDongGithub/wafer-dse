# 代码风格规范

最核心原则：代码清晰、易于验证、可读性好、逻辑扫一眼就能看懂，比代码是否高效、是否鲁棒重要一万倍，代码的清晰整洁永远是编码的第一原则。只有不牺牲清晰整洁性，才能考虑是否高效和鲁棒。

适用于 `src/lp/models/` 下所有模型，以及所有新增模型。

## Model 结构

每个 Model 必须严格遵循三段式：

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
- `build()` 不 import，不做复杂循环。系数全在 `__init__` 算好了。
- `cache_key()` 不能返回 `None`。如果模型参数可变，把参数编码进去。

## 命名

| 元素 | 规范 | 示例 |
|------|------|------|
| 模块 (`.py`) | `_` 前缀，小写+下划线 | `_network.py`, `_bump.py` |
| 类 | 大驼峰 | `SteadyStateModel`, `BumpModel` |
| 函数 | 小写+下划线 | `build_thermal_network` |
| 私有方法/属性 | `_` 前缀 | `self._coeff`, `self._rhs` |
| 变量名 | 简短、数学符号优先 | `L`, `B`, `G`, `b` |

## 函数/方法内编码规则

尽可能的使用文档当中有明确定义的变量名，例如D、B都是文档中明确规定有明确用途的变量，如无必要，不要定义文档中没有定义过的变量。如果产生了新的局部变量，一定写清注释说明定义缘由 


## 注释

- **模块 docstring**：中文，写清楚对应论文哪一节
- **类 docstring**：中文，一句话——这个模型做什么
- **方法 docstring**：中文，关键参数说明
- **代码内注释**：英文，只在非显而易见处使用 `#`。不用中文注释

## 导入

```python
# 标准顺序:  future → stdlib → numpy → lp → 其他
from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from lp.ctx import Model
# 延迟导入 ctx 用 TYPE_CHECKING
if TYPE_CHECKING:
    from lp.ctx import Ctx
```

## 数据类

纯数据容器用 `@dataclass(frozen=True)`。有行为的类（尤其是 Model 子类）用普通 class，手写 `__init__`。

## 审查清单

- [ ] `__init__` 预计算了全部系数？
- [ ] `build()` ≤ 30 行、无 import、无复杂循环？
- [ ] `cache_key()` 返回可哈希元组？
- [ ] 中文只出现在 docstring 中？
- [ ] 模块/类/函数命名符合规范？

## 面向对象

**纯面向对象设计：尽可能不要裸露的模块级函数。** 能放进类的逻辑和方法，统一放类里：

- 算法本体挂在类上（`AnalyticNetworkBuilder.system_of()` 是解析 G/b 的唯一真相，`ThermalNetworkBuilder.precompute()` 是预计算的唯一真相）
- 多态设计的意义在于"调用方只认抽象类"——函数壳会让多态形同虚设
- 模块级只允许：包 `__init__` 的 re-export、与类无关的纯工具（几何判定等极少数）
- 2026-08-13 已执行的例子：热网络的 `build_thermal_system` / `build_thermal_network` 模块函数删除，全部收编进 builder 类
