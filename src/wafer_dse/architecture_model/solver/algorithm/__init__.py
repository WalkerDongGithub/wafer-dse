"""求解器算法的公开入口。

提供纯数学工具，供具体 Solver 实现组合使用。
"""

from wafer_dse.architecture_model.solver.algorithm.derangement import (
    max_weight_derangement,
)
from wafer_dse.architecture_model.solver.algorithm.hungarian import (
    hungarian_min_cost,
)

__all__ = [
    "hungarian_min_cost",
    "max_weight_derangement",
]
