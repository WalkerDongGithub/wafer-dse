#!/usr/bin/env python3
"""E6 规模 vs 求解时间扫描（insight 7，§5.6 数据）.

对 Mesh(n) / Torus(n)，n = 2..6，跑完整 BmaxQuery（固定 lo/hi/step），
记录规模（n、n_terminals、n_links、n_dies）、二分迭代数、总时间、单次 LP 均时。

依据: .dsh/team/artifacts/experiment-design.md §2 E6
用法: PYTHONPATH=src python3 exp/run_scalability.py [params_name]
输出: exp/output/scalability_<params>.csv
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from problem import Ctx, CvxSolver, Runner, ResultStore
from problem.builder import build_scenario
from problem.queries import BmaxQuery
from physical.params import UCIE_16G, UCIE_24G, UCIE_32G
from topology import MeshTopology, TorusTopology
from layout import place

PARAMS = {"ucie-16g": UCIE_16G, "ucie-24g": UCIE_24G, "ucie-32g": UCIE_32G}
LO, HI, STEP = 100.0, 50000.0, 200.0


def main() -> None:
    params_name = sys.argv[1] if len(sys.argv) > 1 else "ucie-32g"
    P = PARAMS[params_name]
    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)

    rows = []
    for family, factory in [("Mesh", MeshTopology), ("Torus", TorusTopology)]:
        for n in range(2, 7):
            topo = factory(n)
            layout = place(topo, P)
            models, meta = build_scenario(topo, "perf+bump+therm", P, layout)
            runner = Runner(CvxSolver(),
                            store=ResultStore(out_dir / ".cache"), log=False)
            t0 = time.perf_counter()
            r = BmaxQuery().solve(runner, lambda b: (Ctx(), models),
                                  lo=LO, hi=HI, step=STEP)
            total = time.perf_counter() - t0
            rows.append({
                "family": family, "n": n,
                "n_terminals": topo.n_terminals, "n_links": topo.n_links,
                "n_dies": meta["n_dies"],
                "B_star": f"{r.B_star:.1f}", "iterations": r.iterations,
                "total_time_s": f"{total:.3f}",
                "per_lp_avg_s": f"{total / max(r.iterations, 1):.4f}",
            })
            print(f"{family}({n}): B*={r.B_star:.0f} iters={r.iterations} "
                  f"total={total:.2f}s dies={meta['n_dies']}")

    out = out_dir / f"scalability_{params_name}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV → {out}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
