"""smoke test —— 在 Mesh(2) 上找 B*。"""
from _helpers import session
from lp import Ctx, BmaxQuery
from topology import Mesh
from physical.bump.bump import UBUMP_45UM

runner, models, _ = session(Mesh(2), UBUMP_45UM)
q = BmaxQuery()

r = q.solve(runner, lambda b: (Ctx(), models), lo=100, hi=50000, step=200)
print(f"\nB* = {r.B_star:.0f} Gbps  ({r.iterations} LP solves)")
