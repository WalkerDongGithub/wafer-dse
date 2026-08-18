# test05 — μbump 预算 (src/problem/models/phys/bumps/_bump.py)

## 模块定位

每个 die 底面有 μbump 阵列（die → interposer）。总 bump 数由面积和 pitch 决定。信号 lane 和电源共享同一批 bump——信号拿得多，电源就拿得少。这是零和竞争。

**核心方程**: $N_{total} = \eta A / p^2$，$N_{pwr} = \lceil P / (V_{dd} \cdot I) \rceil$，$N_{sig} + N_{pwr} \le N_{total}$

```python
import sys; sys.path.insert(0, '../src')
from physical.config.spec_bump import BumpSpec, DieBumpBudget
from problem.models.phys.bumps import BumpModel
from topology import Mesh
from problem import Ctx
```

---

## 1. 预算数字

12×12mm die，45μm pitch，70% 利用率，50W，0.8V，75mA/bump。

$N_{total} = 144 / 0.045^2 \times 0.7 = 49777$
$N_{pwr} = \lceil 50 / (0.8 \times 0.075) \rceil = \lceil 833.3 \rceil = 834$
$N_{sig} = 49777 - 834 = 48943$

信号占 98.3%——UCIe 16mW/lane 时动态功耗微不足道。换 SerDes 425mW/lane 后电源需求会显著增加。

```python
b = DieBumpBudget("d0", BumpSpec("t", 45, 75), 12, 12, 50, 0.8, 0.7)
print(f"total={b.total_bumps}, pwr={b.power_bumps}, sig={b.available}")
print(f"signal fraction = {b.available/b.total_bumps*100:.1f}%")
assert b.total_bumps == 49777
assert b.power_bumps == 834
assert b.available == 48943
```

---

## 2. 功耗翻倍 → 电源 bump 翻倍

用 30W 和 60W 两个精确整除值避免 ceil 取整误差。$30/(0.8\times0.075)=500$，$60/(0.8\times0.075)=1000$。

```python
s = BumpSpec("t", 45, 75)
b30 = DieBumpBudget("d", s, 12, 12, 30, 0.8)
b60 = DieBumpBudget("d", s, 12, 12, 60, 0.8)
print(f"P=30W → {b30.power_bumps} power bumps")
print(f"P=60W → {b60.power_bumps} power bumps")
assert b60.power_bumps == 2 * b30.power_bumps
```

---

## 3. 约束系数

每条 lane 的系数 = $(1/lr) \times (1 + ppl/(V \cdot I))$。第一项 $1/lr$ 是信号 bump，第二项是这条 lane 的动态功耗带来的额外电源 bump。

$B=800, lr=32, ppl=0.016, V=0.8, I=0.075$：
$coeff = 800/32 \times (1 + 0.016/0.06) = 25 \times 1.267 = 31.667$

```python
graph = Mesh(2)
# die == node 恒等映射（当前阶段简化）
n2d = {n: n // 2 for n in range(4)}
d2l = {}
for li, (u, v) in enumerate(graph.links):
    d2l.setdefault(n2d[u], []).append(li)
    if n2d[v] != n2d[u]:
        d2l.setdefault(n2d[v], []).append(li)
d2l = {k: sorted(v) for k, v in d2l.items()}
budget = DieBumpBudget("d0", BumpSpec("t", 45, 75), 12, 12, 50, 0.8, 0.7)
model = BumpModel([budget], d2l, graph.n_links, lane_rate=32.0, power_per_lane=0.016)

ctx = Ctx(); ctx.vector("L", graph.n_links)
model.build(ctx, B=800.0)

c = ctx.constraints[0]
total = sum(abs(t.coeff) for t in c.terms)
expected = 800.0 / 32.0 * (1.0 + 0.016 / (0.8 * 0.075))
print(f"coeff per link = {total / len(c.terms):.4f},  expected = {expected:.4f}")
print(f"rhs = {c.rhs}")
assert abs(total / len(c.terms) - expected) < 1e-6
assert c.rhs == 48943.0
```
