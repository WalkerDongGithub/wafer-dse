#!/usr/bin/env python3
"""
晶圆级交换机 DSE 端到端原型。

用法:
    python scripts/dse_demo.py                        # 默认配置
    python scripts/dse_demo.py configs/my_config.yaml  # 自定义配置

输出: dse_results/DF_*.dse — 每个设计方案一份独立报告
"""

from __future__ import annotations

import sys, math, os

sys.path.insert(0, "src")

from wafer_dse.config import load_config
from wafer_dse.models import NetworkPotential
from wafer_dse.pareto import Metrics, compute_foms
from wafer_dse.physical.bump.bump import (
    DieBumpBudget, UBUMP_25UM, UBUMP_45UM, C4_130UM,
)
from wafer_dse.physical.interposer import Interposer
from wafer_dse.physical.substrate import Substrate
from wafer_dse.physical.thermal import (
    AIR_COOLING, LIQUID_COOLING, IMMERSION, MICROFLUIDIC,
    ThermalConfig, create_solver,
)
from wafer_dse.architecture_model.topology.dragonfly import Dragonfly
from wafer_dse.architecture_model.solver import create_solver as create_arch_solver
from wafer_dse.architecture_model.solver._potential import _PotentialSolver, PotentialConfig
from wafer_dse.trace import get_logger, SummaryWriter

console = get_logger("console")
OUTPUT_DIR = "dse_results"


# ============================================================================
# 配置加载
# ============================================================================

def load_dse_config(path: str | None = None) -> dict:
    """加载 DSE 配置，未指定则用默认。"""
    if path is None:
        path = "configs/dse_demo.yaml"
    return load_config(path)


COOLING_MAP = {
    "Air": AIR_COOLING, "Liquid": LIQUID_COOLING,
    "Immersion": IMMERSION, "Microfluidic": MICROFLUIDIC,
}
BUMP_MAP = {"25μm": UBUMP_25UM, "45μm": UBUMP_45UM}


# ============================================================================
# Phase 0
# ============================================================================

def build_physical(cfg: dict):
    bump_spec = BUMP_MAP[cfg["bump"]["ubump"]]
    c4_spec = C4_130UM
    d = cfg["die"]
    inter = cfg["interposer"]
    sub = cfg["substrate"]

    die = DieBumpBudget(die_label="switch_die", spec=bump_spec,
                        width_mm=d["width_mm"], height_mm=d["height_mm"],
                        power_w=d["power_w"], vdd_v=d["vdd_v"])
    interposers = [
        Interposer(label=f"Interposer_{i}", dies=[die] * inter["dies_per"],
                   area_mm2=inter["area_mm2"])
        for i in range(inter["count"])
    ]
    substrate = Substrate(interposers=interposers,
                          grid_rows=sub["grid_rows"], grid_cols=sub["grid_cols"])
    return die, interposers, substrate


# ============================================================================
# Phase 1: Topology
# ============================================================================

def topology_check(a, p, h, target_bw, log) -> NetworkPotential | None:
    g = a * h + 1
    n_terms = g * a * p
    local_bw = (a - 1) * target_bw / 2
    global_bw = h * target_bw / 2
    bisection_bw = min(local_bw, global_bw)

    log.constraint_table("Topology", [
        ("kind", "Dragonfly", "—", "—"),
        ("a / p / h", f"{a} / {p} / {h}", "—", "—"),
        ("groups (g)", str(g), "—", "—"),
        ("terminals", str(n_terms), "—", "—"),
    ])

    # ── 三层无阻塞验证 ──
    # T1: 二分带宽 (最粗)
    t1_ok = bisection_bw >= target_bw

    # T2: 对抗性精确验证 (det + Hungarian, N≤100)
    t2_bw = None
    if n_terms <= 100:
        try:
            r = create_arch_solver("det").solve(
                Dragonfly(a=a, p=p, h=h), "det", target_bw)
            t2_bw = r.nonblocking_gbps_per_port
        except Exception:
            pass
    t2_ok = (t2_bw >= target_bw) if t2_bw else None

    # T3: 统计带宽 — 随机排列×valiant (N>100 跳过, 太慢)
    import random
    t3_bw = None
    if n_terms <= 100:
        try:
            df_t = Dragonfly(a=a, p=p, h=h)
            terms = df_t.terminals()
            bws = []
            for _ in range(50):
                dsts = list(terms)
                while True:
                    random.shuffle(dsts)
                    if all(s != d for s, d in zip(terms, dsts)):
                        break
                link_load = {}
                for s, d in zip(terms, dsts):
                    paths = df_t.valiant(s, d)
                    if not paths:
                        continue
                    per = 1.0 / len(paths)
                    for path in paths:
                        for k in range(len(path) - 1):
                            lk = (path[k], path[k + 1])
                            link_load[lk] = link_load.get(lk, 0.0) + per
                ml = max(link_load.values()) if link_load else 1.0
                bws.append(target_bw / ml if ml > 0 else float("inf"))
            bws.sort()
            t3_bw = bws[max(0, len(bws) * 10 // 100)]  # p10
        except Exception:
            pass
    t3_ok = (t3_bw is not None and t3_bw >= target_bw)

    def status(bw, ok, method):
        if ok is None:
            return "—", "—"
        if ok:
            return f"{bw:.0f}", f"✓ ({method})"
        return f"{bw:.0f}", f"✗ ({method})"

    t1_val, t1_st = status(bisection_bw, t1_ok, "bisection")
    t2_val, t2_st = status(t2_bw, t2_ok, "Hungarian det") if t2_bw else ("N/A", "N/A>64")
    t3_val = f"{t3_bw:.0f}" if t3_bw else "N/A"
    t3_st = "✓ (rand val)" if t3_ok else (f"✗ ({t3_bw:.0f})" if t3_bw else "N/A")

    log.constraint_table("Nonblocking (target={:.0f}Gbps)".format(target_bw), [
        ("T1 bisection", t1_val, "Gbps", t1_st),
        ("T2 adversarial", t2_val, "Gbps", t2_st),
        ("T3 statistical", t3_val, "Gbps", t3_st),
    ])

    # DSE 通过标准: T1 必须过，T2/T3 参考
    if not t1_ok:
        return None, None, None
    return NetworkPotential(
        topology_name=f"dragonfly_a{a}_p{p}_h{h}", route="MIN",
        terminal_count=n_terms,
        directed_link_count=g * a * (a - 1 + h),
        nonblocking_gbps_per_port=bisection_bw,
        required_internal_speedup=1, required_internal_800g_links=0,
        certificate_status="approximate", worst_link="",
        notes=f"T2={t2_bw or 'N/A'} T3={t3_bw or 'N/A'}",
    ), t2_bw, t3_bw  # return extra data for summary


# ============================================================================
# Phase 2: Physical
# ============================================================================

def physical_check(a, p, h, target_bw, die, interposers, sub, log):
    from wafer_dse.physical.interconnect import get_profile

    ucie = get_profile("UCIe-32G-Advanced")
    serdes = get_profile("SerDes-112G-MR")
    g = a * h + 1
    lanes_per = math.ceil(target_bw / ucie.lane_rate_gbps)
    serdes_per = math.ceil(target_bw / serdes.lane_rate_gbps)

    term_l = p * lanes_per
    intra_l = (a - 1) * lanes_per
    global_l = h * serdes_per
    total_l = term_l + intra_l + global_l
    bump_ok = total_l <= die.available

    log.constraint_table("Physical — μbump", [
        ("pitch", f"{die.spec.pitch_um}", "μm", "—"),
        ("die size", f"{die.width_mm}×{die.height_mm}", "mm", "—"),
        ("die area", f"{die.area_mm2:.0f}", "mm²", "—"),
        ("total bumps", f"{die.total_bumps}",
         f"({die.area_mm2:.0f}mm² × {die.spec.density_per_mm2:.0f}/mm² × {die.utilization:.0%})", "—"),
        ("  └ power", f"-{die.power_bumps}",
         f"({die.power_w}W / {die.vdd_v}V = {die.power_w/die.vdd_v:.1f}A → {die.power_bumps} bumps)", "—"),
        ("  = available", str(die.available), "signal bumps", "—"),
        ("", "", "", ""),
        ("required lanes", str(total_l), "lanes", "—"),
        ("  └ terminal", f"{term_l} ({p} ports × {lanes_per} lanes/{target_bw:.0f}G)", "lanes", "—"),
        ("  └ intra", f"{intra_l} ({a-1} edges × {lanes_per} lanes/{target_bw:.0f}G)", "lanes", "—"),
        ("  └ global", f"{global_l} ({h} ports × {serdes_per} SerDes/{target_bw:.0f}G)", "lanes", "—"),
        ("margin", f"{die.available - total_l}", "bumps", "—"),
        ("feasible", "YES" if bump_ok else "NO", "", "✓" if bump_ok else "✗"),
    ])

    if not bump_ok:
        return None, None

    intra_edges = a * (a - 1) // 2
    intra = interposers[0].route_intra(intra_edge_count=intra_edges,
                                        bandwidth_gbps=target_bw)
    log.constraint_table("Physical — Interposer", [
        ("intra edges", str(intra_edges), "—", "—"),
        ("standard", ucie.name, "—", "—"),
        ("total power", f"{intra.total_power_w:.2f}", "W", "—"),
        ("feasible", "YES" if intra.feasible else "NO",
         "", "✓" if intra.feasible else "✗"),
    ])
    if not intra.feasible:
        return intra, None

    global_edges = g * (h * a) // 2
    gbl = sub.route_global(global_edge_count=global_edges,
                           bandwidth_gbps=target_bw)
    log.constraint_table("Physical — Substrate", [
        ("global edges", str(global_edges), "—", "—"),
        ("standard", serdes.name, "—", "—"),
        ("max distance", f"{sub.max_distance_mm:.0f}", "mm", "—"),
        ("C4 available", f"{sub.c4_budget.available:,}", "bumps", "—"),
        ("total power", f"{gbl.total_power_w:.2f}", "W", "—"),
        ("feasible", "YES" if gbl.feasible else "NO",
         "", "✓" if gbl.feasible else "✗"),
    ])
    return intra, gbl


# ============================================================================
# Main
# ============================================================================

def main(config_path: str | None = None):
    cfg = load_dse_config(config_path)
    cooling = COOLING_MAP[cfg["requirement"]["cooling"]]
    target_bw = cfg["requirement"]["target_bw_gbps"]
    die_size = (cfg["die"]["width_mm"], cfg["die"]["height_mm"])
    interposer_area = cfg["interposer"]["area_mm2"]
    interposer_count = cfg["interposer"]["count"]
    substrate_grid = (cfg["substrate"]["grid_rows"], cfg["substrate"]["grid_cols"])
    search = cfg["search"]

    die, interposers, sub = build_physical(cfg)
    thermal_solver = create_solver("auto")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary = SummaryWriter(OUTPUT_DIR)
    summary.set_config(cfg)

    console.section("Wafer-DSE: Dragonfly Enumeration")
    console.info(f"config={config_path or 'default'}  "
                 f"target={target_bw}Gbps  cooling={cooling.name}  "
                 f"μbump={die.spec.name}  interposers={interposer_count}×{interposer_area:.0f}mm²  "
                 f"dies={cfg['interposer']['dies_per']}×{die_size[0]}mm  "
                 f"substrate={substrate_grid}")

    calib = ThermalConfig(
        die_width_mm=die_size[0], die_height_mm=die_size[1],
        die_count=4, die_power_w=cfg["die"]["power_w"] / 2,
        interposer_area_mm2=interposer_area,
        interposer_count=interposer_count, cooling=cooling,
    )
    thermal_solver.calibrate(calib)
    if thermal_solver.r_eff is not None:
        console.info(f"Thermal: {thermal_solver.name}  "
                     f"R_eff={thermal_solver.r_eff:.4f} K/W")
    else:
        console.info(f"Thermal: {thermal_solver.name} (no MFIT — power-density fallback)")

    results: list[Metrics] = []
    total, feasible = 0, 0

    for a in range(search["a_min"], search["a_max"] + 1):
        for p in range(search["p_min"], search["p_max"] + 1):
            for h in search["h_values"]:
                g = a * h + 1
                total += 1
                label = f"DF_a{a}_p{p}_h{h}_g{g}"
                log = get_logger("report", output_dir=OUTPUT_DIR)
                log.start_design(label)

                net, t2, t3 = topology_check(a, p, h, target_bw, log)
                if net is None:
                    log.finish_design()
                    continue

                intra, gbl = physical_check(a, p, h, target_bw, die,
                                            interposers, sub, log)
                if intra is None or gbl is None or not gbl.feasible:
                    log.finish_design()
                    continue

                total_power = intra.total_power_w + gbl.total_power_w
                total_power += g * a * cfg["die"]["power_w"]
                per_int_power = total_power / interposer_count

                thermal_ok, tmax, margin = True, 0.0, 0.0
                if thermal_solver.is_calibrated and thermal_solver.r_eff is not None:
                    tres = thermal_solver.solve_uniform(per_int_power)
                    thermal_ok, tmax, margin = (
                        tres.feasible, tres.max_temperature_c, tres.margin_k)
                else:
                    tres = create_solver("simple").solve(
                        ThermalConfig(
                            die_power_w=per_int_power,
                            interposer_area_mm2=interposer_area,
                            interposer_count=interposer_count,
                            cooling=cooling))
                    thermal_ok, tmax, margin = (
                        tres.feasible, tres.max_temperature_c, tres.margin_k)

                r_eff_val = thermal_solver.r_eff
                log.constraint_table("Thermal", [
                    ("cooling", cooling.name, "—", "—"),
                    ("R_eff", f"{r_eff_val:.4f}"
                     if r_eff_val else "N/A", "K/W", "—"),
                    ("power/interposer", f"{per_int_power:.1f}", "W", "—"),
                    ("Tmax", f"{tmax:.1f}", "°C", "—"),
                    ("Tjunc max", "85.0", "°C", "—"),
                    ("margin", f"{margin:.1f}", "K", "—"),
                    ("feasible", "YES" if thermal_ok else "NO",
                     "", "✓" if thermal_ok else "✗"),
                ])

                if not thermal_ok:
                    log.finish_design()
                    continue

                feasible += 1
                perf = net.nonblocking_gbps_per_port
                cost = (g * cfg["interposer"]["dies_per"]
                        * die.area_mm2 * die.spec.pitch_um / 1000
                        + g * cfg["interposer"]["dies_per"] * 10)

                log.constraint_table("Summary", [
                    ("total power", f"{total_power:.1f}", "W", "—"),
                    ("cost index", f"{cost:.0f}", "—", "—"),
                    ("nonblock BW", f"{perf:.0f}", "Gbps", "—"),
                ])

                results.append(Metrics(perf=perf, cost=cost, power=total_power,
                                       plan=None, label=label))

                # machine-readable record
                summary.add({
                    "label": label,
                    "topology": {"a": a, "p": p, "h": h, "g": g,
                                 "terminals": net.terminal_count},
                    "architecture": {"route": "MIN",
                                     "T1_bisection_gbps": min((a-1)*target_bw/2, h*target_bw/2),
                                     "T2_adversarial_gbps": t2,
                                     "T3_statistical_gbps": t3},
                    "ubump": {"pitch_um": die.spec.pitch_um,
                              "total": die.total_bumps,
                              "power_bumps": die.power_bumps,
                              "available": die.available,
                              "required_lanes": g * a * (a - 1 + h),  # rough
                              "feasible": True},
                    "interposer": {"intra_edges": a*(a-1)//2,
                                   "power_w": intra.total_power_w,
                                   "feasible": intra.feasible},
                    "substrate": {"global_edges": g*(h*a)//2,
                                  "power_w": gbl.total_power_w,
                                  "feasible": gbl.feasible},
                    "thermal": {"cooling": cooling.name,
                                "r_eff": thermal_solver.r_eff,
                                "power_per_interposer_w": per_int_power,
                                "tmax_c": tmax, "margin_k": margin,
                                "feasible": thermal_ok},
                    "summary": {"total_power_w": total_power,
                                "cost_index": cost,
                                "nonblock_bw_gbps": perf},
                })

                log.finish_design()
                console.info(f"  ✓ {label}")

    console.result(total, feasible, 0)

    if results:
        foms = compute_foms(results)
        frontier = [f for f in foms if f.on_frontier]
        headers = ["Config", "BW(Gbps)", "Cost", "Power(W)", "FOM"]
        rows = [[m.label + (" *" if f.on_frontier else ""),
                 f"{m.perf:.0f}", f"{m.cost:.0f}",
                 f"{m.power:.0f}", f"{f.bw_per_area_power*1000:.4f}"]
                for f, m in [(f, f.metrics) for f in foms[:10]]]
        console.table(headers, rows)
        console.info(f"{len(frontier)} on Pareto frontier, "
                     f"{feasible} feasible")
        console.info(f"Reports: {OUTPUT_DIR}/DF_*.dse  "
                     f"JSON: {summary.dump()}")


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(config_path)
