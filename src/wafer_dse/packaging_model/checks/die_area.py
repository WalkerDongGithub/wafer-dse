"""面积预算检查。

估算单 die 总面积并与上限比较。
"""

from __future__ import annotations

from wafer_dse.models import NetworkPotential, Requirement
from wafer_dse.packaging_model.checks.base import CheckResult, PackagingCheck


class DieAreaCheck(PackagingCheck):
    """面积早筛检查。

    公式：
        die_area = base_die_area
                 + terminal_count × router_area_per_router
                 + required_external_lanes × area_per_external_lane
                 + required_internal_lanes × area_per_internal_lane
    """

    def run(
        self,
        cfg: dict,
        req: Requirement,
        net: NetworkPotential,
        lanes_per_target_port: int,
        port_count: int,
    ) -> CheckResult:
        required_external = port_count * lanes_per_target_port
        required_internal = net.required_internal_800g_links * lanes_per_target_port

        router_area = net.terminal_count * cfg["router_area_mm2"]
        external_area = required_external * cfg["area_per_external_lane_mm2"]
        internal_area = required_internal * cfg["area_per_internal_lane_mm2"]
        die_area = cfg["base_die_area_mm2"] + router_area + external_area + internal_area

        area_limit = req.max_die_area_mm2 or cfg["max_die_area_mm2"]
        passed = die_area <= area_limit

        return CheckResult(
            check_name="die_area",
            passed=passed,
            values={
                "die_area_mm2": die_area,
                "router_area_mm2": router_area,
                "external_area_mm2": external_area,
                "internal_area_mm2": internal_area,
            },
            reason="" if passed else f"die_area={die_area:.1f} > limit={area_limit:.1f} mm²",
        )
