"""单 die 物理估计器。

将 crossbar 端口数 + 外部端口数 + D2D 链路数映射为
面积/功耗/可行性判断。不做网络求解，只做物理账单。
"""

from __future__ import annotations

import math

from wafer_dse.models import DieEstimate


class DieEstimator:
    """单 die 面积/功耗/预算估计器。

    核心假设：
        1. crossbar 面积 = N² × crossbar_cell（O(N²) 交叉点矩阵）
        2. buffer 面积 = total_buffer_bits / (SRAM密度 × 面积效率)
        3. 外部 SerDes 按 lane 数线性累加
        4. D2D PHY 按 lane 数线性累加
        5. die 面积受 reticle limit 约束
        6. D2D lane 数受 die 边沿密度约束

    使用方式：
        est = DieEstimator().estimate(cfg, crossbar_ports=24,
                                      ext_port_count=16, d2d_link_count=3)
        print(f"die area = {est.die_area_mm2:.1f} mm²")
    """

    def estimate(
        self,
        cfg: dict,
        crossbar_ports: int,
        ext_port_count: int,
        d2d_link_count: int,
        target_gbps: float = 800.0,
    ) -> DieEstimate:
        """估算单个 die 的完整物理账单。

        Args:
            cfg: 封装工艺配置 dict (cfg["packaging"])。
            crossbar_ports: crossbar 总端口数（local + intra-die + inter-die + global）。
            ext_port_count: 该 die 对外提供的端口数。
            d2d_link_count: 该 die 上跨 die 的 D2D 链路数。
            target_gbps: 每端口目标带宽 (Gbps)，默认 800。

        Returns:
            DieEstimate — 面积/功耗/可行性。
        """
        # —— lane 换算 ——
        ext_lanes_per_port = math.ceil(
            target_gbps / cfg["ext_lane_rate_gbps"]
        )

        int_lanes_per_port = math.ceil(
            target_gbps / cfg["int_lane_rate_gbps"]
        )

        # —— crossbar 面积：O(N²) ——
        crossbar_area = (crossbar_ports * crossbar_ports
                         * cfg.get("crossbar_cell_mm2", 0.003))

        # —— buffer 面积：O(N) ——
        vc_count = cfg.get("buffer_vc_count", 8)
        vc_depth = cfg.get("buffer_depth", 16)
        flit_width = cfg.get("flit_width", 256)
        sram_density = cfg.get("sram_density_mbit_per_mm2", 10.0)
        area_efficiency = cfg.get("buffer_area_efficiency", 0.25)

        total_buffer_bits = crossbar_ports * vc_count * vc_depth * flit_width
        buffer_area = total_buffer_bits / (sram_density * 1e6 * area_efficiency)

        router_area = crossbar_area + buffer_area

        # —— 外部 SerDes ——
        ext_lanes = ext_port_count * ext_lanes_per_port
        ext_area = ext_lanes * cfg["area_per_external_lane_mm2"]
        ext_power = ext_lanes * cfg["power_per_external_lane_w"]

        # —— D2D PHY ——
        d2d_lanes = d2d_link_count * int_lanes_per_port
        d2d_area = d2d_lanes * cfg["area_per_internal_lane_mm2"]
        d2d_power = d2d_lanes * cfg["power_per_internal_lane_w"]

        # —— 汇总 ——
        base = cfg.get("base_die_area_mm2", 40.0)
        die_area = base + router_area + ext_area + d2d_area

        base_power = cfg.get("base_power_w", 20.0)
        die_power = base_power + ext_power + d2d_power
        # 注意：router 的动态功耗已包含在 power_per_internal_lane 中，
        # buffer 漏电已包含在 base_power 中。这是简化处理。

        # —— 约束检查 ——
        max_die = cfg.get("max_die_area_mm2", 800.0)
        area_ok = die_area <= max_die

        # D2D 边沿预算
        if die_area > 0:
            perimeter = 4.0 * math.sqrt(die_area)  # 正方形近似
        else:
            perimeter = 0.0
        d2d_lane_budget = perimeter * cfg.get("d2d_lanes_per_mm_edge", 10.0)
        d2d_edge_ok = d2d_lanes <= d2d_lane_budget

        return DieEstimate(
            crossbar_ports=crossbar_ports,
            crossbar_area_mm2=crossbar_area,
            buffer_area_mm2=buffer_area,
            router_total_area_mm2=router_area,
            ext_serdes_count=ext_port_count,
            ext_serdes_area_mm2=ext_area,
            ext_serdes_power_w=ext_power,
            d2d_link_count=d2d_link_count,
            d2d_lane_count=d2d_lanes,
            d2d_area_mm2=d2d_area,
            d2d_power_w=d2d_power,
            die_area_mm2=die_area,
            die_power_w=die_power,
            area_ok=area_ok,
            d2d_edge_ok=d2d_edge_ok,
        )
