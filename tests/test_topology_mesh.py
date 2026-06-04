"""Mesh 拓扑严格单元测试。

测试策略：
    1. 坐标系统：往返一致 + 已知映射
    2. det 路由：起终点、邻接性、维序(via y then x)、无环、收敛
    3. valiant 路由：包含 det、路径数、无重复
    4. 基本属性：terminal_num, node_num, is_terminal
"""

from __future__ import annotations

import unittest

from wafer_dse.architecture_model.topology.mesh import Mesh


class TestMeshCoordinates(unittest.TestCase):
    """坐标系统正确性。"""

    def test_roundtrip_all_nodes(self):
        for size in [2, 3, 4, 5, 6, 8]:
            m = Mesh(size)
            for nid in range(size * size):
                loc = m.to_loc(nid)
                back = m.to_node(loc)
                self.assertEqual(back, nid,
                                 f"Mesh({size}): to_node(to_loc({nid})) = {back}")

    def test_known_mappings(self):
        m = Mesh(4)
        self.assertEqual(m.to_loc(0), [0, 0])
        self.assertEqual(m.to_loc(3), [3, 0])       # 第一行末尾
        self.assertEqual(m.to_loc(4), [0, 1])        # 第二行开头
        self.assertEqual(m.to_loc(15), [3, 3])       # 最后一个节点
        self.assertEqual(m.to_node([0, 0]), 0)
        self.assertEqual(m.to_node([3, 3]), 15)
        self.assertEqual(m.to_node([1, 2]), 9)       # 1 + 2*4 = 9

    def test_size3_all_mappings(self):
        m = Mesh(3)
        expected = {
            0: [0, 0], 1: [1, 0], 2: [2, 0],
            3: [0, 1], 4: [1, 1], 5: [2, 1],
            6: [0, 2], 7: [1, 2], 8: [2, 2],
        }
        for nid, expected_loc in expected.items():
            self.assertEqual(m.to_loc(nid), expected_loc)
            self.assertEqual(m.to_node(expected_loc), nid)


class TestMeshBasicProperties(unittest.TestCase):
    """基本属性。"""

    def test_node_counts(self):
        for size in [2, 3, 4, 5, 8]:
            m = Mesh(size)
            self.assertEqual(m.terminal_num(), size * size)
            self.assertEqual(m.node_num(), size * size)
            self.assertEqual(m.node_num(), m.terminal_num())

    def test_all_nodes_are_terminals(self):
        m = Mesh(4)
        for nid in range(16):
            self.assertTrue(m.is_terminal(nid))

    def test_terminals_list(self):
        m = Mesh(4)
        terms = m.terminals()
        self.assertEqual(len(terms), 16)
        self.assertEqual(terms, list(range(16)))


class TestMeshDetRouting(unittest.TestCase):
    """deterministic 路由正确性。"""

    def test_path_endpoints(self):
        """路径必须从 src 开始，到 dst 结束。"""
        m = Mesh(4)
        for src in range(16):
            for dst in range(16):
                if src == dst:
                    path = m.det(src, dst)[0]
                    self.assertEqual(path, [src])
                else:
                    path = m.det(src, dst)[0]
                    self.assertEqual(path[0], src)
                    self.assertEqual(path[-1], dst)

    def test_adjacency(self):
        """每步移动必须在恰好一维上变化 ±1（曼哈顿距离减 1）。"""
        m = Mesh(4)
        for src in range(16):
            for dst in range(16):
                if src == dst:
                    continue
                path = m.det(src, dst)[0]
                for k in range(len(path) - 1):
                    a = m.to_loc(path[k])
                    b = m.to_loc(path[k + 1])
                    manhattan = abs(a[0] - b[0]) + abs(a[1] - b[1])
                    self.assertEqual(manhattan, 1,
                                     f"Mesh(4) {src}→{dst}: step {k}: {a}→{b} not adjacent")

    def test_dimension_order_y_first(self):
        """维序路由：先走 y，再走 x。"""
        m = Mesh(4)
        path = m.det(0, 15)[0]  # [0,0] → [3,3]
        # 前几步应在 y 上移动
        locs = [m.to_loc(n) for n in path]
        # 找到从 y-only 切换到 x-only 的位置
        y_changes = sum(1 for i in range(len(locs) - 1) if locs[i][1] != locs[i + 1][1])
        x_changes = sum(1 for i in range(len(locs) - 1) if locs[i][0] != locs[i + 1][0])
        # 所有 y 变化应在所有 x 变化之前
        seen_x_change = False
        for i in range(len(locs) - 1):
            if locs[i][0] != locs[i + 1][0]:
                seen_x_change = True
            if seen_x_change:
                self.assertEqual(locs[i][1], locs[i + 1][1],
                                 f"y changed after x was already changing: {locs}")

    def test_no_cycles(self):
        """路径中无重复节点。"""
        m = Mesh(4)
        for src in range(16):
            for dst in range(16):
                path = m.det(src, dst)[0]
                self.assertEqual(len(path), len(set(path)),
                                 f"Mesh(4) {src}→{dst}: path has cycles: {path}")

    def test_convergence_guaranteed(self):
        """所有路由必须在合理步数内收敛。"""
        m = Mesh(4)
        for src in range(16):
            for dst in range(16):
                path = m.det(src, dst)[0]
                max_possible = abs(m.to_loc(src)[0] - m.to_loc(dst)[0]) + \
                               abs(m.to_loc(src)[1] - m.to_loc(dst)[1])
                self.assertLessEqual(len(path) - 1, max_possible)


class TestMeshValiantRouting(unittest.TestCase):
    """Valiant 路由正确性。"""

    def test_includes_det_path(self):
        """det 路径始终出现在 valiant 候选集中。"""
        m = Mesh(3)
        for src in range(9):
            for dst in range(9):
                if src == dst:
                    continue
                det_path = m.det(src, dst)[0]
                val_paths = m.valiant(src, dst)
                det_tuple = tuple(det_path)
                val_tuples = [tuple(p) for p in val_paths]
                self.assertIn(det_tuple, val_tuples,
                              f"det path not in valiant for {src}→{dst}")

    def test_all_paths_valid(self):
        """所有 valiant 路径起终点正确。"""
        m = Mesh(3)
        for src in range(9):
            for dst in range(9):
                if src == dst:
                    continue
                for path in m.valiant(src, dst):
                    self.assertEqual(path[0], src)
                    self.assertEqual(path[-1], dst)

    def test_no_duplicate_paths(self):
        """valiant 路径集合无重复。"""
        m = Mesh(3)
        for src in range(9):
            for dst in range(9):
                if src == dst:
                    continue
                paths = m.valiant(src, dst)
                tuples = [tuple(p) for p in paths]
                self.assertEqual(len(tuples), len(set(tuples)))

    def test_path_count(self):
        """valiant 路径数 ≤ 1 + (终端数 - 2)。

        上界 = det直连 + 中间terminal中转。当某些中转路径与 det 路径
        重复时会被 _unique_paths 去重，因此实际数量可能略少。
        """
        m = Mesh(3)
        for src in range(9):
            for dst in range(9):
                if src == dst:
                    continue
                paths = m.valiant(src, dst)
                max_expected = 1 + (9 - 2)  # det + 7 intermediate terminals
                self.assertLessEqual(len(paths), max_expected,
                    f"{src}→{dst}: expected ≤ {max_expected} paths, got {len(paths)}")
                self.assertGreaterEqual(len(paths), 1,
                    f"{src}→{dst}: expected ≥ 1 path, got {len(paths)}")


if __name__ == "__main__":
    unittest.main()
