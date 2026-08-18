"""怀疑优先——独立验算 Dragonfly(a=2,p=1,h=1) L* = 7/3 + 检查不变式合理性。

do 报告 §"待核实" 自陈 Dragonfly L*=7/3 未手工独立验证，
作为审查员必须独立复算。
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from topology import Dragonfly, Mesh, Torus, FullMesh, KaryNCube


def build_coeffs(topo) -> list[np.ndarray]:
    terminals = topo.terminals
    N = len(terminals)
    li = topo.link_index
    n_links = topo.n_links
    coeffs = [np.zeros((N, N), dtype=float) for _ in range(n_links)]
    for i, src in enumerate(terminals):
        for j, dst in enumerate(terminals):
            if i == j:
                continue
            paths = topo.valiant(src, dst)
            K = len(paths)
            if K == 0:
                continue
            for path in paths:
                for k in range(len(path) - 1):
                    e = li[(path[k], path[k + 1])]
                    coeffs[e][i, j] += 1.0
            for e in range(n_links):
                if coeffs[e][i, j] > 0:
                    coeffs[e][i, j] /= K
    return coeffs


def max_over_permutations(c: np.ndarray) -> tuple[float, list[int]]:
    """枚举 N! 个置换 σ，返回 max Σ_i c[i, σ(i)] 及 argmax。

    注意：N=6 时 6!=720，可枚举；N=9 时 362880，仍可枚举。
    """
    N = c.shape[0]
    best_val = -float("inf")
    best_sigma: list[int] = []
    for sigma in itertools.permutations(range(N)):
        val = sum(c[i, sigma[i]] for i in range(N))
        if val > best_val:
            best_val = val
            best_sigma = list(sigma)
    return best_val, best_sigma


def verify_dragonfly():
    """独立验算 Dragonfly(a=2,p=1,h=1) max L* = 7/3"""
    print("=== Dragonfly(a=2,p=1,h=1) 独立验算 ===")
    d = Dragonfly(a=2, p=1, h=1)
    print(f"n_terminals = {d.n_terminals}, n_links = {d.n_links}")
    coeffs = build_coeffs(d)
    L_stars = []
    for e in range(d.n_links):
        L, _ = max_over_permutations(coeffs[e])
        L_stars.append(L)
    print(f"L* (independent enum): {[round(x, 6) for x in L_stars]}")
    print(f"max(L*) = {max(L_stars):.6f}, expected 7/3 = {7/3:.6f}")
    print(f"sum(L*) = {sum(L_stars):.6f}, do report claims 38.0")
    assert abs(max(L_stars) - 7/3) < 1e-9, f"max L* = {max(L_stars)}, expected 7/3"
    assert abs(sum(L_stars) - 38.0) < 1e-6, f"sum = {sum(L_stars)}, expected 38.0"
    print("✓ PASS: Dragonfly max L* = 7/3, sum = 38 (matches cache JSON)")


def verify_all_9_topos_against_cache():
    """9 个拓扑的 L* 与 cache/oblivious_envelopes.json 数值对照"""
    print("\n=== 9 拓扑 L* 与 cache JSON 对照 ===")
    import json
    cache_path = ROOT / "cache" / "oblivious_envelopes.json"
    with open(cache_path) as f:
        cache = json.load(f)

    topos = [
        ("mesh_2x2", Mesh(2)),
        ("mesh_3x3", Mesh(3)),
        ("torus_2x2", Torus(2)),
        ("torus_3x3", Torus(3)),
        ("kary_2_2", KaryNCube(k=2, n=2)),
        ("kary_2_3", KaryNCube(k=2, n=3)),
        ("fullmesh_4", FullMesh(4, p=1)),
        ("fullmesh_6", FullMesh(6, p=1)),
        ("dragonfly_s", Dragonfly(a=2, p=1, h=1)),
    ]
    for label, topo in topos:
        coeffs = build_coeffs(topo)
        L_star = [max_over_permutations(c)[0] for c in coeffs]
        cache_L = cache[label]["L_star"]
        for i, (ind, cach) in enumerate(zip(L_star, cache_L)):
            assert abs(ind - cach) < 1e-5, (
                f"{label} link {i}: independent={ind}, cache={cach}, diff={ind-cach}"
            )
        print(f"✓ {label}: independent L* matches cache ({len(L_star)} links, max={max(L_star):.6f})")


def verify_cache_deterministic():
    """跑两次 ObliviousValiantModel，验证 L* 一致（可复现）"""
    print("\n=== ObliviousValiantModel 可复现性 ===")
    from problem import ObliviousValiantModel
    for label, topo in [("mesh_2x2", Mesh(2)), ("torus_3x3", Torus(3))]:
        L1 = ObliviousValiantModel(topo).solve_envelope()
        L2 = ObliviousValiantModel(topo).solve_envelope()
        for i, (a, b) in enumerate(zip(L1, L2)):
            assert abs(a - b) < 1e-9, f"{label} link {i}: L1={a}, L2={b}"
        print(f"✓ {label}: two runs identical ({len(L1)} links)")


if __name__ == "__main__":
    verify_dragonfly()
    verify_all_9_topos_against_cache()
    verify_cache_deterministic()
    print("\n=== ALL EXTENDED VERIFICATIONS PASSED ===")
