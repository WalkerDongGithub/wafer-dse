"""查询——FeasibilityQuery 和 BmaxQuery。"""
import numpy as np
from lp.ctx import Ctx
from lp.engine import CvxSolver, Runner
from lp.queries.feasibility import FeasibilityQuery
from lp.queries.bmax import BmaxQuery
from lp.models.topo import analyze as analyze_topo
from lp.models.perf.traffic_based import EnvelopeModel, SConjugacyReps
from lp.models.phys.bumps import BumpModel
from lp.models.phys.therm import NetworkModel, build_thermal_network
from topology import Mesh
from physical.bump.bump import DieBumpBudget, UBUMP_45UM


def _build_models():
    cs = analyze_topo(Mesh(2))
    perf = EnvelopeModel(cs, SConjugacyReps(True).select(4))
    budgets = [DieBumpBudget(f'd{i}', UBUMP_45UM, 12, 12, 50, 0.8, 0.7) for i in range(4)]
    bump = BumpModel(cs, budgets)
    G = np.eye(4) * 0.9 - np.eye(4, k=1) * 0.1 - np.eye(4, k=-1) * 0.1
    net = build_thermal_network(G, np.full(4, 240.0), 358.15, cs.die_to_links, cs.n_links)
    therm = NetworkModel(net)
    return [perf, bump, therm]


def test_feasibility_query():
    """FeasibilityQuery——B=800 应可行。"""
    engine = CvxSolver()
    runner = Runner(engine, log=False)
    q = FeasibilityQuery()
    models = _build_models()

    sol = runner.solve(q.query_id, 800.0, Ctx(), models)
    r = q.interpret(sol, Ctx(), 800.0)
    assert r.feasible
    assert r.B == 800.0
    assert len(r.envelope_L) > 0


def test_bmax_query():
    """BmaxQuery——二分搜索找到 B* > 0。"""
    engine = CvxSolver()
    runner = Runner(engine, log=False)
    q = BmaxQuery()
    models = _build_models()

    r = q.solve(runner, lambda b: (Ctx(), models), lo=100, hi=50000, step=200)
    assert r.B_star > 0


print("test_queries: 2/2 PASSED")
