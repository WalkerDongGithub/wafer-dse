"""wafer-dse CLI —— 读 YAML 配置 → 组装模型 → 求解 → 输出结果文档.

用法:
    python src/main.py config/problems/<problem>.yaml

配置文件分工（config/ 目录）:
  params/*.yaml   物理参数（实验设置，可复用）—— ExpParams 的 YAML 化
  problems/*.yaml 问题定义（实验实例）—— 引用 params + 拓扑 + 场景 + query

流程:
  load_problem → ExpParams + 拓扑 + 场景 + query
  place → build_scenario → BmaxQuery/FeasibilityQuery
  → 结果表 + 约束账本（控制台）+ CSV（exp/output/）
"""

from __future__ import annotations

import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

from problem import Ctx, CvxSolver, Runner, ResultStore
from problem.builder import build_scenario
from problem.queries import BmaxQuery, FeasibilityQuery
from layout import place
from physical.params import ExpParams
from diagnostics import solve_diagnostic, full_ledger, print_ledger
from topology import MeshTopology, TorusTopology, KaryNCubeTopology, FullMeshTopology, DragonflyTopology

# ── 拓扑注册表（CLI 编排层的映射，不属于模型层） ───────────────────
_TOPOS = {
    "mesh": MeshTopology,
    "torus": TorusTopology,
    "kary_ncube": KaryNCubeTopology,
    "fullmesh": FullMeshTopology,
    "dragonfly": DragonflyTopology,
}

_SCENARIOS = {"perf", "perf+bump", "perf+bump+therm"}



@dataclass(frozen=True)
class ProblemSpec:
    """一个问题定义（实验实例）的完整输入."""
    params_path: Path
    params: ExpParams
    topo_type: str
    topo_args: list
    scenario: str

    query_type: str
    query_lo: float
    query_hi: float
    query_step: float


def load_problem(path: str | Path) -> ProblemSpec:
    """读问题定义 YAML（含引用的 params 文件），校验后返回 ProblemSpec."""
    p = Path(path)
    d = yaml.safe_load(p.read_text(encoding="utf-8"))

    params_path = Path(d.get("params", ""))
    if not params_path.is_file():
        raise FileNotFoundError(f"params 文件不存在: {params_path}")
    P = ExpParams.from_dict(
        yaml.safe_load(params_path.read_text(encoding="utf-8")))

    topo = d.get("topo", {})
    topo_type = topo.get("type", "")
    if topo_type not in _TOPOS:
        raise ValueError(f"未知拓扑 '{topo_type}'，可选: {sorted(_TOPOS)}")
    topo_args = topo.get("args", [])

    scenario = d.get("scenario", "")
    if scenario not in _SCENARIOS:
        raise ValueError(f"未知场景 '{scenario}'，可选: {sorted(_SCENARIOS)}")


    q = d.get("query", {})
    query_type = q.get("type", "bmax")
    if query_type not in ("bmax", "feasibility"):
        raise ValueError(f"未知 query '{query_type}'，可选: bmax | feasibility")

    return ProblemSpec(
        params_path=params_path, params=P,
        topo_type=topo_type, topo_args=topo_args,
        scenario=scenario,
        query_type=query_type,
        query_lo=float(q.get("lo", 100.0)),
        query_hi=float(q.get("hi", 10000.0)),
        query_step=float(q.get("step", 50.0)),
    )


def solve_problem(spec: ProblemSpec) -> dict:
    """组装 + 求解 + 诊断。返回结果 dict（含 B*、账本）。"""
    topo = _TOPOS[spec.topo_type](*spec.topo_args)
    layout = place(topo, spec.params)
    models, meta = build_scenario(topo, spec.scenario, spec.params, layout)

    store_dir = Path(__file__).resolve().parent.parent / "exp" / "output" / ".cache"
    runner = Runner(CvxSolver(), store=ResultStore(store_dir), log=False)
    if spec.query_type == "bmax":
        r = BmaxQuery().solve(runner, lambda b: (Ctx(), models),
                              lo=spec.query_lo, hi=spec.query_hi,
                              step=spec.query_step)
        B_star, iters = r.B_star, r.iterations
    else:
        sol = runner.solve(FeasibilityQuery.query_id, spec.query_lo,
                           Ctx(), models)
        fr = FeasibilityQuery().interpret(sol, Ctx(), spec.query_lo)
        B_star, iters = (spec.query_lo if fr.feasible else 0.0), 1

    # B* 处诊断（min ΣL 解，绑定约束可靠）
    ledger = {}
    if B_star > 0:
        diag = solve_diagnostic(models, B_star)
        ledger = full_ledger(models, diag.L_star, B_star)

    return {
        "B_star": B_star, "iterations": iters,
        "topo": f"{spec.topo_type}{spec.topo_args}",
        "scenario": spec.scenario, "params": spec.params.name,
        "n_terminals": topo.n_terminals, "n_links": topo.n_links,
        "n_dies": meta["n_dies"],
        "ledger": ledger,
    }


def main(argv: list[str] | None = None) -> int:
    if not argv or len(argv) != 1:
        print("用法: python src/main.py config/problems/<problem>.yaml")
        return 1

    t0 = time.perf_counter()
    spec = load_problem(argv[0])
    print(f"参数组: {spec.params.name}  "
          f"({spec.params.link.name} {spec.params.link.pj_per_bit:.3f} pJ/bit, "
          f"{spec.params.bump.name})")
    print(f"拓扑: {spec.topo_type}{spec.topo_args}  "
          f"场景: {spec.scenario}  query: {spec.query_type}")
    print()

    r = solve_problem(spec)
    elapsed = time.perf_counter() - t0

    if spec.query_type == "bmax":
        print(f"B* = {r['B_star']:.0f} Gbps/端口  "
              f"({r['iterations']} 次 LP, {elapsed:.1f}s)")
    else:
        print(f"B = {r['B_star']:.0f} Gbps: {'可行' if r['B_star'] > 0 else '不可行'}")
    print_ledger(r["ledger"], r["B_star"])

    # CSV 输出
    out_dir = Path(__file__).resolve().parent.parent / "exp" / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{Path(spec.params_path.name).stem}_{spec.topo_type}.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["params", "topo", "scenario", "B_star", "iterations",
                    "n_terminals", "n_links", "n_dies"])
        w.writerow([r["params"], r["topo"], r["scenario"],
                    f"{r['B_star']:.0f}", r["iterations"],
                    r["n_terminals"], r["n_links"], r["n_dies"]])
    print(f"\nCSV → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
