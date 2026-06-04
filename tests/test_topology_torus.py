"""Torus 拓扑严格单元测试。

测试策略：
    1. 坐标系统：往返一致 + 环绕 mod
    2. det 路由：环绕最短路径、邻接性、无环、收敛
    3. valiant 路由：包含 det、路径数、无重复
    4. 基本属性
"""

from __future__ import annotations

import unittest

from wafer_dse.architecture_model.topology.torus import Torus


class TestTorusCoordinates(unittest.TestCase):
    """坐标系统。"""

    def test_roundtrip_all_nodes(self):
        for size in [3, 4, 5, 6]:
            t = Torus(size)
            for nid in range(size * size):
                loc = t.to_loc(nid)
                back = t.to_node(loc)
                self.assertEqual(back, nid,
                                 f"Torus({size}): to_node(to_loc({nid})) = {back}")

    def test_wrap_coordinates(self):
        """环绕坐标应在 mod size 范围内。"""
        t = Torus(4)
        # 坐标 [4, 0] 应被 wrap 到 [0, 0]
        self.assertEqual(t.to_node([4, 0]), 0)
        self.assertEqual(t.to_node([-1, 0]), 3)
        self.assertEqual(t.to_node([0, 5]), 4)  # 0 + 1*4 = 4

    def test_known_mappings(self):
        t = Torus(4)
        self.assertEqual(t.to_loc(0), [0, 0])
        self.assertEqual(t.to_loc(15), [3, 3])


class TestTorusBasicProperties(unittest.TestCase):
    """基本属性。"""

    def test_node_counts(self):
        for size in [3, 4, 5]:
            t = Torus(size)
            self.assertEqual(t.node_num(), size * size)
            self.assertEqual(t.node_num(), t.terminal_num())

    def test_all_nodes_are_terminals(self):
        t = Torus(4)
        for nid in range(16):
            self.assertTrue(t.is_terminal(nid))


class TestTorusDetRouting(unittest.TestCase):
    """deterministic 路由 — 特别关注环绕行为。"""

    def test_path_endpoints(self):
        t = Torus(4)
        for src in range(16):
            for dst in range(16):
                if src == dst:
                    self.assertEqual(t.det(src, dst)[0], [src])
                else:
                    path = t.det(src, dst)[0]
                    self.assertEqual(path[0], src)
                    self.assertEqual(path[-1], dst)

    def test_wrap_shortcut(self):
        """环绕边应提供最短路径。Torus(4): 0→3 应为 1 步（经环绕边）。"""
        t = Torus(4)
        path = t.det(0, 3)[0]
        # 0→3 经 x 维环绕：1 步
        self.assertEqual(len(path), 2)  # [0, 3]
        self.assertEqual(path, [0, 3])

    def test_equal_distance_wrap(self):
        """Torus(4) 0→2: x 方向正反均为 2 步，任选其一。"""
        t = Torus(4)
        path = t.det(0, 2)[0]
        # 应为 2 步（两个方向相等，选正方向 0→1→2 或反方向 0→3→2）
        self.assertEqual(len(path), 3)  # [0, x, 2]

    def test_adjacency(self):
        """每步在恰好一维上变化 ±1 (mod size)，另一维不变。

        Torus(4) 相邻定义：一维变化为 1 或 size-1（即 mod 下的 ±1），
        另一维变化为 0。使用 XOR 逻辑：恰好一维变化。
        """
        t = Torus(4)
        for src in range(16):
            for dst in range(16):
                if src == dst:
                    continue
                path = t.det(src, dst)[0]
                for k in range(len(path) - 1):
                    a = t.to_loc(path[k])
                    b = t.to_loc(path[k + 1])
                    dx = (b[0] - a[0]) % t.size
                    dy = (b[1] - a[1]) % t.size
                    # 一维变化（1 或 size-1），另一维不变（0）
                    x_changed = dx in {1, t.size - 1}
                    y_changed = dy in {1, t.size - 1}
                    self.assertTrue(x_changed != y_changed,
                        f"Torus(4) {src}→{dst} step {k}: "
                        f"{a}→{b} dx={dx} dy={dy} — expected exactly one dim changed")
                    if dx not in {0, 1, t.size - 1}:
                        self.assertEqual(dy, 0)
                    if dy not in {0, 1, t.size - 1}:
                        self.assertEqual(dx, 0)

    def test_no_cycles(self):
        t = Torus(4)
        for src in range(16):
            for dst in range(16):
                path = t.det(src, dst)[0]
                self.assertEqual(len(path), len(set(path)),
                                 f"Torus(4) {src}→{dst}: has cycles")

    def test_convergence_guaranteed(self):
        """所有路由在合理步数内收敛，不应该死循环。"""
        for size in [3, 4, 5, 6]:
            t = Torus(size)
            for src in range(size * size):
                for dst in range(size * size):
                    path = t.det(src, dst)[0]
                    self.assertLessEqual(len(path) - 1, size * size,
                                         f"Torus({size}) {src}→{dst}: too long")

    def test_multi_size(self):
        """多 size 测试确保路由收敛。"""
        for size in [2, 3, 4, 5, 6]:
            t = Torus(size)
            n = size * size
            for src in range(n):
                for dst in range(n):
                    path = t.det(src, dst)[0]
                    self.assertEqual(path[0], src)
                    self.assertEqual(path[-1], dst)


class TestTorusValiantRouting(unittest.TestCase):
    """Valiant 路由。"""

    def test_includes_det_path(self):
        t = Torus(3)
        for src in range(9):
            for dst in range(9):
                if src == dst:
                    continue
                det_tuple = tuple(t.det(src, dst)[0])
                val_tuples = [tuple(p) for p in t.valiant(src, dst)]
                self.assertIn(det_tuple, val_tuples)

    def test_path_count(self):
        """valiant 路径数 ≤ 1 + (终端数 - 2)。

        某些中转路径可能与 det 路径重复，被 _unique_paths 去重。
        """
        t = Torus(3)
        for src in range(9):
            for dst in range(9):
                if src == dst:
                    continue
                paths = t.valiant(src, dst)
                max_expected = 1 + (9 - 2)  # 1 det + 7 intermediate
                self.assertLessEqual(len(paths), max_expected)
                self.assertGreaterEqual(len(paths), 1)

    def test_no_duplicate_paths(self):
        t = Torus(3)
        for src in range(9):
            for dst in range(9):
                if src == dst:
                    continue
                paths = t.valiant(src, dst)
                tuples = [tuple(p) for p in paths]
                self.assertEqual(len(tuples), len(set(tuples)))


if __name__ == "__main__":
    unittest.main()
