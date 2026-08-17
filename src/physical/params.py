"""实验参数组合——论文绘图、讨论都围绕这些组合展开.

两组:
  TOY   — 完全自拟，数字手算友好。准则：模型结果必须与手算一致，
          一眼能发现错误。toy 参数的手算断言见 tests/params/test09_params.md。
  UCIE  — 基于 UCIe 1.1/2.0 Spec Table 1-2 (Advanced Package, 45μm bump)
          的 16/24/32 GT/s 三档。功耗为 UCIe 典型值。
          SerDes 统一标准: OIF-CEI-112G-VSR (最经典档位)。

所有数字来自 src/physical/interconnect/{ucie,serdes}.py 的注册实例，
与 src/physical/bump/bump.py 的预设一一对应，不重复造参数。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from physical.bump.bump import BumpSpec, UBUMP_45UM, C4_130UM


@dataclass(frozen=True)
class DieParams:
    """die 规格.

    §2.8 die 缩放: d(B)=d0+α_d·B, A_die(B)=d(B)², P_peak(B)=P0+β_P·B。
    默认 α_d=β_P=0、d0=None（退化特例，面积/峰值功耗不随 B 变）。
    """

    width_mm: float
    height_mm: float
    static_power_w: float
    vdd_v: float
    d0_mm: float | None = None      # 缩放基线边长 [mm]；None → width_mm（正方形退化）
    alpha_d: float = 0.0            # 边长随 B 增长率 [mm/Gbps]
    beta_p: float = 0.0             # 峰值功耗随 B 增长率 [W/Gbps]

    @property
    def area_mm2(self) -> float:
        return self.width_mm * self.height_mm

    @property
    def base_side_mm(self) -> float:
        return self.width_mm if self.d0_mm is None else self.d0_mm

    def side_mm(self, B: float) -> float:
        """d(B) = d0 + α_d·B."""
        return self.base_side_mm + self.alpha_d * B

    def area_mm2_at(self, B: float) -> float:
        """A_die(B) = d(B)^2."""
        d = self.side_mm(B)
        return d * d

    def peak_power_w(self, B: float) -> float:
        """P_peak(B) = P0 + β_P·B."""
        return self.static_power_w + self.beta_p * B


@dataclass(frozen=True)
class BumpParams:
    """bump 规格（μbump 或 C4）."""
    name: str
    pitch_um: float
    current_per_bump_ma: float
    utilization: float

    @property
    def density_per_mm2(self) -> float:
        return 1e6 / self.pitch_um**2

    def spec(self) -> BumpSpec:
        return BumpSpec(self.name, self.pitch_um, self.current_per_bump_ma)


@dataclass(frozen=True)
class LinkParams:
    """一条链路的互联标准（die 间主互连或组间全局）."""
    name: str
    lane_rate_gbps: float
    power_per_lane_w: float

    @property
    def pj_per_bit(self) -> float:
        """能效 [pJ/bit]. 传统 vs 2.5D vs 3D 的核心对比量."""
        return self.power_per_lane_w / self.lane_rate_gbps * 1e3


@dataclass(frozen=True)
class ThermalParams:
    """热参数（MfitStackConfig 的输入）."""
    r_vert_k_per_w: float
    k_interposer: float
    t_interposer_mm: float
    t_ambient_k: float
    t_max_k: float

    @property
    def thermal_budget_k(self) -> float:
        return self.t_max_k - self.t_ambient_k


@dataclass(frozen=True)
class PackageParams:
    """interposer + 布线参数."""
    interposer_w_mm: float
    interposer_h_mm: float
    metal_layers: int
    lanes_per_mm: float     # 真实 Cu damascene RDL ≈ 500 lines/mm/层
    c4_pitch_mm: float


@dataclass(frozen=True)
class ExpParams:
    """一组实验物理参数 = 论文里讨论的一个"参数组合".

    die / bump / link 是 die 间主互连（2.5D: UCIe+μbump；传统: SerDes+C4）；
    global_link / c4 是组间全局互连（substrate SerDes，统一 112G-VSR）。
    """

    name: str
    die: DieParams
    bump: BumpParams
    link: LinkParams
    global_link: LinkParams
    c4: BumpParams
    thermal: ThermalParams
    pkg: PackageParams

    @classmethod
    def from_dict(cls, d: dict) -> "ExpParams":
        """从 YAML 配置 dict 构造——main.py 的加载路径.

        物理参数不该硬编码：params/*.yaml 是论文"实验设置"的载体，
        本方法把 dict 填进结构体（缺字段由 KeyError 自然报错）。
        """
        return cls(
            name=d["name"],
            die=DieParams(**d["die"]),
            bump=BumpParams(**d["bump"]),
            link=LinkParams(**d["link"]),
            global_link=LinkParams(**d["global_link"]),
            c4=BumpParams(**d["c4"]),
            thermal=ThermalParams(**d["thermal"]),
            pkg=PackageParams(**d["pkg"]),
        )


# ══════════════════════════════════════════════════════════════════
# TOY —— 手算友好。准则：模型输出必须与手算逐位一致。
# ══════════════════════════════════════════════════════════════════
# 选数的理由（每一条都是为了手算）:
#   die 10×10mm, P0=10W, Vdd=1.0V            → 面积 100mm²、电流整数
#   bump 100μm 利用率 1.0                   → 密度恰好 100/mm² → 总数 10000
#   电流 100mA                              → power bumps = 10W/(1.0V×0.1A) = 100
#                                             → signal 预算恰好 9900
#   link 10G/lane, 0.1W/lane                → 1 pJ/bit×10=10pJ/bit 整数
#                                             → bump 系数 (1/10)(1+0.1/(1×0.1)) = 0.2/Gbps
#   R_vert=1.0 K/W, T_amb=300, T_max=400    → 热预算 100K 整数
#   interposer 100×100mm                    → 10×10 网格

TOY = ExpParams(
    name="toy",
    die=DieParams(width_mm=10.0, height_mm=10.0,
                  static_power_w=10.0, vdd_v=1.0),
    bump=BumpParams(name="toy-bump-100μm", pitch_um=100.0,
                    current_per_bump_ma=100.0, utilization=1.0),
    link=LinkParams(name="toy-link-10G", lane_rate_gbps=10.0,
                    power_per_lane_w=0.1),
    global_link=LinkParams(name="toy-serdes-100G", lane_rate_gbps=100.0,
                           power_per_lane_w=1.0),
    c4=BumpParams(name="toy-c4-200μm", pitch_um=200.0,
                  current_per_bump_ma=200.0, utilization=1.0),
    thermal=ThermalParams(r_vert_k_per_w=1.0, k_interposer=100.0,
                          t_interposer_mm=0.1, t_ambient_k=300.0,
                          t_max_k=400.0),
    pkg=PackageParams(interposer_w_mm=100.0, interposer_h_mm=100.0,
                      metal_layers=4, lanes_per_mm=100.0, c4_pitch_mm=1.0),
)

# ══════════════════════════════════════════════════════════════════
# UCIE —— UCIe 1.1/2.0 Spec Table 1-2 (Advanced Package, 45μm bump)
#        三档速率，功耗为 UCIe 典型值。
# ══════════════════════════════════════════════════════════════════

def _ucie(name: str, rate: float, mw: float) -> ExpParams:
    return ExpParams(
        name=name,
        die=DieParams(width_mm=12.0, height_mm=12.0,
                      static_power_w=5.0, vdd_v=0.8),
        bump=BumpParams(name=UBUMP_45UM.name, pitch_um=UBUMP_45UM.pitch_um,
                        current_per_bump_ma=UBUMP_45UM.current_per_bump_ma,
                        utilization=0.9),
        link=LinkParams(name=f"UCIe-{rate:.0f}G-Advanced",
                        lane_rate_gbps=rate, power_per_lane_w=mw),
        global_link=LinkParams(name="SerDes-112G-VSR",
                               lane_rate_gbps=106.25, power_per_lane_w=0.425),
        c4=BumpParams(name=C4_130UM.name, pitch_um=C4_130UM.pitch_um,
                      current_per_bump_ma=C4_130UM.current_per_bump_ma,
                      utilization=0.7),
        thermal=ThermalParams(r_vert_k_per_w=1.5, k_interposer=150.0,
                              t_interposer_mm=0.1, t_ambient_k=300.0,
                              t_max_k=358.15),
        pkg=PackageParams(interposer_w_mm=80.0, interposer_h_mm=80.0,
                          metal_layers=4, lanes_per_mm=500.0,
                          c4_pitch_mm=5.0),
    )


UCIE_16G = _ucie("ucie-16g", 16.0, 0.005)
UCIE_24G = _ucie("ucie-24g", 24.0, 0.009)
UCIE_32G = _ucie("ucie-32g", 32.0, 0.016)

UCIE_SERIES = [UCIE_16G, UCIE_24G, UCIE_32G]
ALL_PARAMS = [TOY] + UCIE_SERIES


# ══════════════════════════════════════════════════════════════════
# YAML 参数数据集加载 —— config/params/*.yaml 是"实验设置"的载体。
# 每个 YAML 一个物理参数组合（技术谱系: 2D/2.5D/3D/晶圆级/光互连）。
# 单一来源是 YAML 文件本身，这里只负责读入，不重复造数字。
# ══════════════════════════════════════════════════════════════════

def load_yaml_params(directory: str) -> dict[str, "ExpParams"]:
    """从目录加载全部 params/*.yaml → {name: ExpParams}.

    供实验矩阵 / 批量 DSE 程序化枚举用。from_dict 把 dict 填进结构体，
    字段缺失由 KeyError 自然报错（参数校验不静默兜底）。
    """
    import glob
    import os

    import yaml

    out: dict[str, ExpParams] = {}
    for path in sorted(glob.glob(os.path.join(directory, "*.yaml"))):
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        p = ExpParams.from_dict(d)
        out[p.name] = p
    return out
