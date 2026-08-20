# test16 — 布线接入 build_scenario (src/problem/builder/_scenario.py + wiring)

## 模块定位

V5 v5.21（作者推翻 G4）把布线 (2d) 升为一级约束：power/gnd 与信号走线共享
interposer RDL，布线饱和常先于 bump 成为绑定约束。本测试验证
`build_scenario` 新增场景档位 `perf+bump+therm+wiring` 能把
`WiringModel`（edge/vert 三维容量，多商品流 lane 布线决策）接入模型列表：

- 场景用 token 解析（`+` 分隔），`wiring` token → 追加 `WiringModel`；
- on-die 链路（from_die == to_die）lane_rate=∞ → 不产生 route_dem 约束；
- 不设 c4_pad（D2D 布线；C4 属 I2I 段，范围外）→ 无 route_c4pad 约束；
- 回归锚点：`perf+bump+therm` 场景的模型列表与接入前逐位一致
  （DataSteward 口径红线：现有三场景语义逐位不变，Mesh(2)/ucie-32g/
  perf+bump+therm B*=11211 数值不能变）。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from problem.builder import build_scenario
from problem.models.perf import ObliviousValiantModel
from problem.models.phys.bumps import BumpModel
from problem.models.phys.therm import SteadyStateModel
from problem.models.phys.wiring import WiringModel
from physical.params import TOY
from topology import MeshTopology, FullMeshTopology
from layout import place
```

---

## 1. 场景 token 解析：perf+bump+therm+wiring 追加 WiringModel

`build_scenario` 按 `+` 拆 token：`bump`/`therm`/`wiring` 各追加一个模型。
`perf+bump+therm+wiring` 应有 4 个模型，顺序为
perf → bump → therm → wiring（与 E3 消融阶梯的逐级加严方向一致）。

```python
topo = MeshTopology(2)
P = TOY
layout = place(topo, P)
models, meta = build_scenario(topo, "perf+bump+therm+wiring", P, layout)

types = [type(m).__name__ for m in models]
print(f"模型列表: {types}")
assert types == ["ObliviousValiantModel", "BumpModel", "SteadyStateModel", "WiringModel"]
assert meta["n_dies"] == 4
print("✓ perf+bump+therm+wiring → 4 模型，wiring 在最后")
```

---

## 2. 回归锚点：perf+bump+therm 模型列表逐位不变

接入前 `perf+bump+therm` 返回 `[perf, bump, therm]`（3 模型）。
token 解析必须保持该行为逐位一致——这是 DataSteward 全部既有数据的口径基础。

```python
models3, _ = build_scenario(topo, "perf+bump+therm", P, layout)
types3 = [type(m).__name__ for m in models3]
print(f"perf+bump+therm 模型列表: {types3}")
assert types3 == ["ObliviousValiantModel", "BumpModel", "SteadyStateModel"]

models2, _ = build_scenario(topo, "perf+bump", P, layout)
types2 = [type(m).__name__ for m in models2]
assert types2 == ["ObliviousValiantModel", "BumpModel"]

models1, _ = build_scenario(topo, "perf", P, layout)
types1 = [type(m).__name__ for m in models1]
assert types1 == ["ObliviousValiantModel"]
print("✓ perf / perf+bump / perf+bump+therm 三场景回归不变")
```

---

## 3. 手算 route_dem 约束：Σ_q x_q = B/lr · L_e

MeshTopology(2) 全 terminal（4 node = 4 die，node_die_map 恒等），
所有链路都是 die→die。toy 参数 lr=10 Gbps/lane。

WiringModel.build 写需求等式 `Σ_q x = B/lr · L_e`（V5 §2(2d)
`M_route→D2D x = ℓ_D2D`，ℓ = B·L/lr）。B=100, lr=10 → 系数 = 10：

```python
from problem import Ctx
from problem.models.phys.wiring import build_wiring_grid, populate_paths

# 手动构造与 build_scenario 相同的 link_specs（die→die，不设 c4_pad）
n2d = layout.node_to_die
link_specs = [{"from_die": n2d[u], "to_die": n2d[v]} for (u, v) in topo.links]
lane_rate = np.full(topo.n_links, P.link.lane_rate_gbps)

grid = build_wiring_grid(layout.placements, P.pkg.interposer_w_mm, P.pkg.interposer_h_mm,
                         P.pkg.metal_layers, P.pkg.lanes_per_mm, P.pkg.c4_pitch_mm)
grid = populate_paths(grid, link_specs)

w = WiringModel(grid, link_specs, list(range(topo.n_links)), lane_rate)
ctx = Ctx(); ctx.vector("L", topo.n_links)
w.build(ctx, B=100.0)

# 找 route_dem_l0：x - (B/lr)·L0 == 0
dem = [c for c in ctx.constraints if c.name == "route_dem_l0"][0]
print(f"route_dem_l0: {dem.sense} rhs={dem.rhs}")
for t in dem.terms:
    print(f"   {t.coeff:+.4g}·{t.var}[{t.idx}]")
assert dem.sense == "==" and dem.rhs == 0.0
assert len(dem.terms) == 2  # x_l0_q0 与 L0
x_coeff = sum(t.coeff for t in dem.terms if t.var.startswith("x_"))
l_coeff = sum(t.coeff for t in dem.terms if t.var == "L")
assert abs(x_coeff - 1.0) < 1e-9, "x 系数应为 1"
assert abs(l_coeff + 10.0) < 1e-9, "L 系数应为 -B/lr = -100/10 = -10"
print("✓ route_dem 系数手算一致：x = (B/lr)·L = 10·L")
```

---

## 4. edge/vert 容量约束存在且 rhs 为正

布线约束族：`route_edge_e*`（边容量）、`route_vert_v*`（顶点容量）。
网格边容量 = 间距 × 金属层数 × lanes_per_mm，恒正；顶点容量 = 邻接边 max × 0.8，恒正。

```python
edges = [c for c in ctx.constraints if c.name.startswith("route_edge_")]
verts = [c for c in ctx.constraints if c.name.startswith("route_vert_")]
c4pads = [c for c in ctx.constraints if c.name.startswith("route_c4pad_")]
print(f"route_edge 约束 {len(edges)} 条, route_vert {len(verts)} 条, route_c4pad {len(c4pads)} 条")
assert len(edges) > 0 and len(verts) > 0
assert all(c.sense == "<=" and c.rhs > 0 for c in edges + verts)
assert len(c4pads) == 0, "D2D 布线不设 c4_pad → 不应有 C4 pad 容量约束（C4 属 I2I 范围外）"
print("✓ edge/vert 容量恒正，无 route_c4pad（范围外）")
```

---

## 5. on-die 链路跳过布线

FullMeshTopology(2,1)：router 节点与同 die 的 terminal 之间是 on-die 链路
（from_die == to_die）。on-die 链路 lane_rate=∞、不产生 route_dem 约束。

```python
topo_fm = FullMeshTopology(2, 1)
layout_fm = place(topo_fm, P)
models_fm, _ = build_scenario(topo_fm, "perf+bump+therm+wiring", P, layout_fm)
w_fm = models_fm[-1]
assert isinstance(w_fm, WiringModel)

# 检查 on-die 链路在 link_specs 中 from==to，且 build 后无对应 route_dem
n2d_fm = layout_fm.node_to_die
on_die = [(u, v) for (u, v) in topo_fm.links if n2d_fm[u] == n2d_fm[v]]
print(f"FullMesh(2,1) on-die 链路 {len(on_die)} 条: {on_die}")

ctx_fm = Ctx(); ctx_fm.vector("L", topo_fm.n_links)
w_fm.build(ctx_fm, B=100.0)
dem_names = {c.name for c in ctx_fm.constraints if c.name.startswith("route_dem_")}
# on-die 链路索引不产生 route_dem
for li, (u, v) in enumerate(topo_fm.links):
    if n2d_fm[u] == n2d_fm[v]:
        assert f"route_dem_l{li}" not in dem_names, f"on-die 链路 l{li} 不应有 route_dem"
print(f"✓ on-die 链路无 route_dem（{len(on_die)} 条跳过）")
```

---

## 6. cache_key 可哈希

WiringModel.cache_key 返回可哈希元组（Runner L1/L2 缓存依赖）。

```python
k = w.cache_key()
assert isinstance(k, tuple) and len(k) > 0
assert k == w.cache_key(), "cache_key 必须幂等"
print(f"✓ cache_key = {k[:3]}... 可哈希")
```

---

## 结论

`build_scenario` 的 `+wiring` 档位接入成功：token 解析保持三旧场景逐位不变
（回归锚点），`perf+bump+therm+wiring` 追加 WiringModel；route_dem 需求等式
手算一致（x = (B/lr)·L）；edge/vert 容量恒正；on-die 链路正确跳过；
D2D 布线不设 c4_pad（C4 属 I2I 范围外，无 route_c4pad 约束）。
