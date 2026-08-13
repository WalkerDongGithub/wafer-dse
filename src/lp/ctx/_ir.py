"""底层 IR —— Engine 的编译目标，不被模型直接使用。"""

from dataclasses import dataclass


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
    """一条线性约束: Σ terms {<=, >=, ==} rhs。

    sense 是字符串 "<=" / ">=" / "=="。
    meaning 是不等式取等号时的物理含义（等式可为空）——绑定诊断的语义来源。
    """
    name: str
    terms: tuple[Term, ...]
    sense: str
    rhs: float = 0.0
    meaning: str = ""
