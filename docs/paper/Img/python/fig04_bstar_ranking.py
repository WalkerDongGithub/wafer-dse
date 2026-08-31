"""Fig. 4 (data): B* ranking under thermal constraints (insight 2, Sec 5.3).

Core conclusion: within each port-count group, feasible configurations are
ranked by the QoS-assured rated bandwidth B* (same settings, same port
count); the ranking is stable across parameter sets (Spearman rho = 1.0,
data-report E1). Honest annotation: under ucie-32g the thermal scenario
dominates -- B* is ~4-5% of the bump-only tier (24x thermal decay,
binding constraints are almost all therm_*), so the ranking shown is the
thermal-constrained ranking.

Source: exp/output/matrix_<params>.csv (DataSteward), scenario
perf+bump+therm.
Outputs: docs/paper/Img/fig04_bstar_ranking.{pdf,svg,png}
"""
from __future__ import annotations

import os

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

PARAMS = ["ucie-16g", "ucie-24g", "ucie-32g"]
COLORS = ["#B9C4D8", "#6C8CC9", "#1A73E8"]
TOPO_ORDER = ["FullMesh(2)", "FullMesh(3)", "Mesh(2)", "Dragonfly(2,1,1)",
              "KaryNCube(2,3)", "Mesh(3)", "Dragonfly(2,2,1)", "Mesh(4)"]
# port-count group boundaries (topo order indices) for x-axis grouping
GROUPS = [("2", [0]), ("3", [1]), ("4", [2]), ("6", [3]),
          ("8", [4]), ("9", [5]), ("12", [6]), ("16", [7])]

data = {}
for ps in PARAMS:
    df = pd.read_csv(os.path.join(EXP, f"matrix_{ps}.csv"))
    df = df[df["scenario"] == "perf+bump+therm"]
    df["B_star"] = pd.to_numeric(df["B_star"], errors="coerce")
    data[ps] = {r["topo"]: r["B_star"] for _, r in df.iterrows()}

fig, ax = plt.subplots(figsize=(7.16, 2.7))
fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.24)

x = np.arange(len(TOPO_ORDER))
width = 0.26
for k, ps in enumerate(PARAMS):
    vals = [data[ps].get(t, np.nan) for t in TOPO_ORDER]
    ax.bar(x + (k - 1) * width, [v / 1000 for v in vals], width,
           color=COLORS[k], label=ps)

ax.set_xticks(x)
ax.set_xticklabels(TOPO_ORDER, fontsize=6)
ax.set_ylabel(r"$B^{*}$ (Gbps)", fontsize=7)
ax.tick_params(labelsize=6)
ax.set_ylim(0, 60)
ax.legend(fontsize=6, frameon=False, title="parameter set", title_fontsize=6,
          loc="upper right")

# port-count group labels above the axes (outside the plot area)
for label, idxs in GROUPS:
    mid = np.mean([i for i in idxs])
    ax.text(mid, 1.03, label, ha="center", va="bottom", fontsize=5.5,
            color="#5F6368", transform=ax.transAxes)
ax.text(-0.13, 1.03, "ports:", ha="right", va="bottom", fontsize=5.5,
        color="#5F6368", transform=ax.transAxes)

# honest annotation: thermal-dominated (24x decay), outside the axes
fig.text(0.985, 0.035,
         "thermal-dominated: B* = ~4-5% of bump tier (24x decay); binding = therm_*",
         ha="right", va="bottom", fontsize=5.5, color="#B45309", style="italic")

out = os.path.join(OUT, "fig04_bstar_ranking")
fig.savefig(f"{out}.pdf")
fig.savefig(f"{out}.svg")
fig.savefig(f"{out}.png", dpi=600)
print(f"saved {out}.pdf / .svg / .png")
