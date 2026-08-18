"""MFIT 3D RC 网络求解器 — 单 interposer 精度。"""

from __future__ import annotations

import os
import sys
import time
import tempfile
from pathlib import Path
from types import SimpleNamespace

from dataclasses import dataclass

import numpy as np

from physical.config.spec_thermal import ThermalConfig, ThermalResult, T_AMBIENT_K
from ._mfit_adapter import (
    build_geometry_dict, build_power_config_dict,
    write_power_seq_csv, htc_for_cooling,
)
from ._base import ThermalSolver
from ._simple import _SimpleSolver

_MFIT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "MFIT"


@dataclass(frozen=True)
class _MfitSimConfig:
    """MFIT 仿真参数。"""
    time_step: float = 0.1
    total_duration: float = 10.0
    power_interval: float = 1.0
    simulation_type: str = "steady"
    use_tuned_C: bool = True
    generate_DSS: bool = False
    generate_heatmap: bool = False


class _MfitSolver(ThermalSolver):
    """MFIT 3D RC 网络求解器。

    对单个 interposer 区域做全 3D 热仿真，返回节点级温度。
    精度最高，需要 C 库 (SuperLU) 和 numpy/scipy。
    C 库不可用时自动回退到 _SimpleSolver。
    """

    name = "mfit"

    def __init__(self, sim_config: _MfitSimConfig | None = None):
        self.sim_config = sim_config or _MfitSimConfig()
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        if self._available is None:
            self._available = self._probe()
        return self._available

    @staticmethod
    def _probe() -> bool:
        try:
            import numpy as np  # noqa: F401
            from scipy.signal import lti  # noqa: F401
        except ImportError:
            return False

        local_lib = os.path.expanduser("~/.local/lib")
        if os.path.isdir(local_lib):
            ld = os.environ.get("LD_LIBRARY_PATH", "")
            if local_lib not in ld:
                os.environ["LD_LIBRARY_PATH"] = f"{local_lib}:{ld}" if ld else local_lib

        try:
            old = os.getcwd()
            os.chdir(str(_MFIT_DIR))
            saved = list(sys.path)
            sys.path.insert(0, str(_MFIT_DIR))
            try:
                import common  # noqa: F401
                from power_class import Power_grid  # noqa: F401
                from package_class import Chiplet_package  # noqa: F401
            finally:
                sys.path = saved
                os.chdir(old)
            return True
        except Exception:
            return False

    def solve(self, config: ThermalConfig) -> ThermalResult:
        if not self.available:
            return self._solve_fallback(config)
        return self._solve_mfit(config)

    def _solve_mfit(self, config: ThermalConfig) -> ThermalResult:
        if config.cooling is None:
            raise ValueError("ThermalConfig.cooling is required")

        t0 = time.perf_counter()
        htc = htc_for_cooling(config.cooling)
        geometry = build_geometry_dict(config, htc)
        power_config = build_power_config_dict(config)

        with tempfile.TemporaryDirectory(prefix="mfit_") as tmp_dir:
            output_dir = tmp_dir
            os.makedirs(os.path.join(output_dir, "output"), exist_ok=True)
            power_seq_file = write_power_seq_csv(power_config, tmp_dir)

            args = SimpleNamespace(
                time_step=self.sim_config.time_step,
                total_duration=self.sim_config.total_duration,
                power_interval=self.sim_config.power_interval,
                simulation_type=self.sim_config.simulation_type,
                is_homogeneous=True,
                use_tuned_C=self.sim_config.use_tuned_C,
                generate_DSS=self.sim_config.generate_DSS,
                generate_heatmap=self.sim_config.generate_heatmap,
                time_heatmap=4.0,
                output_dir=output_dir,
                power_seq_file=power_seq_file,
            )

            old = os.getcwd()
            os.chdir(str(_MFIT_DIR))
            saved = list(sys.path)
            sys.path.insert(0, str(_MFIT_DIR))
            try:
                import common
                from power_class import Power_grid
                from package_class import Chiplet_package

                mat_file = str(_MFIT_DIR / "material_prop.yml")
                materials = common.load_dict_yaml(mat_file)
                utils = common.Utils(geometry["common"])
                pg = Power_grid(power_config, args)
                pg.create_power_seq_grid(utils=utils)
                pkg = Chiplet_package(materials, geometry, pg, args, utils)
                pkg.create_layers()
                pkg.connect_nodes()
                pkg.run_simulation_c_superlu()

                temps = pkg.temperature_all_save[-1]
                node_count = len(temps)

                chiplet_temps = []
                offset = 0
                for layer in pkg.layers:
                    n = layer.layer_total_nodes()
                    if layer.is_power_src():
                        chiplet_temps.extend(temps[offset:offset + n].tolist())
                    offset += n

                t_max = max(chiplet_temps) if chiplet_temps else float(max(temps))
                t_avg = (sum(chiplet_temps) / len(chiplet_temps)
                         if chiplet_temps else float(sum(temps) / node_count))
            finally:
                sys.path = saved
                os.chdir(old)

        elapsed = time.perf_counter() - t0
        margin = config.t_junction_max_k - t_max

        return ThermalResult(
            feasible=margin >= 0,
            solver_name=self.name,
            max_temperature_k=t_max,
            max_temperature_c=t_max - 273.15,
            avg_temperature_k=t_avg,
            margin_k=margin,
            node_count=node_count,
            simulation_time_s=elapsed,
            r_eff=(t_max - T_AMBIENT_K) / (config.die_count * config.die_power_w)
                   if config.die_power_w > 0 else 0,
        )

    def _solve_fallback(self, config: ThermalConfig) -> ThermalResult:
        result = _SimpleSolver().solve(config)
        return ThermalResult(
            feasible=result.feasible,
            solver_name=self.name,
            max_temperature_k=result.max_temperature_k,
            max_temperature_c=result.max_temperature_c,
            avg_temperature_k=result.avg_temperature_k,
            margin_k=result.margin_k,
            fallback=True,
        )

    def calibrate_r_eff(self, config: ThermalConfig) -> float:
        if self.available and config.cooling is not None:
            result = self._solve_mfit(config)
            return result.r_eff or 0.05

        htc_top, _ = htc_for_cooling(config.cooling) if config.cooling else (5000, 25)
        area_m2 = config.interposer_area_mm2 * 1e-6
        return 1.0 / (htc_top * area_m2) if htc_top > 0 else 0.05
