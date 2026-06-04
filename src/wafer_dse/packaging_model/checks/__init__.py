"""封装检查单元集合。

每个检查单元是独立的 PackagingCheck 子类：
    - DieAreaCheck    —— 面积预算
    - PowerCheck      —— 功耗预算
    - ExternalIOCheck —— 外部端口 IO
    - InternalIOCheck —— 内部链路 IO

扩展方式：
    新增检查时在此目录新建文件，实现 PackagingCheck 接口，
    然后在 ALL_CHECKS 注册表中添加。
"""

from __future__ import annotations

from wafer_dse.packaging_model.checks.base import CheckResult, PackagingCheck
from wafer_dse.packaging_model.checks.die_area import DieAreaCheck
from wafer_dse.packaging_model.checks.external_io import ExternalIOCheck
from wafer_dse.packaging_model.checks.internal_io import InternalIOCheck
from wafer_dse.packaging_model.checks.power import PowerCheck

# 注册表：按执行顺序排列的检查单元列表
ALL_CHECKS: list[PackagingCheck] = [
    DieAreaCheck(),
    PowerCheck(),
    ExternalIOCheck(),
    InternalIOCheck(),
]

__all__ = [
    "ALL_CHECKS",
    "CheckResult",
    "DieAreaCheck",
    "ExternalIOCheck",
    "InternalIOCheck",
    "PackagingCheck",
    "PowerCheck",
]
