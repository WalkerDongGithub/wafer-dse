"""实验辅助——构建 session（拓扑 + 模型 + runner）。"""

import numpy as np
from lp import Ctx, CvxSolver, Runner
from lp import analyze_topo, EnvelopeModel, SConjugacyReps
from lp import BumpModel, NetworkModel, build_thermal_network
from physical.bump.bump import DieBumpBudget


def _default_thermal_network(n_nodes: int, die_to_links: dict, n_links: int):
    """默认热网络——1D 链式 M-矩阵，供 smoke test 用。
    正经使用时替换为 physical/thermal/_solver/_hierarchical.py 的输出。"""
    G = np.eye(n_nodes) * 0.9 - np.eye(n_nodes, k=1) * 0.1 - np.eye(n_nodes, k=-1) * 0.1
    b = np.full(n_nodes, 0.8 * 300.0)
    return build_thermal_network(G, b, 358.15, die_to_links, n_links)


def session(topo, bump_spec, die_w=12.0, die_h=12.0, die_pwr=50.0,
            n_dies=None, thermal=None):
    """构建 (runner, models, topo_structure)。

    thermal: ThermalNetwork | None。None 则用默认（smoke test 用）。
    """
    cs = analyze_topo(topo)
    reps = SConjugacyReps(True).select(cs.n_terminals)
    perf = EnvelopeModel(cs, reps)

    nd = n_dies or len(cs.die_to_links)
    budgets = [DieBumpBudget(f'd{i}', bump_spec, die_w, die_h, die_pwr, 0.8, 0.7)
               for i in range(nd)]
    bump = BumpModel(cs, budgets)

    if thermal is None:
        thermal = _default_thermal_network(nd, cs.die_to_links, cs.n_links)
    therm = NetworkModel(thermal)

    engine = CvxSolver()
    runner = Runner(engine)
    return runner, [perf, bump, therm], cs
