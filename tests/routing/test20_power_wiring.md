# test20 — WiringModel power 走线项（V5 §2(2d) v5.25/v5.26，作者 round 21 耦合案例）

## 模块定位

作者 round 21+ 指令【1】标准耦合案例：Power/GND 走线占用 RDL 容量——
power 走线需求过大顶满布线容量 → 必须 (a) 提高散热 或 (b) 降性能（减带宽）
换布线布得下。"功耗—散热—布线/性能"三者互相牵制。

V5 v5.25/v5.26（DomainExpert 定案）数学形式（edge 容量，vert 同理）：

$$
\sum_{l} \frac{B}{\text{lr}_l}(1 + c_{\text{pwr}} s^{\text{dyn}}_l)\, L_l
+ c_{\text{pwr}}(P_0 + \beta_P B) \le \text{cap}_e
$$

- **P_dyn 折进 L 系数**（与 BumpModel 动态功耗先例一致）：信号 lane 越多 →
  P_dyn 越大 → power 走线越多，耦合链完整（带宽→lane→功耗→power 走线）；
- **P0 + β_P·B 为 rhs 扣减**（常数部分，固定 B 下 LP 结构不变，insight 7）；
- c_pwr_lane_per_w 默认 0 = 关闭（向后兼容）。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from physical.layout.thermal_network import DiePlacement
from problem.models.phys.wiring import build_wiring_grid, populate_paths, WiringModel
from problem import Ctx
```

---

## 1. 场景：对角 die（2 条候选路径），fixed 模式 + power 项

d0(0,0), d1(13,13) 对角 → 每条链路 2 条 L 形候选路径。B=100, lr=10,
s_dyn=0.1 W/lane, P0=10W, β_P=0.2, c_pwr_lane_per_w=1.0。

### 手算（link0 首路径上的边 e38）

信号项系数 = B/lr = 100/10 = 10（每链路）。
power 项 = c_pwr·[(B/lr)·s_dyn·L]（折进系数）+ c_pwr·(P0 + β_P·B)（rhs 扣减）：

- L 系数 = (B/lr)(1 + c_pwr·s_dyn) = 10·(1 + 1.0×0.1) = 11.0
- rhs 扣减 = c_pwr·(P0 + β_P·B) = 1.0×(10 + 0.2×100) = 30.0

```python
p = [DiePlacement("d0", 0, 0, 12, 12), DiePlacement("d1", 13, 13, 12, 12)]
g0 = build_wiring_grid(p, 30, 30, 4, 10, 5.0)
specs = [{"from_die": 0, "to_die": 1}, {"from_die": 1, "to_die": 0}]
g = populate_paths(g0, specs)
lane_rate = np.array([10.0, 10.0])
s_dyn = np.array([0.1, 0.1])

# 无 power 项（c_pwr=0，默认）：L 系数 = B/lr = 10
w0 = WiringModel(g, specs, [0, 1], lane_rate, fixed_paths=True)
ctx0 = Ctx(); ctx0.vector("L", 2)
w0.build(ctx0, B=100.0)
c0 = [c for c in ctx0.constraints if c.name == "route_edge_e38"][0]
coeff0 = {t.var: t.coeff for t in c0.terms}
print(f"c_pwr=0: e38 coeff={coeff0} rhs={c0.rhs}")
assert abs(coeff0.get("L", 0.0) - 10.0) < 1e-9, "无 power 项：L 系数 = B/lr = 10"
# 只有 link0 走 e38（link0 首路径含 e38）
assert abs(c0.rhs - 160.0) < 1e-9
print("✓ c_pwr=0（默认）：行为与现有固定路径模式一致（向后兼容）")
```

---

## 2. power 项开启：L 系数 = (B/lr)(1 + c_pwr·s_dyn)，rhs 扣减 c_pwr·(P0+β_P·B)

```python
w = WiringModel(g, specs, [0, 1], lane_rate, fixed_paths=True,
                c_pwr_lane_per_w=1.0, p0_w=10.0, beta_p=0.2, s_dyn=s_dyn)
ctx = Ctx(); ctx.vector("L", 2)
w.build(ctx, B=100.0)

# 找 e38（link0 首路径经过）——可能多个 link 经过，取含 L0 的
c38 = [c for c in ctx.constraints if c.name == "route_edge_e38"][0]
coeff = {t.var: t.coeff for t in c38.terms}
print(f"c_pwr=1: e38 coeff={coeff} rhs={c38.rhs}")

# L0 系数 = (B/lr)(1 + c_pwr·s_dyn) = 10 × 1.1 = 11
assert abs(coeff.get("L", 0.0) - 11.0) < 1e-9, f"L 系数应为 11, 实际 {coeff.get('L',0)}"
# rhs = cap − c_pwr·(P0+β_P·B) = 160 − 30 = 130
assert abs(c38.rhs - 130.0) < 1e-9, f"rhs 应为 130, 实际 {c38.rhs}"
print("✓ power 项：L 系数 10→11（+c_pwr·s_dyn 折进），rhs 160→130（−c_pwr·(P0+β_P·B)）")
```

---

## 3. power 项使布线更紧：同 L 下 lhs 更大 / rhs 更小

固定 L=[1,1]（可行解附近），对比 c_pwr=0 vs 1 的约束余量：
power 项把 lhs 提高（L 系数 +）且 rhs 降低（扣减）→ 布线约束更紧 → B* 更低
（耦合机制：功耗占用 RDL → 降性能/提散热才能布线）。

```python
def slack(ctx, name, L_vals):
    c = [c for c in ctx.constraints if c.name == name][0]
    lhs = sum(t.coeff * L_vals[t.idx] for t in c.terms if t.var == "L")
    return c.rhs - lhs

Lv = [1.0, 1.0]
s0 = slack(ctx0, "route_edge_e38", Lv)
s1 = slack(ctx, "route_edge_e38", Lv)
print(f"e38 余量: c_pwr=0 → {s0:.1f}   c_pwr=1 → {s1:.1f}")
assert s1 < s0, "power 项应使布线余量变小（更紧）"
print("✓ power 项收紧布线约束：功耗占用 RDL 容量的机制成立")
```

---

## 4. optimize 模式同样生效

默认（非 fixed）联合模型也应含 power 项——同一 c_pwr 口径。

```python
w_opt = WiringModel(g, specs, [0, 1], lane_rate, fixed_paths=False,
                    c_pwr_lane_per_w=1.0, p0_w=10.0, beta_p=0.2, s_dyn=s_dyn)
ctxo = Ctx(); ctxo.vector("L", 2)
w_opt.build(ctxo, B=100.0)

# 需求等式不受 power 影响（x 仍 = (B/lr)·L）
dem = [c for c in ctxo.constraints if c.name == "route_dem_l0"][0]
dem_l = {t.var: t.coeff for t in dem.terms}
assert abs(dem_l.get("L", 0.0) + 10.0) < 1e-9, "route_dem 的 L 系数仍 = −B/lr = −10"

# 边容量：x 系数 + 无 power 项直接（x 需求已含 P_dyn）——检查存在 power 扣减的边
# 简化：验证存在 rhs < 原始 cap 的 route_edge（power 扣减生效）
caps = set()
for c in ctxo.constraints:
    if c.name.startswith("route_edge_"):
        caps.add(round(c.rhs, 3))
print(f"optimize 模式 route_edge rhs 集合（含 power 扣减）: {sorted(caps)[:6]}")
assert min(caps) < 160.0, "存在 power 扣减后的边容量"
print("✓ optimize 模式 power 项生效（rhs 扣减）")
```

---

## 5. cache_key 区分 power 项

```python
k0 = WiringModel(g, specs, [0, 1], lane_rate, fixed_paths=True).cache_key()
k1 = WiringModel(g, specs, [0, 1], lane_rate, fixed_paths=True,
                 c_pwr_lane_per_w=1.0, p0_w=10.0, beta_p=0.2, s_dyn=s_dyn).cache_key()
assert k0 != k1, "c_pwr 必须进 cache_key（不同参数不同缓存）"
assert k0 == WiringModel(g, specs, [0, 1], lane_rate, fixed_paths=True).cache_key()
print(f"✓ cache_key 区分 power 项: {k0[:3]}... vs {k1[:3]}...")
```

---

## 结论

WiringModel power 走线项（V5 §2(2d) v5.25/v5.26，作者 round 21 耦合案例）实现：

- **数学形式**：Σ (B/lr)(1 + c_pwr·s_dyn)·L + c_pwr·(P0+β_P·B) ≤ cap——P_dyn 折进
  L 系数（物理完整，与 BumpModel 先例一致），P0+β_P·B 为 rhs 扣减（LP 线性保持）；
- **参数契约**：`c_pwr_lane_per_w` 构造参数（默认 0 关闭），P0/β_P/s_dyn 传入
  （P_die 口径与 (2c) 同源）；
- **两种模式同时生效**（optimize + fixed_paths，同一口径——防不公平基线）；
- 手算锚点：L 系数 10→11、rhs 160→130（c_pwr=1, s_dyn=0.1, P0=10, β_P=0.2, B=100）；
- cache_key 区分参数。
