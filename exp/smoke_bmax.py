"""smoke test —— 在 MeshTopology(2) 上找 B*。"""
from _helpers import session
from problem import Ctx, BmaxQuery
from topology import MeshTopology
from physical.config.spec_bump import UBUMP_45UM

runner, models, _ = session(MeshTopology(2), UBUMP_45UM)
q = BmaxQuery()

r = q.solve(runner, lambda b: (Ctx(), models), lo=100, hi=50000, step=200)
print(f"\nB* = {r.B_star:.0f} Gbps  ({r.iterations} LP solves)")
