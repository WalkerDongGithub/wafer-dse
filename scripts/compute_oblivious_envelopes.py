"""compute_oblivious_envelopes —— 对所有拓扑从小到大算 oblivious L 包络并缓存。

对每个拓扑，用 ObliviousValiantModel 预解 L*（V5 §7.3 子 LP），
结果写入 cache/oblivious_envelopes.json，并打印汇总表。

用法:  python scripts/compute_oblivious_envelopes.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# make src/ importable
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))

from topology import MeshTopology, TorusTopology, KaryNCubeTopology, FullMeshTopology, DragonflyTopology
from problem import ObliviousValiantModel


# ========================================================================
# 拓扑列表（从小到大）
# ========================================================================

TOPOLOGIES = [
    # (label, topo_instance, topo_class_name, topo_args_for_json)
    ("mesh_2x2",      MeshTopology(2),                  "Mesh",      {"size": 2}),
    ("mesh_3x3",      MeshTopology(3),                  "Mesh",      {"size": 3}),
    ("torus_2x2",     TorusTopology(2),                 "Torus",     {"size": 2}),
    ("torus_3x3",     TorusTopology(3),                 "Torus",     {"size": 3}),
    ("kary_2_2",      KaryNCubeTopology(k=2, n=2),      "KaryNCube", {"k": 2, "n": 2, "wrap": True}),
    ("kary_2_3",      KaryNCubeTopology(k=2, n=3),      "KaryNCube", {"k": 2, "n": 3, "wrap": True}),
    ("fullmesh_4",    FullMeshTopology(4, p=1),         "FullMesh",  {"a": 4, "p": 1}),
    ("fullmesh_6",    FullMeshTopology(6, p=1),         "FullMesh",  {"a": 6, "p": 1}),
    ("dragonfly_s",   DragonflyTopology(a=2, p=1, h=1), "Dragonfly", {"a": 2, "p": 1, "h": 1}),
]


def compute_all() -> dict:
    """对每个拓扑算 L*，返回 {label: {n_terminals, n_links, L_star, ...}}."""
    cache = {}
    for label, topo, cls_name, args in TOPOLOGIES:
        N = topo.n_terminals
        E = topo.n_links
        print(f"  computing {label:20s}  N={N:3d}  |E|={E:4d} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        model = ObliviousValiantModel(topo)
        L_star = model.solve_envelope()
        dt = time.perf_counter() - t0
        print(f"done ({dt:.2f}s)")

        cache[label] = {
            "n_terminals": N,
            "n_links": E,
            "L_star": [round(x, 6) for x in L_star],
            "max_L_star": round(max(L_star), 6),
            "mean_L_star": round(sum(L_star) / len(L_star), 6),
            "sum_L_star": round(sum(L_star), 6),
            "topo_class": cls_name,
            "topo_args": args,
        }
    return cache


def print_summary(cache: dict) -> None:
    """打印汇总表."""
    print("\n" + "=" * 78)
    print(f"  {'Topology':<20s} {'N':>4s} {'|E|':>5s} {'max(L*)':>10s} "
          f"{'mean(L*)':>10s} {'Σ(L*)':>10s}")
    print("-" * 78)
    for label, entry in cache.items():
        print(f"  {label:<20s} {entry['n_terminals']:>4d} {entry['n_links']:>5d} "
              f"{entry['max_L_star']:>10.4f} {entry['mean_L_star']:>10.4f} "
              f"{entry['sum_L_star']:>10.4f}")
    print("=" * 78)


def main() -> None:
    cache = compute_all()
    print_summary(cache)

    cache_dir = _project_root / "cache"
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / "oblivious_envelopes.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    print(f"\ncache written to: {cache_path}")


if __name__ == "__main__":
    main()
