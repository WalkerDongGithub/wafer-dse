"""Fig. 3 (data): expansion-ratio envelope invariance (insight 6, Sec 5.2).

Core conclusion: the per-link expansion-ratio envelope L* depends only on
topology + routing + requirement model; it is independent of B and of
physical parameters. For each of 5 topologies, the envelope curves over
4 physical parameter sets (toy / ucie-16g / ucie-24g / ucie-32g) coincide
exactly (measured max |dL*| = 0, data-report E5).

Source: exp/output/envelope_<topo>.csv (DataSteward).
Outputs: docs/paper/Img/fig03_envelope_invariance.{pdf,svg,png}
"""
from __future__ import annotations

import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), "..")
EXP = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "exp", "output")

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 7,
    "axes.linewidth": 0.8,
})

TOPO = ["Mesh(3)", "Torus(3)", "FullMesh(3)", "Dragonfly(2,1,1)", "KaryNCube(2,3)"]
PARAM_SETS = ["toy", "ucie-16g", "ucie-24g", "ucie-32g"]
COLORS = ["#1A73E8", "#B45309", "#188038", "#9334E6"]

fig, axes = plt.subplots(1, 5, figsize=(7.16, 2.35), sharey=True)
fig.subplots_adjust(left=0.07, right=0.985, top=0.86, bottom=0.24, wspace=0.14)

max_delta = 0.0
for ax, topo in zip(axes, TOPO):
    df = pd.read_csv(os.path.join(EXP, f"envelope_{topo}.csv"))
    for ps, color in zip(PARAM_SETS, COLORS):
        ax.plot(df["link_idx"], df[ps], color=color, lw=1.4,
                label=ps if topo == TOPO[0] else None)
    d = max(abs(df[PARAM_SETS[0]] - df[ps]).max() for ps in PARAM_SETS[1:])
    max_delta = max(max_delta, d)
    ax.set_title(topo, fontsize=7)
    ax.tick_params(labelsize=6)
    ax.set_xlabel("link index", fontsize=6.5, labelpad=6)

axes[0].set_ylabel(r"$L^{*}$ (expansion-ratio envelope)", fontsize=6.5)
axes[0].legend(fontsize=5.5, loc="upper right", frameon=False,
               title="4 physical param. sets", title_fontsize=5.5)
for ax in axes[1:]:
    ax.set_yticklabels([])

print(f"max |dL*| across all topologies: {max_delta:.2e}")

out = os.path.join(OUT, "fig03_envelope_invariance")
fig.savefig(f"{out}.pdf")
fig.savefig(f"{out}.svg")
fig.savefig(f"{out}.png", dpi=600)
print(f"saved {out}.pdf / .svg / .png")
