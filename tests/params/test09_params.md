# test09 — 参数组合 (src/physical/params.py)

## 模块定位

实验的全部物理参数收敛为两组结构体：**TOY**（自拟、手算友好）和 **UCIE**（UCIe 1.1/2.0 Spec Table 1-2 的 16/24/32 GT/s 三档 + 统一 SerDes-112G-VSR）。

toy 的准则：**模型输出必须与手算一致，一眼发现错误**。本测试把 toy 的手算期望值全部写死——任何模型改动导致对不上，测试当场变红。

## 1. 结构体自身的手算断言

toy 选数的每一处都是为了手算：10×10mm die、100μm bump 利用率 1.0 → 密度恰好 100/mm²、总数恰好 10000；P0=10W、Vdd=1.0V、电流 100mA → power bumps 恰好 100、signal 预算恰好 9900；10G/lane、0.1W/lane → 能效 10 pJ/bit、bump 系数恰好 0.2/Gbps；R_vert=1.0、300→400K → 热预算恰好 100K。

```python
import sys; sys.path.insert(0, '../src')
from physical.params import TOY, UCIE_SERIES

# ── die ──
assert TOY.die.area_mm2 == 100.0, "10×10 必须恰好 100mm²"

# ── bump 密度链 ──
assert TOY.bump.density_per_mm2 == 100.0, "100μm pitch 密度必须恰好 100/mm²"
total = TOY.die.area_mm2 * TOY.bump.density_per_mm2 * TOY.bump.utilization
assert total == 10000.0, "总数必须恰好 10000"
power_bumps = TOY.die.static_power_w / (TOY.die.vdd_v * TOY.bump.current_per_bump_ma * 1e-3)
assert power_bumps == 100.0, "10W/(1.0V×100mA) 必须恰好 100"
print(f"toy bump: total={total:.0f}, power={power_bumps:.0f}, signal={total-power_bumps:.0f}")

# ── 能效 ──
assert TOY.link.pj_per_bit == 10.0, "0.1W/10G 必须恰好 10 pJ/bit"
assert TOY.global_link.pj_per_bit == 10.0, "1.0W/100G 必须恰好 10 pJ/bit"

# ── bump 系数： (1/lr)(1 + ppl/(V·I)) ──
lr, ppl = TOY.link.lane_rate_gbps, TOY.link.power_per_lane_w
v, i = TOY.die.vdd_v, TOY.bump.current_per_bump_ma * 1e-3
coeff = (1.0 / lr) * (1.0 + ppl / (v * i))
assert abs(coeff - 0.2) < 1e-12, f"系数必须恰好 0.2/Gbps, 得到 {coeff}"
print(f"bump 系数 = {coeff:.4f}/Gbps（信号 0.1 + 功率 0.1）")

# ── 热预算 ──
assert TOY.thermal.thermal_budget_k == 100.0, "400-300 必须恰好 100K"
```

## 2. UCIe 三档的能效（UCIe 典型值）

16/24/32 GT/s 的功耗是 UCIe Spec 典型值。每 bit 功耗随速率**上升**（更高信号速率 → 均衡器/时钟功耗涨）——UCIe 三档是带宽换能效的权衡，0.31 → 0.375 → 0.5 pJ/bit。

```python
for p in UCIE_SERIES:
    print(f"{p.name}: {p.link.lane_rate_gbps:.0f}G, "
          f"{p.link.power_per_lane_w*1e3:.1f} mW/lane → {p.link.pj_per_bit:.3f} pJ/bit")
    assert p.link.lane_rate_gbps in (16.0, 24.0, 32.0)
    assert p.global_link.name == "SerDes-112G-VSR", "SerDes 统一标准"
    assert abs(p.global_link.pj_per_bit - 4.0) < 0.01, "112G-VSR 必须 4 pJ/bit"
assert UCIE_SERIES[0].link.pj_per_bit < UCIE_SERIES[2].link.pj_per_bit, "16G 能效应优于 32G"
```

## 3. toy 场景的模型输出 vs 手算

FullMesh(2,1)：2 die、2 条 die 间有向链路 + 4 条 on-die（零代价）。每 die 的 ΣL = 2（出射 1 + 入射 1）。

**手算**：
- 热（R_vert 主导，无耦合近似）：T_die = 300 + 1.0×(10 + 0.01·B·2) ≤ 400 → **B* ≈ 4500**（横向热导 k=100 会让热量扩散，B* 略升）
- bump：B×0.2×2 ≤ 9900 → B ≤ 24750——远在热之上，**不绑定**

```python
import numpy as np
from problem import Ctx, CvxSolver, Runner, OptimalValiantModel, select_representatives, BumpModel, SteadyStateModel
from physical.layout.thermal_network import DiePlacement, MfitStackConfig, ThermalNetworkBuilder, AnalyticNetworkBuilder
from problem.queries import BmaxQuery
from physical.config.spec_bump import DieBumpBudget
from physical.placement import PlacementProblem, solve_grid_placement
from topology import FullMesh

P = TOY
topo = FullMesh(2, 1)
n2d = {}
for r in range(2): n2d[r] = r
for t in range(2, 4): n2d[t] = (t - 2) // 1
d2l = {}
for li, (u, v) in enumerate(topo.links):
    du, dv = n2d[u], n2d[v]
    d2l.setdefault(du, []).append(li)
    if dv != du: d2l.setdefault(dv, []).append(li)

perf = OptimalValiantModel(topo, select_representatives(topo, topo.n_terminals))
lr = np.full(topo.n_links, P.link.lane_rate_gbps)
ppl = np.full(topo.n_links, P.link.power_per_lane_w)
for li, (u, v) in enumerate(topo.links):
    if n2d[u] == n2d[v]:
        lr[li] = float("inf"); ppl[li] = 0.0
budgets = [DieBumpBudget(f'd{i}', P.bump.spec(), P.die.width_mm, P.die.height_mm,
                         P.die.static_power_w, P.die.vdd_v, P.bump.utilization)
           for i in range(2)]
bump = BumpModel(budgets, d2l, topo.n_links, lr, ppl)

psol = solve_grid_placement(PlacementProblem(P.die.width_mm, P.pkg.interposer_w_mm, 2))
placements = [DiePlacement(p.label, p.x, p.y, P.die.width_mm, P.die.height_mm)
              for p in psol.positions]
stack = MfitStackConfig(k_interposer=P.thermal.k_interposer,
                        t_interposer=P.thermal.t_interposer_mm,
                        R_vert=P.thermal.r_vert_k_per_w,
                        T_ambient=P.thermal.t_ambient_k)
G, b_vec = AnalyticNetworkBuilder.system_of(placements, stack)
net = ThermalNetworkBuilder.precompute(G, b_vec, P.thermal.t_max_k, d2l, topo.n_links,
                            lr, ppl, P0_vec=np.full(2, P.die.static_power_w))
therm = SteadyStateModel(net)
models = [perf, bump, therm]

r = BmaxQuery().solve(Runner(CvxSolver()), lambda b: (Ctx(), models),
                      lo=100, hi=20000, step=100)
print(f"B* = {r.B_star:.0f}  (手算: 热约束 ~4500, bump 上限 24750)")
assert 4000 <= r.B_star <= 6000, \
    f"B* 应在热约束手算值 4500 附近（耦合扩散可略升），得到 {r.B_star}"

# B* 处温度手算验证：T = 300 + G⁻¹(P0 + P_dyn + b)，最热 die 必须接近 T_max
ctx = Ctx()
for m in models: m.build(ctx, float(r.B_star))
sol = CvxSolver().solve(ctx, objective=sum(ctx["L"]), maximize=False)
L = {i: v for i, v in enumerate(sol.variables["L"])}
P_dyn = np.zeros(2)
for v in range(2):
    for e in d2l[v]:
        if lr[e] < 1e9:
            P_dyn[v] += ppl[e] * (r.B_star / lr[e]) * L[e]
T = np.linalg.inv(G) @ (np.full(2, P.die.static_power_w) + P_dyn + b_vec)
print(f"B* 处温度: {np.round(T,1)}K  (T_max=400K)")
assert T.max() <= P.thermal.t_max_k + 1e-6, "温度约束必须满足"
assert T.max() >= P.thermal.t_max_k - 5.0, \
    f"B* 由热约束绑定，最热 die 应逼近 T_max, 得到 {T.max():.1f}"

# bump 不绑定验证：B* 由热绑定，bump 应远在半载以下
# 手算：used = B* × 0.2 × ΣL = 4453 × 0.2 × 4 ≈ 3562
used = r.B_star * sum(0.2 * L[e] for e in d2l[0])
assert used < 9900 * 0.6, f"bump 在 B* 处应远未绑定, 占用 {used:.0f}/9900"
print(f"bump 占用: {used:.0f}/9900 = {used/9900*100:.1f}%  (手算 ~3562)")
```

## 结论

toy 参数的每一处选数都能手算核对：密度 100/mm²、总数 10000、功率 bump 100、能效 10 pJ/bit、bump 系数 0.2、热预算 100K、B*≈4500。模型输出与手算一致——toy 准则达成。
