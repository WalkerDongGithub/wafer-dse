"""Model —— 所有约束模型的共同基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lp.ctx import Ctx


class Model(ABC):
    """约束模型基类。

    build(ctx, B) 往 ctx 添加变量和约束。
    B 由 query 提供——ctx 不持有 B。
    cache_key() 返回模型当前参数的可哈希摘要——runner 用做持久化键。
    """

    @abstractmethod
    def build(self, ctx: Ctx, B: float) -> None:
        ...

    def cache_key(self) -> tuple | None:
        return None
