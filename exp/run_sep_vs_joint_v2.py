#!/usr/bin/env python3
"""E3B v2：布线/面积版分离决策基线 vs 联合模型（V5 v5.21 双阶段）.

联合模型:  perf+bump+therm+wiring+area（单一 LP 联立，含 x_D2D 布线路径优化）。
分离基线: 性能包络定 L* → 独立判 bump / 热 / 布线 / 面积 → 简单交集（min）。
判据（model-ruling §六 / experiment-design §2 E3B v2）:
  C3': ≥2 构型 rel_diff > 0.01（1% 阈值）——分歧成立
  C4': ≥1 构型 B*_joint 绑定族含 route_*/area_*（布线饱和/面积抢占先于 bump/therm）
  C5': 分歧构型机制归因（本脚本输出绑定族，账本归因在报告阶段）
口径: 分离因素用同一批模型子集（bump/therm/wiring/area 各自独立 BmaxQuery；
      wiring 因素保留路径优化自由度——固定候选路径变体需 src 支持，见报告注）。

用法: PYTHONPATH=src python3 exp/run_sep_vs_joint_v2.py [params_name]
输出: exp/output/sep_vs_joint_v2_<params>.csv
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
from topology import (
    DragonflyTopology, FullMeshTopology, KaryNCubeTopology,
    MeshTopology, TorusTopology,
)
from layout import place

PARAMS = {"ucie-32g": UCIE_32G}
TOPOS = {
    "Mesh(2)": MeshTopology(2), "Mesh(3)": MeshTopology(3),
    "Torus(2)": TorusTopology(2), "Torus(3)": TorusTopology(3),
    "KaryNCube(2,3)": KaryNCubeTopology(2, 3),
    "FullMesh(2)": FullMeshTopology(2, 1), "FullMesh(3)": FullMeshTopology(3, 1),
    "Dragonfly(2,1,1)": DragonflyTopology(2, 1, 1),
    "Dragonfly(2,2,1)": DragonflyTopology(2, 2, 1),
}
ALPHA_GRID = [0.0, 0.001, 0.01, 0.05]   # mm/Gbps（面积绑定触发档；0.05 → A_max=1600 闭式上界 560）
LO, HI, STEP = 100.0, 50000.0, 200.0
DIVERGE_RATIO = 0.01  # C3'
# 参数域：default（ucie-32g 原样）vs wiring_tight（lanes_per_mm 收紧，布线饱和触发）
DOMAINS = {
    "default": None,                          # ucie-32g 原样（lanes_per_mm=500）
    "lanes100": 100.0,                        # 布线收紧 5×（CodeEngineer 实测分歧域）
}
SEP_WIRING_OPTIMIZE, SEP_WIRING_FIXED = "optimize", "fixed"


def _apply_domain(P0, domain):
    lanes = DOMAINS.get(domain)
    if lanes is not None:
        return dataclasses.replace(P0, pkg=dataclasses.replace(P0.pkg, lanes_per_mm=lanes))
    return P0


def _build_fixed_wiring(topo, P, layout):
    """分离基线布线因素：固定候选路径版 WiringModel（fixed_paths=True）.

    CodeEngineer 公开 helper（git ed15196，test19 §6 锚定）：与联合 optimize 版
    同一拓扑/参数/网格，仅路径模式不同（首路径直连、无 x 变量），cache_key 区分。
    """
    from problem.builder import build_wiring_fixed
    return build_wiring_fixed(topo, P, layout)


def _subsets(models):
    """按模型类型分因素子集：[perf, bump] / [perf, therm] / [perf, wiring] / [perf, area]."""
    perf = [m for m in models if type(m).__name__ == "ObliviousValiantModel"]
    bump = [m for m in models if type(m).__name__ == "BumpModel"]
    therm = [m for m in models if type(m).__name__ == "SteadyStateModel"]
    wiring = [m for m in models if type(m).__name__ == "WiringModel"]
    area = [m for m in models if type(m).__name__ == "DieAreaModel"]
    return {
        "bump": perf + bump, "therm": perf + therm,
        "wiring": perf + wiring, "area": perf + area,
    }


def _binding_families(ctx, models, B):
    """min-ΣL 解出 B 处绑定约束族（route_*/area_* 识别）。"""
    try:
        c2 = Ctx()
        for m in models:
            m.build(c2, float(B))
        sol = CvxSolver().solve(c2, objective=sum(c2["L"]), maximize=False)
        duals = list(sol.duals.keys()) if sol.duals else []
        fam: dict[str, int] = {}
        for name in duals:
            prefix = name.split("_")[0]
            fam[prefix] = fam.get(prefix, 0) + 1
        return fam
    except Exception:
        return {}


def _bounded_bmax(bmax, runner, models, lo, hi, step):
    """有界 BmaxQuery：若 hi 处仍可行（因素在搜索范围内不绑定）→ 记 inf。

    BmaxQuery 的 hi 翻倍循环在"恒可行因素"（如 α_d=0 的面积约束）上永不终止，
    故先判 hi 可行性；可行 → 该因素在 [lo, hi] 内非绑定（语义同 v1 几何=inf）。
    """
    ok = runner.solve("feasibility", float(hi), Ctx(), models).status in (
        "optimal", "optimal_inaccurate")
    if ok:
        return float("inf")
    return bmax.solve(runner, lambda b: (Ctx(), models),
                      lo=lo, hi=hi, step=step).B_star


def main() -> None:
    argv = list(sys.argv[1:])
    params_name = argv[0] if argv else "ucie-32g"
    rest = argv[1:]
    domain = "default"
    if rest and rest[0] in DOMAINS:
        domain = rest[0]
        rest = rest[1:]
    sep_wiring = SEP_WIRING_OPTIMIZE
    if rest and rest[0] in (SEP_WIRING_OPTIMIZE, SEP_WIRING_FIXED):
        sep_wiring = rest[0]
        rest = rest[1:]
    names = rest or list(TOPOS)          # 可选：指定拓扑子集（分块跑）
    P0 = _apply_domain(PARAMS[params_name], domain)
    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)
    bmax = BmaxQuery()
    rows = []

    for name in names:
        topo = TOPOS[name]
        layout = place(topo, P0)
        for ad in ALPHA_GRID:
            P = dataclasses.replace(P0, die=dataclasses.replace(P0.die, alpha_d=ad))
            models, _ = build_scenario(topo, "perf+bump+therm+wiring+area", P, layout)
            subsets = _subsets(models)
            # 分离布线因素：fixed_paths 版（首路径固定，无 x 优化）替换 optimize 版
            if sep_wiring == SEP_WIRING_FIXED and subsets["wiring"]:
                perf = [m for m in subsets["wiring"]
                        if type(m).__name__ == "ObliviousValiantModel"]
                w_fixed = _build_fixed_wiring(topo, P, layout)
                subsets["wiring"] = perf + [w_fixed]
            runner = Runner(CvxSolver(), store=ResultStore(out_dir / ".cache"), log=False)

            B_joint = _bounded_bmax(bmax, runner, models, LO, HI, STEP)
            vals = {}
            for fname, fmodels in subsets.items():
                if not fmodels or len(fmodels) == 1:
                    vals[fname] = float("inf")
                    continue
                vals[fname] = _bounded_bmax(bmax, runner, fmodels, LO, HI, STEP)
            B_sep = min(vals.values())
            if B_joint == float("inf") and B_sep == float("inf"):
                rel = 0.0                     # 联合/分离均超出搜索范围 → 一致
            elif B_joint == float("inf"):
                rel = float("inf")            # 联合无界而分离有界 → 极端分歧
            else:
                rel = abs(B_sep - B_joint) / B_joint
            fam = _binding_families(Ctx(), models,
                                    HI if B_joint == float("inf") else B_joint)
            rows.append({
                "topo": name, "domain": domain, "sep_wiring": sep_wiring,
                "alpha_d": ad,
                "B_joint": f"{B_joint:.0f}",
                "B_bump_sep": f"{vals['bump']:.0f}",
                "B_therm_sep": f"{vals['therm']:.0f}",
                "B_wiring_sep": f"{vals['wiring']:.0f}",
                "B_area_sep": f"{vals['area']:.0f}",
                "B_sep": f"{B_sep:.0f}",
                "rel_diff": f"{rel:.4f}",
                "divergent(>1%)": rel > DIVERGE_RATIO,
                "joint_binding_families": ";".join(
                    f"{k}:{v}" for k, v in sorted(fam.items())) or "-",
            })
            print(f"{name:<18} α={ad}: joint={B_joint:>9.0f} sep={B_sep:>9.0f} "
                  f"rel={rel:.4f} {'⚠️DIVERGE' if rel > DIVERGE_RATIO else '一致'} "
                  f"bind={sorted(fam)}")

    tag = "fixedpath_" if sep_wiring == SEP_WIRING_FIXED else ""
    out = out_dir / f"sep_vs_joint_v2_{tag}{params_name}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n_div = sum(1 for r in rows if r["divergent(>1%)"])
    n_c4 = sum(1 for r in rows if "route" in r["joint_binding_families"]
               or "area" in r["joint_binding_families"])
    print(f"\nCSV → {out}  ({len(rows)} rows; 分歧 {n_div}; route/area 绑定 {n_c4})")


if __name__ == "__main__":
    main()
