"""smoke test —— 在 Mesh(2) 上跑 feasibility query。"""
from _helpers import session
from lp import Ctx, FeasibilityQuery
from topology import Mesh
from physical.bump.bump import UBUMP_45UM

runner, models, cs = session(Mesh(2), UBUMP_45UM)
q = FeasibilityQuery()

for B in [100, 400, 800, 1600, 3200]:
    sol = runner.solve(q.query_id, float(B), Ctx(), models)
    r = q.interpret(sol, Ctx(), float(B))
    status = "✓" if r.feasible else "✗"
    print(f"B={B:>5} Gbps  {status}  L_max={r.worst_load:.1f}")
