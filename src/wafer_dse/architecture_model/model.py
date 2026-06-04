"""体系结构级初筛 —— 编排层。

职责：
    1. 接收 TopologySpec + Requirement，构建具体拓扑实例。
    2. 通过 create_solver 工厂根据 route 选择求解器。
    3. 委托 Solver 计算无阻塞带宽潜能。
    4. 将求解结果翻译为 NetworkPotential（speedup、链路数、证书状态）。

本模块是薄编排层：
    拓扑定义 → topology.py
    求解策略 → solver/ 子包（interface + algorithm + 具体求解器）
"""

from __future__ import annotations

import math

from wafer_dse.architecture_model.solver import Solver, create_solver
from wafer_dse.architecture_model.topology import (
    Dragonfly,
    KaryNCube,
    Mesh,
    Topology,
    Torus,
)
from wafer_dse.models import NetworkPotential, Requirement, TopologySpec


# ---------------------------------------------------------------------------
# ArchitectureModel
# ---------------------------------------------------------------------------


class ArchitectureModel:
    """拓扑潜能评估编排器。

    求解器选择策略：
        - 默认：根据 spec.route 通过 create_solver() 自动选择匹配的求解器。
        - 显式：传入 solver 参数可覆盖自动选择（用于测试或自定义策略）。

    使用方式：

        # 自动选择求解器
        model = ArchitectureModel()
        net = model.evaluate(req, spec)   # spec.route="det" → FixedRouteSolver

        # 注入自定义求解器（多态扩展点）
        model = ArchitectureModel(solver=MyCustomSolver())
        net = model.evaluate(req, spec)
    """

    def __init__(self, solver: Solver | None = None) -> None:
        """初始化编排器。

        Args:
            solver:
                None  → evaluate() 时根据 spec.route 动态选择求解器。
                非 None → 所有 evaluate() 调用固定使用该求解器。
        """
        self._fixed_solver: Solver | None = solver

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def evaluate(self, req: Requirement, spec: TopologySpec) -> NetworkPotential:
        """输入用户需求 + 拓扑预案，输出网络潜能报告。

        流水线：
            build_topology → select_solver → solver.solve
            → 计算 speedup/links → NetworkPotential
        """
        topo, name = self._build_topology(spec)
        links = self._directed_links(topo)

        # —— 求解器选择：显式注入优先，否则按 route 自动匹配 ——
        solver = self._fixed_solver if self._fixed_solver else create_solver(spec.route)

        result = solver.solve(
            topo=topo,
            route=spec.route,
            link_capacity_gbps=req.target_nonblocking_gbps_per_port,
        )

        # —— 计算所需内部资源 ——
        nonblocking = result.nonblocking_gbps_per_port
        required_speedup = max(
            1,
            math.ceil(req.target_nonblocking_gbps_per_port / max(nonblocking, 1e-12)),
        )
        required_links = len(links) * required_speedup

        status, notes = _certificate_label(req.strictness.mode)

        return NetworkPotential(
            topology_name=name,
            route=spec.route,
            terminal_count=topo.terminal_num(),
            directed_link_count=len(links),
            nonblocking_gbps_per_port=nonblocking,
            required_internal_speedup=required_speedup,
            required_internal_800g_links=required_links,
            certificate_status=status,
            worst_link=str(result.worst_link),
            notes=notes,
        )

    # ------------------------------------------------------------------
    # 拓扑构建
    # ------------------------------------------------------------------

    @staticmethod
    def _build_topology(spec: TopologySpec) -> tuple[Topology, str]:
        """TopologySpec → 内部拓扑实例 + 可读名称。"""
        kind = spec.kind

        if kind == "mesh":
            return Mesh(int(spec.size)), f"mesh{spec.size}x{spec.size}"

        if kind == "torus":
            return Torus(int(spec.size)), f"torus{spec.size}x{spec.size}"

        if kind == "dragonfly":
            return (
                Dragonfly(a=int(spec.a), p=int(spec.p), h=int(spec.h)),
                f"dragonfly_a{spec.a}_p{spec.p}_h{spec.h}",
            )

        if kind == "kary_ncube":
            k = int(spec.size)
            n = int(spec.n) if spec.n is not None else 2
            wrap = bool(spec.wrap) if spec.wrap is not None else True
            wrap_label = "torus" if wrap else "mesh"
            return (
                KaryNCube(k=k, n=n, wrap=wrap),
                f"kary_ncube_k{k}_n{n}_{wrap_label}",
            )

        raise ValueError(f"未知拓扑类型: {kind!r}")

    @staticmethod
    def _directed_links(topo: Topology) -> set[tuple[int, int]]:
        """返回 det 路由会用到的全部有向链路集合。

        用于计算内部链路预算 —— 物理链路集合由拓扑结构决定，
        不受 Valiant 等多路径策略影响。
        """
        import itertools

        links: set[tuple[int, int]] = set()
        for src, dst in itertools.permutations(topo.terminals(), 2):
            path = topo.det(src, dst)[0]
            links.update((path[i], path[i + 1]) for i in range(len(path) - 1))
        return links


# ---------------------------------------------------------------------------
# 证书标签（模块级纯函数）
# ---------------------------------------------------------------------------


def _certificate_label(strictness_mode: str) -> tuple[str, str]:
    """严格程度 → (certificate_status, 可读说明)。"""
    labels = {
        "full": (
            "exact_worst_case",
            "全工况严格：使用固定路由 worst-case assignment 精确求解。",
        ),
        "percent": (
            "conservative_exact",
            "x% 工况严格：当前用全工况 worst-case 作为保守替代。",
        ),
        "benchmark": (
            "not_implemented",
            "特定 benchmark 严格：当前尚未接入 benchmark traffic。",
        ),
        "benchmark_percent": (
            "not_implemented",
            "特定 benchmark 的 x% 工况严格：当前尚未接入 benchmark traffic。",
        ),
    }
    return labels.get(strictness_mode, ("unknown", f"未知严格程度: {strictness_mode}"))
