"""
互连标准抽象基类

每一种互连标准实现此 ABC。注意这里的"标准"粒度——
UCIe 16GT/s 和 UCIe 32GT/s 是**两个不同的标准**（不同的 PHY 设计、
不同的功耗包络、不同的最大距离），各自作为一个实例注册。

使用方式:
    ucie_16 = get_profile("UCIe-16G-Advanced")
    bill = ucie_16.compute(length_mm=2.5, bandwidth_gbps=800)
    print(f"需要 {bill.lanes} lanes, 功耗 {bill.power_w:.1f} W")

数学约定
========
标准 s 包含固定的物理参数:
  - lane_rate_gbps:    单 lane 速率 [Gbps]
  - power_per_lane_w:  单 lane 功耗 [W]
  - loss_db_per_mm:    单位距离损耗 [dB/mm]
  - max_reach_mm:      最大传输距离 [mm]
  - ber:               目标误码率
  - lane_density_per_mm: 边沿密度 [lane/mm]

给定 (length_mm, bandwidth_gbps)，计算:

    lanes = ceil(bandwidth_gbps / lane_rate_gbps)
    power = lanes · power_per_lane_w   +  _distance_power(length, lanes)
    loss   = length · loss_db_per_mm
    width  = lanes / lane_density_per_mm

物理占位 (Footprint) 由 _footprint() 定义，描述该标准在晶圆分区网格上
的实际资源消耗——不仅是两个端点，还包括中间走线区域的类型和层数。
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto


# ===========================================================================
# 布线账单 — 标准 ABC 的统一输出
# ===========================================================================


@dataclass(frozen=True)
class LinkBudget:
    """给定 (length, bandwidth) 的标准输出账单。"""

    profile_name: str            # 所用标准名称
    length_mm: float              # 走线长度 [mm]
    bandwidth_gbps: float         # 需求带宽 [Gbps]

    lanes: int                    # 所需 lane 数
    power_w: float                # 总功耗 [W]
    loss_db: float                # 总损耗 [dB]
    width_mm: float               # die 边沿占用宽度 [mm]
    ber: float                    # 误码率

    feasible: bool                # length ≤ max_reach？
    fail_reason: str = ""         # 不可行时给出原因

    # 物理占位
    footprint: "Footprint" = field(default_factory=lambda: Footprint())


# ===========================================================================
# 物理占位 — 描述在晶圆分区上的资源消耗
# ===========================================================================


class ZoneType(Enum):
    """分区在布线方案中的功能类型。"""
    ENDPOINT = auto()       # 端点分区 (die 所在)
    COPPER_TRACE = auto()   # 铜走线穿越
    WAVEGUIDE = auto()      # 波导穿越 (光互连专用)
    SERDES_PHY = auto()     # SerDes PHY 区域
    PASSIVE = auto()        # 无源直通 (circuit-switching 模式)
    UNUSED = auto()         # 不经过


@dataclass(frozen=True)
class ZoneUsage:
    """单个分区的资源消耗记录。"""
    x: int
    y: int
    zone_type: ZoneType
    layer_count: int = 0        # 本分区占用的布线层数
    lane_count: int = 0         # 穿越本分区的 lane 数


@dataclass(frozen=True)
class Footprint:
    """一条链路在晶圆分区网格上的完整物理占位。"""

    path: tuple[tuple[int, int], ...] = ()
    zones: tuple[ZoneUsage, ...] = ()
    total_layers: int = 0
    total_power_w: float = 0.0

    def merge(self, other: "Footprint") -> "Footprint":
        return Footprint(
            path=self.path + other.path,
            zones=self.zones + other.zones,
            total_layers=max(self.total_layers, other.total_layers),
            total_power_w=self.total_power_w + other.total_power_w,
        )

    @staticmethod
    def empty() -> "Footprint":
        return Footprint()


# ===========================================================================
# 互连标准 ABC
# ===========================================================================


class InterconnectProfile(ABC):
    """互连标准的统一抽象基类。

    每个实例 = 一种具体的互连方案（如 "UCIe-16G-Advanced"）。
    不同速率/不同封装族是**不同的实例**，各自独立注册。

    子类只需提供:
      - 类属性: _name, _params (frozen dict)
      - _footprint() 方法
      - 可选覆写 _distance_power()
    """

    # ---- 子类必须定义 ----

    @property
    @abstractmethod
    def name(self) -> str:
        """该标准的唯一名称，如 "UCIe-16G-Advanced"."""
        ...

    @property
    @abstractmethod
    def _params(self) -> dict:
        """参数快照 (视为只读).

        必须包含: lane_rate_gbps, power_per_lane_w, loss_db_per_mm,
                  max_reach_mm, ber, lane_density_per_mm.
        """
        ...

    # ---- 便捷属性 ----

    @property
    def lane_rate_gbps(self) -> float:    return self._params["lane_rate_gbps"]

    @property
    def power_per_lane_w(self) -> float:  return self._params["power_per_lane_w"]

    @property
    def loss_db_per_mm(self) -> float:    return self._params["loss_db_per_mm"]

    @property
    def max_reach_mm(self) -> float:      return self._params["max_reach_mm"]

    @property
    def ber(self) -> float:               return self._params["ber"]

    @property
    def lane_density_per_mm(self) -> float:
        return self._params.get("lane_density_per_mm", 0.0)

    # ---- 核心计算 (所有标准共用) ----

    def compute(
        self,
        length_mm: float,
        bandwidth_gbps: float,
    ) -> LinkBudget:
        """给定走线长度和带宽目标，计算完整物理账单。"""
        if length_mm > self.max_reach_mm:
            return LinkBudget(
                profile_name=self.name,
                length_mm=length_mm,
                bandwidth_gbps=bandwidth_gbps,
                lanes=0, power_w=0.0, loss_db=0.0, width_mm=0.0,
                ber=self.ber,
                feasible=False,
                fail_reason=(
                    f"距离 {length_mm:.1f}mm 超过 {self.name} "
                    f"最大传输距离 {self.max_reach_mm:.1f}mm"
                ),
            )

        lanes = max(1, int(math.ceil(bandwidth_gbps / self.lane_rate_gbps)))
        loss_db = length_mm * self.loss_db_per_mm
        width_mm = (lanes / self.lane_density_per_mm
                     if self.lane_density_per_mm > 0 else 0.0)
        power_w = lanes * self.power_per_lane_w + self._distance_power(length_mm, lanes)

        return LinkBudget(
            profile_name=self.name,
            length_mm=length_mm,
            bandwidth_gbps=bandwidth_gbps,
            lanes=lanes,
            power_w=power_w,
            loss_db=loss_db,
            width_mm=width_mm,
            ber=self.ber,
            feasible=True,
            footprint=self._footprint(length_mm, lanes),
        )

    # ---- 子类覆写 ----

    @abstractmethod
    def _footprint(self, length_mm: float, lanes: int) -> Footprint:
        """物理占位: 描述该链路在晶圆分区上的资源消耗。

        每种互连标准的物理形态不同:
          - UCIe 并口:  两个 UCIe PHY + 铜走线
          - SerDes:     两个 SerDes 宏 + 差分走线 (可能带中继)
          - 光互连:     两个 CPO 模块 + 波导 + 短铜跳线
          - 外部以太网:  两个 SerDes + PCB 出线 (晶圆外)
        """
        ...

    def _distance_power(self, length_mm: float, lanes: int) -> float:
        """距离相关的附加功耗项。默认 0；SerDes/光互连按需覆写。"""
        return 0.0


# ===========================================================================
# 标准注册表
# ===========================================================================

_registry: dict[str, InterconnectProfile] = {}


def register(std: InterconnectProfile) -> None:
    _registry[std.name] = std


def get_profile(name: str) -> InterconnectProfile:
    if name not in _registry:
        raise KeyError(
            f"未注册的互连标准: {name}. 可用: {list(_registry)}"
        )
    return _registry[name]


def list_profiles() -> list[str]:
    return list(_registry.keys())
