#!/usr/bin/env python3
"""E8 灵敏度小规模验证表（sensitivity-design.md 双轨路径 A：数值有限差分）.

口径（DomainExpert 定案）:
- 细步长 step=20（分辨率陷阱：粗步长隐藏 <4% 效应，结果不引用粗步长）。
- min-ΣL 对偶仅作绑定集识别（单位 ΔΣL/Δrhs，不做 B 解锁量）；B 解锁用数值差分。
- β_P>0 档（power 随 B 缩放，旋钮表完整）+ Dragonfly 补 β_P=0 档（布线绑定域）。

旋钮（改善方向扰动）: ppl(每 lane 功耗 -1%) / R_vert(散热 -1%) / lanes_per_mm(布线容量 +1%) / beta_P(峰值功耗斜率 -1%)。

用法: PYTHONPATH=src python3 exp/run_sensitivity.py [params_name]
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
TOPOS = {
    "Mesh(3)": MeshTopology(3),
    "Dragonfly(2,1,1)": DragonflyTopology(2, 1, 1),
}
STEP = 5.0           # 细步长（灵敏度口径；报告 step 与灵敏度下限）
PERT = 0.05          # 扰动幅度 ±5%（E8 规格；改善方向）
LO, HI = 100.0, 50000.0
BETA_GRID = [0.05]   # Mesh(3) 用 β_P=0.05
BETA_DRAGONFLY = [0.0, 0.05]  # Dragonfly 双档（布线绑定域 + therm 域）


def _knobs(P):
    """改善方向扰动（±5%，E8 规格：top 旋钮 +5% 扰动重解 B* vs 一阶预测）。"""
    d = PERT
    return [
        ("ppl(-5%)", dataclasses.replace(
            P, link=dataclasses.replace(P.link, power_per_lane_w=P.link.power_per_lane_w * (1 - d)))),
        ("R_vert(-5%)", dataclasses.replace(
            P, thermal=dataclasses.replace(P.thermal, r_vert_k_per_w=P.thermal.r_vert_k_per_w * (1 - d)))),
        ("lanes_per_mm(+5%)", dataclasses.replace(
            P, pkg=dataclasses.replace(P.pkg, lanes_per_mm=P.pkg.lanes_per_mm * (1 + d)))),
        ("c4_pitch(+5%)", dataclasses.replace(
            P, pkg=dataclasses.replace(P.pkg, c4_pitch_mm=P.pkg.c4_pitch_mm * (1 + d)))),
        ("beta_P(-5%)", dataclasses.replace(
            P, die=dataclasses.replace(P.die, beta_p=P.die.beta_p * (1 - d)))),
    ]


def _bstar(runner, bmax, topo, P, layout):
    models, _ = build_scenario(topo, "perf+bump+therm+wiring+area", P, layout)
    return bmax.solve(runner, lambda b: (Ctx(), models), lo=LO, hi=HI, step=STEP).B_star


def main() -> None:
    params_name = sys.argv[1] if len(sys.argv) > 1 else "ucie-32g"
    P0 = PARAMS[params_name]
    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)
    rows = []

    for name, topo in TOPOS.items():
        betas = BETA_DRAGONFLY if name.startswith("Dragonfly") else BETA_GRID
        layout = place(topo, P0)
        for bp in betas:
            P = dataclasses.replace(P0, die=dataclasses.replace(P0.die, beta_p=bp))
            runner = Runner(CvxSolver(), store=ResultStore(out_dir / ".cache"), log=False)
            bmax = BmaxQuery()
            B0 = _bstar(runner, bmax, topo, P, layout)
            for label, Pk in _knobs(P):
                B1 = _bstar(runner, bmax, topo, Pk, layout)
                dPct = (B1 - B0) / B0 * 100.0 if B0 > 0 else float("nan")
                rows.append({
                    "topo": name, "beta_p": bp, "knob": label,
                    "B_star_base": f"{B0:.0f}", "B_star_pert": f"{B1:.0f}",
                    "dPct": f"{dPct:+.2f}",
                })
                print(f"{name:<16} β={bp}: {label:<18} B* {B0:.0f} → {B1:.0f} "
                      f"({dPct:+.2f}%)")
            # 该档排名
            sub = [r for r in rows if r["topo"] == name and float(r["beta_p"]) == bp]
            ranking = sorted(sub, key=lambda r: -abs(float(r["dPct"])))
            rank_str = " ".join(f"{r['knob']}({r['dPct']}%)" for r in ranking)
            print(f"  → 解锁旋钮排名: {rank_str}")

    out = out_dir / f"sensitivity_{params_name}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV → {out}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
