#!/usr/bin/env python3
"""实验矩阵：拓扑 × 约束场景 → B* 与瓶颈诊断.

每个拓扑跑三层场景，看物理约束逐层压下来 B* 怎么动：
  perf               — 只有性能包络（B 不约束 → B* 无意义，作基线）
  perf+bump          — + μbump 预算
  perf+bump+therm    — + 几何热网络（L1 稳态）

输出 CSV: exp/output/matrix.csv
用法:
    PYTHONPATH=src python3 exp/run_matrix.py
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import numpy as np

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from problem import Ctx, CvxSolver, Runner, ResultStore

from problem.queries import BmaxQuery
from problem.builder import build_scenario
from physical.params import TOY, UCIE_16G, UCIE_24G, UCIE_32G
from topology import MeshTopology, TorusTopology, KaryNCubeTopology, FullMeshTopology, DragonflyTopology

from layout import place

# ── 参数组合（论文绘图、讨论围绕这些展开） ────────────────────────
PARAM_SETS = {
    "toy": TOY,
    "ucie-16g": UCIE_16G,
    "ucie-24g": UCIE_24G,
    "ucie-32g": UCIE_32G,
}

# ── 拓扑清单 ────────────────────────────────────────────────────
TOPOS = {
    "Mesh(2)":       MeshTopology(2),
    "Mesh(3)":       MeshTopology(3),
    "Mesh(4)":       MeshTopology(4),
    "Torus(2)":      TorusTopology(2),
    "Torus(3)":      TorusTopology(3),
    "KaryNCube(2,2)": KaryNCubeTopology(2, 2),
    "KaryNCube(2,3)": KaryNCubeTopology(2, 3),
    "FullMesh(2)":   FullMeshTopology(2, 1),
    "FullMesh(3)":   FullMeshTopology(3, 1),
    "Dragonfly(2,1,1)": DragonflyTopology(2, 1, 1),
    "Dragonfly(2,2,1)": DragonflyTopology(2, 2, 1),
}

SCENARIOS = ["perf", "perf+bump", "perf+bump+therm"]


_PHYS_PREFIXES = ("bump_", "therm_", "c4_", "route_")


def binding_summary(binding: list[str]) -> tuple[list[str], int]:
    """绑定约束拆成 (物理约束列表, 其余性能/结构性约束数)。"""
    phys = [b for b in binding if b.startswith(_PHYS_PREFIXES)]
    return phys, len(binding) - len(phys)


def main():
    params_name = sys.argv[1] if len(sys.argv) > 1 else "ucie-32g"
    if params_name not in PARAM_SETS:
        raise SystemExit(f"未知参数组 '{params_name}'，可选: {sorted(PARAM_SETS)}")
    P = PARAM_SETS[params_name]

    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)
    log_path = out_dir / f"bmax_{params_name}.log"
    log_path.write_text("")  # 每次运行清空

    runner = Runner(CvxSolver(), store=ResultStore(out_dir / ".cache"),
                     log=False)
    bmax = BmaxQuery()
    rows = []

    print(f"参数组: {params_name}")
    print(f"  die {P.die.width_mm:.0f}×{P.die.height_mm:.0f}mm, "
          f"P0={P.die.static_power_w:.0f}W, {P.link.name} "
          f"({P.link.pj_per_bit:.3f} pJ/bit), {P.bump.name}, "
          f"R_vert={P.thermal.r_vert_k_per_w}K/W")
    print(f"  场景: perf+bump = 性能包络 + μbump 预算；"
          f"perf+bump+therm = 再加 per-die 温度极限")
    print(f"  bmax 迭代细节 → {log_path}")
    print(f"{'topo':<18} {'scenario':<16} {'B*':>9} {'iters':>5} "
          f"{'t(s)':>7}   绑定的物理约束")
    print("-" * 100)

    for name, topo in TOPOS.items():
        layout = place(topo, P)  # 布局是更高层的设计决策，先做
        for sc in SCENARIOS:
            models, meta = build_scenario(topo, sc, P, layout)
            if sc == "perf":
                # 纯性能模型 B 不约束 → B* 无界，bmax 会无限翻倍，跳过
                print(f"{name:<18} {sc:<16} {'unbounded':>9} {'-':>5} "
                      f"{'-':>7}   -")
                rows.append({
                    "topo": name,
                    "n_terminals": topo.n_terminals,
                    "n_links": topo.n_links,
                    "n_dies": meta["n_dies"],
                    "scenario": sc,
                    "B_star": "unbounded",
                    "iterations": "",
                    "n_binding": "",
                    "binding": "",
                    "solve_time_s": "",
                })
                continue
            t0 = time.perf_counter()
            r = bmax.solve(runner, lambda b: (Ctx(), models),
                           lo=100, hi=50000, step=200, log_file=str(log_path))
            elapsed = time.perf_counter() - t0

            # B* 处瓶颈诊断——用 min ΣL 解（无目标求解 duals 不可靠）
            binding = []
            if r.B_star > 0:
                ctx = Ctx()
                for m in models:
                    m.build(ctx, float(r.B_star))
                sol = CvxSolver().solve(ctx, objective=sum(ctx["L"]),
                                        maximize=False)
                binding = list(sol.duals.keys()) if sol.duals else []

            phys, n_other = binding_summary(binding)
            phys_s = ",".join(phys) if phys else "-"
            print(f"{name:<18} {sc:<16} {r.B_star:>9.0f} {r.iterations:>5} "
                  f"{elapsed:>7.1f}   {phys_s}"
                  + (f"  (+{n_other} 性能/结构)" if n_other else ""))

            rows.append({
                "topo": name,
                "n_terminals": topo.n_terminals,
                "n_links": topo.n_links,
                "n_dies": meta["n_dies"],
                "scenario": sc,
                "B_star": f"{r.B_star:.0f}",
                "iterations": r.iterations,
                "n_binding": len(binding),
                "binding": phys_s,
                "solve_time_s": f"{elapsed:.2f}",
            })

    out_path = out_dir / f"matrix_{params_name}.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV → {out_path}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
