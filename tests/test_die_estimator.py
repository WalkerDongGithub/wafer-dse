"""DieEstimator 单元测试。

验证：
    1. crossbar O(N²) 公式 + buffer O(N) 公式手算一致
    2. 面积随端口数增加非线性增长
    3. reticle limit 和 D2D edge budget 边界
"""

from __future__ import annotations

import math
import unittest

from wafer_dse.die_model import DieEstimator


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
    }
    cfg.update(overrides)
    return cfg


class TestDieEstimatorManual(unittest.TestCase):
    """手算验证：已知端口数 → 期望面积。"""

    def setUp(self):
        self.estimator = DieEstimator()
        self.cfg = _sample_cfg()

    def test_ext_lanes_calculation(self):
        """800G/100G = 8 ext lanes; 800G/16G = 50 int lanes per port. 这里只测一个不带 D2D 的小 die。"""
        est = self.estimator.estimate(
            self.cfg,
            crossbar_ports=5,
            ext_port_count=2,
            d2d_link_count=0,
            target_gbps=800,
        )
        # ext_lanes = 2 * ceil(800/100) = 16
        # ext_area = 16 * 0.08 = 1.28
        self.assertAlmostEqual(est.ext_serdes_area_mm2, 1.28)
        # d2d_lanes = 0
        self.assertEqual(est.d2d_lane_count, 0)
        self.assertAlmostEqual(est.d2d_area_mm2, 0.0)

    def test_crossbar_formula(self):
        """crossbar area = N² × crossbar_cell。"""
        est5 = self.estimator.estimate(self.cfg, 5, 1, 0, target_gbps=800)
        est10 = self.estimator.estimate(self.cfg, 10, 1, 0, target_gbps=800)

        # 5² × 0.01 = 0.25
        self.assertAlmostEqual(est5.crossbar_area_mm2, 0.25)
        # 10² × 0.01 = 1.0
        self.assertAlmostEqual(est10.crossbar_area_mm2, 1.0)
        # 端口翻倍 → crossbar 面积 4 倍（O(N²)）
        self.assertAlmostEqual(est10.crossbar_area_mm2 / est5.crossbar_area_mm2, 4.0)

    def test_buffer_formula(self):
        """buffer = N × VC × depth × flit_width / (density × efficiency)。"""
        est = self.estimator.estimate(self.cfg, 5, 1, 0, target_gbps=800)
        # total bits = 5 × 8 × 16 × 256 = 163,840
        # buffer_area = 163840 / (10×10⁶ × 0.1) = 0.16384
        self.assertAlmostEqual(est.buffer_area_mm2, 0.16384, places=5)

    def test_d2d_lane_count(self):
        """d2d link × int_lanes_per_port。"""
        est = self.estimator.estimate(
            self.cfg, crossbar_ports=9, ext_port_count=4,
            d2d_link_count=3, target_gbps=800,
        )
        # int_lanes = ceil(800/16) = 50
        # d2d_lanes = 3 × 50 = 150
        self.assertEqual(est.d2d_lane_count, 150)
        # d2d_area = 150 × 0.012 = 1.8
        self.assertAlmostEqual(est.d2d_area_mm2, 1.8)

    def test_total_area_manual(self):
        """完整手算验证：24 port crossbar, 16 ext, 0 D2D。"""
        est = self.estimator.estimate(
            self.cfg, crossbar_ports=24, ext_port_count=16,
            d2d_link_count=0, target_gbps=800,
        )
        # crossbar = 24² × 0.01 = 5.76
        # buffer = 24 × 8 × 16 × 256 / (10M × 0.1) = 786432 / 1M = 0.786
        # router = 6.546
        # ext_lanes = 16 × 8 = 128
        # ext_area = 128 × 0.08 = 10.24
        # die_area = 40 + 6.546 + 10.24 = 56.786
        self.assertAlmostEqual(est.crossbar_area_mm2, 5.76)
        self.assertAlmostEqual(est.buffer_area_mm2, 0.786432, places=5)
        self.assertAlmostEqual(est.router_total_area_mm2, 6.546432, places=5)
        self.assertAlmostEqual(est.ext_serdes_area_mm2, 10.24)
        self.assertAlmostEqual(est.die_area_mm2, 56.786432, places=5)


class TestDieEstimatorConstraints(unittest.TestCase):
    """reticle limit 和 D2D edge budget 检查。"""

    def setUp(self):
        self.estimator = DieEstimator()
        self.cfg = _sample_cfg()

    def test_area_passes_under_limit(self):
        est = self.estimator.estimate(self.cfg, 24, 16, 0, target_gbps=800)
        self.assertTrue(est.area_ok)  # 57 << 800

    def test_area_fails_over_tiny_limit(self):
        cfg = _sample_cfg(max_die_area_mm2=50)
        est = self.estimator.estimate(cfg, 24, 16, 0, target_gbps=800)
        # die_area ≈ 57 > 50
        self.assertFalse(est.area_ok)

    def test_d2d_edge_passes_small_die(self):
        """小 die 少量 D2D lane → 边沿预算宽松。"""
        est = self.estimator.estimate(
            self.cfg, crossbar_ports=9, ext_port_count=4,
            d2d_link_count=3, target_gbps=800,
        )
        # d2d_lanes = 150
        # die_area ≈ 40 + 0.81 + 0.31 + 2.56 + 1.8 = 45.48
        # perimeter = 4 × √45.48 ≈ 26.98 mm
        # budget = 26.98 × 10 ≈ 270 lanes
        # 150 < 270 → OK
        self.assertTrue(est.d2d_edge_ok)

    def test_d2d_edge_fails_high_density(self):
        """大量 D2D lane 超出边沿供应。"""
        cfg = _sample_cfg(d2d_lanes_per_mm_edge=1.0)  # 极低的边沿密度
        est = self.estimator.estimate(
            cfg, crossbar_ports=9, ext_port_count=4,
            d2d_link_count=20, target_gbps=800,
        )
        # d2d_lanes = 20 × 50 = 1000
        # perimeter ≈ 27mm → budget = 27
        # 1000 > 27 → fail
        self.assertFalse(est.d2d_edge_ok)


class TestDieEstimatorScaling(unittest.TestCase):
    """面积随端口数的缩放行为。"""

    def setUp(self):
        self.estimator = DieEstimator()
        self.cfg = _sample_cfg()

    def test_total_area_increases_with_ports(self):
        est_small = self.estimator.estimate(self.cfg, 5, 2, 0, target_gbps=800)
        est_large = self.estimator.estimate(self.cfg, 50, 20, 10, target_gbps=800)
        self.assertGreater(est_large.die_area_mm2, est_small.die_area_mm2)
        self.assertGreater(est_large.crossbar_area_mm2, est_small.crossbar_area_mm2)

    def test_crossbar_dominates_at_large_N(self):
        """大 N 时 crossbar O(N²) 应主导总面积。"""
        est = self.estimator.estimate(self.cfg, 100, 50, 20, target_gbps=800)
        # crossbar = 100² × 0.01 = 100
        # buffer ≈ 1.64
        # 对于大 N, crossbar >> buffer
        self.assertGreater(est.crossbar_area_mm2, est.buffer_area_mm2 * 5)


if __name__ == "__main__":
    unittest.main()
