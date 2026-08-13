"""
布局问题定义.

正方形 die + 正方形 interposer → 正方形网格.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DieSpec:
    """单个 die."""
    label: str
    side_mm: float          # 正方形边长
    group_id: int = 0
    router_id: int = 0


@dataclass
class PlacementProblem:
    """布局问题输入.

    n = floor(L / d) → n×n 网格, 最多放 n² 个 die.
    """

    die_side_mm: float
    interposer_side_mm: float
    die_count: int
    edges: list[tuple[int, int]] = field(default_factory=list)
    # edges 预留给拓扑感知求解器


@dataclass(frozen=True)
class DiePosition:
    """单个 die 的布局结果."""
    spec: DieSpec
    row: int
    col: int

    @property
    def x(self) -> float:
        return self.col * self.spec.side_mm

    @property
    def y(self) -> float:
        return self.row * self.spec.side_mm

    @property
    def label(self) -> str:
        return self.spec.label


@dataclass(frozen=True)
class PlacementSolution:
    """布局结果."""
    positions: list[DiePosition]
    grid_n: int                     # n × n 网格
    die_side_mm: float
    interposer_side_mm: float

    @property
    def n_dies(self) -> int:
        return len(self.positions)

    @property
    def max_dies(self) -> int:
        return self.grid_n * self.grid_n

    @property
    def interposer_width_mm(self) -> float:
        return self.interposer_side_mm

    @property
    def interposer_height_mm(self) -> float:
        return self.interposer_side_mm

    def die_at(self, row: int, col: int) -> DiePosition | None:
        for p in self.positions:
            if p.row == row and p.col == col:
                return p
        return None

    def summary(self) -> str:
        lines = [
            f"grid {self.grid_n}×{self.grid_n}, "
            f"{self.n_dies}/{self.max_dies} dies, "
            f"interposer {self.interposer_side_mm:.0f}×{self.interposer_side_mm:.0f} mm",
        ]
        for p in self.positions:
            lines.append(f"  {p.label} @ [{p.row},{p.col}] ({p.x:.0f},{p.y:.0f})")
        return "\n".join(lines)
