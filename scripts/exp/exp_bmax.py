"""实验: 求解 B_max — 物理约束支撑的最大端口带宽。

核心思路:
  1. Valiant LP 求解 → 得到 L_e (每链路归一化负载)
  2. 物理约束反解:
     B_max_geom(v) = N_v^sig · R_e / Σ_{e∈δ(v)} L_e   (每 die 的 bump 预算)
     B_max_thermal  = A_total · q_max · R_e / (Σ L_e · P_lane)
  3. B_max = min(min_v B_max_geom(v), B_max_thermal)
  4. 绑定约束 = 给出最小 B_max 的那个约束

这比"800G 一切 OK"有意思得多:
  - 800G 时 bump 有 100× 松弛 → B_max_geom ≈ 80000 Gbps
  - 但随着 B 增长，lane 需求线性增长
  - 某个临界点，bump 或散热先撑不住 → 那就是 B_max

输出: outputs/paper_experiments/bmax.csv
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import csv
import math
from wafer_dse.architecture_model.topology import Dragonfly, Mesh, Torus
from wafer_dse.lp import UnifiedLp
from wafer_dse.lp.geometry import DieConfig, build_die_to_links
from wafer_dse.lp.performance import enumerate_links
from wafer_dse.lp.thermal import ThermalConfig
from wafer_dse.physical.bump.bump import UBUMP_45UM, DieBumpBudget
from wafer_dse.physical.thermal._cooling import (
    AIR_COOLING, LIQUID_COOLING, IMMERSION, MICROFLUIDIC,
)


def compute_bmax(topo, die_configs, bump_spec, thermal_cfg, target_gbps=800.0):
    """求解 LP → 提取 L_e → 解析计算 B_max。

    Returns:
        dict: {
            'B_max_geom': float,        # bump 预算决定的 B 上限
            'B_max_thermal': float,     # 散热决定的 B 上限
            'B_max': float,             # 实际 B_max (两者取 min)
            'binding': str,             # 'geometry' | 'thermal' | 'none'
            't_star': float,
            'per_die_margin': dict,     # {die_label: B_max at that die}
            'slack_at_target': dict,    # {die_label: slack in lanes at target B}
        }
    """
    lane_rate = 32.0  # Gbps/lane (UCIe-32G)
    power_per_lane = 0.005  # W/lane

    # Step 1: 求解 LP
    lp = UnifiedLp(topo, route="valiant", target_gbps=target_gbps)
    if die_configs and bump_spec:
        lp.add_geometry(die_configs, bump_spec)
    if thermal_cfg:
        lp.add_thermal(thermal_cfg)

    result = lp.solve()
    per_link_load = result.per_link_load  # {(u,v): L_e}
    links = list(per_link_load.keys())

    # Step 2: 每 die 的 bump B_max
    die_to_links = build_die_to_links(topo, links=links)
    per_die_bmax = {}
    per_die_slack = {}

    for die_idx, cfg in enumerate(die_configs):
        # 计算 N_sig
        die_budget = DieBumpBudget(
            die_label=cfg.label,
            spec=bump_spec,
            width_mm=cfg.width_mm,
            height_mm=cfg.height_mm,
            power_w=cfg.power_w,
            vdd_v=cfg.vdd_v,
            utilization=cfg.utilization,
        )
        n_sig = die_budget.available

        # Σ L_e for incident links
        incident = die_to_links.get(die_idx, [])
        if not incident:
            per_die_bmax[cfg.label] = float("inf")
            per_die_slack[cfg.label] = float("inf")
            continue

        total_L = sum(per_link_load.get(links[li], 0.0) for li in incident)

        # B_max 满足: total_L * B_max / R_e ≤ n_sig
        # → B_max ≤ n_sig * R_e / total_L
        if total_L > 0:
            per_die_bmax[cfg.label] = n_sig * lane_rate / total_L
        else:
            per_die_bmax[cfg.label] = float("inf")

        # 在 target B 下的 lane 使用量
        lanes_used = total_L * target_gbps / lane_rate
        per_die_slack[cfg.label] = n_sig - lanes_used

    B_max_geom = min(per_die_bmax.values()) if per_die_bmax else float("inf")

    # Step 3: 散热 B_max
    total_L_all = sum(per_link_load.values())
    total_area = (thermal_cfg.total_area_mm2 * thermal_cfg.interposer_count
                  if thermal_cfg else 858.0)
    q_max = thermal_cfg.cooling.max_power_density_w_per_mm2 if thermal_cfg else 2.0

    if total_L_all > 0:
        # Σ L_e · P_lane · B / R_e ≤ A · q_max
        # → B ≤ A · q_max · R_e / (Σ L_e · P_lane)
        B_max_thermal = total_area * q_max * lane_rate / (total_L_all * power_per_lane)
    else:
        B_max_thermal = float("inf")

    # Step 4: 合并
    B_max = min(B_max_geom, B_max_thermal)
    if B_max == float("inf"):
        binding = "none"
    elif B_max == B_max_geom and B_max == B_max_thermal:
        binding = "both"
    elif B_max == B_max_geom:
        binding = "geometry"
    else:
        binding = "thermal"

    return {
        "B_max_geom": B_max_geom,
        "B_max_thermal": B_max_thermal,
        "B_max": B_max,
        "binding": binding,
        "t_star": result.worst_load,
        "per_die_bmax": per_die_bmax,
        "per_die_slack": per_die_slack,
        "total_L": total_L_all,
        "n_links": len(links),
    }


def run(output_dir: str = "outputs/paper_experiments"):
    print("=" * 60)
    print("  实验: B_max — 物理约束支撑的最大端口带宽")
    print("=" * 60)

    # --- 拓扑 ---
    configs = [
        ("DF(1,1,1)", Dragonfly(a=1, p=1, h=1)),
        ("DF(2,1,1)", Dragonfly(a=2, p=1, h=1)),
        ("DF(2,2,1)", Dragonfly(a=2, p=2, h=1)),
        ("DF(2,3,1)", Dragonfly(a=2, p=3, h=1)),
        ("DF(3,2,1)", Dragonfly(a=3, p=2, h=1)),
        ("DF(2,4,1)", Dragonfly(a=2, p=4, h=1)),
        ("DF(2,2,2)", Dragonfly(a=2, p=2, h=2)),
        ("Mesh(4)",    Mesh(4)),
        ("Torus(4)",   Torus(4)),
    ]

    # --- 物理配置 ---
    bump = UBUMP_45UM
    cooling = LIQUID_COOLING

    rows = []
    print(f"\n  {'topology':15s}  {'N':4s}  {'B_max_geom':12s}  {'B_max_thermal':14s}  {'B_max':10s}  {'binding':10s}  {'t*':6s}")
    print(f"  {'-'*85}")

    for label, topo in configs:
        n_terms = len(topo.terminals())
        if n_terms > 30:
            continue

        n_groups = topo.g if hasattr(topo, "g") else 1
        dies = [DieConfig(label=f"die_{i}", width_mm=12, height_mm=12, power_w=50)
                for i in range(n_groups)]
        therm = ThermalConfig(cooling=cooling, target_gbps=800)

        info = compute_bmax(topo, dies, bump, therm, target_gbps=800.0)

        bmax_g = info["B_max_geom"]
        bmax_t = info["B_max_thermal"]
        bmax = info["B_max"]

        row = {
            "topology": label,
            "n_terminals": n_terms,
            "n_groups": n_groups,
            "t_star": info["t_star"],
            "B_max_geom_Gbps": round(bmax_g, 0),
            "B_max_thermal_Gbps": round(bmax_t, 0),
            "B_max_Gbps": round(bmax, 0),
            "binding": info["binding"],
            "total_L": round(info["total_L"], 4),
            "n_links": info["n_links"],
        }
        rows.append(row)

        # 打印
        bmax_g_str = f"{bmax_g:.0f}" if bmax_g != float("inf") else "∞"
        bmax_t_str = f"{bmax_t:.0f}" if bmax_t != float("inf") else "∞"
        bmax_str = f"{bmax:.0f}" if bmax != float("inf") else "∞"
        binding_symbol = "🔴" if info["binding"] != "none" else "🟢"
        print(f"  {label:15s}  {n_terms:4d}  {bmax_g_str:>12s}  {bmax_t_str:>14s}  {bmax_str:>10s}  {binding_symbol} {info['binding']:8s}  {info['t_star']:.4f}")

    # 写 CSV
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "bmax.csv")
    if rows:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n  → {len(rows)} rows → {csv_path}")

    # 分析
    print(f"\n  --- 分析 ---")
    for row in rows:
        if row["B_max_Gbps"] != float("inf") and row["B_max_Gbps"] < 1e5:
            headroom = row["B_max_Gbps"] / 800
            print(f"  {row['topology']:15s}: B_max = {row['B_max_Gbps']:.0f} Gbps "
                  f"({headroom:.0f}× vs 800G), binding = {row['binding']}")

    return rows


if __name__ == "__main__":
    run()
