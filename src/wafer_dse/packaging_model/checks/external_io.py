"""外部端口 IO 预算检查。

将端口数换算为 lane 数，与封装外部 lane 上限比较。
"""

from __future__ import annotations

from wafer_dse.models import NetworkPotential, Requirement
from wafer_dse.packaging_model.checks.base import CheckResult, PackagingCheck


class ExternalIOCheck(PackagingCheck):
    """外部端口 lane 预算检查。

    公式：
        required_external_lanes = port_count × lanes_per_target_port
        external_budget_ports = max_external_lanes / lanes_per_target_port

    检查：port_count ≤ external_budget_ports。
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
        external_budget = cfg["max_external_lanes"] / lanes_per_target_port
        passed = port_count <= external_budget

        return CheckResult(
            check_name="external_io",
            passed=passed,
            values={
                "required_external_lanes": float(required_external),
                "external_budget_ports": external_budget,
            },
            reason=""
            if passed
            else f"ports={port_count} > external budget={external_budget:.1f}",
        )
