#!/usr/bin/env python3
"""E8 灵敏度验证（SensitivityQuery 暂不建；现有 duals + 细步长有限差分）.

规格（experiment-design §2 E8）:
- 2 构型：Mesh(3)/ucie-32g（therm 绑定）+ Dragonfly(2,1,1)/ucie-32g（wiring 绑定）。
  ⚠️ 规格张力：β_P>0 时 Dragonfly 绑定从 C4-pad 布线转 therm——故 Dragonfly 跑 β_P∈{0, 0.05}
  双档覆盖两绑定域（β_P=0 为 wiring 绑定、β_P=0.05 为 therm 绑定），Mesh(3) 跑 β_P=0.05。
- 步骤：min-ΣL duals 绑定识别 → 数值一阶（-1% 小扰动斜率）→ 预测 -5% vs 重解 -5%（误差<20%）→ 排名。
- 判据：S1 绑定集 / S2 一阶误差<20% / S3 排名工程合理 / S4 单调 / S5 Conservative。
- 口径：step=20（细步长），粗步长不引用。

用法: PYTHONPATH=src python3 exp/run_e8.py [params_name]
输出: exp/output/sensitivity_<params>.csv
"""
from __future__ import annotations

import csv
import dataclasses
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from problem import Ctx, CvxSolver, Runner, ResultStore
from problem.builder import build_scenario
from problem.queries import BmaxQuery
from physical.params import UCIE_32G
from topology import DragonflyTopology, MeshTopology
from layout import place

PARAMS = {"ucie-32g": UCIE_32G}
STEP = 2.0
LO, HI = 100.0, 50000.0
CONFIGS = [
    ("Mesh(3)-therm", MeshTopology(3), 0.05),
    ("Dragonfly-wiring", DragonflyTopology(2, 1, 1), 0.0),
    ("Dragonfly-therm", DragonflyTopology(2, 1, 1), 0.05),
]


def _bstar(runner, bq, topo, layout, P):
    models, _ = build_scenario(topo, "perf+bump+therm+wiring+area", P, layout)
    return bq.solve(runner, lambda b: (Ctx(), models), lo=LO, hi=HI, step=STEP).B_star


def _binding(topo, layout, P, B):
    models, _ = build_scenario(topo, "perf+bump+therm+wiring+area", P, layout)
    ctx = Ctx()
    for m in models:
        m.build(ctx, float(B))
    sol = CvxSolver().solve(ctx, objective=sum(ctx["L"]), maximize=False)
    fam = {}
    for cn, lam in (sol.duals or {}).items():
        if abs(lam) > 1e-6:
            fam[cn.split("_")[0]] = fam.get(cn.split("_")[0], 0) + 1
    return sorted(fam)


def _knobs(P):
    d = 0.01  # 小扰动斜率
    return [
        ("ppl(-)", dataclasses.replace(P, link=dataclasses.replace(P.link, power_per_lane_w=P.link.power_per_lane_w * (1 - d))), 0.05),
        ("R_vert(-)", dataclasses.replace(P, thermal=dataclasses.replace(P.thermal, r_vert_k_per_w=P.thermal.r_vert_k_per_w * (1 - d))), 0.05),
        ("lanes_per_mm(+)", dataclasses.replace(P, pkg=dataclasses.replace(P.pkg, lanes_per_mm=P.pkg.lanes_per_mm * (1 + d))), 0.05),
        ("beta_P(-)", dataclasses.replace(P, die=dataclasses.replace(P.die, beta_p=P.die.beta_p * (1 - d))), 0.05),
    ]


def main() -> None:
    params_name = sys.argv[1] if len(sys.argv) > 1 else "ucie-32g"
    P0 = PARAMS[params_name]
    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)
    rows = []

    for label, topo, bp in CONFIGS:
        layout = place(topo, P0)
        P = dataclasses.replace(P0, die=dataclasses.replace(P0.die, beta_p=bp))
        runner = Runner(CvxSolver(), store=ResultStore(out_dir / ".cache"), log=False)
        bq = BmaxQuery()
        B0 = _bstar(runner, bq, topo, layout, P)
        fam = _binding(topo, layout, P, B0)
        print(f"\n{label} (β={bp}): B*={B0:.0f} 绑定族={fam}")

        for kname, Pk, dbig in _knobs(P):
            if kname == "beta_P(-)" and bp == 0.0:
                continue  # β_P=0 时 beta_P 旋钮无意义
            # 斜率：小扰动 -1%（或 +1%）
            Bsmall = _bstar(runner, bq, topo, layout, Pk)
            slope = (Bsmall - B0) / B0 / 0.01  # 每 1%
            # 大扰动重解：±5%（与斜率同方向）
            sgn = 1 if slope >= 0 else -1
            if kname in ("lanes_per_mm(+)"):
                Pbig = dataclasses.replace(P, pkg=dataclasses.replace(P.pkg, lanes_per_mm=P.pkg.lanes_per_mm * (1 + 0.05)))
            elif kname == "ppl(-)":
                Pbig = dataclasses.replace(P, link=dataclasses.replace(P.link, power_per_lane_w=P.link.power_per_lane_w * 0.95))
            elif kname == "R_vert(-)":
                Pbig = dataclasses.replace(P, thermal=dataclasses.replace(P.thermal, r_vert_k_per_w=P.thermal.r_vert_k_per_w * 0.95))
            else:  # beta_P(-)
                Pbig = dataclasses.replace(P, die=dataclasses.replace(P.die, beta_p=P.die.beta_p * 0.95))
            Bbig = _bstar(runner, bq, topo, layout, Pbig)
            # 一阶预测（外推 5%）
            pred = B0 * (1 + slope * 0.05 * sgn)
            err = abs(pred - Bbig) / Bbig * 100.0 if Bbig > 0 else float("nan")
            rows.append({
                "design_point": label, "beta_p": bp, "binding_families": ";".join(fam),
                "knob": kname, "B_star_base": f"{B0:.0f}",
                "slope_pct_per_1pct": f"{slope*100:+.2f}",
                "pred_5pct": f"{pred:.0f}", "resolve_5pct": f"{Bbig:.0f}",
                "first_order_err_pct": f"{err:.1f}",
                "rank_hint": "",
            })
            print(f"  {kname:<16} 斜率 {slope*100:+.2f}%/1% | 预测5% {pred:.0f} vs 重解 {Bbig:.0f} | 误差 {err:.1f}%")

    # 排名（每设计点按 |斜率|）
    for dp in set(r["design_point"] for r in rows):
        sub = [r for r in rows if r["design_point"] == dp]
        sub.sort(key=lambda r: -abs(float(r["slope_pct_per_1pct"])))
        for i, r in enumerate(sub):
            r["rank_hint"] = f"rank{i+1}"
    out = out_dir / f"sensitivity_{params_name}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV → {out}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
