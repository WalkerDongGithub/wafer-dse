"""实验 4: DSE 规模扫描 — Dragonfly 参数枚举 + Pareto 前沿。

枚举 Dragonfly (a,p,h) 参数空间，记录每个设计点的:
  - 性能 (t*, nonblocking_gbps, N)
  - 物理成本 (die count, total area, total power)
  - 可行性 + 约束 slack

生成 Pareto 前沿: max BW vs min area vs min power

输出: outputs/paper_experiments/dse_sweep.csv
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from scripts.exp._runner import Trial, run_trials
from wafer_dse.architecture_model.topology import Dragonfly
from wafer_dse.lp.geometry import DieConfig
from wafer_dse.lp.thermal import ThermalConfig
from wafer_dse.physical.bump.bump import UBUMP_45UM
from wafer_dse.physical.thermal._cooling import LIQUID_COOLING

MAX_TERMINALS = 30


def _build_trials() -> list[Trial]:
    """枚举 Dragonfly 参数空间。"""
    # 默认 die 配置: 12×12mm, 50W
    die_template = DieConfig(label="tpl", width_mm=12, height_mm=12, power_w=50)

    # a: groups per router, p: terminals per router, h: global ports per router
    param_sets = [
        (1, 1, 1),
        (2, 1, 1),
        (2, 2, 1),
        (2, 3, 1),
        (3, 2, 1),
        (2, 4, 1),
        (3, 3, 1),
        (2, 2, 2),
        (3, 2, 2),
        (4, 2, 1),
        (2, 5, 1),
        (4, 3, 1),
    ]

    trials = []
    for a, p, h in param_sets:
        topo = Dragonfly(a=a, p=p, h=h)
        n_terms = len(topo.terminals())
        if n_terms > MAX_TERMINALS:
            continue

        n_groups = topo.g

        # 为每个 group 创建一个 die
        dies = [
            DieConfig(
                label=f"die_g{i}",
                width_mm=die_template.width_mm,
                height_mm=die_template.height_mm,
                power_w=die_template.power_w,
            )
            for i in range(n_groups)
        ]

        # 每个 die 12×12=144mm², 总面积 = n_groups × 144
        total_area = n_groups * die_template.width_mm * die_template.height_mm
        total_power = n_groups * die_template.power_w

        label = f"DF_a{a}_p{p}_h{h}"

        trials.append(Trial(
            label=label,
            topo=topo,
            route="valiant",
            target_gbps=800.0,
            die_configs=dies,
            bump_spec=UBUMP_45UM,
            thermal_cfg=ThermalConfig(cooling=LIQUID_COOLING, target_gbps=800),
            meta={
                "topology": "dragonfly",
                "a": a, "p": p, "h": h, "g": n_groups,
                "n_terminals": n_terms,
                "n_groups": n_groups,
                "total_die_area_mm2": total_area,
                "total_power_w": total_power,
                "density_n_per_area": round(n_terms / total_area, 3) if total_area > 0 else 0,
            },
        ))

    return trials


def run(output_dir: str = "outputs/paper_experiments"):
    print("=" * 60)
    print("  实验 4: DSE 规模扫描 — Dragonfly (a,p,h) 枚举")
    print("=" * 60)

    trials = _build_trials()
    print(f"\n  共 {len(trials)} 个 Dragonfly 设计点 (N ≤ {MAX_TERMINALS})\n")

    rows = run_trials(trials, output_dir=output_dir, csv_name="dse_sweep")

    # 打印设计点对比表
    print(f"\n  --- 设计点对比 (按 N 排序) ---")
    print(f"  {'config':20s}  {'N':4s}  {'groups':6s}  {'area':8s}  {'feas':5s}  {'t*':8s}  {'BW':8s}")
    print(f"  {'-'*70}")
    for row in sorted(rows, key=lambda r: r["n_terminals"]):
        bw = row["nonblocking_gbps"]
        print(f"  {row['label']:20s}  {row['n_terminals']:4d}  "
              f"{row.get('n_groups', 0):6d}  "
              f"{row.get('total_die_area_mm2', 0):8.0f}  "
              f"{'✓' if row['feasible'] else '✗':5s}  "
              f"{row['t_star']:8.4f}  {bw:8.0f}")

    # 计算 Pareto 前沿 (二维简化: max BW vs min total area)
    feasible = [r for r in rows if r["feasible"]]
    print(f"\n  {len(feasible)}/{len(rows)} feasible")

    if feasible:
        # 非支配排序 (BW越大越好, area越小越好)
        frontier = []
        for i, a in enumerate(feasible):
            dominated = False
            for j, b in enumerate(feasible):
                if i == j:
                    continue
                # b dominates a?
                if (b["nonblocking_gbps"] >= a["nonblocking_gbps"] and
                    b.get("total_die_area_mm2", 0) <= a.get("total_die_area_mm2", 0) and
                    (b["nonblocking_gbps"] > a["nonblocking_gbps"] or
                     b.get("total_die_area_mm2", 0) < a.get("total_die_area_mm2", 0))):
                    dominated = True
                    break
            if not dominated:
                frontier.append(a)

        print(f"  Pareto 前沿: {len(frontier)} 个设计点")
        print(f"  {'config':20s}  {'N':4s}  {'area':8s}  {'BW':8s}")
        for f in sorted(frontier, key=lambda r: r["nonblocking_gbps"], reverse=True):
            print(f"  {f['label']:20s}  {f['n_terminals']:4d}  "
                  f"{f.get('total_die_area_mm2', 0):8.0f}  "
                  f"{f['nonblocking_gbps']:8.0f}")

    return rows


if __name__ == "__main__":
    run()
