"""DSE 数据结构。

输入：用户需求、拓扑预案和封装工艺配置。
输出：网络潜能、封装估计和耦合可行性报告。
目的：用少量 dataclass 固定三个模块之间的数据边界，避免模块互相读内部细节。
"""

from __future__ import annotations

from dataclasses import dataclass, field


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
    packaging_config: str
    port_count: int | None = None
    max_die_area_mm2: float | None = None


@dataclass(frozen=True)
class TopologySpec:
    """待考查拓扑：只描述结构本身和 route，不带封装假设。"""

    kind: str
    size: int | None = None      # mesh/torus/kary_ncube: k (radix)
    route: str = "det"
    a: int | None = None          # dragonfly: routers per group
    p: int | None = None          # dragonfly: terminals per router
    h: int | None = None          # dragonfly: global ports per router
    n: int | None = None          # kary_ncube: dimensions (default 2)
    wrap: bool | None = None      # kary_ncube: torus (True) or mesh (False)


@dataclass(frozen=True)
class NetworkPotential:
    """体系结构级输出：拓扑达到目标无阻塞带宽所需的内部资源。"""

    topology_name: str
    route: str
    terminal_count: int
    directed_link_count: int
    nonblocking_gbps_per_port: float
    required_internal_speedup: int
    required_internal_800g_links: int
    certificate_status: str
    worst_link: str
    notes: str = ""


@dataclass(frozen=True)
class PackagingEstimate:
    """封装级输出：单 die/package 能否承载网络需求。"""

    die_area_mm2: float
    power_w: float
    external_800g_port_budget: float
    internal_800g_link_budget: float
    required_external_lanes: int
    required_internal_lanes: int
    area_ok: bool
    power_ok: bool
    external_ports_ok: bool
    internal_links_ok: bool
    details: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class FeasibilityReport:
    """最终耦合报告：两关都通过时 feasible_potential 才为 True。"""

    requirement: Requirement
    topology: TopologySpec
    network: NetworkPotential
    packaging: PackagingEstimate
    feasible_potential: bool
    fail_reasons: tuple[str, ...]
    recommendation: str
