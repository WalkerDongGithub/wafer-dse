# 开发规范

## 测试驱动迭代

**所有模型修改必须遵循以下流程：**

1. **先在 `tests/` 下写 `.md` 测试文件。** 叙述 + 可运行 Python 代码块交替。测试应该讲清楚：输入是什么、公式是什么、预期输出是什么、为什么是这个数。不依赖 solver——纯输入 → 纯输出 → assert。

2. **测试通过我肉眼确认后，再写实现代码。** 如果测试本身有逻辑问题，先改测试达成共识。测试是比代码更重要的产出。

3. **代码风格以 `src/problem/models/` 下现有文件为基准。**
   - `__init__` 预计算全部系数（矩阵、向量、标量）
   - `build(ctx, B)` 只做 B 缩放和写约束，不超过 30 行
   - `cache_key()` 返回可哈希元组（Runner 持久化缓存用）
   - 中文注释只出现在模块/类/函数的 docstring 中，代码内注释用英文

4. **`run_all.py` 全绿才能提交。** `cd tests && PYTHONPATH=../src python3 run_all.py` 必须 0 失败。

5. **如果文档要求的功能只有代码没有测试，直接判定功能缺失**，文档全部重要功能要求都要通过单元测试佐证实现。

## 测试写法

每个 `tests/<模块>/test0X_xxx.md` 是一个独立的教学单元。结构：

```
# test0X — 模块名 (src路径)

## 模块定位          ← 这个模块做什么, 在整体框架中的位置
## 第N步/案例N        ← 具体场景, 公式, 手算, 代码, assert
```

原则：
- **娓娓道来。** 从"我们有一个..."开始，逐步加复杂度。不是堆砌 assert。
- **手算在代码前。** 每个 assert 前面必须有手算过程——读者不需要跑代码就能看懂为什么这个 assert 是对的。
- **不依赖 solver。** 除非测试目标就是 solver 本身。模型测试只检查约束系数、预计算值、表达式求值。
- **LinExpr.evaluate() 可以替代 solver。** 给一组变量值，调 `evaluate()` 拿数值结果，不建 LP。

## 代码风格速查

```python
class SomeModel(Model):
    """一句话——这个模型做什么."""

    def __init__(self, ...):
        # 全部预计算
        self._coeff = ...    # 系数矩阵
        self._rhs = ...      # RHS 向量

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]
        scale = B / self._rate
        for i in range(...):
            (scale * self._coeff[i] @ L) <= self._rhs[i]

    def cache_key(self) -> tuple:
        return ("some_model", self._rate,
                self._coeff.tobytes(), self._rhs.tobytes())
```

## 论文一致性

代码实现的模型必须和 `notes/MATH_MODEL_COMPLETE_V2.md` 中的数学表述一致。对照表在 `notes/MODEL_CODE_TRACE.md`。不一致时，先改文档达成共识，再改代码。
