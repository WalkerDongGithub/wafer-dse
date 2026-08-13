"""热力图 —— die 级温度可视化.

G 的每一行对应一个 die 热节点.
节点位置由 placement 的 (x, y) 决定.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def plot_temperature(
    placements: list,
    G: np.ndarray,
    P_watts: np.ndarray,
    b_vec: np.ndarray,
    T_max: float,
    T_ambient: float,
    *,
    title: str = "Die Temperature",
    save_path: str | Path | None = None,
) -> plt.Figure:
    """绘制 per-die 温度热力图.

    每个 die 是一个矩形，颜色 = 稳态温度.
    同时标注 die 索引、功率、温度.

    Args:
      placements: DiePlacement 列表 (n 个)
      G: 热导矩阵 (n×n)
      P_watts: 每 die 功耗 (n,)
      b_vec: 环境温度项 (n,)
      T_max: 温度上限 (K)
      T_ambient: 环境温度 (K)
    """
    n = len(placements)
    if n == 0:
        return plt.figure()

    T_vec = np.linalg.solve(G, P_watts + b_vec)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # 温度 → 颜色映射 (蓝冷 → 红热)
    norm = plt.Normalize(T_ambient - 5, T_max + 10)
    cmap = plt.cm.RdYlBu_r  # 蓝=冷, 红=热

    xs = [p.x for p in placements]
    ys = [p.y for p in placements]
    ws = [p.w for p in placements]
    hs = [p.h for p in placements]

    interposer_w = max(x + w for x, w in zip(xs, ws)) + 5
    interposer_h = max(y + h for y, h in zip(ys, hs)) + 5

    for i, p in enumerate(placements):
        T = T_vec[i]
        color = cmap(norm(T))
        rect = plt.Rectangle((p.x, p.y), p.w, p.h,
                              fill=True, facecolor=color,
                              edgecolor="black", linewidth=1.2)
        ax.add_patch(rect)

        # 标注
        margin = T_max - T
        ax.text(p.x + p.w / 2, p.y + p.h / 2 + 1.5,
                f"{p.id}", ha="center", fontsize=9, fontweight="bold")
        ax.text(p.x + p.w / 2, p.y + p.h / 2 - 1.5,
                f"T={T:.0f}K\nΔ={margin:+.0f}K\nP={P_watts[i]:.1f}W",
                ha="center", fontsize=7, color="#37474F")

    # G 矩阵标注: 每行/列对应哪个 die
    info_lines = [
        f"G: {n}×{n}  cond={np.linalg.cond(G):.0f}",
        f"T_amb={T_ambient:.0f}K  T_max={T_max:.0f}K",
        f"ΣP={sum(P_watts):.1f}W",
        f"T_max={max(T_vec):.0f}K  T_min={min(T_vec):.0f}K  ΔT={max(T_vec)-min(T_vec):.1f}K",
    ]
    ax.text(0.02, 0.98, "\n".join(info_lines),
            transform=ax.transAxes, fontsize=7, color="#37474F",
            verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", fc="white", ec="#CFD8DC", alpha=0.9))

    # colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Temperature (K)", fontsize=9)
    cbar.ax.axhline(T_max, color="red", linewidth=1.5, linestyle="--")
    cbar.ax.text(1.5, T_max, f"T_max={T_max:.0f}K", fontsize=7, color="red")

    ax.set_xlim(-3, interposer_w)
    ax.set_ylim(-3, interposer_h)
    ax.set_aspect("equal")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title(title, fontsize=12, fontweight="bold")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=200, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        print(f"  -> {save_path}")
    return fig
