"""
MCF-LP routing feasibility on interposer grid.

Given placement (die → grid positions) and edge demands (L_e × B/R_e lanes),
formulate the multi-commodity flow LP to check if all demands can be routed
within grid capacities.

This follows the FPIA grid structure: Manhattan paths on an N×N grid,
each grid edge has a lane capacity C_g, each demand edge needs d_e lanes.

Usage:
    grid = WaferGrid.rect(n=8, die_zones=[(2,3), (4,5), ...])
    checker = RoutingFeasibility(grid)
    result = checker.check(
        positions={0: (2,3), 1: (4,5)},
        demands=[(0, 1, 12.5)],   # (src_die, dst_die, lanes_needed)
    )
    print(result.feasible, result.congested_edges)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from wafer_dse.partition.grid import WaferGrid, PartitionType


@dataclass
class RoutingFeasibilityResult:
    feasible: bool
    max_congestion: float         # max (used / capacity) across all grid edges
    congested_edges: list[tuple[tuple[int, int], tuple[int, int], float]]
    # [(grid_pos_a, grid_pos_b, congestion_ratio), ...]
    solver_name: str = ""
    num_variables: int = 0
    solve_time_s: float = 0.0


class RoutingFeasibility:
    """Check if a set of edge demands can be routed on the WaferGrid.

    Formulates as MCF-LP. The continuous LP is a NECESSARY condition:
    LP infeasible → no integer routing exists.
    LP feasible → integer routing may or may not exist (rounding needed).
    """

    def __init__(self, grid: WaferGrid, capacity_per_edge: int = 256):
        self.grid = grid
        self.capacity = capacity_per_edge  # lanes per grid edge

    # ------------------------------------------------------------------
    # Grid graph
    # ------------------------------------------------------------------

    def _grid_edges(self) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        """All directed Manhattan edges between adjacent valid zones."""
        edges = []
        for (x, y), z in self.grid.zones.items():
            if z.zone_type == PartitionType.UNUSABLE:
                continue
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                np = (nx, ny)
                if np in self.grid.zones and self.grid.zones[np].zone_type != PartitionType.UNUSABLE:
                    edges.append(((x, y), np))
        return edges

    # ------------------------------------------------------------------
    # Simple heuristic (no LP solver needed)
    # ------------------------------------------------------------------

    def check_heuristic(
        self,
        positions: dict[int, tuple[int, int]],
        demands: list[tuple[int, int, float]],  # (src, dst, lanes)
    ) -> RoutingFeasibilityResult:
        """Estimate congestion by routing each demand on its shortest path
        and summing loads. No LP — fast upper bound on feasibility.

        If this passes: LP would likely pass.
        If this fails: LP *might* still pass (rerouting could help).
        """
        grid_edges = self._grid_edges()
        load: dict[tuple, float] = {e: 0.0 for e in grid_edges}

        for src, dst, lanes in demands:
            if src not in positions or dst not in positions:
                continue
            sx, sy = positions[src]
            dx, dy = positions[dst]
            # Manhattan path: horizontal first, then vertical
            path = self._manhattan_path(sx, sy, dx, dy)
            for i in range(len(path) - 1):
                edge = (path[i], path[i + 1])
                if edge in load:
                    load[edge] += lanes

        max_congestion = 0.0
        congested = []
        for e, used in load.items():
            ratio = used / self.capacity if self.capacity > 0 else float("inf")
            if ratio > max_congestion:
                max_congestion = ratio
            if ratio > 1.0:
                congested.append((e[0], e[1], ratio))

        congested.sort(key=lambda x: -x[2])
        return RoutingFeasibilityResult(
            feasible=len(congested) == 0,
            max_congestion=max_congestion,
            congested_edges=congested[:10],
            solver_name="shortest_path_heuristic",
            num_variables=len(grid_edges),
        )

    # ------------------------------------------------------------------
    # LP formulation (cvxpy, optional)
    # ------------------------------------------------------------------

    def check_lp(
        self,
        positions: dict[int, tuple[int, int]],
        demands: list[tuple[int, int, float]],
    ) -> RoutingFeasibilityResult:
        """MCF-LP: find any flow assignment satisfying all demands
        within grid edge capacities.

        For each demand k = (src_k, dst_k) with d_k lanes:
          find flow f_k(e) ≥ 0 s.t.
            flow conservation at each grid node
            Σ_k f_k(e) ≤ C_e for all grid edges e
        """
        try:
            import cvxpy as cvx
        except ImportError:
            return self.check_heuristic(positions, demands)

        import time
        t0 = time.time()

        # Build grid graph
        nodes = [(x, y) for (x, y), z in self.grid.zones.items()
                 if z.zone_type != PartitionType.UNUSABLE]
        node_index = {p: i for i, p in enumerate(nodes)}
        grid_edges = self._grid_edges()
        edge_index = {e: i for i, e in enumerate(grid_edges)}
        n_nodes = len(nodes)
        n_edges = len(grid_edges)

        # Filter demands with valid positions
        valid_demands = [(s, d, lanes) for s, d, lanes in demands
                         if s in positions and d in positions]
        n_demands = len(valid_demands)
        if n_demands == 0:
            return RoutingFeasibilityResult(
                feasible=True, max_congestion=0.0, congested_edges=[],
                solver_name="lp_trivial",
            )

        # Variables: f_k[e] for each demand k and grid edge e
        # Too many variables for large problems. Use path-based formulation:
        # For each demand, we precompute candidate paths and assign flow fractions.

        # Simplified: use node-based flow variables for each demand
        constraints = []
        edge_flow_vars = []

        for k, (src, dst, d_k) in enumerate(valid_demands):
            sp, dp = positions[src], positions[dst]
            si, di = node_index[sp], node_index[dp]

            # Flow variable per grid edge for this demand
            f = cvx.Variable(n_edges, nonneg=True)
            edge_flow_vars.append(f)

            # Flow conservation
            for node, ni in node_index.items():
                inflow = cvx.sum([f[edge_index[(a, b)]] for a, b in grid_edges if b == node])
                outflow = cvx.sum([f[edge_index[(a, b)]] for a, b in grid_edges if a == node])
                if ni == si:
                    constraints.append(outflow - inflow == d_k)
                elif ni == di:
                    constraints.append(outflow - inflow == -d_k)
                else:
                    constraints.append(outflow - inflow == 0)

        # Capacity constraints
        for e, ei in edge_index.items():
            total_flow = cvx.sum([fv[ei] for fv in edge_flow_vars])
            constraints.append(total_flow <= self.capacity)

        # Feasibility problem — no objective, just find any feasible point
        # Add a trivial objective to make cvxpy happy
        obj = cvx.Minimize(0)
        prob = cvx.Problem(obj, constraints)

        try:
            prob.solve(verbose=False, solver=cvx.CLARABEL)
        except cvx.error.SolverError:
            # Fallback: try other solvers or heuristic
            result = self.check_heuristic(positions, demands)
            result.solver_name = "lp_failed_fallback"
            return result

        elapsed = time.time() - t0
        feasible = prob.status in ("optimal", "optimal_inaccurate")

        # Compute congestion
        max_congestion = 0.0
        congested = []
        for e, ei in edge_index.items():
            total = sum(fv.value[ei] if fv.value is not None else 0 for fv in edge_flow_vars)
            ratio = total / self.capacity if self.capacity > 0 else float("inf")
            if ratio > max_congestion:
                max_congestion = ratio
            if ratio > 1.0:
                congested.append((e[0], e[1], float(ratio)))

        congested.sort(key=lambda x: -x[2])

        return RoutingFeasibilityResult(
            feasible=feasible,
            max_congestion=max_congestion,
            congested_edges=congested[:10],
            solver_name=f"lp_{prob.status}",
            num_variables=n_demands * n_edges,
            solve_time_s=elapsed,
        )

    # ------------------------------------------------------------------
    # Main entry: auto-select method
    # ------------------------------------------------------------------

    def check(
        self,
        positions: dict[int, tuple[int, int]],
        demands: list[tuple[int, int, float]],
        use_lp: bool = True,
    ) -> RoutingFeasibilityResult:
        if use_lp:
            return self.check_lp(positions, demands)
        return self.check_heuristic(positions, demands)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _manhattan_path(
        sx: int, sy: int, dx: int, dy: int,
    ) -> list[tuple[int, int]]:
        """Manhattan path: horizontal first, then vertical."""
        path = [(sx, sy)]
        x_step = 1 if dx >= sx else -1
        for x in range(sx + x_step, dx + x_step, x_step):
            path.append((x, sy))
        y_step = 1 if dy >= sy else -1
        for y in range(sy + y_step, dy + y_step, y_step):
            path.append((dx, y))
        return path
