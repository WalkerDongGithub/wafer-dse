from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from wafer_dse.architecture_model import ArchitectureModel
from wafer_dse.models import NetworkPotential, Requirement, Strictness, TopologySpec
from wafer_dse.packaging_model.model import PackagingModel
from wafer_dse.user_interface.driver import run


class ArchitectureModelTest(unittest.TestCase):
    def test_mesh4_reports_network_demand(self):
        req = Requirement(800, 200, Strictness("full"), "unused", port_count=16)
        net = ArchitectureModel().evaluate(req, TopologySpec(kind="mesh", size=4, route="det"))
        self.assertEqual(net.terminal_count, 16)
        self.assertGreater(net.directed_link_count, 0)
        self.assertGreaterEqual(net.required_internal_speedup, 1)
        self.assertEqual(net.certificate_status, "exact_worst_case")


class PackagingModelTest(unittest.TestCase):
    def test_packaging_estimate_couples_internal_links_to_area_and_power(self):
        cfg = Path("configs/example_packaging.yaml")
        req = Requirement(800, 200, Strictness("full"), str(cfg), port_count=16)
        small = NetworkPotential("toy", "det", 16, 10, 800, 1, 10, "exact", "")
        large = NetworkPotential("toy", "det", 16, 10, 200, 4, 40, "exact", "")
        model = PackagingModel(cfg)
        est_small = model.estimate(req, small)
        est_large = model.estimate(req, large)
        self.assertGreater(est_large.die_area_mm2, est_small.die_area_mm2)
        self.assertGreater(est_large.power_w, est_small.power_w)


class UserInterfaceRunTest(unittest.TestCase):
    def test_example_run_writes_reports(self):
        with tempfile.TemporaryDirectory() as td:
            pack = Path("configs/example_packaging.yaml").resolve()
            cfg = Path(td) / "request.yaml"
            cfg.write_text(
                "requirement:\n"
                "  target_nonblocking_gbps_per_port: 800\n"
                "  max_power_w: 200\n"
                "  port_count: 16\n"
                f"  packaging_config: {pack}\n"
                "  strictness:\n"
                "    mode: full\n"
                "topologies:\n"
                "  mesh4:\n"
                "    kind: mesh\n"
                "    size: 4\n"
                "    routes: [det]\n"
                "output:\n"
                "  directory: out\n",
                encoding="utf-8",
            )
            reports = run(cfg)
            self.assertEqual(len(reports), 1)
            self.assertTrue((Path(td) / "out" / "report.md").exists())
            self.assertTrue((Path(td) / "out" / "results.json").exists())


if __name__ == "__main__":
    unittest.main()
