"""
μbump 和 C4 bump 的物理约束 — 统一面积阵列模型。

模型
====
μbump (die → interposer, 面阵列):
  N_total   = η · A_die / pitch²
  I_die     = P_die / V_dd
  N_power   = I_die / I_per_bump
  N_signal + N_power ≤ N_total    (核心方程: 信号+电源竞争总预算)

C4 bump (interposer → substrate, 面阵列):
  N_total   = η · A_interposer / pitch²
  同上结构。
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================================
# BumpSpec: 纯工艺参数
# ============================================================================


@dataclass(frozen=True)
class BumpSpec:
    """一种 bump 工艺的物理规格。

    不包含利用率 —— 那是功耗推导的结果，不是输入。
    """

    name: str                     # "μbump-45μm", "C4-130μm"
    pitch_um: float               # bump 间距 [μm]
    current_per_bump_ma: float    # 单个 power bump 载流能力 [mA]

    # ── 便捷属性 ──

    @property
    def density_per_mm(self) -> float:
        """每 mm 边沿的总 bump 数 (含电源)。"""
        return 1000.0 / self.pitch_um

    @property
    def density_per_mm2(self) -> float:
        """每 mm² 面积的总 bump 数 (用于 C4 底面计算)。"""
        return 1e6 / self.pitch_um ** 2


# ============================================================================
# 预设
# ============================================================================

# μbump (die → interposer, 面阵列): 25μm pitch, ~40mA/bump
UBUMP_25UM = BumpSpec("μbump-25μm", pitch_um=25, current_per_bump_ma=40)
UBUMP_45UM = BumpSpec("μbump-45μm", pitch_um=45, current_per_bump_ma=75)

# C4 (interposer → substrate, 面阵列): 130μm pitch, ~300mA/bump
C4_130UM = BumpSpec("C4-130μm", pitch_um=130, current_per_bump_ma=300)

# Hybrid bond (3D): 纯信号
HYBRID_9UM = BumpSpec("Hybrid-9μm", pitch_um=9, current_per_bump_ma=0.05)
HYBRID_5UM = BumpSpec("Hybrid-5μm", pitch_um=5, current_per_bump_ma=0.05)
HYBRID_1UM = BumpSpec("Hybrid-1μm", pitch_um=1, current_per_bump_ma=0.05)


# ============================================================================
# Die μbump 预算 (功耗感知)
# ============================================================================


@dataclass(frozen=True)
class DieBumpBudget:
    """一个 die 的 μbump 信号池 — 面积阵列模型。

    总 bump 数由 die 面积决定。信号和电源竞争同一总预算。
    """

    die_label: str
    spec: BumpSpec                 # μbump 工艺
    width_mm: float
    height_mm: float
    power_w: float = 50.0          # die 功耗 [W] — 来自 DieEstimator
    vdd_v: float = 0.8             # 供电电压 [V]
    utilization: float = 0.7       # 面积利用率 η（含 test/DFT）

    @property
    def area_mm2(self) -> float:
        return self.width_mm * self.height_mm

    @property
    def total_bumps(self) -> int:
        """总 bump 数（面积阵列）。"""
        return int(self.area_mm2 * self.spec.density_per_mm2 * self.utilization)

    @property
    def power_bumps(self) -> int:
        """电源 bump 数 = ceil(总电流 / 单 bump 载流)。"""
        amps = self.power_w / self.vdd_v
        return max(1, int(__import__('math').ceil(amps * 1000 / self.spec.current_per_bump_ma)))

    @property
    def available(self) -> int:
        """信号 bump 可用量 = 总量 - 电源。"""
        return max(0, self.total_bumps - self.power_bumps)

    @property
    def budget_frac(self) -> float:
        """信号 bump 占比。"""
        return self.available / self.total_bumps if self.total_bumps > 0 else 0.0

    def can_support(self, required_lanes: int) -> bool:
        """信号 bump 是否够。"""
        return required_lanes <= self.available

    def summary(self) -> str:
        return (
            f"{self.die_label}: {self.width_mm:.0f}×{self.height_mm:.0f}mm, "
            f"area={self.area_mm2:.0f}mm², P={self.power_w:.0f}W, "
            f"{self.spec.name} → {self.total_bumps} total "
            f"(-{self.power_bumps}PWR) = {self.available} signal "
            f"(η={self.utilization:.0%}, budget={self.budget_frac:.1%})"
        )


# ============================================================================
# Interposer C4 预算
# ============================================================================


@dataclass(frozen=True)
class C4Budget:
    """一片 interposer 的 C4 信号池 — 面积阵列模型。"""

    spec: BumpSpec                 # C4 工艺 (通常 130μm)
    area_mm2: float                # interposer 面积 [mm²]
    total_power_w: float = 300.0   # interposer 上总功耗 [W]
    vdd_v: float = 0.8
    utilization: float = 0.7       # 面积利用率 η

    @property
    def total_bumps(self) -> int:
        return int(self.area_mm2 * self.spec.density_per_mm2 * self.utilization)

    @property
    def power_bumps(self) -> int:
        amps = self.total_power_w / self.vdd_v
        return max(1, int(__import__('math').ceil(amps * 1000 / self.spec.current_per_bump_ma)))

    @property
    def available(self) -> int:
        return max(0, self.total_bumps - self.power_bumps)

    def summary(self) -> str:
        return (
            f"C4 {self.spec.name}: {self.area_mm2:.0f}mm², P={self.total_power_w:.0f}W, "
            f"{self.total_bumps} total (-{self.power_bumps}PWR) = {self.available} signal"
        )
