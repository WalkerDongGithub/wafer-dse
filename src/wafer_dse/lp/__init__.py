"""统一 LP 引擎。

变量:
    L[e]  —— 每条链路的归一化负载 (e ∈ E, 有向链路)
    D[i,j] —— 双随机流量矩阵 (i,j ∈ terminals, i≠j)
    f[i,j,k] —— 路径分流变量 (valiant 路由)

约束:
    (P) 性能: L ∈ L_perf (双随机 + 路径分流)
    (G) 几何: M·L ≤ b (bump 预算 per die)
    (T) 热:   C·L ≤ d (功率密度)
    (R) 布线:  A·L ≤ c (grid 容量, v2)

使用方式:
    from wafer_dse.lp import UnifiedLp

    lp = UnifiedLp(topo, route="det", link_capacity_gbps=800)
    lp.add_geometry(die_cfg, bump_spec)
    lp.add_thermal(thermal_cfg, cooling)
    result = lp.solve()
    print(result.report())
"""

from wafer_dse.lp.engine import UnifiedLp
from wafer_dse.lp.report import LpResult, LpConstraintStatus

__all__ = [
    "LpConstraintStatus",
    "LpResult",
    "UnifiedLp",
]
