"""Fig. 2 (concept, v0.2): Three-layer physical hierarchy and cross-layer
coupling C1-C4, with the standard coupling case (power-cooling-wiring/
performance triad).

Per DomainExpert figure-intents v0.2 (2026-08-21) + s4-model.md Sec 4.2.2 +
terminology-ledger.md v0.3: vertical three-layer stack (die / interposer /
substrate), numbered cross-layer coupling annotations C1-C4, an emphasized
"first-class constraints" box (v5.21: wiring saturation + die-area upper
bound bind before the bump budget), a dashed expansion-ratio envelope side
box (topological invariant, insight 6), and the power-cooling-wiring/
performance triad ring (author round 21+ directive [1]).

FORBIDDEN by spec: no concrete numeric values, no temperature contour
plots, no G/M matrices (math details go to the appendix).

Outputs: docs/paper/Img/fig02_three_layer_coupling.{pdf,svg,png}
"""
from __future__ import annotations

import os
import sys

import matplotlib as mpl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fig_common as fc

# Self-contained rcParams (same values as fig_common.setup_rc; kept inline so
# the static preflight can audit this script on its own).
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
    "svg.fonttype": "none",           # editable text in SVG
    "pdf.fonttype": 42,               # editable TrueType text in PDF
    "font.size": 8,
    "mathtext.fontset": "dejavusans",
})

W, H = 7.16, 4.42
fig, ax = fc.new_fig(W, H)

texts: list[tuple[str, object]] = []
containers: list[tuple[str, object, str, tuple[float, float, float, float]]] = []


def reg(name: str, t: object) -> object:
    texts.append((name, t))
    return t


def box(name: str, t: object, bname: str, bbox: tuple[float, float, float, float]) -> None:
    texts.append((name, t))
    containers.append((name, t, bname, bbox))


def dot_row(y: float, r: float, n: int, x0: float = 0.62, step: float = 0.21) -> None:
    for k in range(n):
        ax.add_patch(fc.Circle((x0 + step * k, y), r, fc=fc.GRAY, ec="none", zorder=3))


# ---- three-layer stack ------------------------------------------------------
die_b = (0.50, 3.10, 3.00, 4.05)
fc.rbox(ax, *die_b, fc=fc.BLUE_L, ec=fc.BLUE, lw=1.2)
for cx0 in (0.60, 1.07, 1.54):
    fc.rbox(ax, cx0, 3.30, 0.42, 0.42, fc="white", ec=fc.BLUE, lw=1.0, r=0.04)
fc.arrow(ax, 1.02, 3.51, 1.07, 3.51, color=fc.BLUE, lw=1.2, ms=7)
fc.arrow(ax, 1.49, 3.51, 1.54, 3.51, color=fc.BLUE, lw=1.2, ms=7)
box("d2d", fc.txt(ax, 1.35, 3.92, "D2D (UCIe)", size=6, color=fc.INK2), "die", die_b)
for j, line in enumerate(["die level:", "power \u00b7 temperature", "\u03bcbump \u00b7 area bound"]):
    box(f"die.a{j}", fc.txt(ax, 2.05, 3.80 - 0.14 * j, line, size=6, ha="left"), "die", die_b)

dot_row(3.02, 0.025, 9)
reg("ub-label", fc.txt(ax, 3.04, 3.02, "\u03bcbump", size=6, ha="left"))

int_b = (0.50, 2.30, 3.00, 2.98)
fc.rbox(ax, *int_b, fc=fc.AMBER_L, ec=fc.AMBER, lw=1.2)
box("int.t", fc.txt(ax, 0.65, 2.76, "Interposer", size=7, weight="bold", ha="left"), "int", int_b)
box("int.b0", fc.txt(ax, 0.65, 2.56, "RDL wiring: power/gnd +", size=6, ha="left"), "int", int_b)
box("int.b1", fc.txt(ax, 0.65, 2.42, "signal shared \u00b7 C4 out", size=6, ha="left"), "int", int_b)

dot_row(2.22, 0.035, 9)
reg("c4-label", fc.txt(ax, 3.04, 2.22, "C4 bumps", size=6, ha="left"))

sub_b = (0.50, 1.35, 3.00, 2.18)
fc.rbox(ax, *sub_b, fc=fc.PURPLE_L, ec=fc.PURPLE, lw=1.2)
box("sub.t", fc.txt(ax, 0.65, 1.92, "Substrate", size=7, weight="bold", ha="left"), "sub", sub_b)
box("sub.b0", fc.txt(ax, 0.65, 1.66, "I2I SerDes \u00b7 mount-point", size=6, ha="left"), "sub", sub_b)
box("sub.b1", fc.txt(ax, 0.65, 1.52, "temperature", size=6, ha="left"), "sub", sub_b)

# coupling mini-arrows on the stack (C3 down, C4 up), per spec directions
fc.arrow(ax, 2.62, 3.10, 2.62, 2.98, color=fc.GRAY, lw=1.2, ms=7)
fc.arrow(ax, 2.62, 2.18, 2.62, 2.30, color=fc.GRAY, lw=1.2, ms=7)

# ---- C1-C4 annotation boxes (right column, compact rows) --------------------
def cbox(key: str, y0: float, title: str, body: str, color: str,
         arrow_to: tuple[float, float]) -> None:
    y1 = y0 + 0.60
    bb = (3.40, y0, 5.60, y1)
    fc.rbox(ax, *bb, fc="white", ec=color, lw=1.2)
    box(f"{key}.t", fc.txt(ax, 3.50, y0 + 0.42, title, size=7, weight="bold", ha="left"),
        key, bb)
    box(f"{key}.b", fc.txt(ax, 3.50, y0 + 0.20, body, size=6, ha="left"), key, bb)
    return bb


c1_b = cbox("c1", 3.36, "C1 \u00b7 \u03bcbump cross-layer allocation",
            "I2I lanes squeeze D2D \u03bcbump budget", fc.BLUE, (3.00, 3.66))
fc.arrow(ax, 3.40, 3.66, 3.00, 3.66, color=fc.BLUE, lw=1.2)
c3_b = cbox("c3", 2.70, "C3 \u00b7 die power \u2193 inter power",
            "die power \u2192 interposer total power", fc.AMBER, (3.00, 2.90))
fc.arrow(ax, 3.40, 2.90, 3.00, 2.90, color=fc.AMBER, lw=1.2)
c2_b = cbox("c2", 2.04, "C2 \u00b7 inter power \u2192 C4 count",
            "inter power sets the power C4 count", fc.PURPLE, (3.00, 2.22))
fc.arrow(ax, 3.40, 2.30, 3.00, 2.22, color=fc.PURPLE, lw=1.2)
c4_b = cbox("c4", 1.38, "C4 \u00b7 sub temp \u2191 inter ambient",
            "sub temp sets interposer ambient", fc.GRAY, (3.00, 1.68))
fc.arrow(ax, 3.40, 1.68, 3.00, 1.68, color=fc.GRAY, lw=1.2)

# ---- envelope side box (dashed, insight 6) ----------------------------------
env_b = (5.70, 1.44, 6.66, 4.02)
fc.rbox(ax, *env_b, fc="white", ec=fc.BLUE, lw=1.0, ls="--")
box("env.t", fc.txt(ax, 6.18, 3.86, "Envelope L*", size=7, weight="bold"), "env", env_b)
for j, line in enumerate(["topological invariant", "independent of",
                          "B and physics", "pre-solved once", "(insight 6)"]):
    box(f"env.b{j}", fc.txt(ax, 6.18, 3.62 - 0.18 * j, line, size=6), "env", env_b)

# ---- bottom band: first-class constraints (left) + coupling triad (right) ---
fc_box = (0.50, 0.22, 3.30, 1.34)
fc.rbox(ax, *fc_box, fc=fc.GREEN_L, ec=fc.GREEN, lw=2.0)
box("fc.t", fc.txt(ax, 1.90, 1.14, "\u2605 First-class constraints",
                   size=6.5, weight="bold"), "fc", fc_box)
for j, line in enumerate(["wiring saturation +", "die-area upper bound", "bind before the bump budget"]):
    box(f"fc.b{j}", fc.txt(ax, 1.90, 0.92 - 0.17 * j, line, size=6), "fc", fc_box)

triad = (3.40, 0.22, 6.66, 1.34)
fc.rbox(ax, *triad, fc="white", ec=fc.GRAY, lw=1.0)
reg("tr.lab", fc.txt(ax, 3.50, 1.22, "power\u2013cooling\u2013wiring/performance triad",
                     size=6.5, weight="bold", ha="left"))
# triad nodes (triangle) with directional arrows: power -> wiring ->
# cooling/bandwidth -> power (mutual coupling ring)
fc.rbox(ax, 3.55, 0.80, 1.00, 0.26, fc=fc.GRAY_L, ec=fc.GRAY, lw=1.0, r=0.04)
reg("tr.pw", fc.txt(ax, 4.05, 0.93, "P/G routing", size=6))
fc.rbox(ax, 5.30, 0.80, 1.00, 0.26, fc=fc.GRAY_L, ec=fc.GRAY, lw=1.0, r=0.04)
reg("tr.ws", fc.txt(ax, 5.80, 0.93, "wiring saturation", size=6))
fc.rbox(ax, 4.55, 0.36, 1.50, 0.26, fc=fc.GRAY_L, ec=fc.GRAY, lw=1.0, r=0.04)
reg("tr.cb", fc.txt(ax, 5.30, 0.49, "cooling / bandwidth", size=6))
fc.arrow(ax, 4.55, 0.93, 5.30, 0.93, color=fc.GRAY, lw=1.2, ms=8)
fc.arrow(ax, 5.55, 0.80, 5.45, 0.62, color=fc.GRAY, lw=1.2, ms=8)
fc.arrow(ax, 4.85, 0.62, 4.35, 0.80, color=fc.GRAY, lw=1.2, ms=8)

reg("footer", fc.txt(ax, 3.58, 0.13,
                     "thermal \u00b7 electrical \u00b7 geometric \u00b7 performance coupled in one model (insight 4)",
                     size=6, color=fc.INK2))

# ---- computed-aesthetic reports + QA ----------------------------------------
fc.contrast_report([
    ("die-band-blue", fc.INK, fc.BLUE_L),
    ("inter-band-amber", fc.INK, fc.AMBER_L),
    ("sub-band-purple", fc.INK, fc.PURPLE_L),
    ("fc-fill-green", fc.INK, fc.GREEN_L),
    ("triad-node-gray", fc.INK, fc.GRAY_L),
])
fc.golden_report("canvas W/H", W / H)
fc.run_qa("fig02v2", ax, texts, (0, 0, W, H), containers)
out = os.path.join(os.path.dirname(__file__), "..", "fig02_three_layer_coupling")
fig.savefig(f"{out}.pdf")                                # exact 7.16x4.42 in canvas
fig.savefig(f"{out}.svg")                                # editable preview
fig.savefig(f"{out}.png", dpi=600)                       # preview raster
print(f"saved {out}.pdf / {out}.svg / {out}.png")
