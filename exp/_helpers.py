"""实验辅助——构建 session（拓扑 + 模型 + runner）。"""

import numpy as np
from problem import Ctx, CvxSolver, Runner
from problem import EnvelopeModel, select_representatives
from problem import BumpModel, SteadyStateModel, ThermalNetworkBuilder
from physical.config.spec_bump import DieBumpBudget


def _default_thermal_network(n_nodes: int, die_to_links: dict, n_links: int):
    """默认热网络——1D 链式 M-矩阵，供 smoke test 用。
    正经使用时替换为 physical/thermal/_solver/_hierarchical.py 的输出。"""
    G = np.eye(n_nodes) * 0.9 - np.eye(n_nodes, k=1) * 0.1 - np.eye(n_nodes, k=-1) * 0.1
    b = np.full(n_nodes, 0.8 * 300.0)
    return ThermalNetworkBuilder.precompute(G, b, 358.15, die_to_links, n_links)


def _identity_die_to_links(topo) -> dict[int, list[int]]:
    """die == node 恒等映射——每个节点是自己的 die。

    正经使用时替换为 placement 层输出的 node→die 映射。
    """
    d2l: dict[int, list[int]] = {}
    for li, (u, v) in enumerate(topo.links):
        d2l.setdefault(u, []).append(li)
        if v != u:
            d2l.setdefault(v, []).append(li)
    return {k: sorted(v) for k, v in d2l.items()}


def session(topo, bump_spec, die_w=12.0, die_h=12.0, die_pwr=50.0,
            n_dies=None, thermal=None):
    """构建 (runner, models, topo)。

    thermal: ThermalNetwork | None。None 则用默认（smoke test 用）。
    """
    reps = select_representatives(topo, topo.n_terminals)
    perf = EnvelopeModel(topo, reps)

    d2l = _identity_die_to_links(topo)
    nd = n_dies or len(d2l)
    budgets = [DieBumpBudget(f'd{i}', bump_spec, die_w, die_h, die_pwr, 0.8, 0.7)
               for i in range(nd)]
    bump = BumpModel(budgets, d2l, topo.n_links)

    if thermal is None:
        thermal = _default_thermal_network(nd, d2l, topo.n_links)
    therm = SteadyStateModel(thermal)

    engine = CvxSolver()
    runner = Runner(engine)
    return runner, [perf, bump, therm], topo
