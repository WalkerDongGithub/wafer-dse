"""内部策略 — ABC + 算法实现。

策略接收一组 (src, dst, demand) 三元组，计算相对负载。
demand 由 pattern 决定，策略不关心 demand 从哪来。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from wafer_dse.architecture_model.topology import Topology
from ._config import PotentialConfig

# (src, dst, demand) 三元组
Demands = list[tuple[int, int, float]]


class _LoadStrategy(ABC):
    """计算相对负载的内部策略。

    枚举类策略使用 demands (预先计算好的流量需求)，
    搜索类策略使用 terminals (内部搜索最坏排列)，忽略 demands。
    """

    @abstractmethod
    def compute(self, topo: Topology, route_fn,
                demands: Demands, terminals: list[int],
                cfg: PotentialConfig) -> float:
        ...


# ============================================================================
# 枚举 — 给定 demand，叠加所有路径的链路负载
# ============================================================================


class _Enumeration(_LoadStrategy):
    """枚举所有 (src,dst,demand) → 分摊到各路径 → 叠加链路负载 → 取范数。"""

    def compute(self, topo, route_fn,
                demands: Demands, terminals: list[int],
                cfg: PotentialConfig) -> float:
        link_load: dict[tuple[int, int], float] = {}

        for src, dst, demand in demands:
            paths = route_fn(src, dst)
            if not paths:
                continue
            per = demand / len(paths)
            for path in paths:
                for i in range(len(path) - 1):
                    link = (path[i], path[i + 1])
                    link_load[link] = link_load.get(link, 0.0) + per

        return _norm(link_load, cfg)


# ============================================================================
# 范数
# ============================================================================


def _norm(link_load: dict, cfg: PotentialConfig) -> float:
    if not link_load:
        return 0.0
    if cfg.target == "relative_load":
        return max(link_load.values())
    if cfg.target == "power":
        return sum(link_load.values())
    raise ValueError(f"unsupported target: {cfg.target!r}")


# ============================================================================
# Demand 生成 — pattern → [(src, dst, demand)]
# ============================================================================


def _generate_demands(
    pattern: str, terminals: list[int], cfg: PotentialConfig,
) -> Demands:
    """根据 pattern 生成 (src, dst, demand) 列表。"""
    n = len(terminals)

    if pattern == "uniform":
        val = cfg.lambda_scale / (n * (n - 1)) if n > 1 else 0
        return [(s, t, val) for s in terminals for t in terminals if s != t]

    if pattern == "worst_case":
        # worst_case 不由这里生成——搜索策略内部自己找最坏排列
        return []

    raise ValueError(f"unsupported pattern: {pattern!r}")
