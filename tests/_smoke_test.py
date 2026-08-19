"""Smoke test — verify core DSE pipeline works before full-scale run."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from topology import MeshTopology, TorusTopology, FullMeshTopology, DragonflyTopology
from physical.params import load_yaml_params
from layout import place
from problem.builder import build_scenario
from problem.engine import CvxSolver, Runner, ResultStore
from problem.queries import BmaxQuery
from problem.ctx import Ctx

params = load_yaml_params("config/params")
P = params["ucie-12g"]
topo = MeshTopology(2)
layout = place(topo, P)
models, meta = build_scenario(topo, "perf", P, layout)
print(f"Models: {len(models)}, n_dies={meta['n_dies']}")

store_dir = Path("exp/output/.cache")
store_dir.mkdir(parents=True, exist_ok=True)
runner = Runner(CvxSolver(), store=ResultStore(store_dir), log=True)

r = BmaxQuery().solve(runner, lambda b: (Ctx(), models),
                      lo=100.0, hi=2000.0, step=50.0)
print(f"B* = {r.B_star}, iterations = {r.iterations}")

# Cache hit test
runner2 = Runner(CvxSolver(), store=ResultStore(store_dir), log=True)
r2 = BmaxQuery().solve(runner2, lambda b: (Ctx(), models),
                       lo=100.0, hi=2000.0, step=50.0)
print(f"Cache test: B* = {r2.B_star}, hits = {runner2.hits}")
print("SMOKE TEST PASSED")
