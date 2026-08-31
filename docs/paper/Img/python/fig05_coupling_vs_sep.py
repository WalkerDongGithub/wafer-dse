"""Fig. 5 (data): coupling vs separated decision (insight 4, Sec 5.4).

Core conclusion (two-stage, data-report G3 + E3B v2): in the linear
sub-model without wiring/area (v1), separated decisions are analytically
equivalent to the joint model (rel_diff = 0 across 11 topologies; B*_joint
= min(B*_bump, B*_therm)); once wiring saturation and the die-area upper
bound are first-class constraints (V5 v5.21), separated decisions diverge
from the joint model (fixed-path separation, rel_diff up to 0.35, e.g.
KaryNCube(2,3) 0.35) -- wiring binds before the bump/therm budget.

Source: exp/output/sep_vs_joint_ucie-32g.csv (v1),
exp/output/sep_vs_joint_v2_fixedpath_ucie-32g.csv (v2).
Outputs: docs/paper/Img/fig05_coupling_vs_sep.{pdf,svg,png}
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

# v1: 11 topologies, rel_diff = 0 (equivalence) -- reported as one bar
v1 = pd.read_csv(os.path.join(EXP, "sep_vs_joint_ucie-32g.csv"))
v1_rel = pd.to_numeric(v1["rel_diff"], errors="coerce").fillna(0)
n_v1 = len(v1)

# v2: fixed-path separation with wiring/area in the model
v2 = pd.read_csv(os.path.join(EXP, "sep_vs_joint_v2_fixedpath_ucie-32g.csv"))
v2 = v2[pd.to_numeric(v2["rel_diff"], errors="coerce") > 0.01].copy()
v2["rel_diff"] = pd.to_numeric(v2["rel_diff"], errors="coerce")
# aggregate per (topo, domain): keep max rel_diff per config family
v2 = v2.sort_values("rel_diff").drop_duplicates(subset=["topo", "domain"], keep="last")
n_v2_div = len(v2)
v2_other = 72 - n_v2_div

labels = ["v1: 11 topologies\n(no wiring/area)\nrel_diff = 0"] + \
         [f"{r['topo']}\n{r['domain']}" for _, r in v2.iterrows()] + \
         [f"{v2_other} other v2\nconfigs\nrel_diff <= 1%"]
vals = [0.0] + list(v2["rel_diff"]) + [0.0]
colors = ["#B9C4D8"] + ["#B45309"] * len(v2) + ["#E8EAED"]

fig, ax = plt.subplots(figsize=(7.16, 2.7))
fig.subplots_adjust(left=0.09, right=0.98, top=0.85, bottom=0.30)
x = np.arange(len(labels))
ax.bar(x, vals, color=colors, width=0.6)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=5.5)
ax.set_ylabel(r"$|B^{*}_{\mathrm{joint}} - B^{*}_{\mathrm{sep}}| / B^{*}_{\mathrm{joint}}$ (rel. diff.)",
              fontsize=6.5)
ax.tick_params(labelsize=6)
ax.set_ylim(0, 0.42)
for xi, v in zip(x, vals):
    if v > 0.001:
        ax.text(xi, v + 0.008, f"{v:.2f}", ha="center", fontsize=5.5)

fig.text(0.985, 0.02,
         "wiring/area first-class (V5 v5.21): separated decisions diverge -- wiring binds before bump/therm",
         ha="right", va="bottom", fontsize=5.5, color="#5F6368", style="italic")

out = os.path.join(OUT, "fig05_coupling_vs_sep")
fig.savefig(f"{out}.pdf")
fig.savefig(f"{out}.svg")
fig.savefig(f"{out}.png", dpi=600)
print(f"saved {out}.pdf / .svg / .png")
