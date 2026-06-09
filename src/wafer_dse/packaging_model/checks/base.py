"""封装检查抽象接口。

定义所有封装可行性检查的统一契约。
每个检查单元是一个 PackagingCheck 子类，输出 CheckResult。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from wafer_dse.models import NetworkPotential, Requirement


@dataclass(frozen=True)
class CheckResult:
    """单个封装检查的结果。

    Attributes:
        check_name: 检查名称（"die_area" / "power" / "external_io" / "internal_io"）。
        passed: 是否通过。
        values: 计算产生的中间值，聚合到 PackagingEstimate.details 中。
        reason: 未通过时的简要说明。
    """

    check_name: str
    passed: bool = False
    values: dict[str, float] = field(default_factory=dict)
    reason: str = ""


class PackagingCheck(ABC):
    """封装检查抽象基类。

    每个子类代表一种独立的物理可行性检查：
        - DieAreaCheck    —— 面积预算
        - PowerCheck      —— 功耗预算
        - ExternalIOCheck —— 外部端口 lane 预算
        - InternalIOCheck —— 内部链路 lane 预算
    """

    @abstractmethod
    def run(
        self,
        cfg: dict,
        req: Requirement,
        net: NetworkPotential,
        ext_lanes_per_port: int,
        int_lanes_per_port: int,
        port_count: int,
    ) -> CheckResult:
        """执行检查。

        Args:
            cfg: 封装工艺配置 dict（cfg["packaging"]）。
            req: 用户需求。
            net: 体系结构级输出。
            ext_lanes_per_port: 每外部端口所需 lane 数（SerDes 速率）。
            int_lanes_per_port: 每内部 800G-equivalent 链路所需 lane 数（D2D 速率）。
            port_count: 实际端口数。

        Returns:
            CheckResult：通过/失败 + 中间计算值。
        """
        ...
