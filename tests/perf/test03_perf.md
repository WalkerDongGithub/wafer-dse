# test03a — 流量需求模式 (src/lp/models/perf/traffic_based/traffic/)

## 模块定位

`Pattern` 是流量需求矩阵 D_{ij} 的抽象。排列只是生成 D 的一种策略——也可以有均匀负载、热点、任意浮点矩阵。

`EnvelopeModel` 只依赖 `Pattern.demand()` 接口，不关心 D 是怎么来的。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from lp.models.perf.traffic_based.traffic import (
    Pattern, Selector,
    TrafficMatrixPattern, PermutationPattern, PermutationRep,
    ConjugacySelector, DerangementSelector, ManualSelector,
    select_representatives,
)
from lp.models.perf.traffic_based.traffic._conjugacy import (
    _partitions, _canonical_permutation, _is_derangement,
)
```

---

## 1. TrafficMatrixPattern —— 任意需求矩阵

最简单的 Pattern：直接给 D。2 终端，0→1 发 0.5，1→0 发 0.3。

```python
tm = TrafficMatrixPattern("simple", [[0.0, 0.5], [0.3, 0.0]])
print(f"label = {tm.label}, n = {tm.n}")
D = tm.demand()
print(f"D =\n{D}")
assert tm.label == "simple"
assert tm.n == 2
assert isinstance(D, np.ndarray)
assert np.allclose(D, [[0.0, 0.5], [0.3, 0.0]])
assert isinstance(tm, Pattern)
```

`demand()` 返回副本，修改不影响内部：

```python
D = tm.demand()
D[0, 1] = 999.0
assert tm.demand()[0, 1] == 0.5
print("✓ demand() returns a copy")
```

---

## 2. PermutationPattern —— 排列

排列是特例：每行每列恰好一个 1。`sigma = (1, 2, 0)` 表示 0→1, 1→2, 2→0（3-cycle）。

```python
pp = PermutationPattern("3cycle", (1, 2, 0))
print(f"label = {pp.label}, sigma = {pp.sigma}, n = {pp.n}")
assert pp.sigma == (1, 2, 0)
assert pp.n == 3

D = pp.demand()
# 0→1, 1→2, 2→0 各为 1.0，对角 = 0
print(f"D =\n{D}")
assert D[0, 1] == 1.0 and D[0, 0] == 0.0
assert D[1, 2] == 1.0 and D[2, 0] == 1.0
assert isinstance(pp, Pattern)
```

permutation 不含自环（i → i 为 0）：

```python
pp2 = PermutationPattern("with_self", (0, 2, 1))
D2 = pp2.demand()
# 0→0 = 0 (自环不计入需求), 1→2 = 1, 2→1 = 1
assert D2[0, 0] == 0.0 and D2[0, 1] == 0.0 and D2[0, 2] == 0.0
assert D2[1, 2] == 1.0 and D2[2, 1] == 1.0
print(f"D (0→0 filtered) =\n{D2}")
print("✓ self-loop (i→i) excluded from demand")
```

---

## 3. 排列可哈希、可比较

排列用作 cache_key，必须可哈希。

```python
a = PermutationPattern("p", (1, 2, 0))
b = PermutationPattern("p", (1, 2, 0))
c = PermutationPattern("q", (1, 2, 0))
assert hash(a) == hash(b)
assert a == b
assert a != c
print("✓ PermutationPattern is hashable and comparable")
```

---

## 4. PermutationRep 是 PermutationPattern 的别名

```python
assert PermutationRep is PermutationPattern
print("✓ PermutationRep == PermutationPattern")
```

---

## 5. 整数分拆

p(4) = 5：4 分为正整数之和有 5 种写法。每个分拆对应 S_n 的一个共轭类。

```python
print(f"p(4) = {len(_partitions(4))}: {_partitions(4)}")
print(f"p(6) = {len(_partitions(6))}")
assert len(_partitions(4)) == 5
assert len(_partitions(6)) == 11
```

---

## 6. Derangement 过滤

Derangement = 分拆中不含 1（无自环）。n=4 剩 `[4]` 和 `[2,2]` → 2 个代表元。n=6 剩 4 个。

```python
r4 = ConjugacySelector(True).select(4)
r6 = ConjugacySelector(True).select(6)
print(f"derangements(4) = {len(r4)}: {[r.label for r in r4]}")
print(f"derangements(6) = {len(r6)}: {[r.label for r in r6]}")
assert len(r4) == 2
assert len(r6) == 4
```

---

## 7. 标准排列构造

每个 cycle type 有唯一的标准代表元。4-cycle = `(1,2,3,0)`，3+2 cycle = `(1,2,0, 4,3)`。

```python
sigma4 = _canonical_permutation((4,))
print(f"4-cycle = {sigma4}")
assert sigma4 == (1, 2, 3, 0)
assert _is_derangement(sigma4)

sigma32 = _canonical_permutation((3, 2))
print(f"3+2 cycle = {sigma32}")
assert sigma32 == (1, 2, 0, 4, 3)

# 1-cycle 不是 derangement
sigma1 = _canonical_permutation((1,))
assert not _is_derangement(sigma1)
print("✓ canonical permutations correct")
```

---

## 8. select_representatives 返回 list[Pattern]

```python
reps = select_representatives(n_terminals=4)
print(f"select_representatives(4) = {len(reps)} reps")
assert len(reps) > 0
for r in reps:
    assert isinstance(r, Pattern)
print("✓ select_representatives returns list[Pattern]")
```

---

## 9. Selector 多态 —— 三种策略可互换

`Selector` 是 ABC。`ConjugacySelector`、`DerangementSelector`、`ManualSelector` 都实现 `select(n) → list[Pattern]`。

```python
from lp.models.perf.traffic_based.traffic import Selector
from lp.models.perf.traffic_based.traffic._brute import DerangementSelector
from lp.models.perf.traffic_based.traffic._manual import ManualSelector

selectors: list[Selector] = [
    ConjugacySelector(True),
    DerangementSelector(),
    ManualSelector([(1, 0, 3, 2), (2, 3, 0, 1)]),
]

for sel in selectors:
    assert isinstance(sel, Selector)
    reps = sel.select(4)
    print(f"{type(sel).__name__} → {len(reps)} reps: {[r.label for r in reps]}")
    for r in reps:
        assert isinstance(r, Pattern)

print("✓ all Selector implementations return list[Pattern]")
```

### select_representatives 接受自定义 selector

```python
manual = ManualSelector([(1, 0, 3, 2)])
reps = select_representatives(n_terminals=4, selector=manual)
assert len(reps) == 1
assert reps[0].label == "manual_0"
print(f"custom selector → {[r.label for r in reps]}")
```

---

## 当前局限

以上用 $S_n$ 共轭类作为 $\text{Aut}(\mathcal{G})$ 轨道的保守近似——代表元数量偏多，LP 约束更严但不会漏掉最坏情况。真正的 $\text{Aut}(\mathcal{G})$ 轨道计算尚未实现。