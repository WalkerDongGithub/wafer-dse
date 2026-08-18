"""独立验算 ObliviousValiantModel 的关键数学 claim——怀疑优先。

不依赖 ObliviousValiantModel 的实现，从 V5 §7.3 定义重算：
  对每个 OD 对 (i,j)，K_{ij} = len(topo.valiant(src,dst))
  c_{ij}^e = |{k : e ∈ path_k(i,j)}| / K_{ij}
  L_e(D) = Σ_{i,j} c_{ij}^e D_{ij}
  L_e* = max_{D∈Birkhoff} L_e(D)

Birkhoff 多面体顶点 = 置换矩阵，所以 max 在 N! 个置换上枚举即得（小 N）。

claim 1: Mesh(2) link 0 的 L_0* = 3/2，由 σ=(3,2,0,1) 取到
claim 2: FullMesh(4,p=1) terminal-router=1, router-terminal=1, router-router=2/3
claim 3: Torus(3) 所有 36 链路 L* = 6/7 ≈ 0.857
claim 4: Σ oblivious L* ≥ N（不变式）
claim 5: 逐链路 oblivious L*_e ≥ optimal L_e (Mesh(2))
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from topology import Mesh, FullMesh, Torus, KaryNCube, Dragonfly


# ----------------------------------------------------------------------
# 独立实现：从 V5 §7.3 定义直接构造 c^e 并枚举置换求 L*
# ----------------------------------------------------------------------

def build_coeffs(topo) -> list[np.ndarray]:
    """对每条链路 e 构造 c_{ij}^e = (#path 包含 e) / K_{ij}。"""
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
    """枚举 N! 个置换 σ，返回 max Σ_i c[i, σ(i)] 及 argmax。"""
    N = c.shape[0]
    best_val = -float("inf")
    best_sigma: list[int] = []
    for sigma in itertools.permutations(range(N)):
        val = sum(c[i, sigma[i]] for i in range(N))
        if val > best_val:
            best_val = val
            best_sigma = list(sigma)
    return best_val, best_sigma


def verify_mesh2():
    """claim 1: Mesh(2) link 0 L_0* = 3/2，σ=(3,2,0,1)（即 i→σ[i]）"""
    print("\n=== claim 1: Mesh(2) link 0 L_0* = 3/2 ===")
    m = Mesh(2)
    coeffs = build_coeffs(m)
    c0 = coeffs[0]
    print(f"link_index[0] = {m.links[0]}")
    print(f"c^0 matrix (rows i, cols j):\n{c0}")

    val, sigma = max_over_permutations(c0)
    # 注意：σ=(3,2,0,1) 的语义是 i→σ[i]：0→3, 1→2, 2→0, 3→1
    print(f"max L_0(D) over permutations = {val}")
    print(f"argmax sigma (i -> sigma[i]) = {sigma}")

    expected_sigma = [3, 2, 0, 1]
    print(f"expected sigma (test04 claim) = {expected_sigma}")
    match = sigma == expected_sigma
    print(f"sigma matches expected? {match}")

    assert abs(val - 1.5) < 1e-9, f"L_0* = {val}, expected 3/2 = 1.5"
    assert sigma == [3, 2, 0, 1], f"sigma = {sigma}, expected [3,2,0,1]"
    print("✓ PASS: L_0* = 3/2, sigma = [3,2,0,1]")

    # by symmetry, all 8 links should have L*=1.5
    for e in range(m.n_links):
        v, _ = max_over_permutations(coeffs[e])
        assert abs(v - 1.5) < 1e-9, f"link {e} L* = {v}, expected 1.5"
    print("✓ PASS: all 8 links have L* = 1.5 (Mesh(2) symmetry)")


def verify_fullmesh4():
    """claim 2: FullMesh(4,p=1) 三类链路 L* = 1, 1, 2/3"""
    print("\n=== claim 2: FullMesh(4,p=1) 三类链路 ===")
    fm = FullMesh(4, p=1)
    coeffs = build_coeffs(fm)
    # fm.terminals are the die-attached terminals (nodes 4..7), routers are 0..3
    # 链路类型：terminal→router (u>=4, v<4); router→terminal (u<4, v>=4); router→router (both<4)
    tr, rt, rr = [], [], []
    for e, (u, v) in enumerate(fm.links):
        L, _ = max_over_permutations(coeffs[e])
        if u >= 4 and v < 4:
            tr.append(L)
        elif u < 4 and v >= 4:
            rt.append(L)
        else:
            rr.append(L)
    print(f"terminal→router ({len(tr)} links): L* = {tr}")
    print(f"router→terminal ({len(rt)} links): L* = {rt}")
    print(f"router→router  ({len(rr)} links): L* = {rr}")
    for x in tr:
        assert abs(x - 1.0) < 1e-9
    for x in rt:
        assert abs(x - 1.0) < 1e-9
    for x in rr:
        assert abs(x - 2/3) < 1e-9, f"router-router L* = {x}, expected 2/3"
    print("✓ PASS: terminal-router=1, router-terminal=1, router-router=2/3")


def verify_torus3():
    """claim 3: Torus(3) 所有 36 链路 L* = 6/7 ≈ 0.857"""
    print("\n=== claim 3: Torus(3) 所有 36 链路 L* = 6/7 ===")
    t = Torus(3)
    coeffs = build_coeffs(t)
    print(f"n_links = {t.n_links}, n_terminals = {t.n_terminals}")
    L_stars = []
    for e in range(t.n_links):
        L, _ = max_over_permutations(coeffs[e])
        L_stars.append(L)
    unique = set(round(x, 6) for x in L_stars)
    print(f"unique L* values: {unique}")
    print(f"first 5 L*: {[round(x, 6) for x in L_stars[:5]]}")
    # do 报告声称 0.857143 = 6/7
    expected = 6 / 7
    print(f"expected 6/7 = {expected:.6f}")
    for x in L_stars:
        assert abs(x - expected) < 1e-6, f"L* = {x}, expected 6/7 = {expected}"
    print(f"✓ PASS: all {t.n_links} links have L* = 6/7")


def verify_sum_geq_N():
    """claim 4: Σ_e L_e* ≥ N"""
    print("\n=== claim 4: Σ L_e* ≥ N ===")
    for topo in [Mesh(2), FullMesh(4, p=1), Torus(3)]:
        coeffs = build_coeffs(topo)
        N = topo.n_terminals
        total = 0.0
        for e in range(topo.n_links):
            L, _ = max_over_permutations(coeffs[e])
            total += L
        print(f"  {type(topo).__name__}: N={N}, Σ L* = {total:.6f}")
        assert total >= N - 1e-9, f"Σ L* = {total} < N = {N}"
    print("✓ PASS: Σ L* ≥ N for all tested topologies")


def verify_oblivious_geq_optimal_componentwise_mesh2():
    """claim 5: Mesh(2) 上 oblivious L*_e ≥ optimal L_e 逐链路"""
    print("\n=== claim 5: Mesh(2) 逐链路 oblivious ≥ optimal ===")
    from problem import OptimalValiantModel, select_representatives, Ctx, CvxSolver
    m = Mesh(2)
    coeffs = build_coeffs(m)
    obl_L = []
    for e in range(m.n_links):
        L, _ = max_over_permutations(coeffs[e])
        obl_L.append(L)
    reps = select_representatives(m, m.n_terminals)
    opt_m = OptimalValiantModel(m, reps)
    ctx = Ctx()
    opt_m.build(ctx, B=1.0)
    sol = CvxSolver().solve(ctx, objective=sum(ctx["L"]), maximize=False)
    opt_L = sol.variables["L"]
    print(f"oblivious L* = {[round(x, 4) for x in obl_L]}, sum = {sum(obl_L):.6f}")
    print(f"optimal  L  = {[round(x, 4) for x in opt_L]}, sum = {sum(opt_L):.6f}")
    for e in range(m.n_links):
        assert obl_L[e] >= opt_L[e] - 1e-6, f"link {e}: obl {obl_L[e]} < opt {opt_L[e]}"
    assert sum(obl_L) >= sum(opt_L) - 1e-6
    print("✓ PASS: Σ oblivious ≥ Σ optimal, and per-link oblivious ≥ optimal")


if __name__ == "__main__":
    verify_mesh2()
    verify_fullmesh4()
    verify_torus3()
    verify_sum_geq_N()
    verify_oblivious_geq_optimal_componentwise_mesh2()
    print("\n=== ALL VERIFICATIONS PASSED ===")
