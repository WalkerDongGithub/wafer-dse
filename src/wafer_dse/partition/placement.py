"""
Chiplet placement on interposer grid — QP initialization + SA refinement.

Follows FPIA (Jiao et al., TCASI 2024) approach:
  1. QP: minimize weighted quadratic wirelength → continuous initial positions
  2. SA: simulated annealing with HPWL cost → discrete grid assignment

Usage:
    placer = GridPlacer(grid_size=8)
    positions = placer.place(die_ids=[0,1,2,3], edges=[(0,1,1.0), (1,2,2.0)])
    print(positions)  # {0: (3,4), 1: (4,4), ...}
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class PlacementResult:
    positions: dict[int, tuple[int, int]]  # die_id → (x, y)
    hpwl: float                            # half-perimeter wirelength
    iterations: int


class GridPlacer:
    """QP + SA placement on an N×N grid."""

    def __init__(self, grid_size: int = 8, seed: int = 42):
        self.n = grid_size
        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Step 1: QP initial placement (continuous relaxation)
    # ------------------------------------------------------------------

    def _qp_init(
        self,
        die_ids: list[int],
        edges: list[tuple[int, int, float]],  # (u, v, weight)
    ) -> dict[int, tuple[float, float]]:
        """Minimize Σ w_uv [(x_u - x_v)² + (y_u - y_v)²].

        Solved analytically: set x-coordinates to minimize quadratic form.
        For a connected graph, the solution is the weighted centroid of neighbors.
        We use iterative averaging (Jacobi) — converges in a few iterations.
        """
        n_dies = len(die_ids)
        idx = {did: i for i, did in enumerate(die_ids)}

        # Build adjacency
        adj: dict[int, list[tuple[int, float]]] = {did: [] for did in die_ids}
        for u, v, w in edges:
            if u in adj and v in adj:
                adj[u].append((v, w))
                adj[v].append((u, w))

        # Initialize randomly in [0, n)
        xs = {did: self.rng.uniform(0, self.n - 1) for did in die_ids}
        ys = {did: self.rng.uniform(0, self.n - 1) for did in die_ids}

        # Jacobi iteration
        for _ in range(50):
            new_xs: dict[int, float] = {}
            new_ys: dict[int, float] = {}
            for did in die_ids:
                if not adj[did]:
                    new_xs[did] = xs[did]
                    new_ys[did] = ys[did]
                    continue
                wx_sum, wy_sum, w_sum = 0.0, 0.0, 0.0
                for nb, w in adj[did]:
                    wx_sum += w * xs[nb]
                    wy_sum += w * ys[nb]
                    w_sum += w
                new_xs[did] = wx_sum / w_sum
                new_ys[did] = wy_sum / w_sum
            xs, ys = new_xs, new_ys

        return {did: (xs[did], ys[did]) for did in die_ids}

    # ------------------------------------------------------------------
    # Step 2: SA discrete refinement
    # ------------------------------------------------------------------

    def _hpwl(
        self,
        positions: dict[int, tuple[int, int]],
        edges: list[tuple[int, int, float]],
    ) -> float:
        """Half-perimeter wirelength cost."""
        total = 0.0
        for u, v, _ in edges:
            if u in positions and v in positions:
                xu, yu = positions[u]
                xv, yv = positions[v]
                total += abs(xu - xv) + abs(yu - yv)
        return total

    def _sa_refine(
        self,
        positions: dict[int, tuple[int, int]],
        edges: list[tuple[int, int, float]],
        steps: int = 2000,
        t0: float = 10.0,
        t_freeze: float = 0.01,
        cool: float = 0.95,
    ) -> tuple[dict[int, tuple[int, int]], float, int]:
        """Simulated annealing with swap/jump moves."""
        current = dict(positions)
        current_cost = self._hpwl(current, edges)
        best = dict(current)
        best_cost = current_cost
        T = t0
        die_ids = list(current.keys())
        iterations = 0

        while T > t_freeze:
            for _ in range(steps // max(1, int(-math.log(t_freeze / t0) / math.log(cool)))):
                iterations += 1
                # Generate neighbor: swap two dies or move one to empty
                new = dict(current)
                if self.rng.random() < 0.7 and len(die_ids) >= 2:
                    a, b = self.rng.sample(die_ids, 2)
                    new[a], new[b] = new[b], new[a]
                else:
                    a = self.rng.choice(die_ids)
                    new[a] = (
                        self.rng.randint(0, self.n - 1),
                        self.rng.randint(0, self.n - 1),
                    )

                new_cost = self._hpwl(new, edges)
                delta = new_cost - current_cost

                if delta <= 0 or self.rng.random() < math.exp(-delta / T):
                    current, current_cost = new, new_cost
                    if current_cost < best_cost:
                        best, best_cost = dict(current), current_cost

            T *= cool

        return best, best_cost, iterations

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------

    def place(
        self,
        die_ids: list[int],
        edges: list[tuple[int, int, float]],
        steps: int = 2000,
    ) -> PlacementResult:
        """Place dies on the grid. Returns discrete (x,y) positions."""
        # QP init
        qp_positions = self._qp_init(die_ids, edges)

        # Snap to discrete grid
        discrete = {
            did: (
                max(0, min(self.n - 1, int(round(x)))),
                max(0, min(self.n - 1, int(round(y)))),
            )
            for did, (x, y) in qp_positions.items()
        }

        # Resolve collisions (multiple dies snapped to same grid cell)
        discrete = self._resolve_collisions(discrete, die_ids)

        # SA refine
        positions, hpwl, iters = self._sa_refine(discrete, edges, steps=steps)

        return PlacementResult(positions=positions, hpwl=hpwl, iterations=iters)

    def _resolve_collisions(
        self,
        positions: dict[int, tuple[int, int]],
        die_ids: list[int],
    ) -> dict[int, tuple[int, int]]:
        """Move colliding dies to nearest empty grid cells."""
        occupied: set[tuple[int, int]] = set()
        resolved: dict[int, tuple[int, int]] = {}

        # Sort by "closeness to integer" (QP quality)
        order = sorted(die_ids, key=lambda did: 0)  # arbitrary for now
        for did in order:
            pos = positions[did]
            if pos not in occupied:
                resolved[did] = pos
                occupied.add(pos)
            else:
                # Find nearest empty cell
                for r in range(1, self.n):
                    found = False
                    for dx in range(-r, r + 1):
                        for dy in range(-r, r + 1):
                            if abs(dx) + abs(dy) != r:
                                continue
                            nx, ny = pos[0] + dx, pos[1] + dy
                            if 0 <= nx < self.n and 0 <= ny < self.n:
                                np = (nx, ny)
                                if np not in occupied:
                                    resolved[did] = np
                                    occupied.add(np)
                                    found = True
                                    break
                        if found:
                            break
                    if found:
                        break

        return resolved
