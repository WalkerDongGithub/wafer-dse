"""互连标准注册表。

所有具体标准在 import 时自动注册。使用方式:

    from wafer_dse.physical.interconnect import list_profiles, get_profile

    for name in list_profiles():
        std = get_profile(name)
        bill = std.compute(length_mm=3.0, bandwidth_gbps=800)
        if bill.feasible:
            print(f"{name}: {bill.lanes} lanes, {bill.power_w:.1f} W")
"""

from wafer_dse.physical.interconnect.base import (
    Footprint,
    InterconnectProfile,
    LinkBudget,
    ZoneType,
    ZoneUsage,
    get_profile,
    list_profiles,
    register,
)

# 触发注册
from wafer_dse.physical.interconnect import ucie       # noqa: F401
from wafer_dse.physical.interconnect import serdes     # noqa: F401
from wafer_dse.physical.interconnect import optical    # noqa: F401
from wafer_dse.physical.interconnect import ethernet   # noqa: F401
from wafer_dse.physical.interconnect import tsv        # noqa: F401
from wafer_dse.physical.interconnect import tsmc_profiles  # noqa: F401

__all__ = [
    "Footprint",
    "InterconnectProfile",
    "LinkBudget",
    "ZoneType",
    "ZoneUsage",
    "get_profile",
    "list_profiles",
    "register",
]
