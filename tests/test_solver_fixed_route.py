"""FixedRouteSolver 严格单元测试。

测试策略：
    1. 路由验证：不支持的 route 抛错
    2. 已知基准值回归测试
    3. Witness 自洽性：witness traffic 重放验证 worst_load
    4. 单调性：val ≤ det，规模越大 nonblocking 越小
    5. SolverResult 不变性
"""

from __future__ import annotations

import math
import unittest

from wafer_dse.architecture_model.solver.fixed_route import FixedRouteSolver
from wafer_dse.architecture_model.solver.interface import SolverResult
from wafer_dse.architecture_model.topology.mesh import Mesh
from wafer_dse.architecture_model.topology.torus import Torus
from wafer_dse.architecture_model.topology.kary_ncube import KaryNCube
from wafer_dse.architecture_model.topology.dragonfly import Dragonfly


class TestFixedRouteSolverRouteValidation(unittest.TestCase):
    """路由参数验证。"""

    def setUp(self):
        self.solver = FixedRouteSolver()
        self.topo = Mesh(4)

    def test_det_accepted(self):
        result = self.solver.solve(self.topo, "det", 800.0)
        self.assertIsInstance(result, SolverResult)

    def test_val_accepted(self):
        result = self.solver.solve(self.topo, "val", 800.0)
        self.assertIsInstance(result, SolverResult)

    def test_opt_raises(self):
        with self.assertRaises(ValueError):
            self.solver.solve(self.topo, "opt", 800.0)

    def test_unknown_route_raises(self):
        with self.assertRaises(ValueError):
            self.solver.solve(self.topo, "unknown", 800.0)


class TestFixedRouteSolverKnownBaselines(unittest.TestCase):
    """已知基准值 — 不可变的回归测试。"""

    def setUp(self):
        self.solver = FixedRouteSolver()

    def test_mesh4_det(self):
        """Mesh(4) det: worst_load=3.0, nonblocking=800/3≈266.67。"""
        result = self.solver.solve(Mesh(4), "det", 800.0)
        self.assertEqual(result.worst_load, 3.0)
        self.assertAlmostEqual(result.nonblocking_gbps_per_port, 800.0 / 3, places=5)

    def test_mesh4_val(self):
        """Mesh(4) val: worst_load ≤ det（路径更多，拥塞不增）。"""
        result_det = self.solver.solve(Mesh(4), "det", 800.0)
        result_val = self.solver.solve(Mesh(4), "val", 800.0)
        self.assertLessEqual(result_val.worst_load, result_det.worst_load)
        self.assertGreaterEqual(result_val.nonblocking_gbps_per_port,
                                result_det.nonblocking_gbps_per_port)

    def test_torus4_det(self):
        """Torus(4) det: worst_load=2.0, nonblocking=400。"""
        result = self.solver.solve(Torus(4), "det", 800.0)
        self.assertEqual(result.worst_load, 2.0)
        self.assertAlmostEqual(result.nonblocking_gbps_per_port, 400.0, places=5)

    def test_torus4_val(self):
        """Torus(4) val ≤ det。"""
        result_det = self.solver.solve(Torus(4), "det", 800.0)
        result_val = self.solver.solve(Torus(4), "val", 800.0)
        self.assertLessEqual(result_val.worst_load, result_det.worst_load)

    def test_mesh2_det(self):
        """Mesh(2) det: 2×2 mesh，非阻塞带宽应等于链路容量。"""
        result = self.solver.solve(Mesh(2), "det", 800.0)
        self.assertEqual(result.worst_load, 1.0)
        self.assertAlmostEqual(result.nonblocking_gbps_per_port, 800.0, places=5)

    def test_kary_ncube_4x2_wrap_det(self):
        """KaryNCube(4,2,True) det: 与 Torus(4) 相同 worst_load=2.0。"""
        result = self.solver.solve(KaryNCube(4, 2, True), "det", 800.0)
        self.assertEqual(result.worst_load, 2.0)
        self.assertAlmostEqual(result.nonblocking_gbps_per_port, 400.0, places=5)

    def test_dragonfly_2_2_1_det(self):
        """Dragonfly(2,2,1) det: worst_load=4.0。"""
        result = self.solver.solve(Dragonfly(2, 2, 1), "det", 800.0)
        self.assertEqual(result.worst_load, 4.0)


class TestFixedRouteSolverWitnessConsistency(unittest.TestCase):
    """Witness 自洽性 — 关键测试。

    用 witness traffic pattern 重放，计算 worst_link 上的实际负载，
    验证与求解器报告的 worst_load 一致。
    """

    def setUp(self):
        self.solver = FixedRouteSolver()

    def _compute_link_load_from_witness(
        self, topo, route, link, witness, link_capacity=800.0
    ) -> float:
        """给 witness traffic pattern，计算指定链路上的实际负载。"""
        total_load = 0.0
        for src, dst in witness:
            paths = topo.det(src, dst) if route == "det" else topo.valiant(src, dst)
            share = 1.0 / len(paths)
            for path in paths:
                for k in range(len(path) - 1):
                    if (path[k], path[k + 1]) == link:
                        total_load += share
                        break
        return total_load

    def test_witness_self_consistent_mesh4_det(self):
        """Mesh(4) det: witness 重放结果 == worst_load。"""
        topo = Mesh(4)
        result = self.solver.solve(topo, "det", 800.0)
        self.assertIsNotNone(result.worst_link)
        self.assertTrue(len(result.witness) > 0)

        reproduced_load = self._compute_link_load_from_witness(
            topo, "det", result.worst_link, result.witness
        )
        self.assertAlmostEqual(reproduced_load, result.worst_load, places=9,
            msg=f"witness load {reproduced_load} ≠ solver worst_load {result.worst_load}")

    def test_witness_self_consistent_torus4_det(self):
        """Torus(4) det: witness 重放一致。"""
        topo = Torus(4)
        result = self.solver.solve(topo, "det", 800.0)
        self.assertIsNotNone(result.worst_link)
        self.assertTrue(len(result.witness) > 0)

        reproduced_load = self._compute_link_load_from_witness(
            topo, "det", result.worst_link, result.witness
        )
        self.assertAlmostEqual(reproduced_load, result.worst_load, places=9,
            msg=f"witness load {reproduced_load} ≠ solver worst_load {result.worst_load}")

    def test_witness_self_consistent_kary_ncube_3x3_wrap_det(self):
        """KaryNCube(3,3,True) det: witness 重放一致。"""
        topo = KaryNCube(3, 3, True)
        result = self.solver.solve(topo, "det", 800.0)
        self.assertIsNotNone(result.worst_link)
        self.assertTrue(len(result.witness) > 0)

        reproduced_load = self._compute_link_load_from_witness(
            topo, "det", result.worst_link, result.witness
        )
        self.assertAlmostEqual(reproduced_load, result.worst_load, places=9,
            msg=f"witness load {reproduced_load} ≠ solver worst_load {result.worst_load}")

    def test_witness_self_consistent_mesh4_val(self):
        """Mesh(4) val: witness 重放一致。"""
        topo = Mesh(4)
        result = self.solver.solve(topo, "val", 800.0)
        self.assertIsNotNone(result.worst_link)
        self.assertTrue(len(result.witness) > 0)

        reproduced_load = self._compute_link_load_from_witness(
            topo, "val", result.worst_link, result.witness
        )
        self.assertAlmostEqual(reproduced_load, result.worst_load, places=9,
            msg=f"witness load {reproduced_load} ≠ solver worst_load {result.worst_load}")


class TestFixedRouteSolverMonotonicity(unittest.TestCase):
    """单调性。"""

    def setUp(self):
        self.solver = FixedRouteSolver()

    def test_val_not_worse_than_det(self):
        """val 路由的 worst_load ≤ det 路由的 worst_load（路径多→拥塞不增）。

        注意：此性质在 Mesh(4) 和 Torus(4) 上成立。
        对某些拓扑（如 Mesh(3)），Valiant 的确定性 detour 可能导致略微更差的 worst-case
        load，这是 Valiant 路由策略本身的特性，不是 solve error。
        """
        for topo in [Mesh(4), Torus(4)]:
            r_det = self.solver.solve(topo, "det", 800.0)
            r_val = self.solver.solve(topo, "val", 800.0)
            self.assertLessEqual(r_val.worst_load, r_det.worst_load,
                msg=f"{type(topo).__name__}: val load {r_val.worst_load} > det load {r_det.worst_load}")

    def test_larger_topology_lower_nonblocking(self):
        """拓扑越大，nonblocking 越低（拥塞越大）。"""
        r2 = self.solver.solve(Mesh(2), "det", 800.0)
        r4 = self.solver.solve(Mesh(4), "det", 800.0)
        self.assertGreater(r2.nonblocking_gbps_per_port, r4.nonblocking_gbps_per_port)


class TestSolverResultImmutability(unittest.TestCase):
    """SolverResult 是 frozen dataclass。"""

    def test_cannot_modify_result(self):
        result = FixedRouteSolver().solve(Mesh(4), "det", 800.0)
        with self.assertRaises(Exception):
            result.worst_load = 999.0


if __name__ == "__main__":
    unittest.main()
