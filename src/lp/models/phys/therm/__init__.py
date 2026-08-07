"""
热约束族。

ThermalModel —— ABC，功耗 → 温度约束。
  底层实现：
    _network.py    NetworkModel (L1 精度，G⁻¹ 网络)
    _temp_limit.py 散热极限（各点温度 ≤ T_max）
    _warp_limit.py 翘曲极限（各点温差 ≤ ΔT_max，留白）
"""

from lp.ctx import Model


class ThermalModel(Model):
    """热约束族——功耗 → 温度 → 上限 + 翘曲。"""


from lp.models.phys.therm._network import (  # noqa: E402
    ThermalNetwork, NetworkModel, build_thermal_network,
)
from lp.models.phys.therm._temp_limit import PowerDensityModel  # noqa: E402

__all__ = [
    "ThermalModel", "ThermalNetwork", "NetworkModel",
    "build_thermal_network", "PowerDensityModel",
]
