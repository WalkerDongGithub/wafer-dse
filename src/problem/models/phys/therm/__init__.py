"""
热约束族 (LP 约束模板层，纯数学).

本包只保留 LP 约束模板（不 import physical）:
  - L0 (GlobalPowerModel):    总功耗 ≤ 散热能力，不计算 T
  - L1 (SteadyStateModel):    per-die P → G·T = P+b → T ≤ T_max
  - L2 (WarpModel):           相邻 die 温差 ≤ ΔT_max
        （_warp_limit.py 已实现并由 test0402 覆盖，但有意不导出——
          die-die 温差代理撑不起真实翘曲物理、ΔT_max 缺文献，
          V5 无翘曲约束，实现保留作技术记录）

物理/几何部分（DiePlacement / MfitStackConfig / ThermalNetwork /
ThermalNetworkBuilder / AnalyticNetworkBuilder / plot_temperature）
在 physical/layout/thermal_network/，由 problem/builder 直接 import.

所有模型共享的组装步骤:
  ℓ = B · S_bw⁻¹ · L   →   P = P₀ + M · S_dyn · ℓ   →   约束
  精度只影响最后一步的粒度（全局 vs per-die）.

ABC 定义功耗 P 和温度 T 的计算接口；子类只写 LP 约束模板，
不构造热网络——网络由 builder 通过 ThermalNetwork 注入.
"""

from problem.models.phys import PhysModel


class ThermalModel(PhysModel):
    """热约束 ABC —— 功耗 P → 温度 T → 上限约束.

    子类必须实现 build(ctx, B):
      L0: 一条全局不等式 ΣP ≤ A·q_max
      L1: n 条 per-die 不等式 G·T = P+b, T ≤ T_max
      L2: 相邻 die 温差约束（WarpModel 已实现，有意不导出，见模块 docstring）
    """


# ═══════════════════════════════════════════════════════
# 子类 (延迟导入，保持 __init__.py 干净)
# ═══════════════════════════════════════════════════════

from problem.models.phys.therm._temp_limit import GlobalPowerModel   # noqa: E402
from problem.models.phys.therm._steady_state import SteadyStateModel  # noqa: E402

__all__ = [
    "ThermalModel",
    "GlobalPowerModel",
    "SteadyStateModel",
]

