"""晶圆级交换机 DSE — 统一 LP 驱动。

用法:
    python -m wafer_dse --config configs/example_lp.yaml
    python -m wafer_dse --topology dragonfly --a 4 --p 4 --h 2
"""

from __future__ import annotations

import argparse
from pathlib import Path

from wafer_dse.config import load_config
from wafer_dse.models import Requirement, Strictness, TopologySpec
from wafer_dse.lp import UnifiedLp
from wafer_dse.lp.report import LpResult
from wafer_dse.lp.geometry import DieConfig
from wafer_dse.lp.thermal import ThermalConfig
from wafer_dse.physical.bump.bump import UBUMP_45UM
from wafer_dse.physical.thermal._cooling import (
    AIR_COOLING,
    IMMERSION,
    LIQUID_COOLING,
    MICROFLUIDIC,
)

from wafer_dse.architecture_model.topology import (
    Dragonfly,
    KaryNCube,
    Mesh,
    Torus,
)

COOLING_MAP = {
    "Air": AIR_COOLING,
    "Liquid": LIQUID_COOLING,
    "Immersion": IMMERSION,
    "Microfluidic": MICROFLUIDIC,
}


# ============================================================================
# 拓扑构建
# ============================================================================


def _build_topo(spec: TopologySpec):
    """TopologySpec → 具体拓扑实例。"""
    kind = spec.kind
    if kind == "mesh":
        return Mesh(int(spec.size))
    if kind == "torus":
        return Torus(int(spec.size))
    if kind == "dragonfly":
        return Dragonfly(
            a=int(spec.a or 4),
            p=int(spec.p or 4),
            h=int(spec.h or 2),
        )
    if kind == "kary_ncube":
        k = int(spec.size or 4)
        n = int(spec.n or 2)
        wrap = bool(spec.wrap if spec.wrap is not None else True)
        return KaryNCube(k=k, n=n, wrap=wrap)
    raise ValueError(f"未知拓扑类型: {kind!r}")


# ============================================================================
# 配置解析
# ============================================================================


def parse_requirement(cfg: dict) -> Requirement:
    r = cfg.get("requirement", {})
    s = r.get("strictness", {})
    return Requirement(
        target_nonblocking_gbps_per_port=float(
            r.get("target_nonblocking_gbps_per_port", 800)
        ),
        max_power_w=float(r.get("max_power_w", 200)),
        strictness=Strictness(
            mode=s.get("mode", "full"),
            percent=s.get("percent"),
            benchmark=s.get("benchmark"),
        ),
        packaging_config=str(r.get("packaging_config", "")),
        port_count=r.get("port_count"),
        max_die_area_mm2=r.get("max_die_area_mm2"),
    )


def parse_topologies(cfg: dict) -> list[TopologySpec]:
    specs: list[TopologySpec] = []
    tops = cfg.get("topologies", {})
    items = tops.values() if isinstance(tops, dict) else tops
    for item in items:
        for route in item.get("routes", ["det"]):
            specs.append(TopologySpec(
                kind=item["kind"],
                size=item.get("size"),
                route=route,
                a=item.get("a"),
                p=item.get("p"),
                h=item.get("h"),
                n=item.get("n"),
                wrap=item.get("wrap"),
            ))
    return specs


# ============================================================================
# 主流程
# ============================================================================


def run_dse(
    topologies: list[TopologySpec],
    req: Requirement,
    die_cfg: DieConfig | None = None,
    thermal_cfg: ThermalConfig | None = None,
) -> list[LpResult]:
    """对每个拓扑运行统一 LP 评估。"""
    results: list[LpResult] = []

    for spec in topologies:
        print(f"\n{'─'*50}")
        print(f"  评估: {spec.kind}  route={spec.route}", end="")
        if spec.a:
            print(f"  a={spec.a} p={spec.p} h={spec.h}", end="")
        print()

        topo = _build_topo(spec)

        # 构建 LP
        lp = UnifiedLp(
            topo,
            route=spec.route,
            target_gbps=req.target_nonblocking_gbps_per_port,
        )

        if die_cfg:
            if hasattr(topo, "g"):
                n_groups = topo.g
            else:
                n_groups = 1
            die_configs = [
                DieConfig(label=f"die_{i}",
                          width_mm=die_cfg.width_mm,
                          height_mm=die_cfg.height_mm,
                          power_w=die_cfg.power_w)
                for i in range(n_groups)
            ]
            bump = UBUMP_45UM
            lp.add_geometry(die_configs, bump)

        if thermal_cfg:
            lp.add_thermal(thermal_cfg)

        result = lp.solve()
        results.append(result)

        # 简短输出
        status = "✓ FEASIBLE" if result.feasible else "✗ INFEASIBLE"
        print(f"  {status}  L*={result.worst_load:.3f}  "
              f"BW={result.nonblocking_gbps:.0f}Gbps  "
              f"solver={result.solver}")

        for cs in result.constraints:
            mark = "✓" if cs.satisfied else "✗"
            print(f"    {mark} {cs.name}: "
                  f"violation={cs.max_violation:+.4f}  "
                  f"slack={cs.max_slack:.4f}")

    return results


def print_summary(results: list[LpResult], topologies: list[TopologySpec]):
    """打印多设计点对比表。"""
    print(f"\n{'='*70}")
    print("  DSE 结果汇总")
    print(f"{'='*70}")
    header = (
        f"  {'feasible':8s}  {'topology':20s}  {'route':6s}  "
        f"{'L*':8s}  {'BW(Gbps)':10s}  {'solver':16s}"
    )
    print(header)
    print("  " + "-" * len(header))

    for spec, r in zip(topologies, results):
        if spec.a:
            name = f"DF_a{spec.a}_p{spec.p}_h{spec.h}"
        else:
            name = f"{spec.kind}{spec.size or ''}"
        feasible = "✓" if r.feasible else "✗"
        print(f"  {feasible:8s}  {name:20s}  {spec.route:6s}  "
              f"{r.worst_load:8.4f}  {r.nonblocking_gbps:10.1f}  "
              f"{r.solver:16s}")

    feasible_count = sum(1 for r in results if r.feasible)
    print(f"\n  {feasible_count}/{len(results)} designs feasible")
    print("=" * 70)


# ============================================================================
# CLI
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="晶圆级交换机 DSE — 统一 LP 驱动"
    )
    parser.add_argument(
        "--config", "-c", type=str,
        help="YAML/JSON 配置文件路径"
    )
    parser.add_argument(
        "--topology", "-t", type=str, default="dragonfly",
        help="拓扑类型 (dragonfly/mesh/torus/kary_ncube)"
    )
    parser.add_argument("--a", type=int, default=4, help="Dragonfly a")
    parser.add_argument("--p", type=int, default=4, help="Dragonfly p")
    parser.add_argument("--h", type=int, default=2, help="Dragonfly h")
    parser.add_argument("--size", type=int, default=4, help="Mesh/Torus size")
    parser.add_argument(
        "--route", type=str, default="det",
        help="路由策略 (det/valiant)"
    )
    parser.add_argument(
        "--target-gbps", type=float, default=800.0,
        help="端口目标带宽 (Gbps)"
    )
    parser.add_argument(
        "--die-width", type=float, default=12.0,
        help="Die 宽度 (mm)"
    )
    parser.add_argument(
        "--die-height", type=float, default=12.0,
        help="Die 高度 (mm)"
    )
    parser.add_argument(
        "--die-power", type=float, default=50.0,
        help="Die 功耗 (W)"
    )
    parser.add_argument(
        "--cooling", type=str, default="Liquid",
        choices=["Air", "Liquid", "Immersion", "Microfluidic"],
        help="冷却方案"
    )

    args = parser.parse_args()

    if args.config:
        cfg = load_config(args.config)
        req = parse_requirement(cfg)
        specs = parse_topologies(cfg)
        target_gbps = req.target_nonblocking_gbps_per_port
    else:
        target_gbps = args.target_gbps
        req = Requirement(
            target_nonblocking_gbps_per_port=target_gbps,
            max_power_w=500,
            strictness=Strictness(mode="full"),
        )
        specs = [TopologySpec(
            kind=args.topology,
            size=args.size,
            route=args.route,
            a=args.a,
            p=args.p,
            h=args.h,
        )]

    die_cfg = DieConfig(
        label="default",
        width_mm=args.die_width,
        height_mm=args.die_height,
        power_w=args.die_power,
    )

    thermal_cfg = ThermalConfig(
        total_area_mm2=858.0,
        interposer_count=1,
        cooling=COOLING_MAP.get(args.cooling, LIQUID_COOLING),
        target_gbps=target_gbps,
    )

    results = run_dse(specs, req, die_cfg, thermal_cfg)
    print_summary(results, specs)

    if results:
        print()
        print(results[0].report())

    return results


if __name__ == "__main__":
    main()
