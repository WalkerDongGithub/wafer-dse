"""封装级初筛 —— 编排层。

职责：
    1. 加载封装工艺配置。
    2. 将目标带宽换算为 lane 数（共享前提）。
    3. 依次运行所有封装检查单元（面积 / 功耗 / 外部 IO / 内部 IO）。
    4. 聚合检查结果为 PackagingEstimate。

本模块是薄编排层；每个检查单元见 checks/ 子包。
"""

from __future__ import annotations

import math
from pathlib import Path

from wafer_dse.config import load_config
from wafer_dse.models import NetworkPotential, PackagingEstimate, Requirement
from wafer_dse.packaging_model.checks import ALL_CHECKS


class PackagingModel:
    """封装工艺模型：用少量配置参数做早期物理预算估计。

    使用方式：

        model = PackagingModel("configs/example_packaging.yaml")
        est = model.estimate(req, net)
        print(f"area={est.die_area_mm2:.1f} mm², power={est.power_w:.1f} W")
    """

    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self.cfg: dict = load_config(self.config_path)["packaging"]

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def estimate(self, req: Requirement, net: NetworkPotential) -> PackagingEstimate:
        """输入需求和网络潜能，运行全部封装检查并聚合为 PackagingEstimate。

        流水线：
            1. lane 数换算（共享前提）
            2. 依次运行 ALL_CHECKS 中的每个检查单元
            3. 聚合 values 并汇总通过/失败标志
        """
        # —— 第 1 步：lane 数换算 ——
        lanes_per_port = math.ceil(
            req.target_nonblocking_gbps_per_port / self.cfg["lane_rate_gbps"]
        )
        port_count = req.port_count or net.terminal_count

        # —— 第 2 步：运行所有检查单元 ——
        results = [
            check.run(self.cfg, req, net, lanes_per_port, port_count)
            for check in ALL_CHECKS
        ]

        # —— 第 3 步：聚合 ——
        merged: dict[str, float] = {
            "lanes_per_target_port": float(lanes_per_port),
        }
        passed_map: dict[str, bool] = {}
        for r in results:
            merged.update(r.values)
            passed_map[r.check_name] = r.passed

        external_budget = self.cfg["max_external_lanes"] / lanes_per_port
        internal_budget = self.cfg["max_internal_lanes"] / lanes_per_port

        return PackagingEstimate(
            die_area_mm2=merged.get("die_area_mm2", 0.0),
            power_w=merged.get("power_w", 0.0),
            external_800g_port_budget=external_budget,
            internal_800g_link_budget=internal_budget,
            required_external_lanes=int(merged.get("required_external_lanes", 0)),
            required_internal_lanes=int(merged.get("required_internal_lanes", 0)),
            area_ok=passed_map.get("die_area", False),
            power_ok=passed_map.get("power", False),
            external_ports_ok=passed_map.get("external_io", False),
            internal_links_ok=passed_map.get("internal_io", False),
            details=merged,
        )
