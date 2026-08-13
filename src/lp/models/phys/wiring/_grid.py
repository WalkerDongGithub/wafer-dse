"""Interposer 布线网格 v3 —— die-aligned 网格点 + C4 pad.

网格模型:
  - 顶点 = 所有 (die_x ∪ c4_x) × (die_y ∪ c4_y) 的完整网格
  - 边 = 水平邻接 + 垂直邻接
  - 点容量 = 该点所有入射边容量的 max × factor
  - C4 pad = 网格上除 die 顶点外的特定顶点集合
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class WiringGrid:
    n_vertices: int
    n_edges: int

    # 几何
    vx: np.ndarray
    vy: np.ndarray

    # 网格坐标
    grid_ix: np.ndarray    # 每个顶点的列索引
    grid_iy: np.ndarray    # 每个顶点的行索引
    n_cols: int
    n_rows: int

    # 容量
    edge_cap: np.ndarray
    vert_cap: np.ndarray

    # 拓扑
    edges: list[tuple[int, int]]
    vert_edges: list[list[int]]

    # die / C4
    die_vertex: dict[int, int]
    c4_vertices: list[int]
    c4_pad_cap: np.ndarray

    # 候选路径
    path_groups: list[list[list[int]]]


def build_wiring_grid(
    placements,
    interposer_w_mm: float,
    interposer_h_mm: float,
    metal_layers: int = 4,
    lanes_per_mm: float = 200.0,
    c4_pitch_mm: float = 0.5,
    vert_cap_factor: float = 0.8,
) -> WiringGrid:
    """构建 die+C4 混合网格."""

    # 收集 x 坐标 (die 中心 + C4 格点)
    xs = sorted(set(
        [p.x + p.w / 2 for p in placements] +
        [i * c4_pitch_mm for i in range(int(interposer_w_mm / c4_pitch_mm) + 1)]
    ))
    ys = sorted(set(
        [p.y + p.h / 2 for p in placements] +
        [j * c4_pitch_mm for j in range(int(interposer_h_mm / c4_pitch_mm) + 1)]
    ))

    n_cols = len(xs)
    n_rows = len(ys)
    n_vertices = n_cols * n_rows

    vx = np.zeros(n_vertices)
    vy = np.zeros(n_vertices)
    grid_ix = np.zeros(n_vertices, dtype=int)
    grid_iy = np.zeros(n_vertices, dtype=int)

    for ix in range(n_cols):
        for iy in range(n_rows):
            vi = ix * n_rows + iy
            vx[vi] = xs[ix]
            vy[vi] = ys[iy]
            grid_ix[vi] = ix
            grid_iy[vi] = iy

    # 边
    edges: list[tuple[int, int]] = []
    edge_cap_list: list[float] = []
    vert_edges: list[list[int]] = [[] for _ in range(n_vertices)]

    def _add(u, v, cap):
        ei = len(edges)
        edges.append((u, v))
        edge_cap_list.append(cap)
        vert_edges[u].append(ei)
        vert_edges[v].append(ei)

    for ix in range(n_cols):
        for iy in range(n_rows):
            vi = ix * n_rows + iy
            if ix + 1 < n_cols:
                vj = (ix + 1) * n_rows + iy
                cap = abs(xs[ix + 1] - xs[ix]) * metal_layers * lanes_per_mm
                _add(vi, vj, cap)
            if iy + 1 < n_rows:
                vj = ix * n_rows + (iy + 1)
                cap = abs(ys[iy + 1] - ys[iy]) * metal_layers * lanes_per_mm
                _add(vi, vj, cap)

    n_edges = len(edges)

    # 顶点容量
    vert_cap = np.zeros(n_vertices)
    for vi in range(n_vertices):
        max_cap = max((edge_cap_list[ei] for ei in vert_edges[vi]), default=1.0)
        vert_cap[vi] = max_cap * vert_cap_factor

    # die → 最近顶点
    die_vertex: dict[int, int] = {}
    die_occ: set[int] = set()
    for di, p in enumerate(placements):
        cx, cy = p.x + p.w / 2, p.y + p.h / 2
        best = int(np.argmin((vx - cx)**2 + (vy - cy)**2))
        die_vertex[di] = best
        die_occ.add(best)

    # C4 pad 顶点 (C4 格点上且不被 die 占据的顶点)
    c4_vertices: list[int] = []
    for ix in range(n_cols):
        for iy in range(n_rows):
            vi = int(ix * n_rows + iy)
            if vi not in die_occ:
                # 判断是否为 C4 格点: x, y 接近 c4_pitch 的整数倍
                if (abs(vx[vi] % c4_pitch_mm) < 0.01 or
                    abs(vx[vi] % c4_pitch_mm - c4_pitch_mm) < 0.01):
                    c4_vertices.append(vi)

    c4_per_pad = max(1, int(c4_pitch_mm**2 * 59))
    c4_pad_cap = np.full(len(c4_vertices), c4_per_pad)

    return WiringGrid(
        n_vertices=n_vertices, n_edges=n_edges,
        vx=vx, vy=vy,
        grid_ix=grid_ix, grid_iy=grid_iy,
        n_cols=n_cols, n_rows=n_rows,
        edge_cap=np.array(edge_cap_list),
        vert_cap=vert_cap,
        edges=edges, vert_edges=vert_edges,
        die_vertex=die_vertex, c4_vertices=c4_vertices,
        c4_pad_cap=c4_pad_cap,
        path_groups=[],
    )


def _vertex_at(ix, iy, n_rows):
    return int(ix * n_rows + iy)


def populate_paths(grid, link_specs):
    """为每条链路生成候选路径.

    路径 = 在网格上从 src vertex 到 dst vertex 的 L 形最短路径.
    使用网格坐标 (ix, iy) 导航，不需要物理坐标.
    """
    groups: list[list[list[int]]] = []

    for spec in link_specs:
        src_die = spec.get("from_die", -1)
        dst_die = spec.get("to_die")
        c4_idx = spec.get("c4_pad")

        src = grid.die_vertex.get(src_die, -1)
        if src < 0:
            groups.append([[]])
            continue

        if dst_die is not None:
            dst = grid.die_vertex.get(dst_die, -1)
        elif c4_idx is not None and 0 <= c4_idx < len(grid.c4_vertices):
            dst = grid.c4_vertices[c4_idx]
        else:
            groups.append([[]])
            continue

        if dst < 0 or src == dst:
            groups.append([[]])
            continue

        six, siy = grid.grid_ix[src], grid.grid_iy[src]
        dix, diy = grid.grid_ix[dst], grid.grid_iy[dst]

        paths: list[list[int]] = []

        # 路径 1: 先水平后垂直
        e1 = _grid_path_h_then_v(six, siy, dix, diy, grid)
        if e1:
            paths.append(e1)

        # 路径 2: 先垂直后水平
        if six != dix and siy != diy:
            e2 = _grid_path_v_then_h(six, siy, dix, diy, grid)
            if e2 and e2 != e1:
                paths.append(e2)

        if not paths and e1:
            paths.append(e1)
        elif not paths:
            paths.append([])

        groups.append(paths)

    return WiringGrid(
        n_vertices=grid.n_vertices, n_edges=grid.n_edges,
        vx=grid.vx, vy=grid.vy,
        grid_ix=grid.grid_ix, grid_iy=grid.grid_iy,
        n_cols=grid.n_cols, n_rows=grid.n_rows,
        edge_cap=grid.edge_cap, vert_cap=grid.vert_cap,
        edges=grid.edges, vert_edges=grid.vert_edges,
        die_vertex=grid.die_vertex, c4_vertices=grid.c4_vertices,
        c4_pad_cap=grid.c4_pad_cap,
        path_groups=groups,
    )


def _grid_path_h_then_v(six, siy, dix, diy, grid):
    """先沿 x 走到 dix，再沿 y 走到 diy."""
    edges_list = []
    nr = grid.n_rows

    # 水平段
    cx = six
    step = 1 if dix > six else -1
    while cx != dix:
        nx = cx + step
        u = _vertex_at(cx, siy, nr)
        v = _vertex_at(nx, siy, nr)
        ei = _find_edge_idx(u, v, grid)
        if ei is None:
            return None
        edges_list.append(ei)
        cx = nx

    # 垂直段
    cy = siy
    step = 1 if diy > siy else -1
    while cy != diy:
        ny = cy + step
        u = _vertex_at(dix, cy, nr)
        v = _vertex_at(dix, ny, nr)
        ei = _find_edge_idx(u, v, grid)
        if ei is None:
            return None
        edges_list.append(ei)
        cy = ny

    return edges_list


def _grid_path_v_then_h(six, siy, dix, diy, grid):
    """先沿 y 走到 diy，再沿 x 走到 dix."""
    edges_list = []
    nr = grid.n_rows

    cy = siy
    step = 1 if diy > siy else -1
    while cy != diy:
        ny = cy + step
        u = _vertex_at(six, cy, nr)
        v = _vertex_at(six, ny, nr)
        ei = _find_edge_idx(u, v, grid)
        if ei is None:
            return None
        edges_list.append(ei)
        cy = ny

    cx = six
    step = 1 if dix > six else -1
    while cx != dix:
        nx = cx + step
        u = _vertex_at(cx, diy, nr)
        v = _vertex_at(nx, diy, nr)
        ei = _find_edge_idx(u, v, grid)
        if ei is None:
            return None
        edges_list.append(ei)
        cx = nx

    return edges_list


def _find_edge_idx(u, v, grid) -> int | None:
    u, v = int(u), int(v)
    for ei in grid.vert_edges[u]:
        a, b = grid.edges[ei]
        if (a == u and b == v) or (a == v and b == u):
            return ei
    return None
