"""路径枚举——Valiant 候选路径 → 链路 incidence 数据结构。

读者：这里不需要读——知道 _build_path_incidence 和 _enumerate_links
返回什么即可。具体实现是标准图遍历。
"""

import itertools

from topology.base import Topology


def build_path_incidence(topo: Topology, terminals: list[int]) -> dict:
    """Valiant 路径 → 链路 incidence。遍历所有 terminal 对的候选路径。"""
    link_set: dict[tuple[int, int], int] = {}
    pairs: list[tuple[int, int]] = []
    paths_for_pair: list[list[list[int]]] = []

    for src, dst in itertools.permutations(terminals, 2):
        paths = topo.valiant(src, dst)
        if not paths:
            continue
        pi = len(pairs)
        pairs.append((src, dst))
        paths_for_pair.append([])
        for path in paths:
            link_idxs = []
            for k in range(len(path) - 1):
                link = (path[k], path[k + 1])
                if link not in link_set:
                    link_set[link] = len(link_set)
                link_idxs.append(link_set[link])
            paths_for_pair[pi].append(link_idxs)

    links = [None] * len(link_set)
    for link, idx in link_set.items():
        links[idx] = link

    link_incidence: list[list[tuple[int, int]]] = [[] for _ in range(len(links))]
    for pi, path_list in enumerate(paths_for_pair):
        for pj, link_idxs in enumerate(path_list):
            for li in link_idxs:
                link_incidence[li].append((pi, pj))

    return {
        "terminals": terminals, "n_terminals": len(terminals),
        "links": links, "n_links": len(links),
        "pairs": pairs, "n_pairs": len(pairs),
        "paths_for_pair": paths_for_pair,
        "link_incidence": link_incidence,
    }


def enumerate_links(topo: Topology) -> list[tuple[int, int]]:
    """枚举所有有向链路——遍历 det 路径收集 + 去重排序。"""
    links: set[tuple[int, int]] = set()
    for src, dst in itertools.permutations(topo.terminals(), 2):
        paths = topo.det(src, dst)
        if paths:
            path = paths[0]
            for k in range(len(path) - 1):
                links.add((path[k], path[k + 1]))
    return sorted(links)
