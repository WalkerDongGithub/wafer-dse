"""功耗预算检查。

估算总功耗（TDP 早筛）并与上限比较。
"""

from __future__ import annotations

from wafer_dse.models import NetworkPotential, Requirement
from wafer_dse.packaging_model.checks.base import CheckResult, PackagingCheck


class PowerCheck(PackagingCheck):
    """功耗早筛检查。

    公式：
        power = base_power
              + terminal_count × router_power_per_router
              + required_external_lanes × power_per_external_lane
              + required_internal_lanes × power_per_internal_lane

    上限取 min(req.max_power_w, cfg.max_power_w)。
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

        router_power = net.terminal_count * cfg["router_power_w"]
        external_power = required_external * cfg["power_per_external_lane_w"]
        internal_power = required_internal * cfg["power_per_internal_lane_w"]
        power = cfg["base_power_w"] + router_power + external_power + internal_power

        power_limit = min(req.max_power_w, cfg["max_power_w"])
        passed = power <= power_limit

        return CheckResult(
            check_name="power",
            passed=passed,
            values={
                "power_w": power,
                "router_power_w": router_power,
                "external_power_w": external_power,
                "internal_power_w": internal_power,
            },
            reason="" if passed else f"power={power:.1f} > limit={power_limit:.1f} W",
        )
