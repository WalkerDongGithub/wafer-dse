"""性能约束构建 — 链路负载与最坏情况流量。

为统一 LP 提供两种性能约束构建路径:
    1. det 路由: Hungarian 精确最坏情况 → 每链路 L_min[e] 下界
    2. valiant 路由: 构建 D + f + L 的联合 LP 约束矩阵

复用 FixedRouteSolver 的链路权重计算逻辑。
"""

from __future__ import annotations

import itertools

from wafer_dse.architecture_model.topology import Topology
from wafer_dse.architecture_model.solver.rust_backend import batch_derangement


# ============================================================================
# 链路权重计算 — 从 FixedRouteSolver 提取的公共逻辑
# ============================================================================


def build_link_weights(
    topo: Topology,
    route: str = "det",
) -> dict[tuple[int, int], list[list[float]]]:
    """遍历所有 src→dst terminal 对，计算每条链路的负载系数矩阵。

    对每个 (src, dst) demand:
        - 获取候选路径 (det=1条, valiant=多条)
        - 将 demand 均分到每条候选路径
        - 沿路径累加分摊系数到对应链路的 weight[src_idx][dst_idx] 上

    Args:
        topo: 拓扑实例
        route: "det" | "val"

    Returns:
        {link: N×N matrix} — link_weight[(u,v)][i][j] =
            terminal_i → terminal_j 的流量经过链路 (u,v) 的比例 (0~1)
    """
    terminals = topo.terminals()
    n = len(terminals)
    index: dict[int, int] = {node: i for i, node in enumerate(terminals)}
    link_weights: dict[tuple[int, int], list[list[float]]] = {}

    for src, dst in itertools.permutations(terminals, 2):
        paths = (
            topo.det(src, dst) if route == "det"
            else topo.valiant(src, dst)
        )
        share = 1.0 / len(paths)
        si, di = index[src], index[dst]

        for path in paths:
            for k in range(len(path) - 1):
                link = (path[k], path[k + 1])
                if link not in link_weights:
                    link_weights[link] = [
                        [0.0 for _ in range(n)] for _ in range(n)
                    ]
                link_weights[link][si][di] += share

    return link_weights


# ============================================================================
# Step 1: Hungarian 精确最坏情况 (det 路由)
# ============================================================================


def compute_worst_case_loads(
    link_weights: dict[tuple[int, int], list[list[float]]],
) -> dict[tuple[int, int], float]:
    """对每条链路求解 max-weight derangement，返回 per-link 最坏负载。

    每链路的最坏负载 = max_{排列 π, π(i)≠i} Σ_i weight_e[i][π(i)]
    通过 Hungarian (max-weight derangement) 精确求解。

    Args:
        link_weights: build_link_weights() 的输出

    Returns:
        {link: L_min} — 每条链路在最坏排列下的归一化负载
    """
    if not link_weights:
        return {}

    links = list(link_weights.keys())
    matrices = [link_weights[link] for link in links]

    # 优先使用 Rust 批量求解
    results = batch_derangement(matrices)

    return {
        links[i]: load
        for i, (load, _assignment) in enumerate(results)
    }


def compute_global_worst(
    link_weights: dict[tuple[int, int], list[list[float]]],
) -> tuple[float, tuple[int, int] | None]:
    """计算全网最坏链路负载。

    Returns:
        (worst_load, worst_link)
    """
    loads = compute_worst_case_loads(link_weights)
    if not loads:
        return 0.0, None
    worst_link = max(loads, key=loads.get)
    return loads[worst_link], worst_link


# ============================================================================
# Path incidence — 用于 Valiant LP 构建
# ============================================================================


def build_path_incidence(
    topo: Topology,
    terminals: list[int],
) -> dict:
    """构建 Valiant 路由的路径-链路 incidence 数据结构。

    对每个 (src,dst) 对，枚举所有 Valiant 候选路径。
    返回的数据结构可用作 cvxpy LP 的约束构建。

    Returns:
        {
            "terminals": list[int],           # N 个 terminal
            "n_terminals": int,
            "links": list[tuple[int,int]],    # 所有有向链路列表
            "pairs": list[tuple[int,int]],    # (src,dst) 对列表
            "paths_for_pair": [               # 每个 pair 的候选路径列表
                [[link_idx, ...], ...],        # 每条路径是链路索引列表
            ],
            "link_incidence": [               # 每条链路经过哪些 (pair_idx, path_idx)
                [(pair_idx, path_idx), ...],
            ],
        }
    """
    n = len(terminals)
    idx_map = {t: i for i, t in enumerate(terminals)}

    # 收集所有链路和路径
    link_set: dict[tuple[int, int], int] = {}  # link → index
    pairs: list[tuple[int, int]] = []
    paths_for_pair: list[list[list[int]]] = []  # [pair_idx][path_idx] = [link_idx, ...]

    for src, dst in itertools.permutations(terminals, 2):
        paths = topo.valiant(src, dst)
        if not paths:
            continue

        pi = len(pairs)
        pairs.append((src, dst))
        paths_for_pair.append([])

        for path in paths:
            link_indices = []
            for k in range(len(path) - 1):
                link = (path[k], path[k + 1])
                if link not in link_set:
                    link_set[link] = len(link_set)
                link_indices.append(link_set[link])
            paths_for_pair[pi].append(link_indices)

    # 构建反向索引: link → [(pair_idx, path_idx), ...]
    links = [None] * len(link_set)
    for link, idx in link_set.items():
        links[idx] = link

    link_incidence: list[list[tuple[int, int]]] = [
        [] for _ in range(len(links))
    ]
    for pi, path_list in enumerate(paths_for_pair):
        for pj, link_idxs in enumerate(path_list):
            for li in link_idxs:
                link_incidence[li].append((pi, pj))

    return {
        "terminals": terminals,
        "n_terminals": n,
        "links": links,
        "n_links": len(links),
        "pairs": pairs,
        "n_pairs": len(pairs),
        "paths_for_pair": paths_for_pair,
        "link_incidence": link_incidence,
    }


# ============================================================================
# 链路枚举 — 直接遍历拓扑结构 (不经过路径遍历)
# ============================================================================


def enumerate_links(topo: Topology) -> list[tuple[int, int]]:
    """枚举拓扑中所有有向链路。

    通过遍历所有 terminal 对的 det 路径收集链路。
    返回去重后的有向链路列表。

    Args:
        topo: 拓扑实例

    Returns:
        有向链路列表 [(u, v), ...]
    """
    links: set[tuple[int, int]] = set()
    for src, dst in itertools.permutations(topo.terminals(), 2):
        paths = topo.det(src, dst)
        if paths:
            path = paths[0]
            for k in range(len(path) - 1):
                links.add((path[k], path[k + 1]))
    return sorted(links)
