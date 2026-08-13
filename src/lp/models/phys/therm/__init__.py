"""
热约束族.

ABC 定义功耗 P 和温度 T 的计算接口:
  - L0 (GlobalPowerModel):    总功耗 ≤ 散热能力，不计算 T
  - L1 (SteadyStateModel):    per-die P → G·T = P+b → T ≤ T_max
  - L2 (WarpModel):           相邻 die 温差 ≤ ΔT_max (待实现)

所有模型共享的组装步骤:
  ℓ = B · S_bw⁻¹ · L   →   P = P₀ + M · S_dyn · ℓ   →   约束
  精度只影响最后一步的粒度（全局 vs per-die）.
"""

from lp.models.phys import PhysModel


class ThermalModel(PhysModel):
    """热约束 ABC —— 功耗 P → 温度 T → 上限约束.

    子类必须实现 build(ctx, B):
      L0: 一条全局不等式 ΣP ≤ A·q_max
      L1: n 条 per-die 不等式 G·T = P+b, T ≤ T_max
      L2: 相邻 die 温差约束 (待实现)
    """


# ═══════════════════════════════════════════════════════
# 子类 (延迟导入，保持 __init__.py 干净)
# ═══════════════════════════════════════════════════════

from lp.models.phys.therm._temp_limit import GlobalPowerModel   # noqa: E402
from lp.models.phys.therm._steady_state import SteadyStateModel  # noqa: E402
from lp.models.phys.therm.network import (                       # noqa: E402
    ThermalNetwork,
    ThermalNetworkBuilder, AnalyticNetworkBuilder,
    DiePlacement, MfitStackConfig,
)

from lp.models.phys.therm._heatmap import plot_temperature  # noqa: E402

__all__ = [
    "ThermalModel",
    "GlobalPowerModel",
    "ThermalNetwork", "SteadyStateModel",
    "ThermalNetworkBuilder", "AnalyticNetworkBuilder",
    "DiePlacement", "MfitStackConfig",
    "plot_temperature",
]
