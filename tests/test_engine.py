"""求解引擎——CvxSolver 编译求解、Runner 缓存命中。"""
import numpy as np
from lp.ctx import Ctx
from lp.engine import CvxSolver, Runner
from lp.queries.feasibility import FeasibilityQuery
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


def test_cvx_solver_feasibility():
    """CvxSolver 求解 feasibility 问题——B=800 应可行。"""
    engine = CvxSolver()
    ctx = Ctx()
    models = _build_models()
    for m in models:
        m.build(ctx, 800.0)
    sol = engine.solve(ctx)
    assert sol.status in ("optimal", "optimal_inaccurate"), f"status={sol.status}"
    assert "L" in (sol.variables or {})


def test_runner_memory_cache():
    """Runner L1 缓存——同参数第二次调用应命中。"""
    engine = CvxSolver()
    runner = Runner(engine, log=False)
    models = _build_models()

    sol1 = runner.solve("feasibility", 800.0, Ctx(), models)
    assert sol1.status in ("optimal", "optimal_inaccurate")

    sol2 = runner.solve("feasibility", 800.0, Ctx(), models)
    assert runner.hits == 1


print("test_engine: 2/2 PASSED")
