"""封装检查单元严格测试。

测试覆盖：
    - DieAreaCheck    —— 面积预算：正常、超限、req 优先 cfg
    - PowerCheck      —— 功耗预算：正常、超限、min(req, cfg)
    - ExternalIOCheck —— 外部端口：正常、超限
    - InternalIOCheck —— 内部链路：正常、超限
    - CheckResult     —— 不可变性
    - PackagingModel  —— 编排层聚合 + 真实配置文件
"""

from __future__ import annotations

import math
import unittest
from pathlib import Path

from wafer_dse.models import NetworkPotential, PackagingEstimate, Requirement, Strictness
from wafer_dse.packaging_model import (
    ALL_CHECKS,
    CheckResult,
    DieAreaCheck,
    ExternalIOCheck,
    InternalIOCheck,
    PackagingCheck,
    PackagingModel,
    PowerCheck,
)


# ---------------------------------------------------------------------------
# 共享 fixtures
# ---------------------------------------------------------------------------

def _sample_cfg() -> dict:
    """与 example_packaging.yaml 一致的 UCIe 基线配置。

    外部端口: 100G/lane Ethernet SerDes
    D2D 互连: UCIe Advanced Package 16 GT/s, 45μm
    """
    return {
        "max_die_area_mm2": 800,
        "max_power_w": 220,
        "ext_lane_rate_gbps": 100,
        "int_lane_rate_gbps": 16,
        "max_external_lanes": 160,
        "max_internal_lanes": 1600,
        "base_die_area_mm2": 40,
        "router_area_mm2": 1.5,
        "area_per_external_lane_mm2": 0.08,
        "area_per_internal_lane_mm2": 0.012,     # UCIe: PHY 0.006 + 走线 0.006
        "base_power_w": 20,
        "router_power_w": 0.8,
        "power_per_external_lane_w": 0.35,
        "power_per_internal_lane_w": 0.005,      # UCIe: 16G × 0.25 pJ/bit + margin
    }


def _sample_req(**overrides) -> Requirement:
    """默认：800G/port, 200W, full strictness, 16 ports, 800mm² die limit。"""
    defaults = dict(
        target_nonblocking_gbps_per_port=800.0,
        max_power_w=200.0,
        strictness=Strictness("full"),
        packaging_config="unused",
        port_count=16,
        max_die_area_mm2=800.0,
    )
    defaults.update(overrides)
    return Requirement(**defaults)


def _sample_net(**overrides) -> NetworkPotential:
    """mesh4x4 det: 16 terminals, 48 directed links, speedup=3, 144 internal links。"""
    defaults = dict(
        topology_name="mesh4x4",
        route="det",
        terminal_count=16,
        directed_link_count=48,
        nonblocking_gbps_per_port=266.7,
        required_internal_speedup=3,
        required_internal_800g_links=144,
        certificate_status="exact_worst_case",
        worst_link="(0, 1)",
    )
    defaults.update(overrides)
    return NetworkPotential(**defaults)


# ---------------------------------------------------------------------------
# DieAreaCheck
# ---------------------------------------------------------------------------


class TestDieAreaCheck(unittest.TestCase):

    def setUp(self):
        self.check = DieAreaCheck()
        self.cfg = _sample_cfg()
        self.req = _sample_req()
        self.net = _sample_net()
        # ext_lanes = ceil(800/100) = 8, int_lanes = ceil(800/16) = 50
        self.ext_lanes = 8
        self.int_lanes = 50
        self.ports = 16

    # —— 正确性 ——

    def test_computed_area_matches_manual(self):
        """手工验算面积公式。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        # router_area = 16 * 1.5 = 24
        # external_area = (16*8) * 0.08 = 10.24
        # internal_area = (144*50) * 0.012 = 86.4
        # die_area = 40 + 24 + 10.24 + 86.4 = 160.64
        self.assertAlmostEqual(result.values["router_area_mm2"], 24.0)
        self.assertAlmostEqual(result.values["external_area_mm2"], 10.24)
        self.assertAlmostEqual(result.values["internal_area_mm2"], 86.4)
        self.assertAlmostEqual(result.values["die_area_mm2"], 160.64)

    def test_different_port_count_changes_area(self):
        """端口数增加 → 面积增加。"""
        r16 = self.check.run(self.cfg, self.req, self.net,
                             self.ext_lanes, self.int_lanes, 16)
        r32 = self.check.run(self.cfg, self.req, self.net,
                             self.ext_lanes, self.int_lanes, 32)
        self.assertGreater(r32.values["die_area_mm2"], r16.values["die_area_mm2"])

    def test_different_speedup_changes_area(self):
        """speedup 增加 → 内部链路面积增加。"""
        net_small = _sample_net(required_internal_800g_links=72, required_internal_speedup=1)
        net_large = _sample_net(required_internal_800g_links=288, required_internal_speedup=6)
        r_small = self.check.run(self.cfg, self.req, net_small,
                                 self.ext_lanes, self.int_lanes, 16)
        r_large = self.check.run(self.cfg, self.req, net_large,
                                 self.ext_lanes, self.int_lanes, 16)
        self.assertGreater(
            r_large.values["internal_area_mm2"],
            r_small.values["internal_area_mm2"],
        )

    # —— 通过 / 失败 ——

    def test_passes_when_within_limit(self):
        """die_area=160.64 < 800 → 通过。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertTrue(result.passed)
        self.assertEqual(result.reason, "")

    def test_fails_when_over_limit(self):
        """将 limit 设为 50 → 面积 160.64 超标。"""
        cfg = {**self.cfg, "max_die_area_mm2": 50}
        req = _sample_req(max_die_area_mm2=None)  # 让 req 不覆盖
        result = self.check.run(cfg, req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertFalse(result.passed)
        self.assertIn("> limit", result.reason)

    def test_req_limit_overrides_cfg_limit(self):
        """req.max_die_area_mm2 优先于 cfg.max_die_area_mm2。"""
        cfg = {**self.cfg, "max_die_area_mm2": 50}    # cfg: 50
        req = _sample_req(max_die_area_mm2=200.0)       # req: 200 → 应通过
        result = self.check.run(cfg, req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertTrue(result.passed, f"expected pass with req limit=200, got {result.reason}")

    # —— 边界 ——

    def test_zero_terminals(self):
        """0 terminal 仍有 base area。"""
        net = _sample_net(terminal_count=0, required_internal_800g_links=0)
        result = self.check.run(self.cfg, self.req, net,
                                self.ext_lanes, self.int_lanes, 0)
        self.assertAlmostEqual(result.values["die_area_mm2"], self.cfg["base_die_area_mm2"])

    def test_check_name(self):
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertEqual(result.check_name, "die_area")


# ---------------------------------------------------------------------------
# PowerCheck
# ---------------------------------------------------------------------------


class TestPowerCheck(unittest.TestCase):

    def setUp(self):
        self.check = PowerCheck()
        self.cfg = _sample_cfg()
        self.req = _sample_req()
        self.net = _sample_net()
        self.ext_lanes = 8
        self.int_lanes = 50
        self.ports = 16

    # —— 正确性 ——

    def test_computed_power_matches_manual(self):
        """手工验算功耗公式。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        # router_power = 16 * 0.8 = 12.8
        # external_power = (16*8) * 0.35 = 44.8
        # internal_power = (144*50) * 0.005 = 36.0
        # total = 20 + 12.8 + 44.8 + 36.0 = 113.6
        self.assertAlmostEqual(result.values["router_power_w"], 12.8)
        self.assertAlmostEqual(result.values["external_power_w"], 44.8)
        self.assertAlmostEqual(result.values["internal_power_w"], 36.0)
        self.assertAlmostEqual(result.values["power_w"], 113.6)

    # —— 通过 / 失败 ——

    def test_passes_when_within_limit(self):
        """power=113.6 < min(200, 220)=200 → 通过。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertTrue(result.passed)

    def test_fails_when_over_req_limit(self):
        """req.max_power_w=50 → power=113.6 超标。"""
        req = _sample_req(max_power_w=50.0)
        result = self.check.run(self.cfg, req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertFalse(result.passed)
        self.assertIn("> limit", result.reason)

    def test_fails_when_over_cfg_limit(self):
        """cfg.max_power_w=50 < req.max_power_w=200 → min=50, power=113.6 超标。"""
        cfg = {**self.cfg, "max_power_w": 50}
        result = self.check.run(cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertFalse(result.passed)

    def test_uses_min_of_req_and_cfg(self):
        """上限取 min(req.max_power_w, cfg.max_power_w)。"""
        # req=200, cfg=100 → limit=100, power=113.6 → 超标
        cfg = {**self.cfg, "max_power_w": 100}
        result = self.check.run(cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertFalse(result.passed,
                         f"power=113.6 > min(200, 100)=100 should fail")

    # —— 边界 ——

    def test_zero_lanes_zero_power_components(self):
        """lanes=0 → external 和 internal power 为 0。"""
        result = self.check.run(self.cfg, self.req, self.net, 0, 0, 0)
        self.assertAlmostEqual(result.values["external_power_w"], 0.0)
        self.assertAlmostEqual(result.values["internal_power_w"], 0.0)

    def test_check_name(self):
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertEqual(result.check_name, "power")


# ---------------------------------------------------------------------------
# ExternalIOCheck
# ---------------------------------------------------------------------------


class TestExternalIOCheck(unittest.TestCase):

    def setUp(self):
        self.check = ExternalIOCheck()
        self.cfg = _sample_cfg()
        self.req = _sample_req()
        self.net = _sample_net()
        self.ext_lanes = 8
        self.int_lanes = 50
        self.ports = 16

    # —— 正确性 ——

    def test_budget_calculation(self):
        """external_budget = max_external_lanes / ext_lanes = 160/8 = 20。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertAlmostEqual(result.values["external_budget_ports"], 20.0)
        self.assertAlmostEqual(result.values["required_external_lanes"], 128.0)

    # —— 通过 / 失败 ——

    def test_passes_when_ports_fit_budget(self):
        """16 ports ≤ 20 → 通过。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, 16)
        self.assertTrue(result.passed)

    def test_fails_when_ports_exceed_budget(self):
        """30 ports > 20 budget → 失败。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, 30)
        self.assertFalse(result.passed)
        self.assertIn("external budget", result.reason)

    def test_exact_boundary(self):
        """恰好等于 budget → 通过。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, 20)
        self.assertTrue(result.passed)

    def test_budget_changes_with_lane_rate(self):
        """lane_rate 越高 → 每端口 lane 越少 → budget 越多。"""
        # ext_lanes=4 (ceil(800/200)=4), budget=160/4=40
        result = self.check.run(self.cfg, self.req, self.net,
                                ext_lanes_per_port=4, int_lanes_per_port=50, port_count=16)
        self.assertAlmostEqual(result.values["external_budget_ports"], 40.0)

    def test_check_name(self):
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertEqual(result.check_name, "external_io")


# ---------------------------------------------------------------------------
# InternalIOCheck
# ---------------------------------------------------------------------------


class TestInternalIOCheck(unittest.TestCase):

    def setUp(self):
        self.check = InternalIOCheck()
        self.cfg = _sample_cfg()
        self.req = _sample_req()
        self.net = _sample_net()
        self.ext_lanes = 8
        self.int_lanes = 50
        self.ports = 16

    # —— 正确性 ——

    def test_budget_calculation(self):
        """internal_budget = max_internal_lanes / int_lanes = 1600/50 = 32。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertAlmostEqual(result.values["internal_budget_links"], 32.0)
        self.assertAlmostEqual(result.values["required_internal_lanes"], 144 * 50.0)

    # —— 通过 / 失败 ——

    def test_passes_when_links_fit_budget(self):
        """144 links ≤ 32 → 失败（UCIe 内部 budget 更紧）。"""
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertFalse(result.passed)

    def test_fails_when_links_exceed_budget(self):
        """300 links > 32 → 失败。"""
        net = _sample_net(required_internal_800g_links=300)
        result = self.check.run(self.cfg, self.req, net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertFalse(result.passed)
        self.assertIn("internal_links", result.reason)

    def test_exact_boundary(self):
        """恰好等于 budget → 通过。"""
        net = _sample_net(required_internal_800g_links=32)
        result = self.check.run(self.cfg, self.req, net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertTrue(result.passed)

    def test_zero_links_always_passes(self):
        net = _sample_net(required_internal_800g_links=0)
        result = self.check.run(self.cfg, self.req, net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertTrue(result.passed)

    def test_check_name(self):
        result = self.check.run(self.cfg, self.req, self.net,
                                self.ext_lanes, self.int_lanes, self.ports)
        self.assertEqual(result.check_name, "internal_io")


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------


class TestCheckResult(unittest.TestCase):

    def test_defaults(self):
        cr = CheckResult("test")
        self.assertEqual(cr.check_name, "test")
        self.assertEqual(cr.passed, False)
        self.assertEqual(cr.values, {})
        self.assertEqual(cr.reason, "")

    def test_immutable(self):
        cr = CheckResult("test", True, {"x": 1.0}, "ok")
        with self.assertRaises(Exception):
            cr.passed = False
        with self.assertRaises(Exception):
            cr.check_name = "other"


# ---------------------------------------------------------------------------
# ALL_CHECKS registry
# ---------------------------------------------------------------------------


class TestCheckRegistry(unittest.TestCase):

    def test_all_four_checks_registered(self):
        names = {type(c).__name__ for c in ALL_CHECKS}
        self.assertEqual(names, {"DieAreaCheck", "PowerCheck", "ExternalIOCheck", "InternalIOCheck"})

    def test_all_are_packaging_checks(self):
        for check in ALL_CHECKS:
            self.assertIsInstance(check, PackagingCheck)


# ---------------------------------------------------------------------------
# PackagingModel orchestrator
# ---------------------------------------------------------------------------


class TestPackagingModelOrchestrator(unittest.TestCase):

    def setUp(self):
        self.model = PackagingModel("configs/example_packaging.yaml")
        self.req = _sample_req(packaging_config="configs/example_packaging.yaml")
        self.net = _sample_net()

    # —— 基本功能 ——

    def test_returns_packaging_estimate(self):
        est = self.model.estimate(self.req, self.net)
        self.assertIsInstance(est, PackagingEstimate)

    def test_all_fields_populated(self):
        est = self.model.estimate(self.req, self.net)
        self.assertGreater(est.die_area_mm2, 0)
        self.assertGreater(est.power_w, 0)
        self.assertGreater(est.external_800g_port_budget, 0)
        self.assertGreater(est.internal_800g_link_budget, 0)
        self.assertGreater(est.required_external_lanes, 0)
        self.assertGreater(est.required_internal_lanes, 0)
        self.assertIsInstance(est.area_ok, bool)
        self.assertIsInstance(est.power_ok, bool)
        self.assertIsInstance(est.external_ports_ok, bool)
        self.assertIsInstance(est.internal_links_ok, bool)

    def test_mesh4_det_all_pass(self):
        """标准 16 端口 mesh4x4:
        在 UCIe 配置下 internal_links 可能因 50 lane/link 超过 budget。
        但其他检查应通过。"""
        est = self.model.estimate(self.req, self.net)
        self.assertTrue(est.area_ok)       # 160 < 800 ✓
        self.assertTrue(est.power_ok)      # 113.6 < 200 ✓
        self.assertTrue(est.external_ports_ok)  # 16 ≤ 20 ✓
        # internal: 144 links × 50 lane = 7200 lane > 1600 → False
        self.assertFalse(est.internal_links_ok)

    # —— 失败场景 ——

    def test_area_fails_with_tiny_limit(self):
        """面积上限极小 → area_ok=False。"""
        req = _sample_req(
            max_die_area_mm2=10.0,
            packaging_config="configs/example_packaging.yaml",
        )
        est = self.model.estimate(req, self.net)
        self.assertFalse(est.area_ok)
        self.assertGreater(est.die_area_mm2, 10.0)

    def test_power_fails_with_tiny_limit(self):
        """功耗上限极小 → power_ok=False。"""
        req = _sample_req(
            max_power_w=10.0,
            packaging_config="configs/example_packaging.yaml",
        )
        est = self.model.estimate(req, self.net)
        self.assertFalse(est.power_ok)
        self.assertGreater(est.power_w, 10.0)

    def test_external_fails_with_too_many_ports(self):
        """端口过多 → external_ports_ok=False。"""
        req = _sample_req(
            port_count=100,
            packaging_config="configs/example_packaging.yaml",
        )
        est = self.model.estimate(req, self.net)
        self.assertFalse(est.external_ports_ok)

    def test_internal_fails_with_too_much_speedup(self):
        """内部链路过多 → internal_links_ok=False。"""
        net = _sample_net(
            required_internal_800g_links=9999,
            required_internal_speedup=999,
        )
        est = self.model.estimate(self.req, net)
        self.assertFalse(est.internal_links_ok)

    # —— details 聚合 ——

    def test_details_contains_all_check_values(self):
        est = self.model.estimate(self.req, self.net)
        self.assertIn("ext_lanes_per_target_port", est.details)
        self.assertIn("int_lanes_per_target_port", est.details)
        self.assertIn("die_area_mm2", est.details)
        self.assertIn("power_w", est.details)
        self.assertIn("required_external_lanes", est.details)
        self.assertIn("required_internal_lanes", est.details)

    # —— lane 数计算 ——

    def test_lanes_per_port_ceiling(self):
        """800G/100G=8 ext; 801G→9 ext。800G/16G=50 int; 801G→51 int。"""
        req = _sample_req(
            target_nonblocking_gbps_per_port=801.0,
            packaging_config="configs/example_packaging.yaml",
        )
        est = self.model.estimate(req, self.net)
        self.assertAlmostEqual(est.details["ext_lanes_per_target_port"], 9.0)
        self.assertAlmostEqual(est.details["int_lanes_per_target_port"], 51.0)

    def test_port_count_falls_back_to_terminal_count(self):
        """req.port_count=None 时使用 net.terminal_count。"""
        req = _sample_req(port_count=None, packaging_config="configs/example_packaging.yaml")
        est = self.model.estimate(req, self.net)
        # 16 terminals → 16 * 8 = 128 external lanes
        self.assertAlmostEqual(est.details["required_external_lanes"], 128.0)


if __name__ == "__main__":
    unittest.main()
