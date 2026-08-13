# test06 — C4 bump 预算 (src/lp/models/phys/bumps/_c4.py)

## 模块定位

C4 bump 是 interposer 底面的焊球阵列（interposer → substrate）。和 μbump 同样的面积阵列模型，但 pitch 更大（130μm vs 45μm），密度更低。

**核心方程**（论文 §3.3）：

$$N_{total} = \frac{A_{interposer}}{p^2} \times \eta$$
$$N_{pwr} = \left\lceil \frac{P_{total}}{V_{dd} \cdot I_{bump}} \right\rceil$$
$$N_{signal} = N_{total} - N_{pwr}$$

信号和电源竞争同一批焊球。$P_{total}$ 是 interposer 上所有 die 的总功耗——**静态 + 所有 SerDes 链路的动态功耗**。

```python
import sys; sys.path.insert(0, '../src')
from physical.bump.bump import BumpSpec, C4Budget
```

---

## 1. 给定面积和 pitch，总数是确定的

80×80 = 6400mm² interposer，130μm pitch，70% 利用率：

$$N_{total} = 6400 / 0.13^2 \times 0.7 = 265088$$

```python
c4 = C4Budget(BumpSpec("C4-130μm", 130, 300), 6400, 300, 0.8)
print(f"total = {c4.total_bumps}")
assert c4.total_bumps == 265088
```

---

## 2. 电源 bump 数由总功耗决定

$P_{total} = 300\text{W}$，$V_{dd}=0.8\text{V}$，$I_{bump}=300\text{mA}$：

$$N_{pwr} = \lceil 300 / (0.8 \times 0.3) \rceil = \lceil 1250 \rceil = 1250$$

$P_{total}$ 每增加 240W，电源 bump 增加 1000 个。

```python
print(f"P=300W → power_bumps = {c4.power_bumps}")
assert c4.power_bumps == 1250

# P 翻倍 → power_bumps 翻倍
c600 = C4Budget(BumpSpec("C4-130μm", 130, 300), 6400, 600, 0.8)
assert c600.power_bumps == 2 * c4.power_bumps
print(f"P=600W → power_bumps = {c600.power_bumps}")
```

---

## 3. 信号 bump = 总数 − 电源 bump

$$N_{signal} = 265088 - 1250 = 263838$$

```python
assert c4.available == c4.total_bumps - c4.power_bumps
print(f"signal = {c4.available}")
```

信号 bump 的占比取决于 $P_{total}$——功耗越大，电源吃得越多，信号剩得越少。对于 300W 的总功耗，电源只占 0.5%。但如果 SerDes 功耗很大（比如 50 条 SerDes 链路各 10W），$P_{total}$ 可能上 500W，电源 bump 占比就会到 1% 以上。这个比例应该从实际 LP 求解后的 $P_{total}$ 来算，而不是预先假定。

---

## 4. C4 和 μbump 公式相同，参数不同

| | μbump | C4 |
|---|---|---|
| 位置 | die → interposer | interposer → substrate |
| pitch | 45 μm | 130 μm |
| $I_{bump}$ | 75 mA | 300 mA |
| 密度 | ~494 /mm² | ~59 /mm² |
| 服务对象 | 单 die 的 UCIe 链路 | 整个 interposer 的 SerDes 链路 |

公式完全一样——面积阵列，信号和电源零和竞争。只是作用域不同：μbump 是 per-die，C4 是 per-interposer。
