"""DSE 数据契约。

输入：用户需求 (Requirement)、拓扑预案 (TopologySpec)。
输出：统一 LP 求解结果 (LpResult → lp/report.py)。

目的：用少量 dataclass 固定输入侧数据边界。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Strictness:
    """严格程度：full 表示全工况严格；percent 表示 x% 工况用全工况保守替代。"""

    mode: str = "full"
    percent: float | None = None
    benchmark: str | None = None


@dataclass(frozen=True)
class Requirement:
    """用户指令输入：目标带宽、功耗上限、严格程度和封装配置路径。"""

    target_nonblocking_gbps_per_port: float
    max_power_w: float
    strictness: Strictness
    packaging_config: str = ""
    port_count: int | None = None
    max_die_area_mm2: float | None = None


@dataclass(frozen=True)
class TopologySpec:
    """待考查拓扑：只描述结构本身和 route，不带封装假设。"""

    kind: str
    size: int | None = None          # mesh/torus/kary_ncube: k (radix)
    route: str = "det"
    a: int | None = None             # dragonfly: routers per group
    p: int | None = None             # dragonfly: terminals per router
    h: int | None = None             # dragonfly: global ports per router
    n: int | None = None             # kary_ncube: dimensions (default 2)
    wrap: bool | None = None         # kary_ncube: torus (True) or mesh (False)
