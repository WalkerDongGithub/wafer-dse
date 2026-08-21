#!/usr/bin/env python3
"""EC 内部良心检查：die 缩放（α_d, β_P ≠ 0）下可行性对 B 的单调性.

二分搜索（BmaxQuery）前提 = "可行性对 B 单调"；默认 α_d=β_P=0 时严格成立
（低 B 面积约束为松上界）。本脚本在 (α_d, β_P) 网格上沿 B 轴调 FeasibilityQuery，
检测"false → true 反转"。结果只进内部报告给 master，不上论文台面。

依据: .dsh/team/artifacts/experiment-design.md §2 EC；V5 §5.3/§9 待定案
用法: PYTHONPATH=src python3 exp/run_monotonicity.py
输出: exp/output/monotonicity_scan.csv（内部）
"""
from __future__ import annotations

import csv
import dataclasses
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from problem import Ctx, CvxSolver, Runner, ResultStore, FeasibilityQuery
from problem.builder import build_scenario
from physical.params import UCIE_32G
from topology import MeshTopology
from layout import place

ALPHA_GRID = [0.0, 0.01, 0.1]     # mm/Gbps
BETA_GRID = [0.0, 0.05, 0.2]      # W/Gbps
TOPOS = {"Mesh(2)": MeshTopology(2), "Mesh(3)": MeshTopology(3)}
B_GRID = [10, 50, 100, 200, 500, 1000, 2000, 3000, 4000, 5000,
          6000, 8000, 10000, 12000, 15000, 20000, 30000, 50000]


def main() -> None:
    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)
    rows: list[dict] = []

    for tname, topo in TOPOS.items():
        layout = place(topo, UCIE_32G)  # 布局基于基准 die（缩放只在模型内生效）
        for ad in ALPHA_GRID:
            for bp in BETA_GRID:
                P = dataclasses.replace(
                    UCIE_32G,
                    die=dataclasses.replace(UCIE_32G.die, alpha_d=ad, beta_p=bp))
                models, _ = build_scenario(topo, "perf+bump+therm", P, layout)
                runner = Runner(CvxSolver(),
                                store=ResultStore(out_dir / ".cache"), log=False)
                q = FeasibilityQuery()
                feas: list[tuple[float, bool]] = []
                for B in B_GRID:
                    sol = runner.solve(q.query_id, float(B), Ctx(), models)
                    r = q.interpret(sol, Ctx(), float(B))
                    feas.append((B, r.feasible))

                # 单调性检查：升序扫描，找 false→true 反转
                inversions: list[str] = []
                last_false_at: float | None = None
                for B, ok in feas:
                    if not ok:
                        last_false_at = B
                    elif last_false_at is not None:
                        inversions.append(f"false@{last_false_at:.0f}->true@{B:.0f}")
                        last_false_at = None  # 每对只记一次，避免级联
                low_feasible = feas[0][1]  # B=10 是否可行（V3）
                rows.append({
                    "topo": tname, "alpha_d": ad, "beta_p": bp,
                    "low_B_feasible": low_feasible,
                    "n_inversions": len(inversions),
                    "inversions": ";".join(inversions) or "-",
                    "verdict": "MONOTONE" if not inversions else "INVERSION",
                })
                print(f"{tname} α={ad} β={bp}: low_B={low_feasible} "
                      f"inversions={len(inversions)} {inversions[:2]}")

    out = out_dir / "monotonicity_scan.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV → {out}  ({len(rows)} rows, 内部数据不上论文台面)")


if __name__ == "__main__":
    main()
