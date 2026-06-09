"""Rust 后端等价性测试。

测试策略：
    - 当 wafer-solve 二进制可用时，验证 Rust 与纯 Python 产生相同结果。
    - 当二进制不可用时，优雅跳过（unittest.skipUnless）。
"""

from __future__ import annotations

import random
import unittest

from wafer_dse.architecture_model.solver.rust_backend import (
    batch_derangement,
    hungarian_min_cost as rust_hungarian,
    is_rust_available,
)
from wafer_dse.architecture_model.solver.algorithm.derangement import (
    max_weight_derangement as py_derangement,
)
from wafer_dse.architecture_model.solver.algorithm.hungarian import (
    hungarian_min_cost as py_hungarian,
)


def _random_square(n: int, lo: float = -10.0, hi: float = 100.0) -> list[list[float]]:
    return [[random.uniform(lo, hi) for _ in range(n)] for _ in range(n)]


def _random_weight(n: int, lo: float = 0.0, hi: float = 100.0) -> list[list[float]]:
    return [[random.uniform(lo, hi) for _ in range(n)] for _ in range(n)]


# ============================================================================
# Hungarian 等价性
# ============================================================================


@unittest.skipUnless(is_rust_available(), "wafer-solve 二进制不可用")
class TestRustHungarianEquivalence(unittest.TestCase):
    """Rust Hungarian 与纯 Python Hungarian 逐结果对比。"""

    def test_n4_random_20(self):
        for _ in range(20):
            cost = _random_square(4)
            py_total, py_assign = py_hungarian(cost)
            rs_total, rs_assign = rust_hungarian(cost)
            self.assertAlmostEqual(py_total, rs_total, places=9)
            self.assertEqual(py_assign, rs_assign)

    def test_n8_random(self):
        cost = _random_square(8)
        py_total, py_assign = py_hungarian(cost)
        rs_total, rs_assign = rust_hungarian(cost)
        self.assertAlmostEqual(py_total, rs_total, places=9)
        self.assertEqual(py_assign, rs_assign)

    def test_known_solution(self):
        cost = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
        rs_total, rs_assign = rust_hungarian(cost)
        self.assertAlmostEqual(rs_total, 10.0, places=9)
        self.assertEqual(rs_assign, [2, 1, 0])

    def test_all_zeros(self):
        cost = [[0.0, 0.0], [0.0, 0.0]]
        rs_total, rs_assign = rust_hungarian(cost)
        self.assertAlmostEqual(rs_total, 0.0, places=9)
        self.assertEqual(sorted(rs_assign), [0, 1])

    def test_negative_values(self):
        cost = [[-5.0, -3.0], [-2.0, -4.0]]
        rs_total, rs_assign = rust_hungarian(cost)
        self.assertAlmostEqual(rs_total, -9.0, places=9)
        self.assertEqual(rs_assign, [0, 1])

    def test_n0_empty(self):
        rs_total, rs_assign = rust_hungarian([])
        self.assertEqual(rs_total, 0.0)
        self.assertEqual(rs_assign, [])

    def test_n1_single(self):
        rs_total, rs_assign = rust_hungarian([[5.0]])
        self.assertEqual(rs_total, 5.0)
        self.assertEqual(rs_assign, [0])

    def test_non_square_raises(self):
        with self.assertRaises(Exception):
            rust_hungarian([[1.0, 2.0], [3.0]])

    def test_assignment_is_valid_permutation(self):
        for n in [1, 2, 3, 4, 5, 6]:
            cost = _random_square(n)
            _, assign = rust_hungarian(cost)
            self.assertEqual(sorted(assign), list(range(n)))

    def test_row_constant_addition_preserves_assignment(self):
        cost = _random_square(5)
        _, orig_assign = rust_hungarian(cost)
        modified = [row[:] for row in cost]
        c = 100.0
        for j in range(5):
            modified[2][j] += c
        _, mod_assign = rust_hungarian(modified)
        self.assertEqual(mod_assign, orig_assign)


# ============================================================================
# Derangement 等价性
# ============================================================================


@unittest.skipUnless(is_rust_available(), "wafer-solve 二进制不可用")
class TestRustDerangementEquivalence(unittest.TestCase):
    """Rust Derangement 与纯 Python Derangement 逐结果对比。"""

    def test_n4_random_10(self):
        for _ in range(10):
            w = _random_weight(4)
            py_w, py_a = py_derangement(w)
            results = batch_derangement([w])
            rs_w, rs_a = results[0]
            self.assertAlmostEqual(py_w, rs_w, places=9)
            self.assertEqual(py_a, rs_a)

    def test_n8_random(self):
        w = _random_weight(8)
        py_w, py_a = py_derangement(w)
        results = batch_derangement([w])
        rs_w, rs_a = results[0]
        self.assertAlmostEqual(py_w, rs_w, places=9)
        self.assertEqual(py_a, rs_a)

    def test_all_zeros(self):
        w = [[0.0] * 4 for _ in range(4)]
        results = batch_derangement([w])
        rs_w, rs_a = results[0]
        self.assertEqual(rs_w, 0.0)
        self.assertTrue(all(rs_a[i] != i for i in range(4)))

    def test_constant_weights(self):
        n = 5
        w = [[10.0] * n for _ in range(n)]
        results = batch_derangement([w])
        rs_w, rs_a = results[0]
        self.assertAlmostEqual(rs_w, 10.0 * n, places=9)
        self.assertTrue(all(rs_a[i] != i for i in range(n)))

    def test_batch_vs_sequential(self):
        """批量调用与逐个调用结果一致。"""
        matrices = [
            _random_weight(3) for _ in range(10)
        ]
        batch_results = batch_derangement(matrices)
        seq_results = [py_derangement(m) for m in matrices]
        for (bw, ba), (sw, sa) in zip(batch_results, seq_results):
            self.assertAlmostEqual(bw, sw, places=9)
            self.assertEqual(ba, sa)

    def test_n0_empty(self):
        results = batch_derangement([])
        self.assertEqual(results, [])

    def test_n1_empty(self):
        results = batch_derangement([[[5.0]]])
        rs_w, rs_a = results[0]
        self.assertEqual(rs_w, 0.0)
        self.assertEqual(rs_a, [])

    def test_non_square_raises(self):
        with self.assertRaises(Exception):
            batch_derangement([[[1.0, 2.0], [3.0]]])

    def test_no_self_loops(self):
        for n in [2, 3, 4, 5, 6]:
            w = _random_weight(n)
            results = batch_derangement([w])
            _, assign = results[0]
            self.assertTrue(all(assign[i] != i for i in range(n)))

    def test_total_matches_assignment(self):
        for n in [2, 3, 4, 5]:
            w = _random_weight(n)
            results = batch_derangement([w])
            total, assign = results[0]
            expected = sum(w[i][assign[i]] for i in range(n))
            self.assertAlmostEqual(total, expected, places=9)


# ============================================================================
# FixedRouteSolver 回归（Rust 后端透明）
# ============================================================================


@unittest.skipUnless(is_rust_available(), "wafer-solve 二进制不可用")
class TestRustFixedRouteSolverEquivalence(unittest.TestCase):
    """FixedRouteSolver 通过 Rust 后端求解，结果必须与已知基准值一致。"""

    def test_mesh4_det(self):
        from wafer_dse.architecture_model.solver.fixed_route import FixedRouteSolver
        from wafer_dse.architecture_model.topology.mesh import Mesh
        result = FixedRouteSolver().solve(Mesh(4), "det", 800.0)
        self.assertAlmostEqual(result.worst_load, 3.0, places=9)
        self.assertAlmostEqual(result.nonblocking_gbps_per_port, 800.0 / 3.0, places=6)

    def test_mesh2_det(self):
        from wafer_dse.architecture_model.solver.fixed_route import FixedRouteSolver
        from wafer_dse.architecture_model.topology.mesh import Mesh
        result = FixedRouteSolver().solve(Mesh(2), "det", 800.0)
        self.assertAlmostEqual(result.worst_load, 1.0, places=9)
        self.assertAlmostEqual(result.nonblocking_gbps_per_port, 800.0, places=6)

    def test_torus4_det(self):
        from wafer_dse.architecture_model.solver.fixed_route import FixedRouteSolver
        from wafer_dse.architecture_model.topology.torus import Torus
        result = FixedRouteSolver().solve(Torus(4), "det", 800.0)
        self.assertAlmostEqual(result.worst_load, 2.0, places=9)
        self.assertAlmostEqual(result.nonblocking_gbps_per_port, 400.0, places=6)

    def test_dragonfly_det(self):
        from wafer_dse.architecture_model.solver.fixed_route import FixedRouteSolver
        from wafer_dse.architecture_model.topology.dragonfly import Dragonfly
        result = FixedRouteSolver().solve(Dragonfly(a=2, p=2, h=1), "det", 800.0)
        self.assertAlmostEqual(result.worst_load, 4.0, places=9)
        self.assertAlmostEqual(result.nonblocking_gbps_per_port, 200.0, places=6)

    def test_witness_self_consistency(self):
        """通过拓扑路由重放 witness traffic，验证负载自洽。"""
        from wafer_dse.architecture_model.solver.fixed_route import FixedRouteSolver
        from wafer_dse.architecture_model.topology.mesh import Mesh

        topo = Mesh(4)
        result = FixedRouteSolver().solve(topo, "det", 800.0)

        # 重放：对 witness 中每个 (src, dst) 对，沿 det 路径累加链路负载
        link_load: dict[tuple[int, int], float] = {}
        for src, dst in result.witness:
            path = topo.det(src, dst)[0]
            for k in range(len(path) - 1):
                link = (path[k], path[k + 1])
                link_load[link] = link_load.get(link, 0.0) + 1.0

        worst_link = result.worst_link
        self.assertIsNotNone(worst_link)
        replayed_load = link_load.get(worst_link, 0.0)
        self.assertAlmostEqual(replayed_load, result.worst_load, places=9)


if __name__ == "__main__":
    unittest.main()
