"""Hungarian 算法（Kuhn-Munkres）：O(N³) 最小成本完美匹配。

纯数学工具 —— 不感知拓扑、网络、流量等任何上层概念。
输入方阵 cost，输出 (min_total_cost, row→col assignment)。

实现参考：
    https://e-maxx.ru/algo/assignment_hungary
    使用 potentials (u, v) 和交替路增广的标准 O(N³) 版本。
"""

from __future__ import annotations


def hungarian_min_cost(cost: list[list[float]]) -> tuple[float, list[int]]:
    """求 N×N 方阵的最小成本完美匹配。

    Args:
        cost: N×N 矩阵，cost[i][j] 表示 row i 匹配 col j 的成本。
              矩阵必须是方阵；cost[i][j] 可以是任意浮点数（负值也可）。

    Returns:
        (min_total_cost, assignment):
            min_total_cost  — 最小总成本
            assignment      — assignment[i] = j 表示 row i 匹配 col j

    Raises:
        ValueError: cost 不是方阵。

    复杂度：
        O(N³) 时间，O(N) 额外空间。
        对 N ≤ 256 的输入通常在毫秒级完成。

    Example:
        >>> cost = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
        >>> total, assign = hungarian_min_cost(cost)
        >>> total
        10.0
        >>> assign
        [2, 1, 0]
    """
    n = len(cost)
    if n == 0:
        return 0.0, []

    # 防御：确保每行长度一致
    if any(len(row) != n for row in cost):
        raise ValueError("cost 必须为方阵")

    # 势函数和匹配状态
    u = [0.0] * (n + 1)  # row potentials
    v = [0.0] * (n + 1)  # col potentials
    p = [0] * (n + 1)    # p[j] = 匹配到 col j 的 row 编号
    way = [0] * (n + 1)  # 回溯指针：way[j] = 到达 col j 的前一个 col

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (n + 1)
        used = [False] * (n + 1)

        # 在等价图中找增广路
        while True:
            used[j0] = True
            i0 = p[j0]
            delta, j1 = float("inf"), 0

            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j

            # 更新势函数
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        # 沿 way 指针回溯，更新匹配
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    # 构建 assignment 数组
    assignment = [-1] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            assignment[p[j] - 1] = j - 1

    total = sum(cost[i][assignment[i]] for i in range(n))
    return total, assignment
