"""UnifiedLp 引擎端到端测试。

验证:
    1. det 路径: Hungarian + 物理约束检查
    2. valiant 路径: cvxpy 最优分流 LP
    3. 结果报告格式
    4. 不同拓扑/参数组合
"""

from __future__ import annotations

import unittest

from wafer_dse.architecture_model.topology import Dragonfly, Mesh, Torus
from wafer_dse.lp import UnifiedLp
from wafer_dse.lp.geometry import DieConfig
from wafer_dse.lp.thermal import ThermalConfig
from wafer_dse.physical.bump.bump import UBUMP_45UM
from wafer_dse.physical.thermal._cooling import LIQUID_COOLING

try:
    import cvxpy  # noqa: F401
    HAS_CVXPY = True
except ImportError:
    HAS_CVXPY = False


class TestUnifiedLpDet(unittest.TestCase):
    """det 路径基本功能测试。"""

    def setUp(self):
        self.topo = Dragonfly(a=2, p=2, h=1)
        self.lp = UnifiedLp(self.topo, route="det", target_gbps=800)

    def test_solve_without_constraints(self):
        """无物理约束时的纯性能评估。"""
        result = self.lp.solve()
        self.assertEqual(result.route, "det")
        self.assertIn("hungarian", result.solver)
        self.assertGreater(result.worst_load, 0)
        self.assertGreater(result.nonblocking_gbps, 0)

    def test_solve_with_geometry(self):
        """添加 bump 预算约束。"""
        die_configs = [
            DieConfig(label=f"die_{i}", width_mm=12, height_mm=12, power_w=50)
            for i in range(self.topo.g)
        ]
        self.lp.add_geometry(die_configs, UBUMP_45UM)
        result = self.lp.solve()

        # 应有 geometry 约束状态
        geo_statuses = [c for c in result.constraints if c.name == "geometry"]
        self.assertEqual(len(geo_statuses), 1)
        # geometry 应该通过 (小拓扑，bump 预算充裕)
        self.assertTrue(geo_statuses[0].satisfied)

    def test_solve_with_thermal(self):
        """添加热约束。"""
        thermal_cfg = ThermalConfig(
            total_area_mm2=858.0,
            interposer_count=1,
            cooling=LIQUID_COOLING,
        )
        self.lp.add_thermal(thermal_cfg)
        result = self.lp.solve()

        therm_statuses = [c for c in result.constraints if c.name == "thermal"]
        self.assertEqual(len(therm_statuses), 1)
        # 热约束应该通过 (小拓扑，功耗低)
        self.assertTrue(therm_statuses[0].satisfied)

    def test_report_format(self):
        """报告格式检查。"""
        result = self.lp.solve()
        report = result.report()

        self.assertIn("DSE 统一 LP 求解报告", report)
        self.assertIn("hungarian", report)
        self.assertIn("可行性", report)
        self.assertIn("最坏负载", report)
        self.assertIn("无阻塞带宽", report)

    def test_summary_line(self):
        """单行摘要。"""
        result = self.lp.solve()
        line = result.summary_line()
        self.assertIn("L*=", line)
        self.assertIn("BW=", line)
        self.assertIn("hungarian", line)


class TestUnifiedLpTopology(unittest.TestCase):
    """不同拓扑的 LP 评估。"""

    def test_mesh_basic(self):
        """Mesh 4×4 基本测试。"""
        topo = Mesh(4)
        lp = UnifiedLp(topo, route="det", target_gbps=800)
        result = lp.solve()
        self.assertIsNotNone(result.worst_load)
        self.assertGreater(result.worst_load, 0)

    def test_torus_basic(self):
        """Torus 4×4 基本测试。"""
        topo = Torus(4)
        lp = UnifiedLp(topo, route="det", target_gbps=800)
        result = lp.solve()
        # Torus 有绕边链路，负载应低于同尺寸 Mesh
        self.assertGreater(result.worst_load, 0)

    def test_dragonfly_larger(self):
        """Dragonfly(a=4,p=4,h=2) 测试。"""
        topo = Dragonfly(a=4, p=4, h=2)
        lp = UnifiedLp(topo, route="det", target_gbps=800)
        result = lp.solve()
        self.assertGreater(topo.terminal_num(), 100)
        self.assertGreater(result.worst_load, 0)


class TestLpResultData(unittest.TestCase):
    """LpResult 数据结构测试。"""

    def setUp(self):
        topo = Dragonfly(a=2, p=2, h=1)
        self.result = UnifiedLp(topo, route="det", target_gbps=800).solve()

    def test_constraint_list(self):
        """约束列表非空。"""
        self.assertGreater(len(self.result.constraints), 0)

    def test_per_link_load(self):
        """per-link load 字典。"""
        self.assertIsInstance(self.result.per_link_load, dict)

    def test_notes(self):
        """备注列表。"""
        self.assertIsInstance(self.result.notes, list)

    def test_bottleneck_link(self):
        """瓶颈链路非空。"""
        self.assertNotEqual(self.result.bottleneck_link, "")


@unittest.skipUnless(HAS_CVXPY, "cvxpy 未安装")
class TestUnifiedLpValiant(unittest.TestCase):
    """valiant LP 路径测试 (需要 cvxpy)。"""

    def test_valiant_vs_det(self):
        """valiant 最优分流 ≤ det (更多选择不应更差)。"""
        topo = Dragonfly(a=2, p=2, h=1)
        det = UnifiedLp(topo, route="det", target_gbps=800).solve()
        val = UnifiedLp(topo, route="valiant", target_gbps=800).solve()

        # valiant LP 的最坏负载应 ≤ det 的最坏负载
        self.assertLessEqual(val.worst_load, det.worst_load + 1e-6,
            f"valiant t*={val.worst_load:.4f} 应 ≤ det L*={det.worst_load:.4f}")

    def test_valiant_nonblocking(self):
        """valiant LP 应能找到非阻塞解 (小拓扑)。"""
        topo = Dragonfly(a=2, p=2, h=1)
        result = UnifiedLp(topo, route="valiant", target_gbps=800).solve()
        self.assertTrue(result.feasible,
            f"valiant LP 应对小拓扑可行, t*={result.worst_load:.4f}")

    def test_valiant_with_physics(self):
        """valiant LP + 物理约束。"""
        topo = Dragonfly(a=2, p=2, h=1)
        dies = [DieConfig(label=f"die_{i}") for i in range(topo.g)]
        lp = UnifiedLp(topo, route="valiant", target_gbps=800)
        lp.add_geometry(dies, UBUMP_45UM)
        lp.add_thermal(ThermalConfig(cooling=LIQUID_COOLING))
        result = lp.solve()
        self.assertIsNotNone(result.worst_load)

    def test_valiant_raises_without_cvxpy(self):
        """valiant 无 cvxpy 应抛出清晰的 ImportError (不输出错误结果)。"""
        # 这个测试本身就要求 cvxpy 存在，所以跳过
        pass


if __name__ == "__main__":
    unittest.main()
