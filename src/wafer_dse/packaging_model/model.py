"""封装级初筛。

输入：用户需求、体系结构级网络潜能、封装工艺配置。
输出：单 die/package 面积、功耗、外部端口预算、内部链路预算和通过/失败标志。
目的：回答“网络要求的端口和内部链路，当前封装配置是否承载得住”。
"""

from __future__ import annotations

import math
from pathlib import Path

from wafer_dse.config import load_config
from wafer_dse.models import NetworkPotential, PackagingEstimate, Requirement


class PackagingModel:
    """封装工艺模型：用少量配置参数做早期物理预算估计。"""

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.cfg = load_config(self.config_path)["packaging"]

    def estimate(self, req: Requirement, net: NetworkPotential) -> PackagingEstimate:
        """输入需求和网络潜能，输出封装级初筛结果。"""
        # 1) 把目标带宽换算成 lane 数；lane_rate 是工艺/SerDes 假设。
        lanes_per_target_port = math.ceil(req.target_nonblocking_gbps_per_port / self.cfg["lane_rate_gbps"])
        port_count = req.port_count or net.terminal_count
        required_external_lanes = port_count * lanes_per_target_port
        required_internal_lanes = net.required_internal_800g_links * lanes_per_target_port

        # 2) 把封装最多可提供的 lane 数换算成 800G-equivalent port/link 预算。
        external_budget = self.cfg["max_external_lanes"] / lanes_per_target_port
        internal_budget = self.cfg["max_internal_lanes"] / lanes_per_target_port

        # 3) 用线性早筛模型估算面积：固定面积 + router + external lane + internal lane。
        router_area = net.terminal_count * self.cfg["router_area_mm2"]
        external_area = required_external_lanes * self.cfg["area_per_external_lane_mm2"]
        internal_area = required_internal_lanes * self.cfg["area_per_internal_lane_mm2"]
        die_area = self.cfg["base_die_area_mm2"] + router_area + external_area + internal_area

        # 4) 用同样的资源分解估算功耗；这是 TDP 早筛，不是 post-layout power。
        router_power = net.terminal_count * self.cfg["router_power_w"]
        external_power = required_external_lanes * self.cfg["power_per_external_lane_w"]
        internal_power = required_internal_lanes * self.cfg["power_per_internal_lane_w"]
        power = self.cfg["base_power_w"] + router_power + external_power + internal_power

        # 5) 分别检查面积、功耗、外部端口和内部链路四个硬条件。
        area_limit = req.max_die_area_mm2 or self.cfg["max_die_area_mm2"]
        area_ok = die_area <= area_limit
        power_ok = power <= min(req.max_power_w, self.cfg["max_power_w"])
        external_ok = port_count <= external_budget
        internal_ok = net.required_internal_800g_links <= internal_budget

        return PackagingEstimate(
            die_area_mm2=die_area,
            power_w=power,
            external_800g_port_budget=external_budget,
            internal_800g_link_budget=internal_budget,
            required_external_lanes=required_external_lanes,
            required_internal_lanes=required_internal_lanes,
            area_ok=area_ok,
            power_ok=power_ok,
            external_ports_ok=external_ok,
            internal_links_ok=internal_ok,
            details={
                "lanes_per_target_port": lanes_per_target_port,
                "router_area_mm2": router_area,
                "external_area_mm2": external_area,
                "internal_area_mm2": internal_area,
                "router_power_w": router_power,
                "external_power_w": external_power,
                "internal_power_w": internal_power,
            },
        )
