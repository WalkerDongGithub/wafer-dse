#!/usr/bin/env python3
"""E2 双旋钮灵敏度：B = f(要求 R, 约束 C)（insight 3，§5.5 图 6 数据）.

4 档（V5 v5.22 / experiment-design §2 E2 定稿字符串）:
  ref                  = perf+bump+therm                 （R_qos × C_peak，参考档）
  +rated               = perf+bump+therm+rated            （C 放宽：β_P:=0）
  +egress_peak         = perf+bump+therm+egress_peak      （R 放宽：单对流量包络）
  +egress_peak+rated   = perf+bump+therm+egress_peak+rated（双放宽）

两种 β_P 模式:
  default: β_P = P.die.beta_p（默认 0 → C 旋钮退化，如实报告）
  beta_p=0.05: dataclasses.replace 程序化覆盖（未动 YAML）→ C 旋钮有区分度

判定（§2 E2）: M1 单调（R_qos ≤ R_peak；C_peak ≤ C_rated，逐构型）、
              M2 可测效果（≥1 方向上推比 >1.05）、M3 无交叉（严格度偏序无矛盾）。
归一化: B*_档 / B*_参考档，跨拓扑几何均值（§3 评测规范）。

用法: PYTHONPATH=src python3 exp/run_knob.py [params_name] [topo ...]
输出: exp/output/knob_matrix_<params>.csv
"""
from __future__ import annotations

import csv
import dataclasses
import math
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
from topology import (
    DragonflyTopology, FullMeshTopology, KaryNCubeTopology,
    MeshTopology, TorusTopology,
)
from layout import place

PARAMS = {"ucie-16g": UCIE_16G, "ucie-24g": UCIE_24G, "ucie-32g": UCIE_32G}
TOPOS = {
    "FullMesh(2)": FullMeshTopology(2, 1),   # 2 口
    "Mesh(2)": MeshTopology(2),              # 4 口（Torus(2)/KaryNCube(2,2) 同构取一）
    "KaryNCube(2,3)": KaryNCubeTopology(2, 3),  # 8 口
    "Mesh(3)": MeshTopology(3),              # 9 口
    "Torus(3)": TorusTopology(3),            # 9 口（非同构第二代表）
    "Dragonfly(2,1,1)": DragonflyTopology(2, 1, 1),  # 6 口
    "Dragonfly(2,2,1)": DragonflyTopology(2, 2, 1),  # 12 口
    # Mesh(4)〔16 口〕可选（重拓扑控时长，默认不开）
}
SCENARIOS = [
    ("ref", "perf+bump+therm"),
    ("rated", "perf+bump+therm+rated"),
    ("egress_peak", "perf+bump+therm+egress_peak"),
    ("egress_peak_rated", "perf+bump+therm+egress_peak+rated"),
]
BETA_MODES = [("default", None), ("beta_p0.05", 0.05)]  # (label, beta_p 覆盖)
LO, HI, STEP = 100.0, 50000.0, 200.0


def main() -> None:
    argv = list(sys.argv[1:])
    params_name = argv[0] if argv else "ucie-32g"
    names = argv[1:] or list(TOPOS)
    P0 = PARAMS[params_name]
    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)
    bmax = BmaxQuery()
    rows = []

    for name in names:
        topo = TOPOS[name]
        layout = place(topo, P0)
        for beta_label, beta_p in BETA_MODES:
            P = (dataclasses.replace(P0, die=dataclasses.replace(P0.die, beta_p=beta_p))
                 if beta_p is not None else P0)
            for tag, scenario in SCENARIOS:
                models, meta = build_scenario(topo, scenario, P, layout)
                runner = Runner(CvxSolver(),
                                store=ResultStore(out_dir / ".cache"), log=False)
                t0 = time.perf_counter()
                r = bmax.solve(runner, lambda b: (Ctx(), models),
                               lo=LO, hi=HI, step=STEP)
                rows.append({
                    "topo": name, "n_terminals": topo.n_terminals,
                    "mode": beta_label, "scenario": tag,
                    "scenario_str": scenario,
                    "B_star": f"{r.B_star:.0f}", "iterations": r.iterations,
                    "solve_time_s": f"{time.perf_counter()-t0:.2f}",
                })
                print(f"{name:<15} {beta_label:<12} {tag:<16} "
                      f"B*={r.B_star:>7.0f} ({r.iterations} iters)")

    # 比率列（分母 = 同 topo/同 mode 的 ref 档）
    refs = {f"{r['topo']}|{r['mode']}": float(r["B_star"])
            for r in rows if r["scenario"] == "ref"}
    for r in rows:
        base = refs.get(f"{r['topo']}|{r['mode']}")
        b = float(r["B_star"])
        r["B_star_ratio_vs_ref"] = (f"{b/base:.4f}" if base and base > 0 else "")
    fieldnames = ["topo", "n_terminals", "mode", "scenario", "scenario_str",
                  "B_star", "B_star_ratio_vs_ref", "iterations", "solve_time_s"]
    out = out_dir / f"knob_matrix_{params_name}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # 判定（逐 mode 报告）
    print(f"\nCSV → {out}  ({len(rows)} rows)")
    for beta_label in ("default", "beta_p0.05"):
        sub = [r for r in rows if r["mode"] == beta_label]
        if not sub:
            continue
        topos = sorted({r["topo"] for r in sub})
        # M1: 逐构型单调（ref ≤ egress_peak；ref ≤ rated 需 beta_p>0）
        m1_r = all(float(next(r["B_star"] for r in sub
                             if r["topo"] == t and r["scenario"] == "egress_peak"))
                   >= float(next(r["B_star"] for r in sub
                                 if r["topo"] == t and r["scenario"] == "ref"))
                   for t in topos)
        m1_c = all(float(next(r["B_star"] for r in sub
                              if r["topo"] == t and r["scenario"] == "rated"))
                   >= float(next(r["B_star"] for r in sub
                                 if r["topo"] == t and r["scenario"] == "ref"))
                   for t in topos)
        # M2: 上推比几何均值（跨拓扑）
        ratios = [float(next(r["B_star_ratio_vs_ref"] for r in sub
                             if r["topo"] == t and r["scenario"] == "egress_peak"))
                  for t in topos]
        gm = math.exp(sum(math.log(x) for x in ratios) / len(ratios))
        m2 = gm > 1.05
        print(f"[{beta_label}] M1 R 单调={m1_r} | M1 C 单调={m1_c} | "
              f"M2 egress_peak 上推几何均值={gm:.3f} (>1.05: {m2})")
        if beta_label == "default":
            print("  ⚠️ default β_P=0：C 旋钮退化（rated≡peak），M1 C 单调为平凡相等")


if __name__ == "__main__":
    main()
