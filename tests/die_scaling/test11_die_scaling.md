# test11 — die 缩放模型 (V4 §2.8)

## 模块定位

V4 §2.8 把 die 的物理尺寸和峰值功耗建模为端口带宽 B 的仿射函数：

$$
d(B) = d_0 + \alpha_d \cdot B,
\qquad
A_{die}(B) = d(B)^2,
\qquad
P_{peak}(B) = P_0 + \beta_P \cdot B
$$

- $d(B)$ 进 μbump 总预算：$N_{total}(B) = \eta \cdot A_{die}(B)/p^2$。
- $P_{peak}(B)$ 进热约束 rhs 和电源 bump 需求。

当前实现是 $\alpha_d = \beta_P = 0$ 的退化特例（面积/峰值功耗不随 B 变）。本测试用手算锚点验证非退化情形下 bump 约束与热约束的 rhs 随 B 正确缩放。

```python
import sys; sys.path.insert(0, '../src')
import inspect
import numpy as np
from physical.params import DieParams
from physical.config.spec_bump import BumpSpec, DieBumpBudget
from physical.config.spec_thermal import CoolingSolution
from problem import Ctx
from problem.ctx import Model
from problem.models.phys.bumps import BumpModel
from problem.models.phys.therm._temp_limit import GlobalPowerModel
from problem.models.phys.therm._steady_state import SteadyStateModel
from physical.layout.thermal_network import (
    DiePlacement, MfitStackConfig, ThermalNetworkBuilder, AnalyticNetworkBuilder,
)
```

---

## 1. DieParams 的缩放属性

取 $d_0=10$, $\alpha_d=0.1$ mm/Gbps, $\beta_P=0.2$ W/Gbps, $P_0=10$W。

$B=100$ 时：

$$
d(100) = 10 + 0.1 \cdot 100 = 20 \text{ mm},
\qquad
A_{die}(100) = 20^2 = 400 \text{ mm}^2,
\qquad
P_{peak}(100) = 10 + 0.2 \cdot 100 = 30 \text{ W}
$$

```python
d = DieParams(width_mm=10.0, height_mm=10.0, static_power_w=10.0, vdd_v=1.0,
              d0_mm=10.0, alpha_d=0.1, beta_p=0.2)
assert d.side_mm(0.0) == 10.0
assert d.side_mm(100.0) == 20.0
assert d.area_mm2_at(100.0) == 400.0
assert d.peak_power_w(100.0) == 30.0

# 退化特例：不传缩放参数 → α_d=β_P=0, d0=width → 面积/峰值功耗不随 B 变
d0 = DieParams(width_mm=10.0, height_mm=10.0, static_power_w=10.0, vdd_v=1.0)
assert d0.area_mm2_at(100.0) == 100.0
assert d0.peak_power_w(100.0) == 10.0
print("DieParams 缩放属性 ✓")
```

---

## 2. DieBumpBudget 的 B 相关预算

同一组缩放参数 + bump 工艺（pitch=100μm, I=100mA, η=1.0, V=1.0V, P0=10W）。

$B=100$ 时：

$$
N_{total}(100) = 400 \cdot \frac{10^6}{100^2} \cdot 1.0 = 40000,
\qquad
N_{pwr}(100) = \lceil 30 / (1.0 \times 0.1) \rceil = 300,
\qquad
N_{sig}(100) = 40000 - 300 = 39700
$$

$B=0$ 退化为 toy 基线：总数 10000，电源 100，信号 9900。

```python
s = BumpSpec("toy-bump-100μm", 100.0, 100.0)
b = DieBumpBudget("d0", s, 10.0, 10.0, 10.0, 1.0, 1.0,
                  d0_mm=10.0, alpha_d=0.1, beta_p=0.2)
assert b.total_bumps_at(100.0) == 40000
assert b.power_bumps_at(100.0) == 300
assert b.available_at(100.0) == 39700

assert b.total_bumps_at(0.0) == 10000
assert b.power_bumps_at(0.0) == 100
assert b.available_at(0.0) == 9900
print("DieBumpBudget 缩放预算 ✓")
```

---

## 3. BumpModel：rhs 随 B 变

单 die，一条入射链路（lr=10 Gbps, ppl=0.1 W/lane, V=1.0V, I=0.1A）。

链路系数（与 B 无关的 lhs 缩放）：

$$
c = \frac{1}{10}\left(1 + \frac{0.1}{1.0 \times 0.1}\right) = 0.2 / \text{Gbps}
$$

$B=100$ 时写出的约束是 $B \cdot c \cdot L \le N_{sig}(B)$：

$$
100 \cdot 0.2 \cdot L \le 39700
\quad\Longrightarrow\quad
20 L \le 39700
$$

```python
model = BumpModel([b], {0: [0]}, 1, lane_rate=10.0, power_per_lane=0.1)
ctx = Ctx(); ctx.vector("L", 1)
model.build(ctx, B=100.0)
c = ctx.constraints[0]
coeff = sum(t.coeff for t in c.terms)
print(f"bump 约束: {coeff:.1f} L ≤ {c.rhs:.0f}")
assert abs(coeff - 20.0) < 1e-9
assert c.rhs == 39700.0
```

$B=50$ 时，rhs 也要跟着缩：$d(50)=15$, $A=225$, $N_{total}=22500$, $P_{peak}=20$, $N_{pwr}=200$, $N_{sig}=22300$。

$$
50 \cdot 0.2 \cdot L \le 22300
\quad\Longrightarrow\quad
10 L \le 22300
$$

```python
ctx2 = Ctx(); ctx2.vector("L", 1)
model.build(ctx2, B=50.0)
c2 = ctx2.constraints[0]
assert abs(sum(t.coeff for t in c2.terms) - 10.0) < 1e-9
assert c2.rhs == 22300.0
print(f"B=50 时: {sum(t.coeff for t in c2.terms):.1f} L ≤ {c2.rhs:.0f} ✓")
```

---

## 4. SteadyStateModel：rhs 随 β_P·B 变

单 die，$R_{vert}=1.0$，$T_{amb}=300$，$T_{max}=400$，$P_0=10$，$\beta_P=0.2$，一条链路（lr=10, ppl=0.1）。

$G=[1.0]$, $b=[1.0 \cdot 300]=[300]$, $G^{-1}=[1.0]$。

热约束 rhs（V4 §4）：

$$
rhs(B) = T_{max} - G^{-1}(P_{peak}(B) \cdot 1 + b)
       = 400 - (10 + 0.2 B + 300)
       = 90 - 0.2 B
$$

链路系数 $K = G^{-1} \cdot (ppl/lr) = 0.1/10 = 0.01$ K/Gbps。约束是 $B \cdot K \cdot L \le rhs(B)$。

$B=100$：$rhs = 70$，系数 $= 100 \times 0.01 = 1.0$。

$B=50$：$rhs = 80$，系数 $= 50 \times 0.01 = 0.5$。

```python
p = [DiePlacement("d0", 0, 0, 10, 10)]
G, bvec = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=1.0, T_ambient=300.0))
net = ThermalNetworkBuilder.precompute(G, bvec, 400.0, {0: [0]}, 1,
                                       np.array([10.0]), np.array([0.1]),
                                       P0_vec=np.array([10.0]))
model = SteadyStateModel(net, beta_p=0.2)

ctx = Ctx(); ctx.vector("L", 1)
model.build(ctx, B=100.0)
c = ctx.constraints[0]
print(f"B=100: {sum(t.coeff for t in c.terms):.1f} L ≤ {c.rhs:.0f}")
assert abs(sum(t.coeff for t in c.terms) - 1.0) < 1e-9
assert abs(c.rhs - 70.0) < 1e-9

ctx2 = Ctx(); ctx2.vector("L", 1)
model.build(ctx2, B=50.0)
c2 = ctx2.constraints[0]
print(f"B=50 : {sum(t.coeff for t in c2.terms):.1f} L ≤ {c2.rhs:.0f}")
assert abs(sum(t.coeff for t in c2.terms) - 0.5) < 1e-9
assert abs(c2.rhs - 80.0) < 1e-9
print("SteadyStateModel 缩放 rhs ✓")
```

---

## 5. cache_key：编码模型结构，不含 B

`cache_key()` 返回可哈希元组，编码 $\alpha_d/\beta_P/d_0$ 等结构参数；具体 B 值不进 cache_key（B 已在 Runner 缓存 key 里单独存在）。

```python
k1 = SteadyStateModel(net, beta_p=0.2).cache_key()
k2 = SteadyStateModel(net, beta_p=0.2).cache_key()
k3 = SteadyStateModel(net, beta_p=0.0).cache_key()
assert k1 == k2, "相同结构 cache_key 必须相同"
assert k1 != k3, "不同 β_P 是不同模型结构"
assert k1[0] == "therm_l1"

kb1 = BumpModel([b], {0: [0]}, 1, lane_rate=10.0, power_per_lane=0.1).cache_key()
kb2 = BumpModel([b], {0: [0]}, 1, lane_rate=10.0, power_per_lane=0.1).cache_key()
assert kb1 == kb2
assert kb1[0] == "bump_v2"
print("cache_key 结构编码 ✓")
```

---

## 6. 接口补齐

`Model.build` 统一为两参 `(ctx, B)`；`GlobalPowerModel` 补 `cache_key()`。

```python
sig = inspect.signature(Model.build)
params = list(sig.parameters)
assert params == ["self", "ctx", "B"], f"Model.build 应为 (ctx, B), 实际 {params}"

g = GlobalPowerModel(P0_total=10.0, total_area_mm2=100.0,
                     cooling=CoolingSolution("x", 0.5), total_incident_links=4)
key = g.cache_key()
assert isinstance(key, tuple)
assert key[0] == "therm_l0"
assert key == g.cache_key(), "cache_key 必须幂等"
print("接口补齐 ✓")
```

## 结论

§2.8 的 B 依赖已接入两条物理约束：μbump 总预算 $N_{total}(B)$ 与电源需求 $P_{peak}(B)$ 共同决定 bump rhs；$P_{peak}(B)$ 通过 $G^{-1}$ 进入热 rhs。退化特例（$\alpha_d=\beta_P=0$）下所有锚点回到 toy 基线，向后兼容。
