"""拓扑领域类型别名。

不引入运行时开销——纯文档意图。
读到 NodeId 就知道这是节点标识符，不是计数或带宽。
"""

from typing import NewType

# 节点标识符（区别于普通 int）
NodeId: type[int] = int  # NewType('NodeId', int) 会产生运行时开销，用 plain alias

# OD 对 / 链路 — 两个节点的有序对
Pair = tuple[NodeId, NodeId]
