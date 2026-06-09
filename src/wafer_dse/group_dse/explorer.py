"""Group 级 DSE 浏览器。

对一个 Dragonfly group 配置 (a, p, h)：
    1. 用 ArchitectureModel 评估逻辑拓扑的网络性能。
    2. 枚举 K = 1 .. a 种物理 die 分割方案。
    3. 对每种分割调用 DieEstimator 计算单 die 账单。
    4. 汇总为 GroupPlan（包含所有可行方案，按 die 数排序）。
"""

from __future__ import annotations

from wafer_dse.architecture_model.model import ArchitectureModel
from wafer_dse.die_model.estimator import DieEstimator
from wafer_dse.models import (
    GroupPlan,
    PartitionPlan,
    Requirement,
    TopologySpec,
)


class GroupExplorer:
    """Group 级 DSE：找出最小可行的 die 数量来实现一个 Dragonfly group。

    使用方式：
        explorer = GroupExplorer()
        plan = explorer.explore(a=4, p=4, h=2, req=req, cfg=cfg)
        print(f"best: {plan.best_partition.die_count} dies")
    """

    def explore(
        self,
        a: int,
        p: int,
        h: int,
        req: Requirement,
        cfg: dict,
    ) -> GroupPlan:
        """对一个 group 枚举所有物理分割方案。

        Args:
            a: 每组 logical router 数。
            p: 每个 router 的 terminal 数。
            h: 每个 router 的全局端口数。
            req: 用户需求。
            cfg: 封装工艺配置。

        Returns:
            GroupPlan — 包含网络评估 + 所有可行分割方案。
        """
        # —— 第 1 步：评估逻辑拓扑的网络性能 ——
        spec = TopologySpec(kind="dragonfly", a=a, p=p, h=h, route="det")
        net = ArchitectureModel().evaluate(req, spec)

        # —— 第 2 步：枚举物理分割 K = 1 .. a ——
        estimator = DieEstimator()
        target_gbps = req.target_nonblocking_gbps_per_port
        partitions: list[PartitionPlan] = []

        for K in range(1, a + 1):
            if a % K != 0:
                continue  # 当前只支持均匀分割

            r = a // K  # 每个 die 上的 logical router 数

            # crossbar 端口数公式:
            #   r×p:  本 die 上的 terminal 端口
            #   (r-1): 本 die 上多个 router 的内部全互联
            #   (K-1): 连接到同 group 其他 die 的端口
            #   r×h:  本 die 的全局出口端口
            crossbar_ports = r * p + (r - 1) + (K - 1) + r * h
            ext_ports = r * p          # 对外端口数
            d2d_links = (K - 1)        # 跨 die 链路数

            # 注意：当 speedup > 1 时，D2D 链路需要乘以 speedup
            # 因为每条逻辑链路需要更多物理 lane
            if net.required_internal_speedup > 1:
                d2d_links *= net.required_internal_speedup

            die = estimator.estimate(
                cfg,
                crossbar_ports=crossbar_ports,
                ext_port_count=ext_ports,
                d2d_link_count=d2d_links,
                target_gbps=target_gbps,
            )

            # 构造 K 个相同 die 的列表（均匀分割）
            dies = tuple(die for _ in range(K))

            plan = PartitionPlan(
                die_count=K,
                routers_per_die=r,
                dies=dies,
                total_area_mm2=K * die.die_area_mm2,
                total_power_w=K * die.die_power_w,
                feasible=die.area_ok and die.d2d_edge_ok,
            )
            partitions.append(plan)

        # —— 第 3 步：汇总 ——
        best = None
        for plan in partitions:
            if plan.feasible:
                best = plan
                break  # 第一个可行的就是 die 数最少的

        return GroupPlan(
            a=a,
            p=p,
            h=h,
            total_terminals=a * p,
            network=net,
            partitions=tuple(partitions),
            best_partition=best,
        )
