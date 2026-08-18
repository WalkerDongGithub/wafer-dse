"""分层热求解器 — MFIT 标定 + 2D 晶圆热网络。"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from physical.config.spec_thermal import ThermalConfig, ThermalResult, T_AMBIENT_K
from ._base import ThermalSolver
from ._mfit import _MfitSolver


# 基板材料常数
_K_SUBSTRATE_INPLANE = 20.0
_SUBSTRATE_THICKNESS_MM = 1.0
_R_BOTTOM_DEFAULT = 50.0


@dataclass
class _WaferConfig:
    """晶圆级热网络配置。"""
    substrate_grid: tuple[int, int] = (4, 4)
    interposer_pitch_mm: float = 31.0
    interposer_width_mm: float | None = None
    r_bottom: float = _R_BOTTOM_DEFAULT
    k_substrate: float = _K_SUBSTRATE_INPLANE
    substrate_thickness_mm: float = _SUBSTRATE_THICKNESS_MM


class _HierarchicalSolver(ThermalSolver):
    """晶圆级分层热模型。

    用 _MfitSolver 预标定一次 R_eff，
    然后在 wafer 级构建 2D 热扩散网络，微秒级求解。
    支持非均匀功率分配和横向热传导。
    """

    name = "hierarchical"

    def __init__(
        self,
        calibrator: _MfitSolver | None = None,
        wafer_config: _WaferConfig | None = None,
    ):
        self.calibrator = calibrator or _MfitSolver()
        self.wafer_config = wafer_config or _WaferConfig()
        self._r_eff: float | None = None

    def calibrate(self, config: ThermalConfig, force: bool = False) -> float:
        if self._r_eff is not None and not force:
            return self._r_eff
        self._r_eff = self.calibrator.calibrate_r_eff(config)
        return self._r_eff

    @property
    def r_eff(self) -> float | None:
        return self._r_eff

    @property
    def is_calibrated(self) -> bool:
        return self._r_eff is not None

    def solve(self, config: ThermalConfig) -> ThermalResult:
        if self._r_eff is None:
            raise RuntimeError("需要先 calibrate() 标定 R_eff")
        return self._solve_network(config)

    def _solve_network(self, config: ThermalConfig) -> ThermalResult:
        wc = self.wafer_config
        rows, cols = wc.substrate_grid
        n = rows * cols

        if config.powers is not None and len(config.powers) == n:
            p = np.array(config.powers, dtype=np.float64)
        else:
            per = config.per_interposer_power_w
            p = np.full(n, per, dtype=np.float64)

        g_vert = 1.0 / self._r_eff
        g_bottom = 1.0 / wc.r_bottom

        width_mm = wc.interposer_width_mm or wc.interposer_pitch_mm
        a_cross = (wc.substrate_thickness_mm * 1e-3) * (width_mm * 1e-3)
        distance = wc.interposer_pitch_mm * 1e-3
        g_lat = wc.k_substrate * a_cross / distance

        g_mat = np.zeros((n, n), dtype=np.float64)
        b_vec = np.zeros(n, dtype=np.float64)

        for idx in range(n):
            r, c = divmod(idx, cols)
            g_self = g_vert + g_bottom

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    g_self += g_lat
                    g_mat[idx, nr * cols + nc] = -g_lat

            g_mat[idx, idx] = g_self
            b_vec[idx] = p[idx] + (g_vert + g_bottom) * T_AMBIENT_K

        temps = np.linalg.solve(g_mat, b_vec)

        t_max = float(np.max(temps))
        t_avg = float(np.mean(temps))
        margin = config.t_junction_max_k - t_max

        return ThermalResult(
            feasible=margin >= 0,
            solver_name=self.name,
            max_temperature_k=t_max,
            max_temperature_c=t_max - 273.15,
            avg_temperature_k=t_avg,
            margin_k=margin,
            temperatures=temps.tolist(),
            r_eff=self._r_eff,
            node_count=n,
        )

    def solve_uniform(
        self, per_interposer_power_w: float, config: ThermalConfig | None = None,
    ) -> ThermalResult:
        cfg = config or ThermalConfig(die_power_w=per_interposer_power_w)
        return self._solve_network(cfg)

    def hotspot_report(self, result: ThermalResult) -> str:
        rows, cols = self.wafer_config.substrate_grid
        temps_c = [t - 273.15 for t in (result.temperatures or [])]
        if not temps_c:
            return "No temperature data"

        lines = [
            f"Wafer Thermal Report ({rows}×{cols} grid)",
            f"  R_eff={result.r_eff:.4f} K/W",
            f"  Tmax={result.max_temperature_c:.1f}°C  Tavg={result.avg_temperature_k - 273.15:.1f}°C",
            f"  Margin={result.margin_k:.1f}K  Feasible={'YES' if result.feasible else 'NO'}",
            "",
            "  Temperature map [°C]:",
        ]
        for r in range(rows):
            row_temps = temps_c[r * cols:(r + 1) * cols]
            lines.append("  " + " ".join(f"{t:6.1f}" for t in row_temps))
        return "\n".join(lines)
