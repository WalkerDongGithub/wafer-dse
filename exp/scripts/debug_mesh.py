"""最小可验算实验 — 2×2 mesh, 所有参数显式, 所有中间量打印.

用法: PYTHONPATH=src python3 exp/scripts/debug_mesh.py
"""

import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_project_root / "src"))

import numpy as np
from lp import Ctx, CvxSolver, AnalyticNetworkBuilder, ThermalNetworkBuilder
from lp import EnvelopeModel, select_representatives
from lp import BumpModel, SteadyStateModel
from lp import DiePlacement, MfitStackConfig
from physical.bump.bump import BumpSpec, DieBumpBudget
from physical.placement import PlacementProblem, solve_grid_placement
from topology import Mesh

# ═══════════════════════════════════════════════════
# 参数 — 全部在这里改
# ═══════════════════════════════════════════════════

# 拓扑
MESH_SIZE = 2          # 2×2 mesh → 4 terminals, 2 dies (每行一个 die)

# die
DIE_W = 10.0           # mm
DIE_H = 10.0           # mm
DIE_P0 = 50.0          # W 峰值功耗 (交换 die 满载)

# μbump
UBUMP_PITCH = 45       # μm
UBUMP_I     = 75       # mA
UBUMP_ETA   = 0.7
VDD         = 1.0      # V

# UCIe
UCIE_BW  = 10.0        # Gbps/lane
UCIE_PPL = 0.01        # W/lane

# 热
R_VERT    = 0.5        # K/W  (液冷)
T_AMBIENT = 300.0      # K
T_MAX     = 400.0      # K
K_INTERP  = 100.0      # W/(m·K)
T_INTERP  = 0.1        # mm

# 求解
B_TEST = 1000.0        # Gbps — 固定 B 验证可行性

# ═══════════════════════════════════════════════════

print("=" * 60)
print("  2×2 Mesh 最小可验算实验")
print("=" * 60)

# 1. 拓扑
topo = Mesh(MESH_SIZE)
# 1b. 布局 — placement solver 决定网格
d = max(DIE_W, DIE_H)
psol = solve_grid_placement(PlacementProblem(
    die_side_mm=d, interposer_side_mm=2*d, die_count=4))
placements = [DiePlacement(f"d{i}", p.x, p.y, d, d)
              for i, p in enumerate(psol.positions)]
print(f"\n布局: {psol.grid_n}×{psol.grid_n} grid, {len(placements)} dies")
for p in psol.positions:
    print(f"  {p.label} @ [{p.row},{p.col}] ({p.x:.0f},{p.y:.0f})")

# 1c. node→die (每个 terminal 自己一个 die)
n2d = {i: i for i in range(4)}
d2l: dict[int, list[int]] = {}
for li, (u, v) in enumerate(topo.links):
    d2l.setdefault(n2d[u], []).append(li)
    if n2d[v] != n2d[u]:
        d2l.setdefault(n2d[v], []).append(li)
d2l = {k: sorted(v) for k, v in d2l.items()}
print(f"\n拓扑: {topo.n_terminals} terminals, {topo.n_links} links, {len(set(n2d.values()))} dies")

# 2b. 每条链路的互联标准 — 由 die 间距离决定
UCIE_MAX = 25.0  # mm, UCIe Standard Package 最大可达距离
print(f"\n── 链路互联标准 (UCIe_max={UCIE_MAX:.0f}mm) ──")
print(f"  links (前 8 条):")
n_links = topo.n_links
for li in range(min(n_links, 8)):
    u, v = topo.links[li]
    du, dv = n2d[u], n2d[v]
    if du == dv:
        dist = 0.0
        ltype = "on-die (free)"
    else:
        pu, pv = placements[du], placements[dv]
        dist = abs(pu.x + pu.w/2 - pv.x - pv.w/2) + abs(pu.y + pu.h/2 - pv.y - pv.h/2)
        ltype = "UCIe" if dist <= UCIE_MAX else "SerDes"
    print(f"    link[{li}]: node{u}→node{v}  (die{du}→die{dv})  dist={dist:.0f}mm  {ltype}")

# 3. G, b — 推导过程
print(f"\n── G 矩阵推导 ──")
print(f"  R_vert={R_VERT} → G_vert = 1/{R_VERT} = {1/R_VERT:.1f}")
print(f"  k={K_INTERP}, t={T_INTERP}")

stack = MfitStackConfig(R_vert=R_VERT, T_ambient=T_AMBIENT,
                        k_interposer=K_INTERP, t_interposer=T_INTERP)
G, b_vec = AnalyticNetworkBuilder.system_of(placements, stack)

print(f"\n  邻接判定 (d={d}mm):")
for i in range(len(placements)):
    for j in range(i+1, len(placements)):
        pi, pj = placements[i], placements[j]
        ox = max(0, min(pi.x+pi.w, pj.x+pj.w) - max(pi.x, pj.x))
        oy = max(0, min(pi.y+pi.h, pj.y+pj.h) - max(pi.y, pj.y))
        gap_x = min(abs(pj.x-(pi.x+pi.w)), abs(pi.x-(pj.x+pj.w)))
        gap_y = min(abs(pj.y-(pi.y+pi.h)), abs(pi.y-(pj.y+pj.h)))
        if ox > 1e-6 and gap_y < 5:
            g = 2*K_INTERP*T_INTERP*ox/(pi.h+pj.h+gap_y)
            print(f"  d{i}-d{j}: y-adjacent, ox={ox:.0f}, gap_y={gap_y:.1f} → G={g:.1f}")
        elif oy > 1e-6 and gap_x < 5:
            g = 2*K_INTERP*T_INTERP*oy/(pi.w+pj.w+gap_x)
            print(f"  d{i}-d{j}: x-adjacent, oy={oy:.0f}, gap_x={gap_x:.1f} → G={g:.1f}")
        else:
            print(f"  d{i}-d{j}: no adjacency")

print(f"\n  组装: G[i,i] = G_vert + Σ|G[i,j]|")
print(f"  G_vert = {1/R_VERT:.1f}")
for i in range(len(placements)):
    off_sum = sum(abs(G[i,j]) for j in range(len(placements)) if j != i)
    print(f"  G[{i},{i}] = {1/R_VERT:.1f} + {off_sum:.1f} = {G[i,i]:.1f}")

print(f"\nG =\n{G}")
print(f"b = {b_vec}   (G_vert × T_amb = {1/R_VERT:.1f} × {T_AMBIENT})")

# 峰值功耗 → 温度贡献
G_inv = np.linalg.inv(G)
P0_vec = np.full(len(placements), DIE_P0)
T_from_P0 = G_inv @ (P0_vec + b_vec)
print(f"\n── 峰值功耗 → 温度 ──")
print(f"  P_peak = {DIE_P0}W/die × {len(placements)} dies = {DIE_P0*len(placements)}W total")
print(f"  T(P0) = G⁻¹(P0+b) = {T_from_P0}")
print(f"  ΔT_peak = {T_from_P0[0] - T_AMBIENT:.1f}K  (峰值功耗带来的温升)")
print(f"  rhs = T_max - T(P0) = {T_MAX - T_from_P0[0]:.1f}K  (动态功耗可用温升预算)")

# 4. 排列代表元
reps = select_representatives(topo, topo.n_terminals)
print(f"\n排列代表元: {len(reps)}")
for r in reps:
    print(f"  {r.label}: sigma={r.sigma}")

# 5. 性能模型 + mini-sum-L 目标
perf = EnvelopeModel(topo, reps)
ctx_perf = Ctx()
perf.build(ctx_perf, B_TEST)
engine = CvxSolver()
sol_perf = engine.solve(ctx_perf, objective=sum(ctx_perf["L"]), maximize=False)
L_vals = sol_perf.variables["L"]
print(f"\n性能模型 (min ΣL): L = {[f'{v:.3f}' for v in L_vals]}")
print(f"  max L = {max(L_vals):.3f}")

# 6. bump 模型
n_dies = len(placements)
spec = BumpSpec("μbump-45μm", UBUMP_PITCH, UBUMP_I)
budgets = [
    DieBumpBudget(f"d{i}", spec, DIE_W, DIE_H, DIE_P0, VDD, UBUMP_ETA)
    for i in range(n_dies)
]
for bi, bgt in enumerate(budgets[:2]):
    print(f"die{bi} bump: total={bgt.total_bumps}, power={bgt.power_bumps}, signal={bgt.available}")
print(f"  ... ({n_dies} dies total)")

n_links = topo.n_links
lane_rate = np.full(n_links, UCIE_BW)
ppl       = np.full(n_links, UCIE_PPL)
bump = BumpModel(budgets, d2l, n_links, lane_rate, ppl)

# 7. 热模型
P0_vec = np.full(n_dies, DIE_P0)
net = ThermalNetworkBuilder.precompute(G, b_vec, T_MAX, d2l, n_links,
                            lane_rate, ppl, P0_vec=P0_vec)
print(f"\n热网络:")
print(f"  link_coeff =\n{net.link_coeff}")
print(f"  rhs_ambient = {net.rhs_ambient}")
print(f"  手工验算: G⁻¹(P0+b) = {np.linalg.inv(G) @ (P0_vec + b_vec)}")
print(f"  rhs = T_max - G⁻¹(P0+b) = {T_MAX - np.linalg.inv(G) @ (P0_vec + b_vec)}")
therm = SteadyStateModel(net)

# 8. 完整 LP
ctx = Ctx()
perf.build(ctx, B_TEST)
bump.build(ctx, B_TEST)
therm.build(ctx, B_TEST)
sol = engine.solve(ctx, objective=sum(ctx["L"]), maximize=False)
print(f"\n完整 LP (perf+bump+therm): status={sol.status}")
if sol.variables:
    L_final = sol.variables["L"]
    print(f"  L = {[f'{v:.3f}' for v in L_final]}")
    # 功耗
    ell = B_TEST * np.array(L_final) / UCIE_BW
    P = P0_vec.copy()
    for v in range(n_dies):
        for e in d2l.get(v, []):
            P[v] += UCIE_PPL * ell[e]
    T = np.linalg.solve(G, P + b_vec)
    print(f"  ℓ   = {[f'{v:.1f}' for v in ell]}")
    print(f"  P   = {[f'{v:.1f}' for v in P]} W")
    print(f"  T   = {[f'{v:.1f}' for v in T]} K")
    print(f"  T_max margin = {[f'{T_MAX - t:.1f}' for t in T]} K")

    # 显示绑定约束
    if sol.duals:
        binding = [k for k, v in sol.duals.items() if abs(v) > 1e-6]
        print(f"\n  绑定约束 ({len(binding)}):")
        for b in binding[:10]:
            print(f"    {b}: dual={sol.duals[b]:.4f}")

# 9. B* 搜索
print(f"\n{'='*60}")
print("  B* 二分搜索")
print(f"{'='*60}")

def feasible(b):
    c = Ctx()
    for m in [perf, bump, therm]:
        m.build(c, float(b))
    return engine.solve(c, objective=sum(c["L"]), maximize=False).status in ("optimal", "optimal_inaccurate")

lo, hi = 100.0, 50000.0
if not feasible(lo):
    print(f"  B={lo:.0f} infeasible!")
else:
    while feasible(hi):
        lo, hi = hi, hi * 2
    iters = 0
    while hi - lo > 100:
        mid = (lo + hi) / 2
        iters += 1
        ok = feasible(mid)
        if ok: lo = mid
        else: hi = mid
    print(f"  B* = {lo:.0f} Gbps  ({iters} LP solves)")

    # B* 处详细诊断
    ctx_b = Ctx()
    for m in [perf, bump, therm]:
        m.build(ctx_b, lo)
    sol_b = engine.solve(ctx_b, objective=sum(ctx_b["L"]), maximize=False)
    Lb = sol_b.variables["L"]
    ell_b = lo * np.array(Lb) / UCIE_BW
    P_b = P0_vec.copy()
    for v in range(n_dies):
        for e in d2l.get(v, []):
            P_b[v] += UCIE_PPL * ell_b[e]
    T_b = np.linalg.solve(G, P_b + b_vec)
    print(f"  @B*: L={[f'{v:.3f}' for v in Lb]}")
    print(f"       ℓ={[f'{v:.1f}' for v in ell_b]}")
    print(f"       P={[f'{v:.1f}' for v in P_b]} W")
    print(f"       T={[f'{v:.1f}' for v in T_b]} K")
