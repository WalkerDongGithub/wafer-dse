"""Max-weight Derangement 算法严格单元测试。

测试策略：
    1. 穷举验证：N ≤ 8 时枚举所有 derangement，确认返回最大权重
    2. 约束验证：assignment[i] ≠ i 始终成立
    3. 边界：N=0, N=1, 全零, 常数权重
"""

from __future__ import annotations

import itertools
import math
import random
import unittest

from wafer_dse.architecture_model.solver.algorithm.derangement import (
    max_weight_derangement,
)


def _derangements(n: int) -> list[tuple[int, ...]]:
    """返回 N 的所有 derangement（无自环排列）。"""
    result = []
    for perm in itertools.permutations(range(n)):
        if all(perm[i] != i for i in range(n)):
            result.append(perm)
    return result


def _random_weight(n: int, lo: float = 0.0, hi: float = 100.0) -> list[list[float]]:
    """生成 N×N 随机非负权重矩阵。"""
    return [[random.uniform(lo, hi) for _ in range(n)] for _ in range(n)]


class TestDerangementExhaustive(unittest.TestCase):
    """穷举验证：derangement 结果 = 全局最大权重。"""

    def _brute_force_max(self, weight: list[list[float]]) -> tuple[float, list[int]]:
        """穷举所有 derangement 找最大权重。"""
        n = len(weight)
        best_w = -1.0
        best_perm: list[int] = []
        for perm in _derangements(n):
            total = sum(weight[i][perm[i]] for i in range(n))
            if total > best_w:
                best_w = total
                best_perm = list(perm)
        return best_w, best_perm

    def test_n2_exhaustive(self):
        for _ in range(20):
            w = _random_weight(2)
            h_total, h_assign = max_weight_derangement(w)
            b_total, _ = self._brute_force_max(w)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertTrue(all(h_assign[i] != i for i in range(2)))

    def test_n3_exhaustive(self):
        for _ in range(20):
            w = _random_weight(3)
            h_total, h_assign = max_weight_derangement(w)
            b_total, _ = self._brute_force_max(w)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertTrue(all(h_assign[i] != i for i in range(3)))

    def test_n4_exhaustive(self):
        for _ in range(10):
            w = _random_weight(4)
            h_total, h_assign = max_weight_derangement(w)
            b_total, _ = self._brute_force_max(w)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertTrue(all(h_assign[i] != i for i in range(4)))

    def test_n5_exhaustive(self):
        """N=5: !5=44 derangements，穷举轻松。"""
        for _ in range(5):
            w = _random_weight(5)
            h_total, h_assign = max_weight_derangement(w)
            b_total, _ = self._brute_force_max(w)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertTrue(all(h_assign[i] != i for i in range(5)))

    def test_n6_exhaustive(self):
        """N=6: !6=265 derangements。"""
        for _ in range(3):
            w = _random_weight(6)
            h_total, h_assign = max_weight_derangement(w)
            b_total, _ = self._brute_force_max(w)
            self.assertAlmostEqual(h_total, b_total, places=9)
            self.assertTrue(all(h_assign[i] != i for i in range(6)))

    def test_n7_exhaustive(self):
        """N=7: !7=1854 derangements。"""
        w = _random_weight(7)
        h_total, h_assign = max_weight_derangement(w)
        b_total, _ = self._brute_force_max(w)
        self.assertAlmostEqual(h_total, b_total, places=9)
        self.assertTrue(all(h_assign[i] != i for i in range(7)))

    def test_n8_exhaustive(self):
        """N=8: !8=14833 derangements — 最终确认。"""
        w = _random_weight(8)
        h_total, h_assign = max_weight_derangement(w)
        b_total, _ = self._brute_force_max(w)
        self.assertAlmostEqual(h_total, b_total, places=9)
        self.assertTrue(all(h_assign[i] != i for i in range(8)))


class TestDerangementConstraints(unittest.TestCase):
    """约束与边界验证。"""

    def test_n0_empty(self):
        total, assign = max_weight_derangement([])
        self.assertEqual(total, 0.0)
        self.assertEqual(assign, [])

    def test_n1_empty(self):
        """N=1 无法构造 derangement → 返回空。"""
        total, assign = max_weight_derangement([[5.0]])
        self.assertEqual(total, 0.0)
        self.assertEqual(assign, [])

    def test_all_zeros(self):
        """全零权重 → 任意 derangement 权重为 0。"""
        w = [[0.0] * 4 for _ in range(4)]
        total, assign = max_weight_derangement(w)
        self.assertEqual(total, 0.0)
        self.assertTrue(all(assign[i] != i for i in range(4)))

    def test_constant_weights(self):
        """所有权重相等 → 任意 derangement 总权重相同 (= (n-1) * c)。"""
        n = 5
        w = [[10.0] * n for _ in range(n)]
        total, assign = max_weight_derangement(w)
        self.assertAlmostEqual(total, 10.0 * n, places=9)
        self.assertTrue(all(assign[i] != i for i in range(n)))

    def test_diagonal_only_nonzero(self):
        """仅对角有非零权重 → derangement 权重为 0（无法选对角）。"""
        n = 4
        w = [[(100.0 if i == j else 0.0) for j in range(n)] for i in range(n)]
        total, assign = max_weight_derangement(w)
        self.assertEqual(total, 0.0)
        self.assertTrue(all(assign[i] != i for i in range(n)))

    def test_non_square_raises(self):
        with self.assertRaises(ValueError):
            max_weight_derangement([[1.0, 2.0], [3.0]])

    def test_assignment_is_permutation(self):
        """结果必须是有效排列。"""
        for n in [2, 3, 4, 5, 6]:
            w = _random_weight(n)
            _, assign = max_weight_derangement(w)
            self.assertEqual(sorted(assign), list(range(n)))

    def test_total_matches_assignment(self):
        """返回值 total 必须等于 sum(weight[i][assign[i]])。"""
        for n in [2, 3, 4, 5]:
            w = _random_weight(n)
            total, assign = max_weight_derangement(w)
            expected = sum(w[i][assign[i]] for i in range(n))
            self.assertAlmostEqual(total, expected, places=9)


if __name__ == "__main__":
    unittest.main()
