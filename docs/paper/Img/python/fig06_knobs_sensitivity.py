"""Fig. 6 (data): B = f(requirement, constraint) two-knob monotonicity
(insight 3, Sec 5.5) + sensitivity knob-unlocking ranking (E8).

Panel (a): geometric-mean B* up-shift over the 7-topology subset per
scenario tier, for the default mode (requirement knob: egress_peak vs
QoS ref -> ~2.64x, structure-backed by single-pair envelope <= 1 vs
doubly-stochastic worst case ~2) and the beta_P=0.05 mode (constraint
knob: rated vs peak -> 17.9-28.6x, peak-power term dominates).

Panel (b): sensitivity per knob (5% improvement) in therm-bound domains:
R_vert > beta_P > ppl unlock bandwidth (more cooling / lower power beat
link tuning); in the C4-pad wiring-bound domain (Dragonfly-wiring) no
smooth knob unlocks B* (discrete grid effect, per E8 report).

Source: exp/output/knob_matrix_<params>.csv, exp/output/sensitivity_ucie-32g.csv.
Outputs: docs/paper/Img/fig06_knobs_sensitivity.{pdf,svg,png}
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

# ---- panel (a): two-knob up-shift (GM over topologies, per mode x tier) ----
tiers = ["ref", "egress_peak", "rated", "egress_peak_rated"]
frames = [pd.read_csv(os.path.join(EXP, f"knob_matrix_{ps}.csv")) for ps in
          ["ucie-16g", "ucie-24g", "ucie-32g"]]
knob = pd.concat(frames)
knob["B_star_ratio_vs_ref"] = pd.to_numeric(knob["B_star_ratio_vs_ref"], errors="coerce")
gm = knob.groupby(["mode", "scenario"])["B_star_ratio_vs_ref"].apply(
    lambda s: np.exp(np.mean(np.log(s)))).unstack()

fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.7))
fig.subplots_adjust(left=0.09, right=0.985, top=0.84, bottom=0.25, wspace=0.30)

x = np.arange(len(tiers))
w = 0.34
for k, mode in enumerate(["default", "beta_p0.05"]):
    vals = [gm.loc[mode, t] if t in gm.columns else np.nan for t in tiers]
    axes[0].plot(x, vals, "o-", color=["#1A73E8", "#B45309"][k], lw=1.4, ms=4,
                 label={"default": "requirement knob (default)",
                        "beta_p0.05": "constraint knob ($\\beta_P{=}0.05$)"}[mode])
    for xi, v in zip(x, vals):
        if not np.isnan(v) and v > 1.05:
            axes[0].annotate(f"{v:.2g}x", (xi, v), textcoords="offset points",
                             xytext=(0, 4), ha="center", fontsize=5)
axes[0].set_xticks(x)
axes[0].set_xticklabels(["ref\n(QoS)", "egress\npeak", "rated", "peak\\\nrated"],
                        fontsize=6)
axes[0].set_ylabel("GM B* up-shift (x ref)", fontsize=6.5)
axes[0].tick_params(labelsize=6)
axes[0].set_yscale("log")
axes[0].set_ylim(0.5, 100)
axes[0].legend(fontsize=5.5, frameon=False, loc="upper left")
axes[0].set_title("(a) two-knob monotonicity (insight 3)", fontsize=7)

# ---- panel (b): sensitivity knob-unlocking (therm-bound domains) ----
sen = pd.read_csv(os.path.join(EXP, "sensitivity_ucie-32g.csv"))
sen["dPct"] = 100 * (sen["resolve_5pct"] - sen["B_star_base"]) / sen["B_star_base"]
dom = {"Mesh(3)-therm": "#1A73E8", "Dragonfly-therm": "#188038"}
x2 = np.arange(4)
knob_names = ["R_vert(-)", "beta_P(-)", "ppl(-)", "lanes_per_mm(+)"]
for dp, color in dom.items():
    sub = sen[sen["design_point"] == dp].set_index("knob")
    vals = [sub.loc[f"{k}(-)" if k != "lanes_per_mm(+)" else k, "dPct"]
            if (f"{k}(-)" if k != "lanes_per_mm(+)" else k) in sub.index else 0.0
            for k in ["R_vert", "beta_P", "ppl", "lanes_per_mm"]]
    axes[1].plot(x2, vals, "o-", color=color, lw=1.3, ms=4, label=dp)
axes[1].set_xticks(x2)
axes[1].set_xticklabels(["$R_{vert}$", "$\\beta_P$", "$p_{lane}$", "wiring\ncap."], fontsize=6)
axes[1].set_ylabel(r"$\Delta B^{*}$ per 5% knob improvement (%)", fontsize=6, labelpad=10)
axes[1].tick_params(labelsize=6)
axes[1].set_ylim(-1, 8)
axes[1].legend(fontsize=5.5, frameon=False, loc="upper left")
axes[1].set_title("(b) knob unlocking (insight 5)", fontsize=7)
axes[1].text(0.98, -1.9, "C4-pad wiring-bound domain: no smooth knob unlocks",
             ha="right", fontsize=5, color="#5F6368", style="italic")

out = os.path.join(OUT, "fig06_knobs_sensitivity")
fig.savefig(f"{out}.pdf")
fig.savefig(f"{out}.svg")
fig.savefig(f"{out}.png", dpi=600)
print(f"saved {out}.pdf / .svg / .png")
