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


# ===========================================================================
# 层次化 DSE 数据结构
# ===========================================================================


@dataclass(frozen=True)
class DieEstimate:
    """单 die 物理估计。

    将一个特定规模的 crossbar + 外部 SerDes + D2D PHY
    放在一个 reticle-limited die 上的面积/功耗账单。
    """

    crossbar_ports: int
    """crossbar 端口总数 = r×p + (r-1) + (K-1) + r×h。"""

    crossbar_area_mm2: float
    """O(N²) 交叉开关矩阵面积。"""

    buffer_area_mm2: float
    """O(N) buffer 面积（SRAM）。"""

    router_total_area_mm2: float
    """crossbar + buffer。"""

    ext_serdes_count: int
    """本 die 上的外部 800G 端口数。"""

    ext_serdes_area_mm2: float

    ext_serdes_power_w: float

    d2d_link_count: int
    """本 die 上跨 die 的 D2D 链路数。"""

    d2d_lane_count: int
    """d2d_link_count × int_lanes_per_port。"""

    d2d_area_mm2: float

    d2d_power_w: float

    die_area_mm2: float
    """总面积 = base + router + ext_serdes + d2d。"""

    die_power_w: float

    area_ok: bool
    """die_area ≤ reticle limit。"""

    d2d_edge_ok: bool
    """D2D lane 数 ≤ die 边沿可供应 lane 数。"""


@dataclass(frozen=True)
class PartitionPlan:
    """一种 group 的物理分割方案：用 K 个 die 实现同一组 logical routers。"""

    die_count: int
    """K = 1..a。"""

    routers_per_die: int
    """每个 die 上承载的 logical router 数 r = a/K。"""

    dies: tuple[DieEstimate, ...]
    """每个 die 的物理账单（K 个元素）。"""

    total_area_mm2: float

    total_power_w: float

    feasible: bool
    """所有 die 的 area_ok 和 d2d_edge_ok 都为 True。"""


@dataclass(frozen=True)
class GroupPlan:
    """一个 Dragonfly group 的完整 DSE 结果。

    包含逻辑拓扑的网络性能评估，以及所有可行的物理分割方案。
    """

    a: int
    p: int
    h: int

    total_terminals: int
    """a × p。"""

    network: NetworkPotential
    """体系结构评估结果（组内全互联 + 全局出口）。"""

    partitions: tuple[PartitionPlan, ...]
    """按 die_count 升序排列的所有可行分割方案。"""

    best_partition: PartitionPlan | None
    """die_count 最小（面积效率最高）的可行方案。"""


@dataclass(frozen=True)
class WaferPlan:
    """晶圆级汇总：多个 group + 组间互连的完整物理方案。"""

    group_count: int
    """g 个 group。"""

    group_config: str
    """"(a,p,h)" 字符串。"""

    groups: tuple[GroupPlan, ...]

    inter_group_topo: str
    """组间拓扑："full_mesh" | "dragonfly_L2"。"""

    inter_group_link_count: int
    """组间链路总数。"""

    inter_group_lane_count: int
    """组间 lane 总数（走 package 基板）。"""

    total_terminals: int

    total_dies: int

    total_area_mm2: float

    total_power_w: float

    feasible: bool
    """所有 group 可行 AND 组间互连在 package 预算内。"""
