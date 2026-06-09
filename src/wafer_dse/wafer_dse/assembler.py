"""晶圆级 DSE 汇编器。

递归结构的两层：
    Layer 1 (Group): WaferAssembler 枚举 (a,p,h,g) → 调用 GroupExplorer
    Layer 2 (Die):   GroupExplorer 枚举 K → 调用 ArchitectureModel + DieEstimator

组间互连走 package 基板（UCIe Standard Package），受 max_internal_lanes 约束。
组内互连走 interposer（UCIe Advanced Package），受 die 边沿 D2D 密度约束。
"""

from __future__ import annotations

import math

from wafer_dse.group_dse.explorer import GroupExplorer
from wafer_dse.models import Requirement, WaferPlan


class WaferAssembler:
    """晶圆级 DSE 汇编器。

    使用方式：
        assembler = WaferAssembler()
        plans = assembler.explore(total_ports=64, req=req, cfg=cfg)
        for plan in plans:
            print(f"{plan.group_count} groups, {plan.total_dies} dies, "
                  f"area={plan.total_area_mm2:.0f}mm²")
    """

    def explore(
        self,
        total_ports: int,
        req: Requirement,
        cfg: dict,
        h_values: tuple[int, ...] = (2, 4),
    ) -> list[WaferPlan]:
        """枚举所有 (a, p, h, g) 组合，输出晶圆方案。

        Args:
            total_ports: 晶圆总端口数。
            req: 用户需求（target_gbps, strictness 等）。
            cfg: 封装工艺配置。
            h_values: 要尝试的全局端口数 (per router)，默认 (2, 4)。

        Returns:
            WaferPlan 列表 — 按 total_dies 升序排列。
        """
        results: list[WaferPlan] = []
        explorer = GroupExplorer()

        # 枚举所有满足 a × p × g = total_ports 的组合
        for a in self._divisors(total_ports):
            for h in h_values:
                # 每个 router 需要足够端口: p + (a-1) + h
                # 至少 p ≥ 1
                remaining = total_ports // a
                for p in self._divisors(remaining):
                    g = remaining // p  # group 数
                    if g < 1:
                        continue

                    # 检查 crossbar 端口数不会太离谱
                    # （单 die K=1 时 crossbar_ports = a×p + (a-1) + a×h）
                    max_cb_ports = a * p + (a - 1) + a * h
                    if max_cb_ports > cfg.get("max_crossbar_ports", 256):
                        continue

                    # —— 对每个 group 跑 GroupExplorer ——
                    group_plan = explorer.explore(a, p, h, req, cfg)

                    if group_plan.best_partition is None:
                        continue  # 这个 group 配置物理上不可行

                    # —— 组间互连预算 ——
                    # g 个 group 全互联: g(g-1) 条组间链路
                    # 每条组间链路 = a×h 个 global port 成对
                    # 简化：group 间全互联，每个 group-pair 一条等效链路
                    inter_group_links = g * (g - 1)  # 全互联
                    #  每条组间链路用 pkg 通道: 用 int_lanes 计算
                    int_lanes_per_port = math.ceil(
                        req.target_nonblocking_gbps_per_port
                        / cfg["int_lane_rate_gbps"]
                    )
                    inter_group_lanes = inter_group_links * int_lanes_per_port

                    # 组间走 package 基板，检查 max_internal_lanes
                    pkg_lane_budget = cfg.get("max_internal_lanes", 1600)
                    inter_group_ok = inter_group_lanes <= pkg_lane_budget

                    total_dies = g * group_plan.best_partition.die_count
                    total_area = g * group_plan.best_partition.total_area_mm2
                    total_power = g * group_plan.best_partition.total_power_w

                    plan = WaferPlan(
                        group_count=g,
                        group_config=f"a{a}_p{p}_h{h}",
                        groups=tuple(group_plan for _ in range(g)),
                        inter_group_topo="full_mesh",
                        inter_group_link_count=inter_group_links,
                        inter_group_lane_count=inter_group_lanes,
                        total_terminals=g * a * p,
                        total_dies=total_dies,
                        total_area_mm2=total_area,
                        total_power_w=total_power,
                        feasible=(inter_group_ok
                                  and group_plan.best_partition.feasible),
                    )
                    results.append(plan)

        results.sort(key=lambda p: (p.total_dies, p.total_area_mm2))
        return results

    @staticmethod
    def _divisors(n: int) -> list[int]:
        """返回 n 的所有正因子，升序排列。"""
        divs = []
        for i in range(1, int(math.sqrt(n)) + 1):
            if n % i == 0:
                divs.append(i)
                if i != n // i:
                    divs.append(n // i)
        divs.sort()
        return divs
