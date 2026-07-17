"""
拓扑边 → 分区 → 互连标准的离散搜索问题定义

这是 Phase 2 的核心: 将体系结构层证明可行的逻辑拓扑，映射到
晶圆分区网格上的物理布线方案。

问题定义 (不绑定求解方法)
============================

给定:
  - 逻辑拓扑图 G = (V, E), 每条边 e 需求带宽 B_e  [Gbps]
  - 分区网格 P (N×N), Manhattan 距离 d: P×P → R  [mm]
  - 互连标准库 S = {s₁, s₂, s₃, s₄}, 每个标准有 grades(s)
  - 全局布线层数上限 L_max (如 4)

搜索:
  - 节点到分区的赋值 f: V → P
  - 每条边的标准选择和档位 σ_grade(e) : E → (s, grade)
  - 每条边的分区路径 path(e) : E → P* (有序分区序列)

硬约束:
  1. 距离约束: d(f(u), f(v)) ≤ max_reach(σ(e))  ∀e=(u,v)
  2. 边沿容量: Σ_{e incident to v} lanes(e) ≤ lane_budget(f(v))  ∀v∈V
  3. 布线层数: max_{zone∈P} Σ_{e: zone∈path(e)} layers(e) ≤ L_max
  4. 分区占用: path(e) 中每个分区的 lane 计数不超分区容量
  5. 损耗预算: d(e) × loss(σ(e)) ≤ loss_budget(e)

目标 (多目标):
  minimize Σ_e power(σ(e), d(e))          [总功耗]
  minimize Σ_e cost(σ(e))                  [总成本]
  maximize min_e BW(e)                     [瓶颈带宽]

这是 constrained multi-commodity assignment + resource-constrained
shortest path 的混合问题。NP-hard。

求解策略 (分层，逐步增加精度):
  Level 0: 贪心 — 每条边独立选"距离够用的最省功耗标准"
  Level 1: ILP — 小规模 (N≤12, |E|≤100) 精确解
  Level 2: 启发式/Agent — 大规模搜索

本模块只定义问题。求解器放在本项目或 agent 中独立实现。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from wafer_dse.physical.interconnect.base import (
    Footprint,
    InterconnectProfile,
    LinkBudget,
)
from wafer_dse.partition.grid import PartitionType, WaferGrid, Zone


# ===========================================================================
# 拓扑边 (从 Topology ABC 简化而来)
# ===========================================================================


@dataclass(frozen=True)
class LogicalEdge:
    """一条逻辑拓扑边: 连接两个 switch die 的有向或无向链路。"""

    src_id: int            # 源节点编号 (对应 Topology 中 node id)
    dst_id: int            # 目的节点编号
    bandwidth_gbps: float  # 该链路的带宽需求 [Gbps]
    label: str = ""        # 人类可读标签

    # 可选的 loss_budget; None = 使用标准的自然损耗、不做显式约束
    loss_budget_db: Optional[float] = None


@dataclass(frozen=True)
class LogicalTopology:
    """从体系结构层传来的简化拓扑: 节点集 + 边集。

    这个结构是 Phase 1 (ArchitectureModel) → Phase 2 (布线搜索) 的桥梁。
    """

    node_ids: tuple[int, ...]            # 节点编号集合
    edges: tuple[LogicalEdge, ...]       # 拓扑边集合
    label: str = ""                      # 如 "Dragonfly_a4p2h2"

    @property
    def node_count(self) -> int:
        return len(self.node_ids)

    @property
    def edge_count(self) -> int:
        return len(self.edges)


# ===========================================================================
# 布线问题定义
# ===========================================================================


class SearchStrategy(Enum):
    """求解策略枚举 (用于以后切换求解器)。"""
    GREEDY = auto()     # 贪心: 每条边独立最短可行路径
    ILP = auto()        # 整数线性规划
    AGENT = auto()      # LLM/RL Agent 搜索


@dataclass
class RoutingProblem:
    """Phase 2 布线搜索问题的完整定义。

    这是 DSE 框架的核心数据结构: 把"问题是什么"说清楚，
    求解器只是这个数据结构的一个消费者。

    使用方式:
        problem = RoutingProblem(topology=..., grid=..., standards=...)
        # 将来:
        #   solver = GreedySolver(problem)
        #   result = solver.solve()
        # 或:
        #   agent = RoutingAgent(problem)
        #   result = agent.search(max_iterations=1000)
    """

    topology: LogicalTopology
    grid: WaferGrid
    standards: tuple[str, ...] = (
        "UCIe-8G-Standard", "UCIe-16G-Standard",
        "UCIe-12G-Advanced", "UCIe-16G-Advanced", "UCIe-24G-Advanced", "UCIe-32G-Advanced",
        "SerDes-112G-VSR", "SerDes-112G-MR", "SerDes-112G-LR", "SerDes-224G-VSR",
        "Optical-1.6T-8λ", "Optical-3.2T-16λ",
        "Ethernet-800G", "Ethernet-1.6T",
        "TSV-3D-9μm", "TSV-3D-5μm", "TSV-3D-1μm",
    )

    # 全局约束
    max_routing_layers: int = 4           # 晶圆级布线层数上限
    max_loss_db: float = 30.0             # 全局损耗上限

    # 搜索偏好 (多目标权重)
    weight_power: float = 0.5             # 功耗权重 (0-1)
    weight_cost: float = 0.3              # 成本权重
    weight_performance: float = 0.2       # 性能权重 (带宽余量)

    def summary(self) -> str:
        """问题的可读摘要。"""
        g = self.grid
        t = self.topology
        return (
            f"RoutingProblem: {t.label}, {t.node_count} nodes, {t.edge_count} edges\n"
            f"  Grid: {g.n}×{g.n} @ {g.zone_size_mm:.0f}mm, "
            f"switch zones={len(g.switch_zones())}\n"
            f"  Standards: {self.standards}\n"
            f"  Constraints: max_layers={self.max_routing_layers}, "
            f"max_loss={self.max_loss_db}dB"
        )


# ===========================================================================
# 布线结果 (一条边的方案)
# ===========================================================================


@dataclass(frozen=True)
class RoutedEdge:
    """一条逻辑边在物理分区网格上的完整布线方案。

    这是 Phase 2 的输出原子。聚合所有 RoutedEdge 即为全网布线方案。
    """

    edge: LogicalEdge
    profile_name: str           # 选用的互连标准 (如 "UCIe-16G-Advanced")
    path: tuple[tuple[int, int], ...]  # 分区路径 [(x,y), ...]
    budget: LinkBudget           # 物理账单
    feasible: bool
    fail_reason: str = ""

    @property
    def total_layers(self) -> int:
        return self.budget.footprint.total_layers

    @property
    def total_power_w(self) -> float:
        return self.budget.power_w


@dataclass(frozen=True)
class RoutingPlan:
    """全网布线方案 — Phase 2 的最终输出。

    包含所有边的 RoutedEdge 和聚合后的全局指标。
    """

    problem: RoutingProblem
    edges: tuple[RoutedEdge, ...]

    @property
    def all_feasible(self) -> bool:
        return all(e.feasible for e in self.edges)

    @property
    def total_power_w(self) -> float:
        return sum(e.total_power_w for e in self.edges if e.feasible)

    @property
    def max_routing_layers_used(self) -> int:
        return max((e.total_layers for e in self.edges if e.feasible), default=0)

    def summary(self) -> str:
        """布线方案的可读摘要。"""
        n_feasible = sum(1 for e in self.edges if e.feasible)
        n_total = len(self.edges)
        standards_used = set(e.profile_name for e in self.edges if e.feasible)
        lines = [
            f"RoutingPlan: {n_feasible}/{n_total} edges feasible",
            f"  Total power: {self.total_power_w:.1f} W",
            f"  Max layers: {self.max_routing_layers_used}",
            f"  Standards used: {sorted(standards_used)}",
        ]
        return "\n".join(lines)


# ===========================================================================
# 贪心求解器 (Level 0 — 最简单，用于快速验证)
# ===========================================================================


class GreedyRouter:
    """贪心布线器: 每条边独立选择"距离够用且最省功耗"的标准。

    这是最 naive 的求解器——用于:
      1. 验证问题定义的正确性
      2. 提供 baseline 供更高级求解器比较
      3. 快速判断"至少有一条可行路径"（可行性筛查）

    算法: O(|E| × |S|) — 每条边遍历所有注册标准。
    """

    def __init__(self, problem: RoutingProblem):
        from wafer_dse.physical.interconnect import get_profile

        self._problem = problem
        self._standards = [
            get_profile(name) for name in problem.standards
        ]

    def solve(self) -> RoutingPlan:
        routed: list[RoutedEdge] = []

        for edge in self._problem.topology.edges:
            switch_zones = self._problem.grid.switch_zones()
            if edge.src_id >= len(switch_zones) or edge.dst_id >= len(switch_zones):
                routed.append(RoutedEdge(
                    edge=edge, profile_name="",
                    path=(), budget=LinkBudget(
                        profile_name="",
                        length_mm=0, bandwidth_gbps=edge.bandwidth_gbps,
                        lanes=0, power_w=0, loss_db=0, width_mm=0, ber=0,
                        feasible=False,
                        fail_reason=f"节点 {edge.src_id} 或 {edge.dst_id} 无对应分区",
                    ),
                    feasible=False, fail_reason="no partition assigned",
                ))
                continue

            src_zone = switch_zones[edge.src_id]
            dst_zone = switch_zones[edge.dst_id]
            length = self._problem.grid.distance(src_zone, dst_zone)

            # 遍历所有标准，找最优可行方案
            best: Optional[RoutedEdge] = None
            for std in self._standards:
                bill = std.compute(length_mm=length, bandwidth_gbps=edge.bandwidth_gbps)
                if not bill.feasible:
                    continue
                if best is None or bill.power_w < best.budget.power_w:
                    best = RoutedEdge(
                        edge=edge,
                        profile_name=std.name,
                        path=(src_zone, dst_zone),
                        budget=bill,
                        feasible=True,
                    )

            if best is None:
                routed.append(RoutedEdge(
                    edge=edge, profile_name="",
                    path=(src_zone, dst_zone),
                    budget=LinkBudget(
                        profile_name="",
                        length_mm=length, bandwidth_gbps=edge.bandwidth_gbps,
                        lanes=0, power_w=0, loss_db=0, width_mm=0, ber=0,
                        feasible=False,
                    ),
                    feasible=False,
                    fail_reason=f"无标准可覆盖 {length:.1f}mm @{edge.bandwidth_gbps}Gbps",
                ))
            else:
                routed.append(best)

        return RoutingPlan(problem=self._problem, edges=tuple(routed))
                            budget=bill,
                            feasible=True,
                        )

            if best is None:
                routed.append(RoutedEdge(
                    edge=edge, profile_name="", grade_name="",
                    path=(src_zone, dst_zone),
                    budget=LinkBudget(
                        profile_name="", grade_name="",
                        length_mm=length, bandwidth_gbps=edge.bandwidth_gbps,
                        lanes=0, power_w=0, loss_db=0, width_mm=0, ber=0,
                        feasible=False,
                    ),
                    feasible=False,
                    fail_reason=f"无标准可覆盖 {length:.1f}mm @{edge.bandwidth_gbps}Gbps",
                ))
            else:
                routed.append(best)

        return RoutingPlan(problem=self._problem, edges=tuple(routed))
