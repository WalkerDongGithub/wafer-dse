"""DSE 日志器 ABC。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DseLogger(ABC):
    """DSE 结构化日志接口。

    所有检查点通过此接口输出推导过程，
    子类实现不同的输出格式 (console / file / json)。
    """

    @abstractmethod
    def section(self, title: str) -> None:
        """开始一个检查阶段。"""
        ...

    @abstractmethod
    def check(self, name: str, passed: bool, **kv: Any) -> None:
        """记录一次检查。kv 包含推导数据。"""
        ...

    @abstractmethod
    def info(self, message: str) -> None:
        """通用信息。"""
        ...

    @abstractmethod
    def table(self, headers: list[str], rows: list[list[Any]]) -> None:
        """输出表格。"""
        ...

    @abstractmethod
    def result(self, total: int, feasible: int, frontier: int) -> None:
        """输出 DSE 汇总结果。"""
        ...
