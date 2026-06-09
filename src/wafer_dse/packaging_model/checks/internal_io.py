"""内部链路 IO 预算检查。

将内部 800G-equivalent 链路数换算为 lane 数，与封装内部 lane 上限比较。
"""

from __future__ import annotations

from wafer_dse.models import NetworkPotential, Requirement
from wafer_dse.packaging_model.checks.base import CheckResult, PackagingCheck


class InternalIOCheck(PackagingCheck):
    """内部链路 lane 预算检查。

    公式：
        required_internal_lanes = required_internal_800g_links × lanes_per_target_port
        internal_budget_links = max_internal_lanes / lanes_per_target_port

    检查：required_internal_800g_links ≤ internal_budget_links。
    """

    def run(
        self,
        cfg: dict,
        req: Requirement,
        net: NetworkPotential,
        ext_lanes_per_port: int,
        int_lanes_per_port: int,
        port_count: int,
    ) -> CheckResult:
        required_internal = net.required_internal_800g_links * int_lanes_per_port
        internal_budget = cfg["max_internal_lanes"] / int_lanes_per_port
        passed = net.required_internal_800g_links <= internal_budget

        return CheckResult(
            check_name="internal_io",
            passed=passed,
            values={
                "required_internal_lanes": float(required_internal),
                "internal_budget_links": internal_budget,
            },
            reason=""
            if passed
            else f"internal_links={net.required_internal_800g_links} > budget={internal_budget:.1f}",
        )
