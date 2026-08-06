"""实验 2: 多约束耦合 — 逐步添加约束，观察 feasible 边界变化。

核心论点: 性能、几何、热三组约束通过 L 耦合。
逐步添加约束 → 展示哪些设计点从 feasible 翻转为 infeasible。

场景:
  1. 纯性能 (无物理约束)
  2. + Bump 预算 (几何约束)
  3. + 功率密度 (热约束)
  4. + 全部约束

输出: outputs/paper_experiments/constraint_coupling.csv
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from scripts.exp._runner import Trial, run_trials
from wafer_dse.architecture_model.topology import Dragonfly, Mesh, Torus
from wafer_dse.lp.geometry import DieConfig
from wafer_dse.lp.thermal import ThermalConfig
from wafer_dse.physical.bump.bump import UBUMP_45UM, UBUMP_25UM
from wafer_dse.physical.thermal._cooling import AIR_COOLING, LIQUID_COOLING, IMMERSION

MAX_TERMINALS = 24


def _build_trials() -> list[Trial]:
    """构建所有 (拓扑 × 约束组合) 的 Trial。"""
    # --- 物理配置 ---
    # Comfortable: 12×12mm, 50W, μbump 45μm
    die_comfortable = [
        DieConfig(label="die_c", width_mm=12, height_mm=12, power_w=50)
    ]
    # Tight: 6×6mm, 80W, more links per die → tighter bump budget
    die_tight = [
        DieConfig(label="die_t", width_mm=6, height_mm=6, power_w=80)
    ]

    # --- 拓扑 ---
    topologies = [
        ("DF_a2_p2_h1", Dragonfly(a=2, p=2, h=1)),
        ("DF_a2_p3_h1", Dragonfly(a=2, p=3, h=1)),
        ("DF_a3_p2_h1", Dragonfly(a=3, p=2, h=1)),
        ("DF_a2_p4_h1", Dragonfly(a=2, p=4, h=1)),
        ("Mesh_4x4",    Mesh(4)),
        ("Torus_4x4",   Torus(4)),
    ]

    # --- 约束场景 ---
    # (scenario_name, die_configs, bump, thermal_cfg)
    # None thermal/geom means skip that constraint
    air = ThermalConfig(cooling=AIR_COOLING, target_gbps=800)
    liquid = ThermalConfig(cooling=LIQUID_COOLING, target_gbps=800)
    immersion = ThermalConfig(cooling=IMMERSION, target_gbps=800)

    scenarios = [
        ("pure_perf",   None,          None,       None),
        ("+bump_tight", die_tight,     UBUMP_45UM, None),
        ("+bump_comfy", die_comfortable, UBUMP_45UM, None),
        ("+thermal_air",None,          None,       air),
        ("+thermal_liq",None,          None,       liquid),
        ("+thermal_imm",None,          None,       immersion),
        ("+all_tight",  die_tight,     UBUMP_45UM, air),
        ("+all_medium", die_comfortable, UBUMP_45UM, liquid),
        ("+all_loose",  die_comfortable, UBUMP_25UM, immersion),
    ]

    trials = []
    for tname, topo in topologies:
        n_terms = len(topo.terminals())
        if n_terms > MAX_TERMINALS:
            continue

        # 为每个拓扑扩 die configs 到正确的 die 数量
        n_groups = topo.g if hasattr(topo, "g") else 1

        for sname, die_cfgs, bump, therm in scenarios:
            # 扩展 die configs
            if die_cfgs:
                expanded = [
                    DieConfig(
                        label=f"{die_cfgs[0].label}_{i}",
                        width_mm=die_cfgs[0].width_mm,
                        height_mm=die_cfgs[0].height_mm,
                        power_w=die_cfgs[0].power_w,
                    )
                    for i in range(n_groups)
                ]
            else:
                expanded = None

            trials.append(Trial(
                label=f"{tname}_{sname}",
                topo=topo,
                route="valiant",
                target_gbps=800.0,
                die_configs=expanded,
                bump_spec=bump,
                thermal_cfg=therm,
                meta={
                    "topology": tname.split("_")[0],
                    "scenario": sname,
                    "n_terminals": n_terms,
                },
            ))

    return trials


def run(output_dir: str = "outputs/paper_experiments"):
    print("=" * 60)
    print("  实验 2: 多约束耦合")
    print("  逐步添加 bump/热约束，观察 feasible 边界变化")
    print("=" * 60)

    trials = _build_trials()
    print(f"\n  共 {len(trials)} 个设计点 (N ≤ {MAX_TERMINALS})\n")

    rows = run_trials(trials, output_dir=output_dir, csv_name="constraint_coupling")

    # 打印耦合矩阵
    print(f"\n  --- 约束耦合矩阵 (✓ = feasible, ✗ = infeasible) ---")
    scenarios = sorted(set(r["scenario"] for r in rows))
    tnames = sorted(set(r["topology"] for r in rows))

    # 表头
    header = f"  {'topology':20s}"
    for s in scenarios:
        header += f"  {s:16s}"
    print(header)
    print(f"  {'-'*len(header)}")

    for tname in tnames:
        line = f"  {tname:20s}"
        for s in scenarios:
            matching = [r for r in rows
                        if r["topology"] == tname and r["scenario"] == s]
            if matching:
                mark = "✓" if matching[0]["feasible"] else "✗"
                tstar = matching[0]["t_star"]
                line += f"  {mark} (t*={tstar:.2f})     "
            else:
                line += f"  {'-':16s}"
        print(line)

    # 翻转分析
    print(f"\n  --- 约束翻转分析 ---")
    for tname in tnames:
        pure = [r for r in rows
                if r["topology"] == tname and r["scenario"] == "pure_perf"]
        if not pure:
            continue
        was_feasible = pure[0]["feasible"]
        for s in scenarios:
            if s == "pure_perf":
                continue
            matching = [r for r in rows
                        if r["topology"] == tname and r["scenario"] == s]
            if matching and was_feasible and not matching[0]["feasible"]:
                print(f"  {tname}: feasible → INFEAIBLE when [{s}]")

    return rows


if __name__ == "__main__":
    run()
