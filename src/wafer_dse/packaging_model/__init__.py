"""封装级初筛模块。

公开 API：
    PackagingModel —— 编排器，运行所有封装检查并输出 PackagingEstimate
    PackagingCheck / CheckResult —— 检查单元抽象接口（可扩展）
    DieAreaCheck / PowerCheck / ExternalIOCheck / InternalIOCheck —— 具体检查单元

模块结构：
    model.py          编排层（薄 facade）
    checks/
        base.py       PackagingCheck ABC + CheckResult
        die_area.py   面积检查
        power.py      功耗检查
        external_io.py 外部端口 IO 检查
        internal_io.py 内部链路 IO 检查
        __init__.py   检查注册表 + 导出
"""

from wafer_dse.packaging_model.checks import (
    ALL_CHECKS,
    CheckResult,
    DieAreaCheck,
    ExternalIOCheck,
    InternalIOCheck,
    PackagingCheck,
    PowerCheck,
)
from wafer_dse.packaging_model.model import PackagingModel

__all__ = [
    "ALL_CHECKS",
    "CheckResult",
    "DieAreaCheck",
    "ExternalIOCheck",
    "InternalIOCheck",
    "PackagingCheck",
    "PackagingModel",
    "PowerCheck",
]
