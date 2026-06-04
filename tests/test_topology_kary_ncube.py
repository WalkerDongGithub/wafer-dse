"""KaryNCube 拓扑严格单元测试 ⭐

这是新增模块的核心测试。KaryNCube 是 Mesh/Torus 的 n 维泛化。

测试策略：
    1. 参数验证
    2. 坐标往返（多配置，全部节点）
    3. 规模正确性
    4. 路由正确性：维序(dim n-1→0)、邻接、最短方向、边界
    5. n=1 特例
    6. 2D 与 Mesh/Torus 的一致性
"""

from __future__ import annotations

import unittest

from wafer_dse.architecture_model.topology.kary_ncube import KaryNCube
from wafer_dse.architecture_model.topology.mesh import Mesh


class TestKaryNCubeValidation(unittest.TestCase):
    """参数验证。"""

    def test_k_too_small(self):
        with self.assertRaises(ValueError):
            KaryNCube(k=1, n=2)

    def test_n_too_small(self):
        with self.assertRaises(ValueError):
            KaryNCube(k=4, n=0)

    def test_minimal_valid(self):
        """k=2, n=1: 最小有效配置。"""
        kc = KaryNCube(k=2, n=1)
        self.assertEqual(kc.terminal_num(), 2)
        self.assertEqual(kc.node_num(), 2)


class TestKaryNCubeCoordinates(unittest.TestCase):
    """坐标系统 — 多配置全面验证。"""

    CONFIGS = [
        (2, 1), (2, 2), (3, 2), (4, 2),
        (2, 3), (3, 3), (4, 3),
        (2, 4),
    ]

    def test_roundtrip_all_configs(self):
        """对所有 (k,n) 配置，验证全部 k^n 个节点的往返一致性。"""
        for k, n in self.CONFIGS:
            kc = KaryNCube(k=k, n=n)
            for node in range(k ** n):
                loc = kc.to_loc(node)
                back = kc.to_node(loc)
                self.assertEqual(back, node,
                                 f"KaryNCube({k},{n}): node {node} -> loc {loc} -> back {back}")

    def test_coordinate_dimension_count(self):
        """坐标维度必须等于 n。"""
        for k, n in self.CONFIGS:
            kc = KaryNCube(k=k, n=n)
            for node in range(k ** n):
                loc = kc.to_loc(node)
                self.assertEqual(len(loc), n,
                                 f"KaryNCube({k},{n}): node {node} loc dims={len(loc)}, expected {n}")

    def test_coordinate_range(self):
        """所有坐标值在 [0, k-1] 范围内。"""
        for k, n in self.CONFIGS:
            kc = KaryNCube(k=k, n=n)
            for node in range(k ** n):
                loc = kc.to_loc(node)
                for dim_idx, val in enumerate(loc):
                    self.assertTrue(0 <= val < k,
                                    f"KaryNCube({k},{n}): node {node} dim {dim_idx} = {val} ∉ [0,{k-1}]")


class TestKaryNCubeSizes(unittest.TestCase):
    """规模正确性。"""

    def test_terminal_counts(self):
        cases = [
            ((4, 2), 16),
            ((4, 3), 64),
            ((3, 4), 81),
            ((2, 3), 8),
            ((5, 1), 5),
            ((3, 2), 9),
            ((2, 2), 4),
            ((6, 2), 36),
        ]
        for (k, n), expected in cases:
            kc = KaryNCube(k=k, n=n)
            self.assertEqual(kc.terminal_num(), expected,
                             f"KaryNCube({k},{n}): expected {expected}")
            self.assertEqual(kc.node_num(), expected)

    def test_all_nodes_are_terminals(self):
        for k, n in [(2, 2), (3, 3), (4, 2)]:
            kc = KaryNCube(k=k, n=n)
            for node in range(k ** n):
                self.assertTrue(kc.is_terminal(node))


class TestKaryNCubeDetRouting(unittest.TestCase):
    """deterministic 路由 — 最全面的测试集。"""

    # 测试的 (k, n, wrap) 配置
    ROUTING_CONFIGS = [
        (2, 1, True),   # 1D ring
        (2, 1, False),  # 1D line
        (4, 2, True),   # 2D torus
        (4, 2, False),  # 2D mesh
        (3, 2, True),   # small 2D torus
        (3, 3, True),   # 3D torus
        (3, 3, False),  # 3D mesh
        (2, 3, True),   # 3D hypercube
    ]

    def test_path_endpoints(self):
        """所有路由起点=src，终点=dst。"""
        for k, n, wrap in self.ROUTING_CONFIGS:
            kc = KaryNCube(k=k, n=n, wrap=wrap)
            N = k ** n
            for src in range(N):
                for dst in range(N):
                    if src == dst:
                        path = kc.det(src, dst)[0]
                        self.assertEqual(path, [src])
                    else:
                        path = kc.det(src, dst)[0]
                        self.assertEqual(path[0], src,
                                         f"({k},{n},wrap={wrap}) {src}→{dst}: path[0]={path[0]}")
                        self.assertEqual(path[-1], dst,
                                         f"({k},{n},wrap={wrap}) {src}→{dst}: path[-1]={path[-1]}")

    def test_dimension_order(self):
        """维序路由：高维(dim n-1)先对齐，低维(dim 0)最后。

        验证方法：检查路径中每次变动的维度，应是从高到低单调不增的序列。
        """
        for k, n, wrap in self.ROUTING_CONFIGS:
            kc = KaryNCube(k=k, n=n, wrap=wrap)
            N = k ** n
            for src in range(N):
                for dst in range(N):
                    if src == dst:
                        continue
                    path = kc.det(src, dst)[0]
                    changed_dims = []
                    prev_loc = kc.to_loc(path[0])
                    for node in path[1:]:
                        cur_loc = kc.to_loc(node)
                        # 找到变化的维度
                        for dim in range(n):
                            if cur_loc[dim] != prev_loc[dim]:
                                changed_dims.append(dim)
                                break
                        prev_loc = cur_loc

                    # 变化的维度应单调不增（从高维到低维）
                    for i in range(len(changed_dims) - 1):
                        self.assertGreaterEqual(changed_dims[i], changed_dims[i + 1],
                            f"({k},{n},wrap={wrap}) {src}→{dst}: "
                            f"dim order {changed_dims} not non-increasing")

    def test_single_dimension_change_per_step(self):
        """每步只在恰好一个维度上变化。"""
        for k, n, wrap in self.ROUTING_CONFIGS:
            kc = KaryNCube(k=k, n=n, wrap=wrap)
            N = k ** n
            for src in range(N):
                for dst in range(N):
                    if src == dst:
                        continue
                    path = kc.det(src, dst)[0]
                    for i in range(len(path) - 1):
                        a = kc.to_loc(path[i])
                        b = kc.to_loc(path[i + 1])
                        diffs = sum(1 for dim in range(n) if a[dim] != b[dim])
                        self.assertEqual(diffs, 1,
                            f"({k},{n},wrap={wrap}) {src}→{dst}: "
                            f"step {i}: {a}→{b} changes {diffs} dims")

    def test_adjacency_no_wrap(self):
        """wrap=False: 每步坐标变化恰好 ±1（不穿越边界）。"""
        for k, n in [(4, 2), (3, 3), (2, 2)]:
            kc = KaryNCube(k=k, n=n, wrap=False)
            N = k ** n
            for src in range(N):
                for dst in range(N):
                    if src == dst:
                        continue
                    path = kc.det(src, dst)[0]
                    for i in range(len(path) - 1):
                        a = kc.to_loc(path[i])
                        b = kc.to_loc(path[i + 1])
                        for dim in range(n):
                            diff = b[dim] - a[dim]
                            self.assertIn(diff, {-1, 0, 1},
                                f"no-wrap ({k},{n}) {src}→{dst} step {i}: diff={diff}")
                            if diff != 0:
                                self.assertNotEqual(diff, 0)

    def test_shortest_wrap_direction(self):
        """wrap=True: 每步选择最短环绕方向。

        验证：diff = (dst - src) % k; step = 1 if diff ≤ k//2 else -1。
        """
        kc = KaryNCube(k=4, n=2, wrap=True)
        # 0→3: src[0]=0, dst[0]=3, diff=(3-0)%4=3 > 2, step=-1 → 走环绕 0→3
        path = kc.det(0, 3)[0]
        self.assertEqual(path, [0, 3], f"0→3 should be 1 step via wrap, got {path}")

        # 0→1: src[0]=0, dst[0]=1, diff=1 ≤ 2, step=+1 → 0→1
        path = kc.det(0, 1)[0]
        self.assertEqual(path, [0, 1])

    def test_no_boundary_crossing_no_wrap(self):
        """wrap=False: 所有坐标始终在 [0, k-1] 内。"""
        for k, n in [(4, 2), (3, 3)]:
            kc = KaryNCube(k=k, n=n, wrap=False)
            N = k ** n
            for src in range(N):
                for dst in range(N):
                    path = kc.det(src, dst)[0]
                    for node in path:
                        loc = kc.to_loc(node)
                        for dim in range(n):
                            self.assertTrue(0 <= loc[dim] < k,
                                f"no-wrap ({k},{n}) {src}→{dst}: "
                                f"coordinate {loc[dim]} out of [0,{k-1}]")

    def test_no_cycles(self):
        """路径无重复节点。"""
        for k, n, wrap in [(4, 2, True), (4, 2, False), (3, 3, True)]:
            kc = KaryNCube(k=k, n=n, wrap=wrap)
            N = k ** n
            for src in range(N):
                for dst in range(N):
                    path = kc.det(src, dst)[0]
                    self.assertEqual(len(path), len(set(path)),
                        f"({k},{n},wrap={wrap}) {src}→{dst}: has cycles")

    def test_convergence_guaranteed(self):
        """路由在所有配置下收敛。"""
        for k, n, wrap in self.ROUTING_CONFIGS:
            kc = KaryNCube(k=k, n=n, wrap=wrap)
            N = k ** n
            for src in range(N):
                for dst in range(N):
                    path = kc.det(src, dst)[0]
                    self.assertEqual(path[-1], dst,
                        f"({k},{n},wrap={wrap}) {src}→{dst}: did not converge, "
                        f"path ends at {path[-1]}")


class TestKaryNCubeN1(unittest.TestCase):
    """n=1 特殊情况。"""

    def test_1d_line_routing(self):
        """1D mesh (wrap=False): 只能单向移动。"""
        kc = KaryNCube(k=5, n=1, wrap=False)
        # 0→4: 必须走 0→1→2→3→4
        path = kc.det(0, 4)[0]
        self.assertEqual(path, [0, 1, 2, 3, 4])

    def test_1d_ring_shortest(self):
        """1D torus (wrap=True): 选最短环绕。"""
        kc = KaryNCube(k=5, n=1, wrap=True)
        # 0→4: diff=(4-0)%5=4 > 2, step=-1 → 0→4 一步
        path = kc.det(0, 4)[0]
        self.assertEqual(path, [0, 4])

        # 0→2: diff=2 ≤ 2, step=+1 → 0→1→2
        path = kc.det(0, 2)[0]
        self.assertEqual(path, [0, 1, 2])


class TestKaryNCubeConsistencyWithMesh(unittest.TestCase):
    """与 Mesh 的结构一致性（不是路由一致性，因为路由维序可能不同）。"""

    def test_same_node_count_as_mesh(self):
        """KaryNCube(k, 2, False) 与 Mesh(k) 节点数相同。"""
        for k in [3, 4, 5]:
            kc = KaryNCube(k=k, n=2, wrap=False)
            m = Mesh(k)
            self.assertEqual(kc.terminal_num(), m.terminal_num())
            self.assertEqual(kc.node_num(), m.node_num())

    def test_coordinate_system_compatible(self):
        """坐标表示兼容：[x, y] 格式。"""
        kc = KaryNCube(k=4, n=2, wrap=False)
        m = Mesh(4)
        # 前几个节点的坐标应一致
        for node in range(16):
            kc_loc = kc.to_loc(node)
            m_loc = m.to_loc(node)
            self.assertEqual(kc_loc, m_loc,
                             f"node {node}: KaryNCube={kc_loc}, Mesh={m_loc}")


if __name__ == "__main__":
    unittest.main()
