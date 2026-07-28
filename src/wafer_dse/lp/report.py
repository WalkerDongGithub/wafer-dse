"""LP 求解结果与灵敏度报告。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LpConstraintStatus:
    """单个约束组的求解状态。"""

    name: str                     # "performance" | "geometry" | "thermal" | "routing"
    satisfied: bool               # 该组所有约束是否满足
    max_violation: float          # 最大违反量 (≤0 表示满足, >0 表示违反)
    max_slack: float              # 最大松弛量 (≥0)
    binding_constraints: list[str]  # 绑定约束的名称列表
    dual_values: dict[str, float] = field(default_factory=dict)  # 对偶变量 (cvxpy 路径)


@dataclass
class LpResult:
    """统一 LP 的求解输出。

    包含可行性判断、各约束组的边际分析、以及对偶变量灵敏度。
    """

    feasible: bool
    solver: str = ""              # "hungarian" | "cvxpy-clarabel" | "cvxpy-fallback"
    route: str = ""               # "det" | "valiant"

    # 性能指标
    worst_load: float = 0.0       # 全网最坏链路负载
    nonblocking_gbps: float = 0.0 # 无阻塞带宽 (Gbps/port)
    bottleneck_link: str = ""     # 瓶颈链路标识

    # 约束状态
    constraints: list[LpConstraintStatus] = field(default_factory=list)

    # 原始数据
    per_link_load: dict[tuple[int, int], float] = field(default_factory=dict)
    per_link_slack: dict[tuple[int, int], float] = field(default_factory=dict)

    # 求解元数据
    num_variables: int = 0
    num_constraints: int = 0
    solve_time_s: float = 0.0
    notes: list[str] = field(default_factory=list)

    def report(self) -> str:
        """生成人类可读的求解报告。"""
        lines = [
            "=" * 60,
            f"  DSE 统一 LP 求解报告",
            "=" * 60,
            "",
            f"  求解器:     {self.solver}",
            f"  路由策略:   {self.route}",
            f"  可行性:     {'✓ FEASIBLE' if self.feasible else '✗ INFEASIBLE'}",
            "",
            f"  --- 性能 ---",
            f"  最坏负载:   {self.worst_load:.4f}",
            f"  无阻塞带宽:  {self.nonblocking_gbps:.1f} Gbps/port",
        ]
        if self.bottleneck_link:
            lines.append(f"  瓶颈链路:   {self.bottleneck_link}")

        lines += [
            "",
            "  --- 约束状态 ---",
        ]

        for cs in self.constraints:
            status = "✓" if cs.satisfied else "✗"
            lines.append(
                f"  {status} {cs.name:12s}  "
                f"margin={-cs.max_violation:+.4f}  "
                f"slack={cs.max_slack:.4f}"
            )
            if cs.binding_constraints:
                lines.append(
                    f"     binding: {', '.join(cs.binding_constraints[:5])}"
                )

        if self.notes:
            lines += ["", "  --- 备注 ---"]
            for note in self.notes:
                lines.append(f"  · {note}")

        lines += [
            "",
            f"  变量数: {self.num_variables},  约束数: {self.num_constraints}",
            f"  求解时间: {self.solve_time_s:.3f}s",
            "",
            "=" * 60,
        ]
        return "\n".join(lines)

    def summary_line(self) -> str:
        """单行摘要，用于多设计点对比表。"""
        return (
            f"{'✓' if self.feasible else '✗'}  "
            f"L*={self.worst_load:.3f}  "
            f"BW={self.nonblocking_gbps:.0f}Gbps  "
            f"{self.solver}"
        )
