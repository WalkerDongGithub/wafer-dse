"""布局可视化 —— 调试用，非核心功能."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def plot_placement(
    solution,
    *,
    title: str = "Interposer Placement",
    save_path: str | None = None,
):
    """绘制 die 在 interposer 上的布局."""
    positions = solution.positions
    if not positions:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # 按 group 着色
    colors = plt.cm.Set2.colors
    group_ids = sorted(set(p.spec.group_id for p in positions))

    for p in positions:
        c = colors[p.spec.group_id % len(colors)]
        rect = plt.Rectangle((p.x, p.y), p.spec.width_mm, p.spec.height_mm,
                              fill=True, facecolor=c, alpha=0.5,
                              edgecolor="black", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(p.cx, p.cy, f"{p.label}\n[{p.row},{p.col}]",
                ha="center", va="center", fontsize=8, fontweight="bold")

    # interposer 框
    ax.add_patch(plt.Rectangle(
        (0, 0), solution.interposer_width_mm, solution.interposer_height_mm,
        fill=False, edgecolor="gray", linewidth=2, linestyle="--"))

    ax.set_xlim(-5, solution.interposer_width_mm + 5)
    ax.set_ylim(-5, solution.interposer_height_mm + 5)
    ax.set_aspect("equal")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title(title)

    # 图例
    legend_items = []
    for gid in group_ids:
        c = colors[gid % len(colors)]
        legend_items.append(
            mpatches.Patch(facecolor=c, alpha=0.5, label=f"group {gid}"))
    ax.legend(handles=legend_items, fontsize=8, loc="upper right")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  -> {save_path}")
    return fig
