"""面积约束族 —— die 面积上界（V5 §2 (2f)）。

DieAreaModel —— 常数约束 0 ≤ A_max − d(B)²，纯 B 门槛。
"""

from problem.models.phys.area._die_area import DieAreaModel

__all__ = ["DieAreaModel"]
