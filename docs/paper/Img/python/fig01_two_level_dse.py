"""Fig. 1 (concept, v0.2): Two-Level DSE framework overview.

Per DomainExpert figure-intents v0.2 (2026-08-21) + s4-model.md Sec 4.0:
vertical three-stage layout centered on the design of a SINGLE INTERPOSER —
design-space input (4 boxes, cartesian product) -> outer discrete
enumeration layer (reusing mature chiplet DSE flows, NP-hard) ->
physical-parameter interface (decoupling band) -> inner feasibility model
for a given configuration (coupling performance/thermal/electrical/
geometric; with a dashed expansion-ratio envelope side box as topological
invariant) -> optimal rated bandwidth B* with rank-and-screen feedback.

Terminology follows terminology-ledger.md v0.3 (two-level DSE; rated
bandwidth B with a QoS guarantee; expansion-ratio envelope).

FORBIDDEN by spec: no "LP"/"linear programming" wording, no bisection
diagram, no Pareto front, no whole-wafer view (single-interposer focus).

Outputs: docs/paper/Img/fig01_two_level_dse.{pdf,svg,png}
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

W, H = 7.16, 4.42            # full-width ISCA, 7.16/4.42 = 1.620 ~ golden
MX = 0.35
fig, ax = fc.new_fig(W, H)

texts: list[tuple[str, object]] = []
containers: list[tuple[str, object, str, tuple[float, float, float, float]]] = []


def reg(name: str, t: object) -> object:
    texts.append((name, t))
    return t


def box(name: str, t: object, bname: str, bbox: tuple[float, float, float, float]) -> None:
    texts.append((name, t))
    containers.append((name, t, bname, bbox))


# ---- 1. design space input --------------------------------------------------
reg("tag1", fc.txt(ax, 0.50, 4.20, "\u2460 design space input (discrete)",
                   size=6.5, color=fc.INK2, ha="left"))
in_xs = [0.50, 2.06, 3.62, 5.18]
in_w, in_h, in_y = 1.44, 0.52, 3.62
in_defs = [
    ("Topology family", ["Mesh \u00b7 Torus \u00b7 KNCube", "FullMesh \u00b7 Dragonfly"]),
    ("Layout", ["die placement"]),
    ("Packaging", ["2.5D / 3D, RDL"]),
    ("Interconnect", ["UCIe \u00b7 OIF-CEI"]),
]
for i, (x0, (title, body)) in enumerate(zip(in_xs, in_defs)):
    bb = (x0, in_y, x0 + in_w, in_y + in_h)
    fc.rbox(ax, *bb, fc=fc.BLUE_L, ec=fc.BLUE, lw=1.0)
    cx = x0 + in_w / 2
    box(f"in{i}.t", fc.txt(ax, cx, 3.96, title, size=7, weight="bold"), f"in{i}", bb)
    for j, line in enumerate(body):
        box(f"in{i}.b{j}", fc.txt(ax, cx, 3.78 - 0.14 * j, line, size=6), f"in{i}", bb)
for gx in (2.00, 3.56, 5.12):
    reg(f"times{gx}", fc.txt(ax, gx, 3.84, "\u00d7", size=7.5, color=fc.INK2))
fc.arrow(ax, 3.58, 3.62, 3.58, 3.54, color=fc.GRAY, lw=1.2)

# ---- 2. outer discrete enumeration layer ------------------------------------
outer = (MX, 3.00, W - MX, 3.52)
fc.rbox(ax, *outer, fc="white", ec=fc.BLUE, lw=1.4)
box("out.tag", fc.txt(ax, 0.50, 3.46, "\u2461 outer discrete enumeration layer",
                      size=6.5, color=fc.INK2, ha="left"), "outer", outer)
box("out.sub", fc.txt(ax, 3.58, 3.28,
                      "reuses mature chiplet DSE flows (RapidChiplet / FireLink / FPIA) \u00b7 NP-hard",
                      size=7), "outer", outer)
fc.rbox(ax, 6.10, 3.16, 0.56, 0.20, fc=fc.BLUE, ec=fc.BLUE, lw=0.8)
box("ins1", fc.txt(ax, 6.38, 3.26, "insight 1", size=6.5, color="white"),
    "ins1-box", (6.10, 3.16, 6.66, 3.36))

# ---- 3. physical-parameter interface ----------------------------------------
ibar = (MX, 2.56, W - MX, 2.98)
fc.rbox(ax, *ibar, fc=fc.GRAY_L, ec=fc.GRAY, lw=1.0)
box("if.l1", fc.txt(ax, 3.58, 2.90, "\u2462 physical-parameter interface \u2014 decoupled",
                    size=7, color=fc.INK2), "ibar", ibar)
box("if.l2", fc.txt(ax, 3.58, 2.72,
                    "passes only physical parameters (die size \u00b7 pitch \u00b7 thermal resistance \u00b7 power coefficients)",
                    size=6, color=fc.INK2), "ibar", ibar)
fc.arrow(ax, 0.60, 3.00, 0.60, 2.56, color=fc.GRAY, lw=1.4)
fc.arrow(ax, 6.56, 2.56, 6.56, 3.00, color=fc.GRAY, lw=1.0)
box("if.down", fc.txt(ax, 0.72, 2.84, "configuration + physical parameters",
                      size=6, color=fc.INK2, ha="left"), "ibar", ibar)
box("if.up", fc.txt(ax, 6.44, 2.84, "B* \u2192 rank & screen (insight 1)",
                    size=6, color=fc.INK2, ha="right"), "ibar", ibar)

# ---- 4. inner feasibility model (single interposer focus) -------------------
inner = (MX, 0.55, W - MX, 2.56)
fc.rbox(ax, *inner, fc="white", ec=fc.AMBER, lw=1.4)
box("in.tag", fc.txt(ax, 0.50, 2.48,
                     "\u2463 inner feasibility model for a given configuration",
                     size=6.5, color=fc.INK2, ha="left"), "inner", inner)

# single interposer schematic (the design object: die array + interposer +
# substrate boundary), per round 21+ directive [3]
box("si.lab", fc.txt(ax, 0.55, 2.18, "single interposer", size=6.5, weight="bold", ha="left"),
    "si", (0.50, 0.85, 2.30, 2.30))
for cx0 in (0.62, 0.98, 1.34):
    fc.rbox(ax, cx0, 1.62, 0.30, 0.24, fc="white", ec=fc.BLUE, lw=1.0, r=0.03)
fc.arrow(ax, 0.92, 1.74, 0.98, 1.74, color=fc.BLUE, lw=1.0, ms=7)
fc.arrow(ax, 1.28, 1.74, 1.34, 1.74, color=fc.BLUE, lw=1.0, ms=7)
fc.rbox(ax, 0.55, 1.36, 1.70, 0.20, fc=fc.AMBER_L, ec=fc.AMBER, lw=1.0, r=0.02)
fc.rbox(ax, 0.55, 1.08, 1.70, 0.20, fc=fc.GRAY_L, ec=fc.GRAY, lw=0.8, r=0.02, ls="--")
reg("sub-b", fc.txt(ax, 0.55, 0.94, "substrate boundary", size=6, color=fc.INK2, ha="left"))

# four constraint families coupled in one model
reg("cp.t", fc.txt(ax, 2.45, 2.10, "couples in one model", size=6.5, weight="bold", ha="left"))
for j, line in enumerate(["performance", "thermal", "electrical", "geometric \u00b7 (insight 4)"]):
    reg(f"cp.b{j}", fc.txt(ax, 2.45, 1.90 - 0.18 * j, line, size=6, ha="left"))

# expansion-ratio envelope: dashed side box, topological invariant (insight 6)
env_b = (4.60, 1.85, 6.66, 2.50)
fc.rbox(ax, *env_b, fc="white", ec=fc.BLUE, lw=1.0, ls="--")
box("env.t", fc.txt(ax, 5.63, 2.40, "expansion-ratio envelope",
                    size=6.5, weight="bold"), "env", env_b)
for j, line in enumerate(["topological invariant \u00b7", "independent of B, physics", "(insight 6)"]):
    box(f"env.b{j}", fc.txt(ax, 5.63, 2.22 - 0.14 * j, line, size=6), "env", env_b)

# output: optimal rated bandwidth B* (right-lower), screening loop
outb = (4.60, 0.75, 6.66, 1.75)
fc.rbox(ax, *outb, fc=fc.GREEN_L, ec=fc.GREEN, lw=1.2)
box("out.t", fc.txt(ax, 5.63, 1.58, "B* \u2014 optimal rated bandwidth", size=7.5, weight="bold"),
    "out", outb)
box("out.b0", fc.txt(ax, 5.63, 1.40, "with a QoS guarantee", size=6.5), "out", outb)
box("out.b1", fc.txt(ax, 5.63, 1.18, "rank by B* \u2192 designer", size=6.5), "out", outb)
box("out.b2", fc.txt(ax, 5.63, 1.02, "evaluates point-by-point (insight 5)", size=6.5), "out", outb)

# ---- computed-aesthetic reports + QA ----------------------------------------
fc.contrast_report([
    ("band-title-on-blue", "white", fc.BLUE),
    ("input-fill-blue", fc.INK, fc.BLUE_L),
    ("inner-fill-amber", fc.INK, fc.AMBER_L),
    ("output-fill-green", fc.INK, fc.GREEN_L),
    ("secondary-on-white", fc.INK2, "white"),
])
fc.golden_report("canvas W/H", W / H)
fc.run_qa("fig01v2", ax, texts, (0, 0, W, H), containers)
out = os.path.join(os.path.dirname(__file__), "..", "fig01_two_level_dse")
fig.savefig(f"{out}.pdf")                                # exact 7.16x4.42 in canvas
fig.savefig(f"{out}.svg")                                # editable preview
fig.savefig(f"{out}.png", dpi=600)                       # preview raster
print(f"saved {out}.pdf / {out}.svg / {out}.png")
