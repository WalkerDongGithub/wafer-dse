"""Hungarian 算法严格单元测试。

测试策略：
    1. 穷举验证：N ≤ 8 时枚举所有排列，确认 Hungarian 返回全局最优
    2. 边界：N=0, N=1, 全零, 非方阵, 负值
    3. 数学性质：行/列常数不变性，排列有效性
"""

from __future__ import annotations

import itertools
import math
import random
import unittest

from wafer_dse.architecture_model.solver.algorithm.hungarian import (
    hungarian_min_cost,
)


class TestHungarianExhaustive(unittest.TestCase):
    """穷举验证：对随机矩阵，Hungarian 结果 = 全局最优。"""

    def _brute_force_min(self, cost: list[list[float]]) -> tuple[float, list[int]]:
        """穷举所有排列找最小值（仅用于小 N 验证）。"""
        n = len(cost)
        best_cost = float("inf")
        best_perm = []
        for perm in itertools.permutations(range(n)):
            total = sum(cost[i][perm[i]] for i in range(n))
            if total < best_cost:
                best_cost = total
                best_perm = list(perm)
        return best_cost, best_perm

    def _random_square(self, n: int, lo: float = -10.0, hi: float = 100.0) -> list[list[float]]:
        """生成 N×N 随机方阵。"""
        return [[random.uniform(lo, hi) for _ in range(n)] for _ in range(n)]

    def test_n0_empty(self):
        total, assign = hungarian_min_cost([])
        self.assertEqual(total, 0.0)
        self.assertEqual(assign, [])

    def test_n1_single(self):
        total, assign = hungarian_min_cost([[5.0]])
        self.assertEqual(total, 5.0)
        self.assertEqual(assign, [0])

    def test_n2_exhaustive(self):
        for _ in range(20):
            cost = self._random_square(2)
            h_total, h_assign = hungarian_min_cost(cost)
            b_total, _ = self._brute_force_min(cost)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertEqual(sorted(h_assign), [0, 1])

    def test_n3_exhaustive(self):
        for _ in range(20):
            cost = self._random_square(3)
            h_total, h_assign = hungarian_min_cost(cost)
            b_total, _ = self._brute_force_min(cost)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertEqual(sorted(h_assign), [0, 1, 2])

    def test_n4_exhaustive(self):
        for _ in range(10):
            cost = self._random_square(4)
            h_total, h_assign = hungarian_min_cost(cost)
            b_total, _ = self._brute_force_min(cost)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertEqual(sorted(h_assign), [0, 1, 2, 3])

    def test_n5_exhaustive(self):
        for _ in range(5):
            cost = self._random_square(5)
            h_total, h_assign = hungarian_min_cost(cost)
            b_total, _ = self._brute_force_min(cost)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertEqual(sorted(h_assign), list(range(5)))

    def test_n7_exhaustive(self):
        """N=7: 5040 permutations — 单次确认。"""
        cost = self._random_square(7)
        h_total, h_assign = hungarian_min_cost(cost)
        b_total, _ = self._brute_force_min(cost)
        self.assertAlmostEqual(h_total, b_total, places=9)
        self.assertEqual(sorted(h_assign), list(range(7)))

    def test_n8_exhaustive(self):
        """N=8: 40320 permutations — 最终确认。"""
        cost = self._random_square(8)
        h_total, h_assign = hungarian_min_cost(cost)
        b_total, _ = self._brute_force_min(cost)
        self.assertAlmostEqual(h_total, b_total, places=9)
        self.assertEqual(sorted(h_assign), list(range(8)))


class TestHungarianEdgeCases(unittest.TestCase):
    """边界与特殊情况。"""

    def test_all_zeros(self):
        cost = [[0.0, 0.0], [0.0, 0.0]]
        total, assign = hungarian_min_cost(cost)
        self.assertEqual(total, 0.0)
        self.assertEqual(sorted(assign), [0, 1])

    def test_negative_values(self):
        cost = [[-5.0, -3.0], [-2.0, -4.0]]
        total, assign = hungarian_min_cost(cost)
        # 行 0→列 0(-5) + 行 1→列 1(-4) = -9, 或 行 0→列 1(-3) + 行 1→列 0(-2) = -5
        # 最优 = -9
        self.assertAlmostEqual(total, -9.0, places=9)
        self.assertEqual(assign, [0, 1])

    def test_non_square_raises(self):
        with self.assertRaises(ValueError):
            hungarian_min_cost([[1.0, 2.0], [3.0]])

    def test_assignment_is_valid_permutation(self):
        """assignment 必须是 0..N-1 的排列。"""
        for n in [1, 2, 3, 4, 5, 6]:
            cost = [[random.uniform(0, 100) for _ in range(n)] for _ in range(n)]
            _, assign = hungarian_min_cost(cost)
            self.assertEqual(sorted(assign), list(range(n)),
                             f"N={n}: assignment 不是有效排列: {assign}")


class TestHungarianMathProperties(unittest.TestCase):
    """数学性质不变式。"""

    def test_row_constant_addition_preserves_assignment(self):
        """某行全部加 c：最优分配不变，总成本 +c。"""
        cost = [[random.uniform(0, 100) for _ in range(5)] for _ in range(5)]
        _, orig_assign = hungarian_min_cost(cost)

        # 给第 2 行所有元素加 100
        modified = [row[:] for row in cost]
        c = 100.0
        for j in range(5):
            modified[2][j] += c

        mod_total, mod_assign = hungarian_min_cost(modified)
        orig_total = sum(cost[i][orig_assign[i]] for i in range(5))

        self.assertEqual(mod_assign, orig_assign)
        self.assertAlmostEqual(mod_total, orig_total + c, places=9)

    def test_column_constant_addition_preserves_assignment(self):
        """某列全部加 c：最优分配不变，总成本 +c。"""
        cost = [[random.uniform(0, 100) for _ in range(5)] for _ in range(5)]
        _, orig_assign = hungarian_min_cost(cost)

        modified = [row[:] for row in cost]
        c = 50.0
        for i in range(5):
            modified[i][3] += c

        mod_total, mod_assign = hungarian_min_cost(modified)
        orig_total = sum(cost[i][orig_assign[i]] for i in range(5))

        self.assertEqual(mod_assign, orig_assign)
        self.assertAlmostEqual(mod_total, orig_total + c, places=9)

    def test_known_solution(self):
        """已知最优解的标准测试用例。"""
        cost = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
        total, assign = hungarian_min_cost(cost)
        # 最优：assign=[2,1,0] → 3+4+3=10
        # 注意 docstring 中声称 total=8 是错误的
        self.assertEqual(total, 10.0)
        self.assertEqual(assign, [2, 1, 0])


if __name__ == "__main__":
    unittest.main()
