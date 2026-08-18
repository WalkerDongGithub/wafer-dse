"""
布线约束 — 边容量 + 点容量 + C4 pad 容量.

物理问题: die→die 或 die→C4 pad 的 lane 需要在 interposer 金属层上走线.
          每条网格边有容量上限, 每个网格交点有通过上限,
          每个 C4 pad 有 bump 数上限.

和 BumpModel / NetworkModel 一致的写法:
  __init__ 预计算全部系数, build() 只声明变量 + 写约束.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from problem.models.phys import PhysModel
from problem.models.phys.wiring._grid import (
    WiringGrid, build_wiring_grid, populate_paths,
)

if TYPE_CHECKING:
    from problem.ctx import Ctx


class WiringModel(PhysModel):
    """Interposer 布线容量约束.

    __init__ 预计算: 每条网格边/点/C4 pad 上有哪些 (link, path) 经过.
    build() 只声明 x 变量 + 写需求/容量不等式.
    """

    def __init__(self, grid: WiringGrid,
                 link_specs: list[dict],
                 link_indices: list[int],
                 lane_rates: np.ndarray):
        n_links = len(link_indices)
        pg = grid.path_groups

        # -- 每条链路的元数据 --
        # _link_meta = [(li, lane_rate, n_paths, path_start_idx), ...]
        self._link_meta: list[tuple[int, float, int, int]] = []
        total_paths = 0
        for i in range(n_links):
            li = link_indices[i]
            lr = float(lane_rates[li])
            paths = pg[i] if i < len(pg) else []
            n_paths = len(paths) if paths and paths[0] else 0
            start = total_paths
            total_paths += n_paths
            self._link_meta.append((li, lr, n_paths, start))

        self._total_paths = total_paths
        self._n_links = n_links

        # -- 边容量: _edge_incident[ei] = [(path_idx,), ...] --
        self._edge_incident: list[list[int]] = [
            _collect_edge(ei, grid, n_links, pg, self._link_meta)
            for ei in range(grid.n_edges)
        ]
        self._edge_cap = grid.edge_cap

        # -- 点容量: _vert_incident[vi] = [path_idx, ...] --
        self._vert_incident: list[list[int]] = [
            _collect_vertex(vi, grid, n_links, pg, self._link_meta)
            for vi in range(grid.n_vertices)
        ]
        self._vert_cap = grid.vert_cap

        # -- C4 pad 容量: _c4_links[pi] = [link_index, ...] --
        self._c4_pad_links: list[list[int]] = [[] for _ in grid.c4_vertices]
        for i in range(n_links):
            spec = link_specs[i] if i < len(link_specs) else {}
            pi = spec.get("c4_pad")
            if pi is not None and 0 <= pi < len(grid.c4_vertices):
                self._c4_pad_links[pi].append(link_indices[i])
        self._c4_pad_cap = grid.c4_pad_cap
        self._lane_rates = lane_rates

    # -- build ----------------------------------------------------------

    def build(self, ctx: Ctx, B: float) -> None:
        L = ctx["L"]

        # 声明 x 变量
        x_vars: list = [None] * self._total_paths
        for (li, lr, n_paths, start) in self._link_meta:
            if n_paths == 0 or lr >= 1e9:
                continue
            for qi in range(n_paths):
                x_vars[start + qi] = ctx.scalar(f"x_l{li}_q{qi}")

        # 需求约束: Σ_q x = B/lr · L_e
        for (li, lr, n_paths, start) in self._link_meta:
            if n_paths == 0 or lr >= 1e9:
                continue
            total = sum(x_vars[start + qi] for qi in range(n_paths))
            ctx.constrain(f"route_dem_l{li}",
                          total - (B / lr) * L[li], "==", 0.0)

        # 边容量
        for ei, incident in enumerate(self._edge_incident):
            if not incident:
                continue
            expr = sum(x_vars[pi] for pi in incident)
            ctx.constrain(f"route_edge_e{ei}", expr, "<=",
                          float(self._edge_cap[ei]),
                          meaning=f"布线边 e{ei} 通道容量用尽")

        # 点容量
        for vi, incident in enumerate(self._vert_incident):
            if not incident:
                continue
            expr = sum(x_vars[pi] for pi in incident)
            ctx.constrain(f"route_vert_v{vi}", expr, "<=",
                          float(self._vert_cap[vi]),
                          meaning=f"布线顶点 v{vi} 容量用尽")

        # C4 pad 容量
        for pi, links in enumerate(self._c4_pad_links):
            if not links:
                continue
            expr = sum((B / float(self._lane_rates[li])) * L[li]
                       for li in links)
            ctx.constrain(f"route_c4pad_p{pi}", expr, "<=",
                          float(self._c4_pad_cap[pi]),
                          meaning=f"C4 pad p{pi} 布线容量用尽")

    def cache_key(self) -> tuple:
        return ("wiring_v1", self._total_paths,
                tuple(tuple(ei) for ei in self._edge_incident[:10]),
                len(self._vert_incident),
                len(self._c4_pad_links))


# ═══════════════════════════════════════════════════════════
# 预计算辅助
# ═══════════════════════════════════════════════════════════


def _collect_edge(ei, grid, n_links, path_groups, link_meta):
    """经过边 ei 的所有 (link, path) 的全局 path_idx 列表."""
    result = []
    for i in range(min(n_links, len(path_groups))):
        _, _, n_paths, start = link_meta[i]
        for qi, path_edges in enumerate(path_groups[i]):
            if ei in path_edges:
                result.append(start + qi)
    return result


def _collect_vertex(vi, grid, n_links, path_groups, link_meta):
    """经过顶点 vi 的所有 path_idx 列表."""
    result = []
    for i in range(min(n_links, len(path_groups))):
        _, _, n_paths, start = link_meta[i]
        for qi, path_edges in enumerate(path_groups[i]):
            for ei in path_edges:
                u, v = grid.edges[ei]
                if vi == u or vi == v:
                    result.append(start + qi)
                    break
    return result


# ═══════════════════════════════════════════════════════════
# 便捷构建器
# ═══════════════════════════════════════════════════════════


def make_wiring_model(
    placements,
    link_specs,
    link_indices,
    lane_rates,
    *,
    interposer_w_mm=80.0,
    interposer_h_mm=80.0,
    metal_layers=4,
    lanes_per_mm=200.0,
    c4_pitch_mm=5.0,
) -> WiringModel:
    """一站式构建."""
    grid = build_wiring_grid(
        placements, interposer_w_mm, interposer_h_mm,
        metal_layers, lanes_per_mm, c4_pitch_mm,
    )
    for spec in link_specs:
        if spec.get("c4_pad") is None and spec.get("from_die") is not None:
            dv = grid.die_vertex.get(spec["from_die"])
            if dv is not None and grid.c4_vertices:
                dx, dy = grid.vx[dv], grid.vy[dv]
                best = min(range(len(grid.c4_vertices)),
                           key=lambda pi: (grid.vx[grid.c4_vertices[pi]] - dx)**2
                                         + (grid.vy[grid.c4_vertices[pi]] - dy)**2)
                spec["c4_pad"] = best
    grid = populate_paths(grid, link_specs)
    return WiringModel(grid, link_specs, link_indices, lane_rates)


__all__ = [
    "WiringModel",
    "WiringGrid",
    "build_wiring_grid", "build_routing_grid", "populate_paths",
    "make_wiring_model", "make_routing_model",
]

# backward compat
make_routing_model = make_wiring_model
build_routing_grid = build_wiring_grid
