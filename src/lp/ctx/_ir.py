"""底层 IR —— Engine 的编译目标，不被模型直接使用。"""

from dataclasses import dataclass
from enum import Enum, auto


@dataclass
class VarSpec:
    """变量声明。"""
    name: str
    shape: int = 1
    nonneg: bool = True


@dataclass(frozen=True)
class Term:
    """线性项: coefficient × var_name[idx]。"""
    var: str
    idx: int = 0
    coeff: float = 1.0

    def __str__(self) -> str:
        return f"{self.coeff:+.4g}·{self.var}[{self.idx}]"


@dataclass(frozen=True)
class LinearC:
    """一条线性约束: Σ terms {<=, >=, ==} rhs。"""
    name: str
    terms: tuple[Term, ...]
    sense: str
    rhs: float = 0.0


class Sense(Enum):
    LE = auto()   # ≤
    GE = auto()   # ≥
    EQ = auto()   # ==

    def __str__(self) -> str:
        return {Sense.LE: "<=", Sense.GE: ">=", Sense.EQ: "=="}[self]
