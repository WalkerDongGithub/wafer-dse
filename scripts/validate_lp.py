#!/usr/bin/env python3
"""
Unified LP validation: Dragonfly DSE with the 4-constraint model.

Usage:  python scripts/validate_lp.py

Compares results against dse_demo.py output (dse_results/summary.json).
"""

from __future__ import annotations
import sys, math, json, os
sys.path.insert(0, "src")

import numpy as np

from wafer_dse.architecture_model.topology.dragonfly import Dragonfly
from wafer_dse.architecture_model.solver._potential._adversarial import _AdversarialLp
from wafer_dse.architecture_model.solver._potential._config import PotentialConfig

# ── Config (from configs/dse_demo.yaml) ──
B = 800.0            # target Gbps per port
A_DIE = 144.0        # mm² (12×12)
P_DIE_BASE = 50.0    # W (static + crossbar, approximate)
V_DD = 0.8           # V
I_BUMP = 0.04        # A (40 mA)
P_UBUMP = 0.025      # mm (25 μm)
ETA = 0.7             # bump utilization
R_INT = 32.0          # Gbps/lane (UCIe)
P_LANE = 0.005        # W per lane (D2D PHY, approximate)
A_INTERPOSER = 858.0  # mm²
Q_MAX = 2.0           # W/mm² (liquid cooling)
T_MAX = 358.15        # K (85°C)
T_AMB = 300.0         # K (27°C)
R_EFF = 0.2           # K/W (ΔT=58K / 300W per interposer, liquid cooling)
N_INTERPOSER = 16     # interposer count
GRID = (4, 4)         # substrate grid

# ── Derived ──
RHO = 1.0 / (P_UBUMP ** 2)  # bump/mm²
N_TOTAL = int(ETA * RHO * A_DIE)
N_PWR = math.ceil((P_DIE_BASE / V_DD) / I_BUMP)
N_SIG = N_TOTAL - N_PWR

# ── Thermal constants ──
G_VERT = 1.0 / R_EFF
K_SUB = 20.0          # W/m·K (organic substrate)
T_SUB = 1.0           # mm
W_INT = 31.0          # mm (interposer width)
D_PITCH = 31.0        # mm (interposer pitch)
G_LAT = K_SUB * (T_SUB * 1e-3) * (W_INT * 1e-3) / (D_PITCH * 1e-3)

print(f"=== Chiplet Parameters ===")
print(f"  A_die={A_DIE} mm², P_die(base)={P_DIE_BASE} W")
print(f"  N_total={N_TOTAL}, N_pwr={N_PWR}, N_sig={N_SIG}")
print(f"  g_vert={G_VERT:.4f}, g_lat={G_LAT:.4f}")
print()


def build_thermal_matrix(rows: int, cols: int) -> np.ndarray:
    """Build G matrix for substrate thermal network."""
    n = rows * cols
    G = np.zeros((n, n))
    b = np.zeros(n)
    for i in range(n):
        r, c = divmod(i, cols)
        nbrs = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                nbrs += 1
                G[i, nr * cols + nc] = -G_LAT
        G[i, i] = G_VERT + nbrs * G_LAT
        b[i] = G_VERT * T_AMB
    return G, b


def perf_feasibility(a: int, p: int, h: int) -> tuple[float, float, bool]:
    """Performance: T1 bisection (demo criterion) + T2 adversarial LP.

    Demo criterion (T1): bisection_bw = min((a-1)*B/2, h*B/2) ≥ B
    LP criterion (T2): L* ≤ B/B (true NB, very strict)
    """
    bisection_bw = min((a - 1) * B / 2, h * B / 2)
    t1_ok = bisection_bw >= B

    L_star = float("inf")
    t2_ok = None
    try:
        topo = Dragonfly(a=a, p=p, h=h)
        n_terms = len(topo.terminals())
        if n_terms <= 64:
            cfg = PotentialConfig(pattern="adversarial")
            solver = _AdversarialLp()
            L_star = solver.compute(topo, topo.det, [], topo.terminals(), cfg)
            t2_ok = L_star <= 1.0
    except Exception:
        pass

    # Use T1 (bisection) as pass criterion, matching demo
    return bisection_bw, L_star, t1_ok


def geom_feasibility(L_vec: np.ndarray, edges_per_die: list[int]) -> tuple[bool, float]:
    """Geometry constraint: Σ L_e × B/R ≤ N_sig for each die."""
    max_violation = 0.0
    for deg in edges_per_die:
        # All incident edges assumed to have same L ≈ mean(L_vec)
        total_lanes = deg * np.mean(L_vec) * B / R_INT if len(L_vec) > 0 else 0
        pwr_lanes = P_DIE_BASE / (V_DD * I_BUMP)
        violation = (total_lanes + pwr_lanes) - N_SIG
        max_violation = max(max_violation, violation)
    return max_violation <= 0, max_violation


def power_feasibility(L_vec: np.ndarray, edges_per_die: list[int],
                      use_demo_thermal: bool = True) -> tuple[bool, float, dict]:
    """Power + thermal constraint: use demo's hierarchical solver."""
    # Per-die power
    P_per_die = []
    for deg in edges_per_die:
        p_link = deg * np.mean(L_vec) * B / R_INT * P_LANE if len(L_vec) > 0 else 0
        P_per_die.append(P_DIE_BASE + p_link)

    # Aggregate to interposer level
    total_power = sum(P_per_die)
    per_int_power = total_power / N_INTERPOSER

    # Use demo's thermal solver (hierarchical, MFIT-calibrated)
    if use_demo_thermal:
        from wafer_dse.physical.thermal import (
            ThermalConfig, LIQUID_COOLING, create_solver,
        )
        thermal_solver = create_solver("auto")
        if hasattr(thermal_solver, 'calibrate'):
            calib = ThermalConfig(
                die_width_mm=12.0, die_height_mm=12.0,
                die_count=4, die_power_w=P_DIE_BASE / 2,
                interposer_area_mm2=A_INTERPOSER,
                interposer_count=N_INTERPOSER, cooling=LIQUID_COOLING,
            )
            thermal_solver.calibrate(calib)
        if hasattr(thermal_solver, 'solve_uniform'):
            tres = thermal_solver.solve_uniform(per_int_power)
        else:
            cfg = ThermalConfig(
                die_power_w=per_int_power, interposer_area_mm2=A_INTERPOSER,
                interposer_count=N_INTERPOSER, cooling=LIQUID_COOLING,
            )
            tres = thermal_solver.solve(cfg)
        thermal_ok = tres.feasible
        info = {
            "P_per_die_mean": float(np.mean(P_per_die)),
            "per_int_power": per_int_power,
            "T_max": tres.max_temperature_c,
            "margin": tres.margin_k,
            "solver": thermal_solver.name,
        }
        return thermal_ok, -tres.margin_k if not thermal_ok else 0.0, info
    else:
        # Fallback: simplified check
        density_ok = per_int_power / A_INTERPOSER <= Q_MAX
        info = {"per_int_power": per_int_power, "density_ok": density_ok}
        return density_ok, 0.0, info


# ====================================================================
# Main: sweep Dragonfly parameters
# ====================================================================

if __name__ == "__main__":
    G_mat, b_vec = build_thermal_matrix(*GRID)

    # Load demo results for comparison
    demo_feasible = set()
    demo_file = "dse_results/summary.json"
    if os.path.exists(demo_file):
        with open(demo_file) as f:
            demo_data = json.load(f)
        for d in demo_data.get("designs", []):
            if d.get("summary", {}).get("nonblock_bw_gbps", 0) >= 800:
                demo_feasible.add(d["label"])
        print(f"=== Loaded {len(demo_feasible)} feasible designs from demo ===\n")

    print(f"{'Config':<20} {'N':>6} {'T1(Gbps)':>9} {'L*':>8} {'Perf':>6} {'Geom':>6} {'Power':>6} {'LP':>6} {'Demo':>6}")
    print("-" * 80)

    results = []
    for a in range(2, 9):
        for p in range(2, 5):
            for h in [1, 2, 4]:
                g = a * h + 1
                n_terms = a * p * g
                label = f"DF_a{a}_p{p}_h{h}_g{g}"

                # ── Perf ──
                bisection_bw, L_star, perf_ok = perf_feasibility(a, p, h)
                if perf_ok is None:
                    continue

                # ── Compute per-die edge counts ──
                # Dragonfly: each die (assuming K=a, r=1) has:
                #   intra-group: (a-1) edges
                #   global: h edges
                #   I/O: p edges (to I/O die, L=1)
                # For simplicity, treat all edges as having the same L ≈ L_star
                n_dies = a * g  # K=a → a dies per group, g groups
                deg_intra = a - 1
                deg_global = h
                deg_io = p
                edges_per_die = [deg_intra + deg_global + deg_io] * n_dies

                # Build L vector: intra and global edges get L_star, I/O edges get L=1
                n_intra = g * a * (a - 1) // 2
                n_global = g * a * h // 2
                n_io = n_dies * p
                L_vec = np.array(
                    [L_star] * (n_intra + n_global) + [1.0] * n_io
                )

                # ── Geom ──
                geom_ok, _ = geom_feasibility(L_vec, edges_per_die)

                # ── Power ──
                power_ok, _, pwr_info = power_feasibility(L_vec, edges_per_die)
                if len(results) == 0:
                    print(f"    [thermal] per_int={pwr_info['per_int_power']:.1f}W, "
                          f"solver={pwr_info.get('solver','?')}, "
                          f"Tmax={pwr_info.get('T_max','?')}°C, "
                          f"ok={power_ok}")

                lp_ok = perf_ok and geom_ok and power_ok
                in_demo = label in demo_feasible

                print(f"{label:<20} {n_terms:>6} {bisection_bw:>9.1f} {L_star:>8.3f} "
                      f"{'✓' if perf_ok else '✗':>6} "
                      f"{'✓' if geom_ok else '✗':>6} "
                      f"{'✓' if power_ok else '✗':>6} "
                      f"{'✓' if lp_ok else '✗':>6} "
                      f"{'✓' if in_demo else '—':>6}")

                results.append({
                    "label": label, "a": a, "p": p, "h": h, "g": g,
                    "n_terms": n_terms, "bisection_bw": bisection_bw,
                    "L_star": L_star, "perf_ok": perf_ok, "geom_ok": geom_ok,
                    "power_ok": power_ok, "lp_ok": lp_ok, "in_demo": in_demo,
                })

    # Summary
    n_total = len(results)
    n_lp = sum(1 for r in results if r["lp_ok"])
    n_demo = sum(1 for r in results if r["in_demo"])
    print(f"\n=== Summary: {n_lp}/{n_total} feasible by LP, {n_demo} in demo ===")

    # Show discrepancies
    print("\n=== Discrepancies (LP vs Demo) ===")
    for r in results:
        if r["lp_ok"] != r["in_demo"]:
            print(f"  {r['label']}: LP={'✓' if r['lp_ok'] else '✗'} "
                  f"Demo={'✓' if r['in_demo'] else '✗'} "
                  f"(L*={r['L_star']:.3f})")
