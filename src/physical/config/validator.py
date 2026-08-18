"""配置完整性校验 — YAML dict → 必填字段检查, 缺字段报错不兜底.

解决什么问题: 在 ExpParams.from_dict 之前做一次显式的结构校验, 把 KeyError
转成带字段名的清晰错误信息.
怎么用:
    from physical.config.validator import validate_params_dict
    d = load_config("config/params/ucie-32g.yaml")
    validate_params_dict(d)   # 缺字段抛 ValueError, 带字段名
读者: 这是物理参数的校验层; 数据契约 (ExpParams) 在 physical/params.py.

注意: 本模块只做结构校验, 不做语义校验 (数值合理性、单位换算等由消费方负责).
"""

from __future__ import annotations

from typing import Any


# ============================================================================
# ExpParams 必填字段表 — 与 physical/params.py ExpParams.from_dict 对齐
# ============================================================================

_PARAMS_TOP_KEYS = {"name", "die", "bump", "link", "global_link", "c4", "thermal", "pkg"}

_DIE_KEYS = {"width_mm", "height_mm", "static_power_w", "vdd_v"}
_BUMP_KEYS = {"name", "pitch_um", "current_per_bump_ma", "utilization"}
_LINK_KEYS = {"name", "lane_rate_gbps", "power_per_lane_w"}
_THERMAL_KEYS = {"r_vert_k_per_w", "k_interposer", "t_interposer_mm", "t_ambient_k", "t_max_k"}
_PKG_KEYS = {"interposer_w_mm", "interposer_h_mm", "metal_layers", "lanes_per_mm", "c4_pitch_mm"}


def _check_keys(d: dict[str, Any], required: set[str], section: str) -> None:
    """检查 dict 是否包含全部必填键, 缺失抛 ValueError 带字段名."""
    missing = required - set(d.keys())
    if missing:
        raise ValueError(
            f"参数校验失败 [{section}]: 缺少必填字段 {sorted(missing)}"
        )


def validate_params_dict(d: dict[str, Any]) -> None:
    """校验 ExpParams 的 YAML dict 结构完整性.

    Args:
        d: 从 YAML 读出的 dict (config.load_config 的返回值).

    Raises:
        ValueError: 缺少必填字段时, 错误信息包含 section + 字段名.
    """
    if not isinstance(d, dict):
        raise TypeError(f"params dict 必须是 dict, 收到 {type(d).__name__}")

    _check_keys(d, _PARAMS_TOP_KEYS, "top-level")

    _check_keys(d["die"], _DIE_KEYS, "die")
    _check_keys(d["bump"], _BUMP_KEYS, "bump")
    _check_keys(d["link"], _LINK_KEYS, "link")
    _check_keys(d["global_link"], _LINK_KEYS, "global_link")
    _check_keys(d["c4"], _BUMP_KEYS, "c4")
    _check_keys(d["thermal"], _THERMAL_KEYS, "thermal")
    _check_keys(d["pkg"], _PKG_KEYS, "pkg")


__all__ = ["validate_params_dict"]
