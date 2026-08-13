"""布局设计（更高层）—— 拓扑分片 + die 摆放.

布局是设计决策，在 exp 层做出，然后作为输入传给 lp.builder。
lp 层不碰 placement 求解器。
"""

from __future__ import annotations

from lp.builder import Layout
from lp import DiePlacement
from physical.params import ExpParams
from physical.placement import PlacementProblem, solve_grid_placement
from topology import FullMesh, Dragonfly


def node_die_map(topo) -> dict[int, int]:
    """拓扑节点 → die 的分片映射.

    Mesh/Torus/KaryNCube 全 terminal：1 node = 1 die。
    FullMesh / Dragonfly：按 router 分 die（每个 die 放 1 router + p terminals）。
    """
    if isinstance(topo, FullMesh):
        a, p = topo.a, topo.p
        m = {r: r for r in range(a)}
        m.update({t: (t - a) // p for t in range(a, a + a * p)})
        return m
    if isinstance(topo, Dragonfly):
        a, p, h = topo.a, topo.p, topo.h
        m = {}
        for gi in range(topo.g):
            for ri in range(a):
                for t in range(p + 1):
                    m[t + ri * (p + 1) + gi * a * (p + 1)] = gi * a + ri
        return m
    return {i: i for i in range(topo.node_num())}


def place(topo, P: ExpParams) -> Layout:
    """布局设计入口：分片 + 网格摆放 → Layout.

    当前用 GridFillSolver（逐行填充，feasible-only）。
    将来拓扑感知求解器替换这里，lp builder 不用改。
    """
    n2d = node_die_map(topo)
    n_dies = len(set(n2d.values()))

    sol = solve_grid_placement(PlacementProblem(
        die_side_mm=P.die.width_mm,
        interposer_side_mm=P.pkg.interposer_w_mm,
        die_count=n_dies))
    placements = tuple(
        DiePlacement(p.label, p.x, p.y, P.die.width_mm, P.die.height_mm)
        for p in sol.positions)
    return Layout(placements=placements, node_to_die=n2d)
