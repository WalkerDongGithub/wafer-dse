"""
μbump 和 C4 bump 的物理约束。

这是整个 DSE 物理模型的最底层 — 不依赖任何其他模块。
Bump 先于互连标准: 工艺决定 bump → bump 数决定可选标准。

模型
====
μbump (die → interposer 上界面, 按周长计算):
  N_total   = 2(w + h) / pitch
  I_die     = P_die / V_dd
  N_power   = I_die / I_per_bump
  N_test    = N_total × 0.03
  N_signal  = N_total - N_power - N_test

C4 bump (interposer → substrate 下界面, 按面积计算):
  N_total   = A / pitch²
  (C4 的 P_die 是 interposer 上所有 die 功耗之和 + interposer 漏电)
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
# 常用规格预设
# ============================================================================

# μbump (die → interposer)
#   电流参考: 45μm Cu pillar → ~75mA, 25μm → ~40mA
UBUMP_45UM = BumpSpec("μbump-45μm",  pitch_um=45,  current_per_bump_ma=75)
UBUMP_25UM = BumpSpec("μbump-25μm",  pitch_um=25,  current_per_bump_ma=40)

# C4 bump (interposer → substrate): SnAg solder → ~300mA
C4_130UM = BumpSpec("C4-130μm", pitch_um=130, current_per_bump_ma=300)

# Hybrid bond (3D stacking): Cu-Cu → ~50μA (几乎不载流，纯信号)
HYBRID_9UM  = BumpSpec("Hybrid-9μm",  pitch_um=9,  current_per_bump_ma=0.05)
HYBRID_5UM  = BumpSpec("Hybrid-5μm",  pitch_um=5,  current_per_bump_ma=0.05)
HYBRID_1UM  = BumpSpec("Hybrid-1μm",  pitch_um=1,  current_per_bump_ma=0.05)


# ============================================================================
# Die μbump 预算 (功耗感知)
# ============================================================================


@dataclass(frozen=True)
class DieBumpBudget:
    """一个 die 的 μbump 信号池。

    由 die 尺寸、bump 工艺、和 die 功耗共同决定。
    功耗越高 → 电源 bump 占比越大 → 信号 bump 越少。
    """

    die_label: str
    spec: BumpSpec                 # μbump 工艺
    width_mm: float
    height_mm: float
    power_w: float = 50.0          # die 功耗 [W] — 来自 DieEstimator
    vdd_v: float = 0.8             # 供电电压 [V]
    test_fraction: float = 0.03    # 测试/DFT bump 占比

    @property
    def perimeter_mm(self) -> float:
        return 2 * (self.width_mm + self.height_mm)

    @property
    def total_bumps(self) -> int:
        """总 bump 数 (含电源+信号+测试)。"""
        return int(self.perimeter_mm * self.spec.density_per_mm)

    @property
    def power_bumps(self) -> int:
        """电源 bump 数 = ceil(总电流 / 单 bump 载流)。"""
        amps = self.power_w / self.vdd_v
        return max(1, int(__import__('math').ceil(amps * 1000 / self.spec.current_per_bump_ma)))

    @property
    def test_bumps(self) -> int:
        return max(1, int(self.total_bumps * self.test_fraction))

    @property
    def available(self) -> int:
        """可用信号 bump 数 = 总量 - 电源 - 测试。"""
        return max(0, self.total_bumps - self.power_bumps - self.test_bumps)

    @property
    def utilization(self) -> float:
        """实际信号 bump 占比 (推导值, 非输入)。"""
        return self.available / self.total_bumps if self.total_bumps > 0 else 0.0

    def can_support(self, required_lanes: int) -> bool:
        return required_lanes <= self.available

    def summary(self) -> str:
        return (
            f"{self.die_label}: {self.width_mm:.0f}×{self.height_mm:.0f}mm, "
            f"perimeter={self.perimeter_mm:.0f}mm, P={self.power_w:.0f}W, "
            f"{self.spec.name} → {self.total_bumps} total "
            f"(-{self.power_bumps}PWR -{self.test_bumps}TST) = {self.available} signal "
            f"(η={self.utilization:.1%})"
        )


# ============================================================================
# Interposer C4 预算
# ============================================================================


@dataclass(frozen=True)
class C4Budget:
    """一片 interposer 的 C4 信号池 (下界面 → substrate)。

    按面积 + 总功耗计算。interposer 上所有 die 的功耗之和
    决定需要多少 C4 电源 bump。
    """

    spec: BumpSpec                 # C4 工艺 (通常 130μm)
    area_mm2: float                # interposer 面积 [mm²]
    total_power_w: float = 300.0   # interposer 上所有 die 总功耗 + 漏电 [W]
    vdd_v: float = 0.8
    test_fraction: float = 0.03

    @property
    def total_bumps(self) -> int:
        return int(self.area_mm2 * self.spec.density_per_mm2)

    @property
    def power_bumps(self) -> int:
        amps = self.total_power_w / self.vdd_v
        return max(1, int(__import__('math').ceil(amps * 1000 / self.spec.current_per_bump_ma)))

    @property
    def test_bumps(self) -> int:
        return max(1, int(self.total_bumps * self.test_fraction))

    @property
    def available(self) -> int:
        return max(0, self.total_bumps - self.power_bumps - self.test_bumps)

    def summary(self) -> str:
        return (
            f"C4 {self.spec.name}: {self.area_mm2:.0f}mm², P={self.total_power_w:.0f}W, "
            f"{self.total_bumps} total "
            f"(-{self.power_bumps}PWR -{self.test_bumps}TST) = {self.available} signal"
        )
