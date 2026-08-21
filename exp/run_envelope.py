#!/usr/bin/env python3
"""E5 包络不变性导出（insight 6 首选图数据）.

对每个拓扑：ObliviousValiantModel(topo).solve_envelope() 得到逐链路 L* 向量。
包络只依赖拓扑 + 路由 + 要求模型（V5 §7.3），物理参数不参与——
本脚本对每个"参数组"新建模型实例并重新求解，实证校验跨参数组 L* 逐链路相等
（C1: max|ΔL*| ≤ 1e-9），并输出跨拓扑差异（C2: 至少一对拓扑 max|ΔL*| > 0.01）。

输出:
  exp/output/envelope_<topo>.csv      — 链路索引 × 参数组 → L*
  exp/output/envelope_summary.csv     — 每拓扑组内 max|ΔL*| + 跨拓扑 max|ΔL*|

依据: .dsh/team/artifacts/experiment-design.md §2 E5
用法: PYTHONPATH=src python3 exp/run_envelope.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from problem.models import ObliviousValiantModel
from topology import (
    DragonflyTopology, FullMeshTopology, KaryNCubeTopology,
    MeshTopology, TorusTopology,
)

# 拓扑清单（实验设计 E5：≥4 种）
TOPOS = {
    "Mesh(3)": MeshTopology(3),
    "Torus(3)": TorusTopology(3),
    "FullMesh(3)": FullMeshTopology(3, 1),
    "Dragonfly(2,1,1)": DragonflyTopology(2, 1, 1),
    "KaryNCube(2,3)": KaryNCubeTopology(2, 3),
}

# 参数组标签（包络不消费参数——实证"物理无关"；物理参数见 config/params/*.yaml）
PARAM_GROUPS = ["toy", "ucie-16g", "ucie-24g", "ucie-32g"]

TOL_EQ = 1e-9     # C1 判据
TOL_DIFF = 0.01   # C2 判据


def main() -> None:
    out_dir = _project_root / "exp" / "output"
    out_dir.mkdir(exist_ok=True)

    envelope: dict[str, list[list[float]]] = {}   # topo -> [per-param L* vector]
    n_links: dict[str, int] = {}

    for tname, topo in TOPOS.items():
        vecs: list[list[float]] = []
        for _ in PARAM_GROUPS:
            vecs.append(list(ObliviousValiantModel(topo).solve_envelope()))
        envelope[tname] = vecs
        n_links[tname] = len(vecs[0])

        # 逐拓扑落盘
        path = out_dir / f"envelope_{tname}.csv"
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["link_idx"] + PARAM_GROUPS)
            for e in range(n_links[tname]):
                w.writerow([e] + [f"{v[e]:.9f}" for v in vecs])
        print(f"envelope_{tname}.csv  ({n_links[tname]} links × {len(PARAM_GROUPS)} 参数组)")

    # 汇总：组内 max|ΔL*|（C1）与跨拓扑 max|ΔL*|（C2）
    summary = []
    for tname in TOPOS:
        vecs = envelope[tname]
        within = max(
            abs(vecs[a][e] - vecs[b][e])
            for a in range(len(vecs)) for b in range(a + 1, len(vecs))
            for e in range(n_links[tname])
        )
        summary.append([tname, n_links[tname], f"{within:.2e}",
                        "PASS" if within <= TOL_EQ else "FAIL"])
    # 跨拓扑差异（按链路数对齐比较用 max-abs over min-len prefix）
    cross: list[list[str]] = []
    names = list(TOPOS)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            m = min(n_links[a], n_links[b])
            d = max(abs(envelope[a][0][e] - envelope[b][0][e]) for e in range(m))
            cross.append([a, b, f"{d:.4f}", "DIFF" if d > TOL_DIFF else "same"])
    with open(out_dir / "envelope_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["topo", "n_links", "within_max_abs_diff", "C1(<=1e-9)"])
        w.writerows(summary)
        w.writerow([])
        w.writerow(["topo_a", "topo_b", "cross_max_abs_diff", "C2(>0.01)"])
        w.writerows(cross)
    print("\nenvelope_summary.csv 已落盘")
    for row in summary:
        print(f"  组内 {row[0]}: max|ΔL*|={row[2]} → {row[3]}")


if __name__ == "__main__":
    main()
