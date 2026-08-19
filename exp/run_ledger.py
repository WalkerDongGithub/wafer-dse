#!/usr/bin/env python3
"""约束账本扫描 —— 沿 B 轴报告每个约束家族的关键值演化.

对每个拓扑: bmax 找 B*，然后在 B*/4, B*/2, 3B*/4, B* 四个点解
min ΣL（真实包络），输出每点账本:
  - 性能: max L
  - μbump: 最紧 die 的占用率
  - 热: 最热 die 的温度与 margin

谁在 B 增长中最先碰壁，一目了然。

用法:
    PYTHONPATH=src python3 exp/run_ledger.py [topo_name ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))
if str(_project_root / "exp") not in sys.path:
    sys.path.insert(0, str(_project_root / "exp"))

from problem import Ctx, CvxSolver, Runner, ResultStore

from problem.queries import BmaxQuery
from physical.config.spec_bump import DieBumpBudget, UBUMP_45UM
from physical.placement import PlacementProblem, solve_grid_placement
from topology import MeshTopology, TorusTopology, KaryNCubeTopology, FullMeshTopology, DragonflyTopology

from diagnostics import (
    full_ledger, print_ledger,
    solve_diagnostic,
)
from run_matrix import TOPOS
from problem.builder import build_scenario
from physical.params import UCIE_32G
from layout import place

T_MAX_K = 358.15


def main():
    names = sys.argv[1:] or list(TOPOS.keys())
    runner = Runner(CvxSolver(),
                    store=ResultStore(Path("exp/output/.cache")), log=False)
    bmax = BmaxQuery()

    for name in names:
        topo = TOPOS[name]
        layout = place(topo, UCIE_32G)
        models, meta = build_scenario(topo, "perf+bump+therm", UCIE_32G, layout)
        r = bmax.solve(runner, lambda b: (Ctx(), models),
                       lo=100, hi=50000, step=200,
                       log_file="exp/output/bmax_ledger.log")
        if r.B_star <= 0:
            print(f"{name}: B* 不存在，跳过")
            continue

        print(f"\n{'='*72}\n{name}  B* = {r.B_star:.0f} Gbps")
        for frac in (0.25, 0.5, 0.75, 1.0):
            B = r.B_star * frac
            diag = solve_diagnostic(models, B)
            ledger = full_ledger(models, diag.L_star, B, T_max=T_MAX_K)
            print_ledger(ledger, B, f"({frac:.0%} of B*)")
            if diag.binding:
                print("  绑定 (按 |dual| 降序):")
                for b in diag.binding:
                    print(f"    {b.name:>22}  [{b.family}]  "
                          f"dual={b.dual:+.3f}  {b.meaning}")


if __name__ == "__main__":
    main()
