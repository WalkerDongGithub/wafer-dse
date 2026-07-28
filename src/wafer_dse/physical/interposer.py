"""
Interposer 物理模型 — 统一端口 + 面积 bump。

一个 interposer 容纳多颗 die，提供 interposer 内 D2D 布线。
所有 off-die 端口统一处理：每条链路 e 消耗 L_e × B / R_e 条 lane。

核心约束（per die）：
    Σ L_e · B/R_e  +  P_die / (V_dd · I_bump)  ≤  η · ρ · A_die

使用方式:
    interposer = Interposer(dies=[...], area_mm2=858)
    result = interposer.route_intra(edges, bandwidth_gbps=800)
    print(result.feasible, result.total_power_w)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from wafer_dse.physical.bump.bump import DieBumpBudget, UBUMP_25UM
from wafer_dse.physical.interconnect import get_profile, list_profiles
from wafer_dse.physical.interconnect.base import InterconnectProfile


# ============================================================================
# 布线结果
# ============================================================================


@dataclass(frozen=True)
class RouteResult:
    """一组边在 interposer 内的布线方案。"""

    chosen_standard: str
    feasible: bool
    fail_reason: str = ""

    lanes_per_edge: int = 0
    power_per_edge_w: float = 0.0
    total_power_w: float = 0.0
    die_lane_usage: tuple[int, ...] = ()   # 每个 die 消耗的 lane 数

    @property
    def success(self) -> bool:
        return self.feasible


# ============================================================================
# Interposer
# ============================================================================


@dataclass
class Interposer:
    """一个 reticle 大小的硅中介层。"""

    label: str
    dies: list[DieBumpBudget]
    area_mm2: float = 858.0             # reticle 面积 (~26×33mm)
    _max_die_distance_mm: float = 2.0   # 紧密布局下相邻 die 的 PHY-to-PHY 距离

    @property
    def die_count(self) -> int:
        return len(self.dies)

    @property
    def max_dies(self) -> int:
        """面积约束：最多能放多少颗 die。"""
        if not self.dies:
            return 999
        die_area = self.dies[0].width_mm * self.dies[0].height_mm
        return int(self.area_mm2 * 0.7 / die_area)

    def can_fit(self, n_dies: int) -> bool:
        return n_dies <= self.max_dies

    # ------------------------------------------------------------------
    # 核心：布线检查（统一约束）
    # ------------------------------------------------------------------

    def route(
        self,
        edges: list[tuple[int, int, float]],  # [(src_die_idx, dst_die_idx, L_e), ...]
        bandwidth_gbps: float = 800.0,
    ) -> RouteResult:
        """为所有边选最优物理标准，检查 per-die bump 预算。

        edges: [(src, dst, L_e), ...] — L_e 为归一化负载（来自性能 LP）。
        """
        # 遍历所有可用标准，按 lane 速率降序
        candidates = sorted(
            [get_profile(n) for n in list_profiles()
             if n.startswith("UCIe-") and "Advanced" in n],
            key=lambda s: s.lane_rate_gbps,
            reverse=True,
        )

        for std in candidates:
            bill = std.compute(
                length_mm=self._max_die_distance_mm,
                bandwidth_gbps=bandwidth_gbps,
            )
            if not bill.feasible:
                continue

            # lane 速率为 R_e，每条边的 lane 消耗 = L_e × B / R_e
            # （简化：当前假设所有边用同一标准）
            R = std.lane_rate_gbps
            lanes_per_unit = bandwidth_gbps / R

            # 统计每个 die 的总 lane 消耗
            die_lanes = [0] * len(self.dies)
            for src, dst, L_e in edges:
                lanes = L_e * lanes_per_unit
                die_lanes[src] += lanes
                die_lanes[dst] += lanes

            # 检查 per-die 约束：Σ L_e × B/R_e ≤ N_sig
            # N_sig = N_total - N_pwr（bump 类已内置）
            all_ok = True
            for i, die in enumerate(self.dies):
                if die_lanes[i] > die.available:
                    all_ok = False
                    break

            if not all_ok:
                continue

            # 通过
            total_lanes = sum(die_lanes) // 2  # 每条边数了两次
            return RouteResult(
                chosen_standard=std.name,
                feasible=True,
                lanes_per_edge=int(lanes_per_unit),
                power_per_edge_w=bill.power_w,
                total_power_w=bill.power_w * len(edges),
                die_lane_usage=tuple(die_lanes),
            )

        return RouteResult(
            chosen_standard="",
            feasible=False,
            fail_reason=(
                f"无 UCIe Advanced 标准能同时满足距离≤{self._max_die_distance_mm}mm "
                f"和所有 die 的 bump 预算"
            ),
        )

    # ------------------------------------------------------------------
    # 便捷方法
    # ------------------------------------------------------------------

    def route_intra(
        self,
        intra_edge_count: int,
        bandwidth_gbps: float = 800.0,
    ) -> RouteResult:
        """简化接口：组内全互联（所有 L_e = 1，即专用端口假设）。"""
        n = len(self.dies)
        if n < 2 or intra_edge_count <= 0:
            return RouteResult(
                chosen_standard="", feasible=False,
                fail_reason=f"invalid: {n} dies, {intra_edge_count} edges",
            )
        # 生成恰好 intra_edge_count 条边，循环分配 die 对
        edges: list[tuple[int, int, float]] = []
        for k in range(intra_edge_count):
            src = k % n
            dst = (k // n + 1 + src) % n  # 错开不同邻接
            edges.append((src, dst, 1.0))
        return self.route(edges, bandwidth_gbps)

    def summary(self) -> str:
        return (
            f"{self.label}: {self.die_count} dies, {self.area_mm2:.0f}mm², "
            f"max_dies={self.max_dies}"
        )
