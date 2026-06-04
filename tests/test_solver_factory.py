"""create_solver 工厂单元测试。

测试策略：
    - 支持的 route 返回正确类型
    - 不支持的 route 抛 ValueError
    - 返回的 solver 的 supported_routes 包含输入 route
"""

from __future__ import annotations

import unittest

from wafer_dse.architecture_model.solver import create_solver, FixedRouteSolver, Solver


class TestCreateSolver(unittest.TestCase):

    def test_det_returns_fixed_route_solver(self):
        solver = create_solver("det")
        self.assertIsInstance(solver, FixedRouteSolver)
        self.assertIsInstance(solver, Solver)

    def test_val_returns_fixed_route_solver(self):
        solver = create_solver("val")
        self.assertIsInstance(solver, FixedRouteSolver)

    def test_opt_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            create_solver("opt")
        self.assertIn("opt", str(ctx.exception))

    def test_unknown_route_raises_value_error(self):
        with self.assertRaises(ValueError):
            create_solver("nonexistent")

    def test_returned_solver_supports_requested_route(self):
        for route in ["det", "val"]:
            solver = create_solver(route)
            self.assertIn(route, solver.supported_routes)

    def test_different_calls_return_different_instances(self):
        """每次调用返回新的求解器实例。"""
        s1 = create_solver("det")
        s2 = create_solver("det")
        self.assertIsNot(s1, s2)


if __name__ == "__main__":
    unittest.main()
