"""Max-weight derangement 求解器。

将 max-weight derangement 问题归约为 Hungarian min-cost assignment：
    1. 把 max-weight 转换为 min-cost（取反 + 归一化偏移）
    2. 把禁止的自环（i → i）设置为极大成本
    3. 调用 Hungarian 算法得到最优 derangement

纯数学工具 —— 不感知拓扑/网络概念。
"""

from __future__ import annotations

from wafer_dse.architecture_model.solver.algorithm.hungarian import (
    hungarian_min_cost,
)


def max_weight_derangement(weight: list[list[float]]) -> tuple[float, list[int]]:
    """求解 max-weight derangement（无自环排列的最大权重匹配）。

    约束：assignment[i] ≠ i —— 每个元素不能匹配到自己。

    算法：
        1. 将 weight[i][i]（自环）替换为极大成本 M，在 Hungarian 中不可选。
        2. 将 max-weight 问题转为 min-cost：
           cost[i][j] = max_w - weight[i][j]  (j ≠ i)
           cost[i][i] = M  (禁止自环)
        3. 用 Hungarian 求 min-cost perfect matching。
        4. 总权重 = sum(weight[i][assignment[i]])。

    Args:
        weight: N×N 矩阵，weight[i][j] 为 row i → col j 的权重。
                可以是任意非负浮点数。

    Returns:
        (max_total_weight, assignment):
            max_total_weight — 最大总权重
            assignment       — assignment[i] = j 且 j ≠ i

    Raises:
        RuntimeError: 不存在有效 derangement（例如 N=1 时唯一选择是自环）。
        ValueError: weight 不是方阵或为空。

    Example:
        >>> w = [[0, 5, 3], [4, 0, 2], [3, 1, 0]]
        >>> total, assign = max_weight_derangement(w)
        >>> total  # 5 + 4 + 1 = 10 或 3 + 4 + 1 = 8
        10.0
        >>> all(assign[i] != i for i in range(3))
        True
    """
    n = len(weight)
    if n <= 1:
        return 0.0, []

    if any(len(row) != n for row in weight):
        raise ValueError("weight 必须为方阵")

    max_w = max(max(row) for row in weight)

    # 自环成本设为极大值，使 Hungarian 不会选中自环
    big = max(1.0, max_w) * (n + 1) * 1e9

    # max-weight → min-cost 转换
    cost = [
        [
            big if i == j else max_w - weight[i][j]
            for j in range(n)
        ]
        for i in range(n)
    ]

    _, assignment = hungarian_min_cost(cost)

    # 防御性检查
    if any(assignment[i] == i for i in range(n)):
        raise RuntimeError(
            "不存在有效 derangement；请检查 terminal 数是否 ≥ 2。"
        )

    total = sum(weight[i][assignment[i]] for i in range(n))
    return total, assignment
