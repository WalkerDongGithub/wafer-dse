"""
Interposer 物理模型。

一个 interposer 容纳 ~6 个 die (取决于 reticle 面积和 die 尺寸)。
Interposer 内走线: μbump → interposer 铜线 → μbump (或 → C4 出 substrate)。

职责:
  1. 判断一组 die 能否放进 interposer (面积)
  2. 判断组内 D2D 能否 route (距离 → UCIe 标准选择)
  3. 为每条 intra-group edge 选出最佳可行 UCIe 标准
  4. 计算每个 die 的 μbump 消耗

使用方式:
    interposer = Interposer(dies=[...], area_mm2=858, bump=UBUMP_45UM)
    result = interposer.route_intra(edges, bandwidth_gbps=800)
    print(result.feasible, result.profile_name, result.total_power_w)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from wafer_dse.physical.bump.bump import BumpSpec, DieBumpBudget, UBUMP_45UM
from wafer_dse.physical.interconnect import get_profile, list_profiles
from wafer_dse.physical.interconnect.base import InterconnectProfile


# ============================================================================
# Interposer 级布线结果
# ============================================================================


@dataclass(frozen=True)
class IntraRouteResult:
    """一组 intra-group 边在 interposer 内的布线方案。"""

    chosen_standard: str               # 选用的标准, 如 "UCIe-32G-Advanced"
    feasible: bool
    fail_reason: str = ""

    # 每条边的记账
    lanes_per_edge: int = 0           # 每条 UCIe-D2D 链路消耗的 lane 数
    power_per_edge_w: float = 0.0
    total_power_w: float = 0.0

    # 每个 die 的 bump 消耗
    die_bump_usage: tuple[int, ...] = ()   # 每个 die 消耗的 μbump 数

    @property
    def success(self) -> bool:
        return self.feasible


# ============================================================================
# Interposer
# ============================================================================


@dataclass
class Interposer:
    """一个 reticle 大小的硅中介层。

    容纳多颗 die，提供 interposer 内 D2D 布线能力。
    """

    label: str                          # "Interposer_0"
    dies: list[DieBumpBudget]           # 该 interposer 上的 die 列表
    area_mm2: float = 858.0             # reticle 面积 (~26×33mm)
    bump: BumpSpec = field(default=UBUMP_45UM)  # μbump 工艺

    # 内部缓存: 最大 die 距离 (2×2 compact 布局的近似)
    # 简化: 假设 die 紧密排成 2×2/3×2 网格
    _max_die_distance_mm: float = 2.0   # 对角线 ~1.4mm, 加 detour margin → 2mm

    @property
    def die_count(self) -> int:
        return len(self.dies)

    @property
    def max_dies(self) -> int:
        """该 interposer 最多能放多少颗 die (面积约束)。"""
        if not self.dies:
            return 999
        die_area = self.dies[0].width_mm * self.dies[0].height_mm
        # 扣除 routing overhead (~30%)
        return int(self.area_mm2 * 0.7 / die_area)

    def can_fit(self, group_size: int) -> bool:
        """a 个 die 能否放进这个 interposer。"""
        return group_size <= self.max_dies

    # ------------------------------------------------------------------
    # 核心: intra-group 布线检查
    # ------------------------------------------------------------------

    def route_intra(
        self,
        intra_edge_count: int,      # 组内 D2D 边数 (e.g. a(a-1)/2)
        bandwidth_gbps: float = 800.0,
    ) -> IntraRouteResult:
        """为组内全互联选最优 UCIe 标准。

        策略: 遍历所有 UCIe-Advanced 标准，选第一个满足条件的最优解。
        优先条件: 距离够 → bump 够 → 功耗最低。
        """
        ucie_advanced = [
            n for n in list_profiles()
            if n.startswith("UCIe-") and "Advanced" in n
        ]
        # 按速率降序 (高速 = 更少 lane → 省 bump, 优先试)
        ucie_advanced.sort(key=lambda n: get_profile(n).lane_rate_gbps, reverse=True)

        for name in ucie_advanced:
            std = get_profile(name)

            # 距离检查
            bill = std.compute(
                length_mm=self._max_die_distance_mm,
                bandwidth_gbps=bandwidth_gbps,
            )
            if not bill.feasible:
                continue

            # Bump 检查: 每个 die 的 degree = intra_edge_count × lanes_per_edge / a
            # 简化: 全互联, 每个 die 度 = a-1, 每条边消耗 bill.lanes
            lanes_per_edge = bill.lanes
            # 每个 die 需要: (a-1) 条 D2D 链路
            per_die_lanes = (len(self.dies) - 1) * lanes_per_edge if self.dies else 0

            all_ok = True
            for die in self.dies:
                if per_die_lanes > die.available:
                    all_ok = False
                    break

            if not all_ok:
                continue

            # 通过!
            return IntraRouteResult(
                chosen_standard=name,
                feasible=True,
                lanes_per_edge=lanes_per_edge,
                power_per_edge_w=bill.power_w,
                total_power_w=bill.power_w * intra_edge_count,
                die_bump_usage=tuple(per_die_lanes for _ in self.dies),
            )

        return IntraRouteResult(
            chosen_standard="",
            feasible=False,
            fail_reason=(
                f"无 UCIe Advanced 标准能同时满足距离≤{self._max_die_distance_mm}mm "
                f"和每个 die 的 μbump 预算"
            ),
        )

    def summary(self) -> str:
        return (
            f"{self.label}: {self.die_count} dies, {self.area_mm2:.0f}mm², "
            f"μbump={self.bump.name}, max_dies={self.max_dies}"
        )
