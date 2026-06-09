"""GroupExplorer 单元测试。

验证：
    1. crossbar 端口数公式: r×p + (r-1) + (K-1) + r×h
    2. 不同 K 产生的 PartitionPlan 数量正确
    3. K=1 (单 die) 应该比 K=a (全拆) 面积小
    4. 全流程不报错
"""

from __future__ import annotations

import unittest

from wafer_dse.group_dse import GroupExplorer
from wafer_dse.models import Requirement, Strictness


def _sample_req(**overrides) -> Requirement:
    defaults = dict(
        target_nonblocking_gbps_per_port=800.0,
        max_power_w=200.0,
        strictness=Strictness("full"),
        packaging_config="unused",
        port_count=None,
        max_die_area_mm2=800.0,
    )
    defaults.update(overrides)
    return Requirement(**defaults)


def _sample_cfg(**overrides) -> dict:
    cfg = {
        "ext_lane_rate_gbps": 100,
        "int_lane_rate_gbps": 16,
        "area_per_external_lane_mm2": 0.08,
        "power_per_external_lane_w": 0.35,
        "area_per_internal_lane_mm2": 0.012,
        "power_per_internal_lane_w": 0.005,
        "base_die_area_mm2": 40,
        "base_power_w": 20,
        "max_die_area_mm2": 800,
        "d2d_lanes_per_mm_edge": 10,
        "crossbar_cell_mm2": 0.01,
        "buffer_vc_count": 8,
        "buffer_depth": 16,
        "flit_width": 256,
        "sram_density_mbit_per_mm2": 10.0,
        "buffer_area_efficiency": 0.1,
        "max_crossbar_ports": 256,
        "max_internal_lanes": 1600,
        "max_external_lanes": 160,
        "router_area_mm2": 1.5,
        "router_power_w": 0.8,
        "max_power_w": 220,
    }
    cfg.update(overrides)
    return cfg


class TestGroupExplorerPartitions(unittest.TestCase):
    """验证分割方案的端口数公式和数量。"""

    def setUp(self):
        self.explorer = GroupExplorer()
        self.req = _sample_req()
        self.cfg = _sample_cfg()

    def test_a4_p4_h2_produces_three_partitions(self):
        """a=4 能被 K=1,2,4 整除 → 3 个分割方案。"""
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)
        self.assertEqual(len(plan.partitions), 3)  # K=1,2,4
        die_counts = [p.die_count for p in plan.partitions]
        self.assertEqual(die_counts, [1, 2, 4])

    def test_a3_p4_h2_produces_two_partitions(self):
        """a=3 只能被 K=1,3 整除 → 2 个分割方案。"""
        plan = self.explorer.explore(a=3, p=4, h=2, req=self.req, cfg=self.cfg)
        self.assertEqual(len(plan.partitions), 2)  # K=1,3

    def test_crossbar_ports_formula_K1(self):
        """K=1, r=4: ports = 4×4 + 3 + 0 + 4×2 = 27。"""
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)
        k1 = plan.partitions[0]  # K=1
        die = k1.dies[0]
        # r=4, K=1: 4×4 + (4-1) + 0 + 4×2 = 16+3+0+8 = 27
        self.assertEqual(die.crossbar_ports, 27)

    def test_crossbar_ports_formula_K2(self):
        """K=2, r=2: ports = 2×4 + 1 + 1 + 2×2 = 14。"""
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)
        k2 = plan.partitions[1]  # K=2
        die = k2.dies[0]
        self.assertEqual(die.crossbar_ports, 14)

    def test_crossbar_ports_formula_K4(self):
        """K=4, r=1: ports = 1×4 + 0 + 3 + 1×2 = 9。"""
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)
        k4 = plan.partitions[2]  # K=4
        die = k4.dies[0]
        self.assertEqual(die.crossbar_ports, 9)


class TestGroupExplorerScaling(unittest.TestCase):
    """分割方案的物理行为。"""

    def setUp(self):
        self.explorer = GroupExplorer()
        self.req = _sample_req()
        self.cfg = _sample_cfg()

    def test_K1_has_smallest_total_area(self):
        """单 die 总面积应最小（无 D2D 开销）。"""
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)

        areas = [p.total_area_mm2 for p in plan.partitions]
        # K=1 应该面积最小
        self.assertLess(areas[0], areas[-1],
                        f"K=1 area {areas[0]} should be less than K=4 area {areas[-1]}")

    def test_K_larger_means_more_d2d_per_die(self):
        """K 越大 → 每个 die 的 D2D 基础链路越多（speedup 放大前）。"""
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)
        # D2D 逻辑链路 = (K-1), 再 × speedup
        # dragonfly(4,4,2) 的 speedup > 1
        base_counts = [p.dies[0].d2d_link_count for p in plan.partitions]
        # 验证单调性: K 越大 → d2d 越多
        self.assertGreater(base_counts[1], base_counts[0])
        self.assertGreater(base_counts[2], base_counts[1])

    def test_best_partition_is_K1(self):
        """a=4,p=4,h=2 在 800G 下 K=1 应该可行且被选为最佳。"""
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)
        self.assertIsNotNone(plan.best_partition)
        # K=1 应该 feasible 且是 best（die 数最少）
        if plan.best_partition is not None:
            self.assertEqual(plan.best_partition.die_count, 1)


class TestGroupExplorerOutput(unittest.TestCase):
    """输出字段完整性。"""

    def setUp(self):
        self.explorer = GroupExplorer()
        self.req = _sample_req()
        self.cfg = _sample_cfg()

    def test_group_plan_fields_populated(self):
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)
        self.assertEqual(plan.a, 4)
        self.assertEqual(plan.p, 4)
        self.assertEqual(plan.h, 2)
        self.assertEqual(plan.total_terminals, 16)
        self.assertIsNotNone(plan.network)
        self.assertGreater(plan.network.terminal_count, 0)

    def test_partition_plan_fields_populated(self):
        plan = self.explorer.explore(a=4, p=4, h=2, req=self.req, cfg=self.cfg)
        for pp in plan.partitions:
            self.assertGreater(pp.die_count, 0)
            self.assertEqual(len(pp.dies), pp.die_count)
            self.assertGreater(pp.total_area_mm2, 0)
            for die in pp.dies:
                self.assertGreater(die.die_area_mm2, 0)
                self.assertGreater(die.crossbar_ports, 0)


if __name__ == "__main__":
    unittest.main()
