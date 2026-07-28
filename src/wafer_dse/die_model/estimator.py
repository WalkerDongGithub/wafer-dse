"""单 die 物理估计器 — r 个独立 crossbar。

每个 die 上有 r 个 router，每个 router 有独立的 crossbar（M 端口）。
总 crossbar 面积 = r × M² × A_cell（而非 (rM)² × A_cell）。
"""

from __future__ import annotations

import math

from wafer_dse.models import DieEstimate


class DieEstimator:
    """单 die 面积/功耗估计器。

    核心假设：
        1. r 个独立 crossbar，每个 M 端口，面积 ∝ r·M²
        2. buffer ∝ r·M（每端口 VC 缓冲）
        3. D2D PHY 按总端口数线性累加
        4. die 面积受 reticle limit 约束
    """

    def estimate(
        self,
        cfg: dict,
        routers_per_die: int = 1,     # r
        ports_per_router: int = 16,   # M
        d2d_port_count: int = 0,      # |δ(v)| — 该 die 上 off-die D2D 端口数
        target_gbps: float = 800.0,
        int_lane_rate_gbps: float = 32.0,
    ) -> DieEstimate:
        """估算单 die 物理账单。

        Args:
            cfg: 封装工艺配置。
            routers_per_die: r — 该 die 上有几个 router。
            ports_per_router: M — 每个 router 的 crossbar 端口数。
            d2d_port_count: 该 die 上 off-die D2D 端口总数。
            target_gbps: 每端口目标带宽。
            int_lane_rate_gbps: D2D lane 速率 R_e。
        """
        r = routers_per_die
        M = ports_per_router
        total_ports = r * M

        # —— crossbar 面积：r 个小 crossbar ——
        crossbar_area = r * M * M * cfg.get("crossbar_cell_mm2", 0.003)

        # —— buffer 面积：∝ total_ports ——
        vc_count = cfg.get("buffer_vc_count", 8)
        vc_depth = cfg.get("buffer_depth", 16)
        flit_width = cfg.get("flit_width", 256)
        sram_density = cfg.get("sram_density_mbit_per_mm2", 10.0)
        area_efficiency = cfg.get("buffer_area_efficiency", 0.25)

        total_buffer_bits = total_ports * vc_count * vc_depth * flit_width
        buffer_area = total_buffer_bits / (sram_density * 1e6 * area_efficiency)

        router_area = crossbar_area + buffer_area

        # —— D2D PHY ——
        lanes_per_port = math.ceil(target_gbps / int_lane_rate_gbps)
        d2d_lanes = d2d_port_count * lanes_per_port
        d2d_area = d2d_lanes * cfg.get("area_per_internal_lane_mm2", 0.0)
        d2d_power = d2d_lanes * cfg.get("power_per_internal_lane_w", 0.0)

        # —— 汇总 ——
        base_area = cfg.get("base_die_area_mm2", 40.0)
        die_area = base_area + router_area + d2d_area

        base_power = cfg.get("base_power_w", 20.0)
        die_power = base_power + d2d_power

        # —— 约束 ——
        max_die = cfg.get("max_die_area_mm2", 800.0)
        area_ok = die_area <= max_die

        return DieEstimate(
            crossbar_ports=total_ports,
            crossbar_area_mm2=crossbar_area,
            buffer_area_mm2=buffer_area,
            router_total_area_mm2=router_area,
            ext_serdes_count=0,          # 交换 die 无 SerDes
            ext_serdes_area_mm2=0.0,
            ext_serdes_power_w=0.0,
            d2d_link_count=d2d_port_count,
            d2d_lane_count=d2d_lanes,
            d2d_area_mm2=d2d_area,
            d2d_power_w=d2d_power,
            die_area_mm2=die_area,
            die_power_w=die_power,
            area_ok=area_ok,
            d2d_edge_ok=True,           # 面积阵列下不适用周长检查
        )
