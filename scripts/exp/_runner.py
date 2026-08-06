"""共享实验运行器 — 批量调用 UnifiedLp，CSV 输出。"""

from __future__ import annotations

import csv
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from wafer_dse.lp import UnifiedLp
from wafer_dse.lp.engine import _has_cvxpy
from wafer_dse.lp.report import LpResult
from wafer_dse.architecture_model.topology import Topology

# 默认输出目录
DEFAULT_OUTPUT_DIR = "outputs/paper_experiments"


@dataclass
class Trial:
    """一次 LP 求解的输入规格。"""

    label: str                     # 人类可读标签，如 "DF_a4_p4_h2_mesh"
    topo: Topology
    route: str = "valiant"
    target_gbps: float = 800.0
    die_configs: list | None = None
    bump_spec: object | None = None
    thermal_cfg: object | None = None
    meta: dict | None = None       # 额外元数据 (a, p, h, size, ...)


def run_trials(
    trials: list[Trial],
    output_dir: str = DEFAULT_OUTPUT_DIR,
    csv_name: str = "results",
    progress: bool = True,
) -> list[dict]:
    """批量运行一组 Trial，将结果写入 CSV。

    Args:
        trials: 待求解的 Trial 列表
        output_dir: CSV 输出目录
        csv_name: CSV 文件名（不含扩展名）
        progress: 是否打印进度

    Returns:
        每行结果的 dict 列表（即 CSV 的行）
    """
    if not _has_cvxpy():
        raise ImportError(
            "实验需要 cvxpy (Valiant LP 路径)。 pip install \".[lp]\""
        )

    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f"{csv_name}.csv")

    rows: list[dict] = []

    n = len(trials)
    for i, trial in enumerate(trials):
        t0 = time.time()

        # 构建 + 求解
        lp = UnifiedLp(trial.topo, route=trial.route, target_gbps=trial.target_gbps)

        if trial.die_configs and trial.bump_spec:
            lp.add_geometry(trial.die_configs, trial.bump_spec)
        if trial.thermal_cfg:
            lp.add_thermal(trial.thermal_cfg)

        result = lp.solve()
        elapsed = time.time() - t0

        # 扁平化为一行
        row = _flatten(trial, result, elapsed)
        rows.append(row)

        if progress:
            status = "✓" if result.feasible else "✗"
            print(f"  [{i+1:3d}/{n}] {status} {trial.label:40s}  "
                  f"t*={result.worst_load:.4f}  "
                  f"BW={result.nonblocking_gbps:.0f}Gbps  "
                  f"{elapsed:.2f}s")

    # 写 CSV — 收集所有行的 key 的并集作为 fieldnames
    fieldnames = list(dict.fromkeys(
        k for row in rows for k in row
    ))
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  → {len(rows)} rows → {csv_path}")
    return rows


def _flatten(trial: Trial, result: LpResult, elapsed: float) -> dict:
    """将 Trial + LpResult 扁平化为单个 dict。"""
    row = {
        "label": trial.label,
        "route": trial.route,
        "target_gbps": trial.target_gbps,
        "feasible": result.feasible,
        "t_star": result.worst_load,
        "nonblocking_gbps": result.nonblocking_gbps,
        "bottleneck_link": result.bottleneck_link,
        "solver": result.solver,
        "solve_time_s": round(elapsed, 4),
        "num_vars": result.num_variables,
        "num_constraints": result.num_constraints,
        "n_terminals": len(trial.topo.terminals()),
        "n_links": len(result.per_link_load),
    }

    # 元数据
    if trial.meta:
        for k, v in trial.meta.items():
            row[k] = v

    # 约束状态
    for cs in result.constraints:
        row[f"{cs.name}_satisfied"] = cs.satisfied
        row[f"{cs.name}_violation"] = round(cs.max_violation, 6)
        row[f"{cs.name}_slack"] = round(cs.max_slack, 6)
        row[f"{cs.name}_binding"] = "|".join(cs.binding_constraints[:3])

    # 备注
    row["notes"] = " | ".join(result.notes)

    return row
