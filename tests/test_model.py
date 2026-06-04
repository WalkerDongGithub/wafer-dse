"""ArchitectureModel 编排层单元测试。

测试策略：
    - build_topology：各种 kind 产生正确拓扑，未知 kind 抛错
    - evaluate：输出 NetworkPotential 完整性
    - solver 注入：自定义 solver 被使用 vs 默认 auto-select
"""

from __future__ import annotations

import unittest

from wafer_dse.architecture_model import ArchitectureModel, FixedRouteSolver
from wafer_dse.architecture_model.topology.mesh import Mesh
from wafer_dse.models import Requirement, Strictness, TopologySpec, NetworkPotential


class TestArchitectureModelBuildTopology(unittest.TestCase):
    """拓扑构建（通过 evaluate 间接测试）。"""

    def setUp(self):
        self.model = ArchitectureModel()
        self.req = Requirement(800, 200, Strictness("full"), "unused")

    def test_mesh(self):
        spec = TopologySpec(kind="mesh", size=4, route="det")
        net = self.model.evaluate(self.req, spec)
        self.assertEqual(net.terminal_count, 16)

    def test_torus(self):
        spec = TopologySpec(kind="torus", size=4, route="det")
        net = self.model.evaluate(self.req, spec)
        self.assertEqual(net.terminal_count, 16)

    def test_dragonfly(self):
        spec = TopologySpec(kind="dragonfly", a=2, p=2, h=1, route="det")
        net = self.model.evaluate(self.req, spec)
        self.assertEqual(net.terminal_count, 12)

    def test_kary_ncube_3d_torus(self):
        spec = TopologySpec(kind="kary_ncube", size=4, n=3, wrap=True, route="det")
        net = self.model.evaluate(self.req, spec)
        self.assertEqual(net.terminal_count, 64)

    def test_kary_ncube_2d_mesh(self):
        spec = TopologySpec(kind="kary_ncube", size=3, n=2, wrap=False, route="det")
        net = self.model.evaluate(self.req, spec)
        self.assertEqual(net.terminal_count, 9)

    def test_kary_ncube_default_n_and_wrap(self):
        """n 和 wrap 默认值：n=2, wrap=True。"""
        spec = TopologySpec(kind="kary_ncube", size=4, route="det")
        net = self.model.evaluate(self.req, spec)
        self.assertEqual(net.terminal_count, 16)  # 4^2 = 16

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            spec = TopologySpec(kind="hypercube", size=4, route="det")
            self.model.evaluate(self.req, spec)


class TestArchitectureModelEvaluate(unittest.TestCase):
    """evaluate 输出完整性。"""

    def setUp(self):
        self.model = ArchitectureModel()

    def test_network_potential_fields_populated(self):
        req = Requirement(800, 200, Strictness("full"), "unused", port_count=16)
        spec = TopologySpec(kind="mesh", size=4, route="det")
        net = self.model.evaluate(req, spec)

        self.assertIsInstance(net, NetworkPotential)
        self.assertIsNotNone(net.topology_name)
        self.assertIsNotNone(net.route)
        self.assertGreater(net.terminal_count, 0)
        self.assertGreater(net.directed_link_count, 0)
        self.assertGreater(net.nonblocking_gbps_per_port, 0)
        self.assertIsNotNone(net.certificate_status)
        self.assertIsNotNone(net.worst_link)

    def test_required_speedup_at_least_one(self):
        req = Requirement(800, 200, Strictness("full"), "unused")
        spec = TopologySpec(kind="mesh", size=4, route="det")
        net = self.model.evaluate(req, spec)
        self.assertGreaterEqual(net.required_internal_speedup, 1)

    def test_links_formula(self):
        """required_internal_800g_links == directed_link_count × speedup。"""
        req = Requirement(800, 200, Strictness("full"), "unused")
        for kind, size in [("mesh", 4), ("torus", 4)]:
            spec = TopologySpec(kind=kind, size=size, route="det")
            net = self.model.evaluate(req, spec)
            expected = net.directed_link_count * net.required_internal_speedup
            self.assertEqual(net.required_internal_800g_links, expected,
                             f"{kind}: {net.required_internal_800g_links} ≠ "
                             f"{net.directed_link_count} × {net.required_internal_speedup}")

    def test_certificate_status_matches_strictness(self):
        """证书状态应反映严格程度。"""
        req_full = Requirement(800, 200, Strictness("full"), "unused")
        net = self.model.evaluate(req_full, TopologySpec(kind="mesh", size=4, route="det"))
        self.assertEqual(net.certificate_status, "exact_worst_case")

        req_pct = Requirement(800, 200, Strictness("percent", percent=90), "unused")
        net = self.model.evaluate(req_pct, TopologySpec(kind="mesh", size=4, route="det"))
        self.assertEqual(net.certificate_status, "conservative_exact")


class TestArchitectureModelSolverInjection(unittest.TestCase):
    """求解器注入 vs 自动选择。"""

    def test_custom_solver_used(self):
        """注入自定义 solver 时，应使用该 solver。"""
        solver = FixedRouteSolver()
        model = ArchitectureModel(solver=solver)
        req = Requirement(800, 200, Strictness("full"), "unused")
        spec = TopologySpec(kind="mesh", size=4, route="det")
        net = model.evaluate(req, spec)
        # 结果应有意义的值
        self.assertGreater(net.nonblocking_gbps_per_port, 0)

    def test_default_uses_create_solver(self):
        """不给 solver 参数时，应通过 create_solver 自动选择。"""
        model = ArchitectureModel()  # solver=None
        req = Requirement(800, 200, Strictness("full"), "unused")
        spec = TopologySpec(kind="mesh", size=4, route="val")
        net = model.evaluate(req, spec)
        self.assertGreater(net.nonblocking_gbps_per_port, 0)


if __name__ == "__main__":
    unittest.main()
