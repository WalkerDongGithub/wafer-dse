"""
Substrate 级互联模型。

多个 interposer 贴在有机基板上，基板走线视为充裕 (面积 70× reticle，
20+ 层)。Interposer 间全互联，走 SerDes-112G-MR。

职责:
  1. 计算 interposer 间全局链路的最远距离
  2. 为 global link 选标准 (SerDes-MR)
  3. 检查 C4 预算

使用方式:
    sub = Substrate(interposers=[...], grid=(4,4))
    result = sub.route_global(global_edge_count=..., bandwidth_gbps=800)
    print(result.feasible, result.total_power_w)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from physical.bump.bump import BumpSpec, C4Budget, C4_130UM
from physical.interconnect import get_profile
from physical.interposer import Interposer


# ============================================================================
# Global 布线结果
# ============================================================================


@dataclass(frozen=True)
class GlobalRouteResult:
    """interposer 间 global link 的布线方案。"""

    chosen_standard: str          # "SerDes-112G-MR"
    feasible: bool
    fail_reason: str = ""

    lanes_per_edge: int = 0
    power_per_edge_w: float = 0.0
    total_power_w: float = 0.0
    total_c4_needed: int = 0      # 所有 global link 共消耗的 C4 数

    @property
    def success(self) -> bool:
        return self.feasible


# ============================================================================
# Substrate
# ============================================================================


@dataclass
class Substrate:
    """有机基板: 承载多个 interposer，提供 interposer 间全互联。"""

    interposers: list[Interposer]
    grid_rows: int = 4
    grid_cols: int = 4
    c4_spec: BumpSpec = field(default=C4_130UM)

    # ── 几何 ──
    _interposer_spacing_mm: float = 31.0   # ~26 + 5mm gap
    _interposer_height_mm: float = 38.0    # ~33 + 5mm gap

    @property
    def max_distance_mm(self) -> float:
        """4×4 网格中对角 interposer 间的最远走线距离 (含绕线因子)。"""
        dx = (self.grid_cols - 1) * self._interposer_spacing_mm
        dy = (self.grid_rows - 1) * self._interposer_height_mm
        return math.sqrt(dx ** 2 + dy ** 2) * 1.3

    # ── 计算属性 ──

    @property
    def c4_budget(self) -> C4Budget:
        """所有 interposer 的总 C4 信号池。"""
        total_area = len(self.interposers) * 858.0
        total_power = len(self.interposers) * 300.0  # 每 interposer ~300W
        return C4Budget(
            spec=self.c4_spec,
            area_mm2=total_area,
            total_power_w=total_power,
        )

    def route_global(
        self,
        global_edge_count: int,        # 总 global link 数
        bandwidth_gbps: float = 800.0,
    ) -> GlobalRouteResult:
        """为 global link 选标准。

        策略: SerDes-112G-MR 是唯一覆盖 ~250mm 且功耗可接受的标准。
        """
        std = get_profile("SerDes-112G-MR")
        bill = std.compute(
            length_mm=self.max_distance_mm,
            bandwidth_gbps=bandwidth_gbps,
        )

        if not bill.feasible:
            return GlobalRouteResult(
                chosen_standard="",
                feasible=False,
                fail_reason=(
                    f"SerDes-112G-MR 无法覆盖 {self.max_distance_mm:.0f}mm"
                ),
            )

        lanes_per_edge = bill.lanes
        total_c4 = global_edge_count * lanes_per_edge * 2  # 每条 link 用 2 端 C4

        if total_c4 > self.c4_budget.available:
            return GlobalRouteResult(
                chosen_standard="SerDes-112G-MR",
                feasible=False,
                fail_reason=(
                    f"C4 不够: 需要 {total_c4}, 可用 {self.c4_budget.available}"
                ),
                lanes_per_edge=lanes_per_edge,
                power_per_edge_w=bill.power_w,
                total_power_w=bill.power_w * global_edge_count,
                total_c4_needed=total_c4,
            )

        return GlobalRouteResult(
            chosen_standard="SerDes-112G-MR",
            feasible=True,
            lanes_per_edge=lanes_per_edge,
            power_per_edge_w=bill.power_w,
            total_power_w=bill.power_w * global_edge_count,
            total_c4_needed=total_c4,
        )

    def summary(self) -> str:
        c4 = self.c4_budget
        return (
            f"Substrate: {len(self.interposers)} interposers "
            f"({self.grid_rows}×{self.grid_cols}), "
            f"max_distance={self.max_distance_mm:.0f}mm, "
            f"C4 pool={c4.available} signals"
        )
