"""
TopoStructure —— 从拓扑一次性提取所有模型需要的连接数据。

存在意义：
  perf/phys/therm 三个模型都需要路径信息、链路列表、die 分组。
  analyze() 算一次，frozen dataclass 分发——避免重复计算。

用法：
    cs = analyze(topo, node_to_die={...})
    perf = EnvelopeModel(cs, reps)
    bump = BumpModel(cs, budgets)

读者指南：
  - TopoStructure 字段 → 看这里
  - 路径枚举实现 → 看 _walk.py（一般不需要）
"""

from __future__ import annotations

from dataclasses import dataclass

from topology.base import Topology
from lp.models.topo._walk import build_path_incidence, enumerate_links


@dataclass(frozen=True)
class TopoStructure:
    """从拓扑一次性提取的全部结构数据——frozen，构造后只读。"""

    n_terminals: int
    n_links: int
    n_pairs: int
    terminals: list[int]
    ordered_links: list[tuple[int, int]]
    """有序链路 [(src, dst), ...]——与链路索引一一对应。"""
    paths_for_pair: list[list[list[int]]]
    """paths_for_pair[pi] = 第 pi 个 pair 的候选路径，每条路径 = 链路索引列表。"""
    link_incidence: list[list[tuple[int, int]]]
    """link_incidence[li] = 经过链路 li 的 (pair_idx, path_idx) 列表。"""
    pairs: list[tuple[int, int]]
    """pairs[pi] = (src_node, dst_node)。"""
    die_to_links: dict[int, list[int]]
    """die 索引 → 该 die 的 incident 链路索引列表。"""


def analyze(topo: Topology,
            node_to_die: dict[int, int] | None = None,
            ) -> TopoStructure:
    """从拓扑一次性提取全部结构数据。

    node_to_die: 节点 → die 映射。默认每节点一个 die。
    """
    terminals = list(topo.terminals())
    incid = build_path_incidence(topo, terminals)
    ordered = enumerate_links(topo)

    if node_to_die is None:
        node_to_die = {n: n for n in range(topo.node_num())}

    d2l: dict[int, set[int]] = {}
    for li, (u, v) in enumerate(ordered[:incid["n_links"]]):
        du, dv = node_to_die.get(u, 0), node_to_die.get(v, 0)
        d2l.setdefault(du, set()).add(li)
        if dv != du:
            d2l.setdefault(dv, set()).add(li)

    return TopoStructure(
        n_terminals=incid["n_terminals"],
        n_links=incid["n_links"],
        n_pairs=incid["n_pairs"],
        terminals=terminals,
        ordered_links=ordered[:incid["n_links"]],
        paths_for_pair=incid["paths_for_pair"],
        link_incidence=incid["link_incidence"],
        pairs=incid["pairs"],
        die_to_links={k: sorted(v) for k, v in d2l.items()},
    )
