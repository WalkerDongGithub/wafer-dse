"""实验 1: 可扩展性 — Valiant LP 求解规模 vs 拓扑规模。

测试多种拓扑在不同规模下的变量数、约束数、求解时间。
限制: N ≤ 30 (Valiant LP 的变量数 ~ O(N²·g)，大拓扑会内存爆炸)

输出: outputs/paper_experiments/scalability.csv
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from scripts.exp._runner import Trial, run_trials
from wafer_dse.architecture_model.topology import Dragonfly, Mesh, KaryNCube

MAX_TERMINALS = 30  # 硬限制，超过则跳过


def _dragonfly_trials() -> list[Trial]:
    """Dragonfly 拓扑规模扫描。"""
    configs = [
        (1, 1, 1),
        (2, 1, 1),
        (2, 2, 1),
        (2, 3, 1),
        (3, 2, 1),
        (2, 4, 1),
        (3, 3, 1),
        (2, 2, 2),
        (3, 2, 2),
    ]
    trials = []
    for a, p, h in configs:
        topo = Dragonfly(a=a, p=p, h=h)
        n_terms = len(topo.terminals())
        if n_terms > MAX_TERMINALS:
            continue
        trials.append(Trial(
            label=f"DF_a{a}_p{p}_h{h}",
            topo=topo,
            route="valiant",
            target_gbps=800.0,
            meta={"topology": "dragonfly", "a": a, "p": p, "h": h,
                  "g": topo.g, "n_terminals": n_terms},
        ))
    return trials


def _mesh_trials() -> list[Trial]:
    """Mesh 规模扫描。"""
    trials = []
    for s in [2, 3, 4, 5]:
        topo = Mesh(s)
        n_terms = len(topo.terminals())
        if n_terms > MAX_TERMINALS:
            continue
        trials.append(Trial(
            label=f"Mesh_{s}x{s}",
            topo=topo,
            route="valiant",
            target_gbps=800.0,
            meta={"topology": "mesh", "size": s, "n_terminals": n_terms},
        ))
    return trials


def _kary_ncube_trials() -> list[Trial]:
    """k-ary n-cube 规模扫描。"""
    configs = [
        (2, 2, True),
        (3, 2, True),
        (4, 2, True),
        (2, 3, True),   # 2×2×2 = 8 terminals
        (3, 3, True),   # 3×3×3 = 27 terminals
    ]
    trials = []
    for k, n, wrap in configs:
        topo = KaryNCube(k=k, n=n, wrap=wrap)
        n_terms = len(topo.terminals())
        if n_terms > MAX_TERMINALS:
            continue
        label = f"KaryNCube_k{k}_n{n}_{'torus' if wrap else 'mesh'}"
        trials.append(Trial(
            label=label,
            topo=topo,
            route="valiant",
            target_gbps=800.0,
            meta={"topology": "kary_ncube", "k": k, "n": n, "wrap": wrap,
                  "n_terminals": n_terms},
        ))
    return trials


def run(output_dir: str = "outputs/paper_experiments"):
    print("=" * 60)
    print("  实验 1: 可扩展性 — Valiant LP 变量数/约束数/求解时间 vs N")
    print("=" * 60)

    all_trials = _dragonfly_trials() + _mesh_trials() + _kary_ncube_trials()
    print(f"\n  共 {len(all_trials)} 个设计点 (N ≤ {MAX_TERMINALS})\n")

    rows = run_trials(all_trials, output_dir=output_dir, csv_name="scalability")
    print(f"\n  --- 汇总 ---")
    print(f"  {'label':25s}  {'N':4s}  {'vars':6s}  {'constr':6s}  {'t*':8s}  {'time(s)':8s}")
    print(f"  {'-'*70}")
    for row in rows:
        print(f"  {row['label']:25s}  {row['n_terminals']:4d}  "
              f"{row['num_vars']:6d}  {row['num_constraints']:6d}  "
              f"{row['t_star']:8.4f}  {row['solve_time_s']:8.3f}")
    return rows


if __name__ == "__main__":
    run()
