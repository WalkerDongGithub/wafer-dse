#!/usr/bin/env python3
"""G3 分离决策基线 vs 联合模型（insight 4，E3B 数据）.

分离基线（DomainExpert 定案形态）: 性能包络先定 L* → 独立判定 bump 电气 /
独立判定热 / 独立判定几何面积 → 取各自可行域的简单交集作为"分离决策"结论。
顺序解多次 LP（BmaxQuery on 单因素模型），非新 query。

联合模型: BmaxQuery on [perf, bump, therm]（单一 LP 联立）。

分歧判据（E3 C3）: 可行判定不同 或 |B*_sep − B*_joint|/B*_joint > 1%。

依据: .dsh/team/artifacts/experiment-design.md §2 E3B
用法: PYTHONPATH=src python3 exp/run_sep_vs_joint.py [params_name]
输出: exp/output/sep_vs_joint_<params>.csv
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from problem import Ctx, CvxSolver, Runner, ResultStore
from problem.builder import build_scenario
from problem.queries import BmaxQuery
from physical.params import UCIE_16G, UCIE_24G, UCIE_32G
from topology import (
    DragonflyTopology, FullMeshTopology, KaryNCubeTopology,
    MeshTopology, TorusTopology,
)
from layout import place

PARAMS = {"ucie-16g": UCIE_16G, "ucie-24g": UCIE_24G, "ucie-32g": UCIE_32G}
TOPOS = {
    "Mesh(2)": MeshTopology(2), "Mesh(3)": MeshTopology(3),
    "Mesh(4)": MeshTopology(4), "Torus(2)": TorusTopology(2),
    "Torus(3)": TorusTopology(3), "KaryNCube(2,2)": KaryNCubeTopology(2, 2),
    "KaryNCube(2,3)": KaryNCubeTopology(2, 3),
    "FullMesh(2)": FullMeshTopology(2, 1), "FullMesh(3)": FullMeshTopology(3, 1),
    "Dragonfly(2,1,1)": DragonflyTopology(2, 1, 1),
    "Dragonfly(2,2,1)": DragonflyTopology(2, 2, 1),
}
LO, HI, STEP = 100.0, 50000.0, 200.0
DIVERGE_RATIO = 0.01  # E3 C3: >1%


def main() -> None:
    params_name = sys.argv[1] if len(sys.argv) > 1 else "ucie-32g"
    P = PARAMS[params_name]
    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)
    bmax = BmaxQuery()
    rows = []

    for name, topo in TOPOS.items():
        layout = place(topo, P)
        models_full, _ = build_scenario(topo, "perf+bump+therm", P, layout)
        models_bump, _ = build_scenario(topo, "perf+bump", P, layout)
        perf, _, therm = models_full          # [perf, bump, therm]
        runner = Runner(CvxSolver(),
                        store=ResultStore(out_dir / ".cache"), log=False)

        B_joint = bmax.solve(runner, lambda b: (Ctx(), models_full),
                             lo=LO, hi=HI, step=STEP).B_star
        B_bump = bmax.solve(runner, lambda b: (Ctx(), models_bump),
                            lo=LO, hi=HI, step=STEP).B_star
        B_therm = bmax.solve(runner, lambda b: (Ctx(), [perf, therm]),
                             lo=LO, hi=HI, step=STEP).B_star
        B_geo = float("inf")                  # α=β=0: 面积不随 B 变，恒可行
        B_sep = min(B_bump, B_therm, B_geo)
        rel = abs(B_sep - B_joint) / B_joint if B_joint > 0 else float("nan")
        divergent = rel > DIVERGE_RATIO
        rows.append({
            "topo": name, "B_joint": f"{B_joint:.0f}",
            "B_bump_sep": f"{B_bump:.0f}", "B_therm_sep": f"{B_therm:.0f}",
            "B_geo_sep": "inf", "B_sep": f"{B_sep:.0f}",
            "rel_diff": f"{rel:.4f}", "divergent(>1%)": divergent,
        })
        print(f"{name:<18} joint={B_joint:>9.0f} sep={B_sep:>9.0f} "
              f"(bump {B_bump:>7.0f} / therm {B_therm:>7.0f}) "
              f"rel={rel:.4f} {'⚠️DIVERGE' if divergent else '一致'}")

    out = out_dir / f"sep_vs_joint_{params_name}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n_div = sum(1 for r in rows if r["divergent(>1%)"])
    print(f"\nCSV → {out}  ({len(rows)} rows, 分歧构型 {n_div})")


if __name__ == "__main__":
    main()
