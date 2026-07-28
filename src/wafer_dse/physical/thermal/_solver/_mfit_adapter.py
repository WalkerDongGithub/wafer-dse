"""
MFIT 适配器 — 纯函数，无状态。

将 wafer-dse 的 ThermalConfig 转换为 MFIT 所需的 geometry / power_config
dict。所有函数都是纯数据转换，不依赖 MFIT import。
"""

from __future__ import annotations

import math
import os
import tempfile

from .._cooling import CoolingSolution
from .._config import ThermalConfig


# ============================================================================
# MFIT 层堆叠常量
# ============================================================================

_DEFAULT_LAYER_THICKNESSES: dict[str, float] = {
    "substrate_1": 0.5, "substrate_2": 0.5,
    "c4": 0.08, "interposer": 0.1,
    "ubump": 0.025, "chiplet": 0.1,
    "tim": 0.05, "lid1": 0.25, "lid2": 0.25,
}

_DEFAULT_LAYER_NODES: dict[str, tuple[int, int]] = {
    "substrate_1": (4, 4), "substrate_2": (4, 4),
    "c4": (4, 4), "interposer": (4, 4),
    "ubump": (2, 2), "chiplet": (2, 2), "tim": (2, 2),
    "lid1": (4, 4), "lid2": (4, 4),
}

_COOLING_HTC: dict[str, tuple[float, float]] = {
    "Air": (500, 10), "Liquid": (5000, 25),
    "Immersion": (10000, 100), "Microfluidic": (20000, 200),
}


# ============================================================================
# 冷却方案 → HTC
# ============================================================================


def htc_for_cooling(cooling: CoolingSolution) -> tuple[float, float]:
    """将 wafer-dse 冷却方案映射为 MFIT 边界热传导系数。

    返回 (bc_top_htc, bc_bottom_htc) [W/m²K]。
    """
    return _COOLING_HTC.get(cooling.name, (5000, 25))


# ============================================================================
# 辅助函数
# ============================================================================


def _find_chiplet_grid(die_count: int) -> tuple[int, int]:
    """找到最接近正方形的 die 网格布局 (nx, ny)。"""
    nx = int(math.ceil(math.sqrt(die_count)))
    while nx > 0:
        if die_count % nx == 0:
            return (nx, die_count // nx)
        nx -= 1
    return (die_count, 1)


# ============================================================================
# 公共 API: dict 构造
# ============================================================================


def build_geometry_dict(
    config: ThermalConfig,
    htc: tuple[float, float] | None = None,
    layer_thicknesses: dict[str, float] | None = None,
) -> dict:
    """根据 ThermalConfig 构造 MFIT geometry dict。

    参数
    ----
    config : ThermalConfig
    htc : (top, bottom) HTC，None 则从 config.cooling 推断
    layer_thicknesses : 覆盖默认层厚度

    返回 MFIT Chiplet_package 可接受的 geometry dict。
    """
    if htc is None and config.cooling is not None:
        htc = htc_for_cooling(config.cooling)
    bc_top, bc_bottom = htc or (5000, 25)

    thick = dict(_DEFAULT_LAYER_THICKNESSES)
    if layer_thicknesses:
        thick.update(layer_thicknesses)

    nx, ny = _find_chiplet_grid(config.die_count)
    interposer_side = math.sqrt(config.interposer_area_mm2)

    # die 间距
    total_die_x = nx * config.die_width_mm
    total_die_y = ny * config.die_height_mm
    spacing_x = (interposer_side - total_die_x) / (nx + 1) if nx > 0 else 0
    spacing_y = (interposer_side - total_die_y) / (ny + 1) if ny > 0 else 0
    chiplet_spacing = max(min(spacing_x, spacing_y), 0.5)

    # 累积 Z 坐标
    z = 0.0

    def next_z(t: float) -> tuple[float, float]:
        nonlocal z
        start = z
        z += t
        return start, t

    layers = {}
    chiplet_start_x = chiplet_spacing
    chiplet_start_y = chiplet_spacing

    # --- substrate_1 ---
    s, t = next_z(thick["substrate_1"])
    layers["substrate_1"] = _make_layer(
        "substrate", t, 0, 0, s,
        _DEFAULT_LAYER_NODES["substrate_1"], under_chiplet=False,
    )

    # --- substrate_2 ---
    s, t = next_z(thick["substrate_2"])
    layers["substrate_2"] = _make_layer(
        "substrate", t, 0, 0, s,
        _DEFAULT_LAYER_NODES["substrate_2"], under_chiplet=False,
    )

    # --- c4 ---
    s, t = next_z(thick["c4"])
    layers["c4"] = _make_layer(
        "c4", t, 0, 0, s,
        _DEFAULT_LAYER_NODES["c4"], under_chiplet=False,
    )

    # --- interposer ---
    s, t = next_z(thick["interposer"])
    layers["interposer"] = _make_layer(
        "interposer", t, 0, 0, s,
        _DEFAULT_LAYER_NODES["interposer"], under_chiplet=False,
    )

    # --- ubump ---
    s, t = next_z(thick["ubump"])
    layers["ubump"] = _make_layer(
        "ubump", t, chiplet_start_x, chiplet_start_y, s,
        _DEFAULT_LAYER_NODES["ubump"], under_chiplet=True,
    )

    # --- chiplet (热源) ---
    s, t = next_z(thick["chiplet"])
    layers["chiplet"] = _make_layer(
        "chiplet", t, chiplet_start_x, chiplet_start_y, s,
        _DEFAULT_LAYER_NODES["chiplet"], under_chiplet=True, power_src=True,
    )

    # --- tim ---
    s, t = next_z(thick["tim"])
    layers["tim"] = _make_layer(
        "tim", t, chiplet_start_x, chiplet_start_y, s,
        _DEFAULT_LAYER_NODES["tim"], under_chiplet=True,
    )

    # --- lid1 ---
    s, t = next_z(thick["lid1"])
    layers["lid1"] = _make_layer(
        "lid", t, 0, 0, s,
        _DEFAULT_LAYER_NODES["lid1"], under_chiplet=False,
    )

    # --- lid2 ---
    s, t = next_z(thick["lid2"])
    layers["lid2"] = _make_layer(
        "lid", t, 0, 0, s,
        _DEFAULT_LAYER_NODES["lid2"], under_chiplet=False,
    )

    return {
        "common": {
            "x_length": interposer_side,
            "y_length": interposer_side,
            "z_length": z,
            "chiplet_x": config.die_width_mm,
            "chiplet_y": config.die_height_mm,
            "chiplet_spacing": chiplet_spacing,
            "n_chiplet_x": nx,
            "n_chiplet_y": ny,
            "bc_top_htc": bc_top,
            "bc_bottom_htc": bc_bottom,
            "ambient_temp": 300.0,
        },
        "layers": layers,
    }


def build_power_config_dict(config: ThermalConfig) -> dict:
    """根据 ThermalConfig 构造 MFIT power_config dict。

    每 die 一个 power block，占满 chiplet 区域，功率均匀分布。
    ubump/tim 层只做几何对齐，不含 power blocks。
    """
    nx, ny = _find_chiplet_grid(config.die_count)
    side = math.sqrt(config.interposer_area_mm2)
    spacing_x = (side - nx * config.die_width_mm) / (nx + 1) if nx > 0 else 1.0
    spacing_y = (side - ny * config.die_height_mm) / (ny + 1) if ny > 0 else 1.0
    sp = max(min(spacing_x, spacing_y), 0.5)

    chiplet_dict = {}
    ubump_tim_dict = {}
    idx = 0
    for i in range(nx):
        for j in range(ny):
            idx += 1
            name = f"chiplet_{idx}"
            cx = sp + i * (config.die_width_mm + sp)
            cy = sp + j * (config.die_height_mm + sp)

            chiplet_dict[name] = {
                "start_chiplet_x": cx,
                "start_chiplet_y": cy,
                "layout_blocks": {
                    "chiplet": {
                        "start_point_x": 0,
                        "start_point_y": 0,
                        "length_x": config.die_width_mm,
                        "length_y": config.die_height_mm,
                        "max_power": config.die_power_w,
                    }
                },
            }
            ubump_tim_dict[name] = {
                "start_chiplet_x": cx,
                "start_chiplet_y": cy,
            }

    return {
        "chiplet": chiplet_dict,
        "ubump": ubump_tim_dict,
        "tim": ubump_tim_dict,
    }


def build_power_seq_csv(power_config: dict) -> str:
    """生成 MFIT 所需的 power_seq CSV 字符串。

    稳态仿真只需要一列 (100%)。返回 CSV 文本。
    """
    rows = []
    for layer_name, layer_data in power_config.items():
        for chiplet_name, chiplet_data in layer_data.items():
            if "layout_blocks" in chiplet_data:
                for block_name in chiplet_data["layout_blocks"]:
                    rows.append(f"{layer_name}_{chiplet_name}_{block_name},100")
    return "\n".join(rows) + "\n"


def write_power_seq_csv(power_config: dict, tmp_dir: str) -> str:
    """生成 power_seq CSV 文件，返回文件路径。"""
    csv_path = os.path.join(tmp_dir, "power_seq.csv")
    with open(csv_path, "w") as f:
        f.write(build_power_seq_csv(power_config))
    return csv_path


# ============================================================================
# 内部
# ============================================================================


def _make_layer(
    material: str,
    thickness: float,
    x: float, y: float, z: float,
    nodes: tuple[int, int],
    under_chiplet: bool = False,
    power_src: bool = False,
) -> dict:
    return {
        "thickness": thickness,
        "nodes": {
            "uniform": True,
            "under_chiplet": under_chiplet,
            "x_nodes": nodes[0],
            "y_nodes": nodes[1],
        },
        "start_point": {"x": x, "y": y, "z": z},
        "power_src": power_src,
        "material": material,
    }
