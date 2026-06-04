"""Dragonfly 拓扑严格单元测试。

测试策略：
    1. 坐标往返
    2. 结构属性：terminal/node 数量、is_terminal 判定
    3. det 路由：同组内、跨组、terminal→router 第一步
    4. Valiant 路由优化：路径数 << 终端数、路径有效性
    5. 最小化拓扑
"""

from __future__ import annotations

import unittest

from wafer_dse.architecture_model.topology.dragonfly import Dragonfly


class TestDragonflyStructure(unittest.TestCase):
    """结构与坐标。"""

    def test_roundtrip_all_nodes(self):
        """对所有节点验证 to_node(to_loc(id)) == id。"""
        for a, p, h in [(2, 2, 1), (1, 1, 1), (2, 3, 1), (3, 2, 2)]:
            df = Dragonfly(a=a, p=p, h=h)
            for nid in range(df.node_num()):
                loc = df.to_loc(nid)
                back = df.to_node(loc)
                self.assertEqual(back, nid,
                                 f"Dragonfly({a},{p},{h}): node {nid} -> loc {loc} -> back {back}")

    def test_terminal_count(self):
        """terminal_num() == g * a * p。"""
        df = Dragonfly(a=2, p=2, h=1)
        g = df.g  # a*h + 1 = 3
        self.assertEqual(g, 3)
        self.assertEqual(df.terminal_num(), g * 2 * 2)  # 12
        self.assertEqual(df.node_num(), g * 2 * (2 + 1))  # 18

    def test_is_terminal(self):
        """terminal 判定：loc[2] != 0。"""
        df = Dragonfly(a=2, p=2, h=1)
        for nid in range(df.node_num()):
            loc = df.to_loc(nid)
            is_term = df.is_terminal(nid)
            self.assertEqual(is_term, loc[2] != 0,
                             f"node {nid} loc={loc}: is_terminal={is_term}")

    def test_node_counts_multiple_configs(self):
        configs = [
            (2, 2, 1, 3, 12, 18),   # (a, p, h, g, terminals, nodes)
            (1, 1, 1, 2, 2, 4),
            (2, 1, 1, 3, 6, 12),
            (3, 2, 1, 4, 24, 36),
        ]
        for a, p, h, g, terms, nodes in configs:
            df = Dragonfly(a=a, p=p, h=h)
            self.assertEqual(df.g, g)
            self.assertEqual(df.terminal_num(), terms)
            self.assertEqual(df.node_num(), nodes)


class TestDragonflyDetRouting(unittest.TestCase):
    """deterministic 路由。"""

    def test_path_endpoints(self):
        df = Dragonfly(a=2, p=2, h=1)
        for src in range(df.node_num()):
            for dst in range(df.node_num()):
                if src == dst:
                    self.assertEqual(df.det(src, dst)[0], [src])
                else:
                    path = df.det(src, dst)[0]
                    self.assertEqual(path[0], src)
                    self.assertEqual(path[-1], dst)

    def test_terminal_first_step_to_router(self):
        """从 terminal 出发的第一步总是到本 router（loc[2]=0）。"""
        df = Dragonfly(a=2, p=2, h=1)
        for src in range(df.node_num()):
            if not df.is_terminal(src):
                continue
            for dst in range(df.node_num()):
                if src == dst or not df.is_terminal(dst):
                    continue
                path = df.det(src, dst)[0]
                if len(path) > 1:
                    first_hop = path[1]
                    first_loc = df.to_loc(first_hop)
                    self.assertEqual(first_loc[2], 0,
                                     f"src {src}→{dst}: first hop {first_hop} should be router")

    def test_intra_group_routing(self):
        """同 group 内的 src→dst：路径不离开该 group。"""
        df = Dragonfly(a=2, p=2, h=1)
        # 找同一 group 内的两个 terminal
        # group 0: routers 0,1 each with terminals 1,2
        # node numbering: terminal + router*(p+1) + group*(p+1)*a
        src_group0 = df.to_node([0, 0, 1])   # group 0, router 0, terminal 1
        dst_group0 = df.to_node([0, 1, 1])   # group 0, router 1, terminal 1
        path = df.det(src_group0, dst_group0)[0]
        for node in path:
            loc = df.to_loc(node)
            self.assertEqual(loc[0], 0, f"intra-group path left group 0 at node {node}")

    def test_inter_group_has_global_hop(self):
        """跨 group 路由必须有全局链路跳（group 变化）。"""
        df = Dragonfly(a=2, p=2, h=1)
        src = df.to_node([0, 0, 1])   # group 0
        dst = df.to_node([1, 0, 1])   # group 1
        path = df.det(src, dst)[0]
        groups = [df.to_loc(n)[0] for n in path]
        # 必须有 group 变化
        self.assertTrue(any(groups[i] != groups[i + 1] for i in range(len(groups) - 1)),
                        f"inter-group path has no global hop: {path}")

    def test_no_cycles(self):
        df = Dragonfly(a=2, p=2, h=1)
        for src in range(df.node_num()):
            for dst in range(df.node_num()):
                if not df.is_terminal(src) or not df.is_terminal(dst):
                    continue
                if src == dst:
                    continue
                path = df.det(src, dst)[0]
                self.assertEqual(len(path), len(set(path)))

    def test_convergence(self):
        """所有 terminal→terminal 路由收敛。"""
        df = Dragonfly(a=2, p=2, h=1)
        terms = df.terminals()
        for src in terms:
            for dst in terms:
                path = df.det(src, dst)[0]
                self.assertEqual(path[-1], dst)


class TestDragonflyValiantRouting(unittest.TestCase):
    """Valiant 路由 — Dragonfly 优化版。"""

    def test_valiant_paths_valid(self):
        df = Dragonfly(a=2, p=2, h=1)
        terms = df.terminals()
        for src in terms:
            for dst in terms:
                if src == dst:
                    continue
                paths = df.valiant(src, dst)
                for path in paths:
                    self.assertEqual(path[0], src)
                    self.assertEqual(path[-1], dst)

    def test_valiant_fewer_paths_than_base(self):
        """Dragonfly 优化的 valiant 路径数 << 终端数（基类枚举所有 terminal）。"""
        df = Dragonfly(a=2, p=2, h=1)
        terms = df.terminals()
        # 基类 valiant: 1 + (terminal_count - 2) = 1 + 10 = 11
        # Dragonfly valiant: 1 + (g - 2) = 1 + 1 = 2 (if inter-group)
        sg = df.to_loc(terms[0])[0]
        for dst in terms[1:]:
            dg = df.to_loc(dst)[0]
            paths = df.valiant(terms[0], dst)
            if sg != dg:
                # inter-group: 1 det + (g-2) global routers
                expected = 1 + max(0, df.g - 2)
                self.assertEqual(len(paths), expected,
                                 f"inter-group {terms[0]}→{dst}: expected {expected} paths")
            self.assertLess(len(paths), len(terms),
                            f"valiant paths ({len(paths)}) should be << terminals ({len(terms)})")

    def test_includes_det_path(self):
        df = Dragonfly(a=2, p=2, h=1)
        terms = df.terminals()
        for src in terms[:4]:  # sample
            for dst in terms[:4]:
                if src == dst:
                    continue
                det_tuple = tuple(df.det(src, dst)[0])
                val_tuples = [tuple(p) for p in df.valiant(src, dst)]
                self.assertIn(det_tuple, val_tuples)

    def test_no_duplicate_paths(self):
        df = Dragonfly(a=2, p=2, h=1)
        terms = df.terminals()
        for src in terms[:4]:
            for dst in terms[:4]:
                if src == dst:
                    continue
                paths = df.valiant(src, dst)
                tuples = [tuple(p) for p in paths]
                self.assertEqual(len(tuples), len(set(tuples)))


class TestDragonflyMinimal(unittest.TestCase):
    """最小化拓扑：a=1, p=1, h=1。"""

    def test_minimal_structure(self):
        df = Dragonfly(a=1, p=1, h=1)
        self.assertEqual(df.g, 2)          # a*h + 1 = 2
        self.assertEqual(df.terminal_num(), 2)
        self.assertEqual(df.node_num(), 4)

    def test_minimal_routing(self):
        df = Dragonfly(a=1, p=1, h=1)
        terms = df.terminals()
        src, dst = terms[0], terms[1]
        path = df.det(src, dst)[0]
        self.assertEqual(path[0], src)
        self.assertEqual(path[-1], dst)


if __name__ == "__main__":
    unittest.main()
