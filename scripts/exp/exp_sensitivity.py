"""实验 3: 灵敏度分析 — 约束松弛 → t* 的变化。

对固定拓扑，扫描每个约束的 RHS（右手边），观察 t* 的变化曲线。

扫描维度:
  1. 带宽需求 (target_gbps): 200→1600 Gbps  — 性能约束边界
  2. Bump 预算 (die area 倍率): 0.1×→3.0×     — 几何约束边界
  3. 散热能力 (q_max 倍率): 0.1×→3.0×          — 热约束边界

输出: outputs/paper_experiments/sensitivity_bw.csv
      outputs/paper_experiments/sensitivity_geom.csv
      outputs/paper_experiments/sensitivity_thermal.csv
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from wafer_dse.architecture_model.topology import Dragonfly
from wafer_dse.lp import UnifiedLp
from wafer_dse.lp.sensitivity import sweep_constraint_rhs
from wafer_dse.lp.geometry import DieConfig
from wafer_dse.lp.thermal import ThermalConfig
from wafer_dse.physical.bump.bump import UBUMP_45UM
from wafer_dse.physical.thermal._cooling import LIQUID_COOLING


def run(output_dir: str = "outputs/paper_experiments"):
    print("=" * 60)
    print("  实验 3: 灵敏度分析 — 约束松弛 vs t*")
    print("=" * 60)

    # --- 基础配置: DF(2,2,1), 800Gbps target ---
    topo = Dragonfly(a=2, p=2, h=1)
    n_groups = topo.g
    print(f"  基础拓扑: Dragonfly(a=2,p=2,h=1), g={n_groups}, N={len(topo.terminals())}")
    print(f"  t*(800Gbps,纯性能) = 1.0 (恰好边界)")

    # === Sweep 1: 带宽需求 ===
    print(f"\n  --- Sweep 1: 端口目标带宽 ---")
    multipliers = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]

    base_lp = UnifiedLp(topo, route="valiant", target_gbps=800.0)
    dies = [DieConfig(label=f"die_{i}") for i in range(n_groups)]
    base_lp.add_geometry(dies, UBUMP_45UM)
    base_lp.add_thermal(ThermalConfig(cooling=LIQUID_COOLING, target_gbps=800))

    sweep_constraint_rhs(
        base_lp, "performance", multipliers,
        output_dir=output_dir, csv_name="sensitivity_bw",
    )

    # === Sweep 2: Bump 预算 (die area) ===
    print(f"\n  --- Sweep 2: Die 面积 (bump 预算缩放) ---")
    area_multipliers = [0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]

    base_lp2 = UnifiedLp(topo, route="valiant", target_gbps=800.0)
    base_lp2.add_geometry(dies, UBUMP_45UM)
    base_lp2.add_thermal(ThermalConfig(cooling=LIQUID_COOLING, target_gbps=800))

    sweep_constraint_rhs(
        base_lp2, "geometry", area_multipliers,
        output_dir=output_dir, csv_name="sensitivity_geom",
    )

    # === Sweep 3: 散热能力 ===
    print(f"\n  --- Sweep 3: 散热能力 (q_max 缩放) ---")
    q_multipliers = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]

    base_lp3 = UnifiedLp(topo, route="valiant", target_gbps=800.0)
    base_lp3.add_geometry(dies, UBUMP_45UM)
    base_lp3.add_thermal(ThermalConfig(cooling=LIQUID_COOLING, target_gbps=800))

    sweep_constraint_rhs(
        base_lp3, "thermal", q_multipliers,
        output_dir=output_dir, csv_name="sensitivity_thermal",
    )

    print(f"\n  → CSV 文件已生成在 {output_dir}/")
    print(f"    sensitivity_bw.csv, sensitivity_geom.csv, sensitivity_thermal.csv")


if __name__ == "__main__":
    run()
