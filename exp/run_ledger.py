#!/usr/bin/env python3
"""约束账本扫描 —— 沿 B 轴报告每个约束家族的关键值演化.

对每个拓扑: bmax 找 B*，然后在 B*/4, B*/2, 3B*/4, B* 四个点解
min ΣL（真实包络），输出每点账本:
  - 性能: max L
  - μbump: 最紧 die 的占用率
  - 热: 最热 die 的温度与 margin

谁在 B 增长中最先碰壁，一目了然。

用法:
    PYTHONPATH=src python3 exp/run_ledger.py [--params ucie-32g] [topo_name ...]
    --params 可选（默认 ucie-32g）；拓扑名缺省 = 全部 11 种。
输出: 控制台 + exp/output/ledger_<topo>.csv
"""

from __future__ import annotations

import csv
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
from physical.params import UCIE_16G, UCIE_24G, UCIE_32G
from layout import place

PARAMS = {"ucie-16g": UCIE_16G, "ucie-24g": UCIE_24G, "ucie-32g": UCIE_32G}

T_MAX_K = 358.15


def main():
    argv = list(sys.argv[1:])
    params_name = "ucie-32g"
    if "--params" in argv:
        i = argv.index("--params")
        params_name = argv[i + 1]
        del argv[i:i + 2]
    P = PARAMS[params_name]
    names = argv or list(TOPOS.keys())
    runner = Runner(CvxSolver(),
                    store=ResultStore(Path("exp/output/.cache")), log=False)
    bmax = BmaxQuery()
    out_dir = Path("exp/output")
    out_dir.mkdir(exist_ok=True)

    for name in names:
        topo = TOPOS[name]
        layout = place(topo, P)
        models, meta = build_scenario(topo, "perf+bump+therm", P, layout)
        r = bmax.solve(runner, lambda b: (Ctx(), models),
                       lo=100, hi=50000, step=200,
                       log_file=str(out_dir / "bmax_ledger.log"))
        if r.B_star <= 0:
            print(f"{name}: B* 不存在，跳过")
            continue

        print(f"\n{'='*72}\n{name}  B* = {r.B_star:.0f} Gbps")
        rows = []
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

            # CSV 行（E3A 账本产物）
            perf = ledger.get("perf") or {}
            bump = ledger.get("bump") or []
            therm = ledger.get("therm") or []
            worst_bump = max(bump, key=lambda r: r["util"]) if bump else {}
            worst_therm = min(therm, key=lambda r: r["margin"]) if therm else {}
            fam: dict[str, int] = {}
            for b in diag.binding:
                fam[b.family] = fam.get(b.family, 0) + 1
            rows.append({
                "topo": name, "frac_of_Bstar": f"{frac:.2f}", "B_gbps": f"{B:.0f}",
                "perf_max_L": f"{perf.get('max_L', float('nan')):.4f}",
                "bump_worst_die": worst_bump.get("die", ""),
                "bump_util": f"{worst_bump.get('util', float('nan')):.4f}",
                "therm_worst_die": worst_therm.get("die", ""),
                "therm_T_K": f"{worst_therm.get('T', float('nan')):.2f}",
                "therm_margin_K": f"{worst_therm.get('margin', float('nan')):+.2f}",
                "binding_families": ";".join(f"{k}:{v}" for k, v in sorted(fam.items())) or "-",
            })
        path = out_dir / f"ledger_{params_name}_{name}.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"\nCSV → {path}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
