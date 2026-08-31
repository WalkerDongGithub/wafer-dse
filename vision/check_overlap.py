"""Pairwise bbox overlap checker for vision/examples/*.tex heat-flow figures.

Every element of a figure -- node boxes, edge segments, label texts -- gets a
bounding box and all boxes are tested pairwise for intersection. The layout
is declared here in tikz cm coordinates, identical to the .tex files (see
the build() function and the figure table). Text widths use a conservative
estimate of 0.55 em/char; if the estimate shows no collision, the real
render (usually narrower) cannot collide either.

Rules:
- edge segments vs their own endpoint nodes are excluded (edges leave from
  node anchors by construction);
- labels vs their own edge are excluded (labels intentionally sit on their
  edge); labels are checked against every OTHER edge;
- touching boxes (gap <= tol) are not collisions.

Usage:  python3 vision/check_overlap.py [fig...]
Figures: 2p5d / heatsink / 3d   (default: all)
"""
from __future__ import annotations

import sys

PT = 0.03528          # cm per pt
SMALL, SCRIPTSIZE = 10.0, 7.0
# Conservative em/char, calibrated against pdftotext -bbox measurements:
# scriptsize labels measure ~0.66 em/char, small node text ~0.45-0.5 em/char.
CHAR_W_SMALL = 0.55
CHAR_W_SCRIPT = 0.70
TOL = 0.02            # cm; touching within this gap is not a collision


def tw(s: str, pt: float, char_w: float = CHAR_W_SCRIPT) -> float:
    return len(s) * char_w * pt * PT


def th(nlines: int, pt: float) -> float:
    return nlines * 1.15 * pt * PT


def rect(cx: float, cy: float, w: float, h: float) -> tuple[float, float, float, float]:
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def seg_bbox(p1: tuple[float, float], p2: tuple[float, float]) -> tuple[float, float, float, float]:
    return (min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1]))


def boxes_overlap(a: tuple[float, float, float, float],
                  b: tuple[float, float, float, float], tol: float = TOL) -> bool:
    return not (a[2] <= b[0] + tol or b[2] <= a[0] + tol
                or a[3] <= b[1] + tol or b[3] <= a[1] + tol)


def seg_intersect(p1, p2, q1, q2) -> bool:
    """True if closed segments (p1,p2) and (q1,q2) intersect."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    d1, d2 = cross(p1, p2, q1), cross(p1, p2, q2)
    d3, d4 = cross(q1, q2, p1), cross(q1, q2, p2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    def on(o, a, b):
        return (min(a[0], b[0]) - 1e-9 <= o[0] <= max(a[0], b[0]) + 1e-9
                and min(a[1], b[1]) - 1e-9 <= o[1] <= max(a[1], b[1]) + 1e-9)
    return (abs(d1) < 1e-9 and on(q1, p1, p2)) or (abs(d2) < 1e-9 and on(q2, p1, p2)) \
        or (abs(d3) < 1e-9 and on(p1, q1, q2)) or (abs(d4) < 1e-9 and on(p2, q1, q2))


def seg_rect_intersect(p1, p2, r: tuple[float, float, float, float]) -> bool:
    """True if segment (p1,p2) touches rectangle r (inclusive)."""
    def in_rect(p):
        return r[0] - 1e-9 <= p[0] <= r[2] + 1e-9 and r[1] - 1e-9 <= p[1] <= r[3] + 1e-9
    if in_rect(p1) or in_rect(p2):
        return True
    corners = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
    return any(seg_intersect(p1, p2, corners[i], corners[(i + 1) % 4]) for i in range(4))


# --------------------------------------------------------------------------
# Layout (tikz cm coordinates; identical to the .tex files).
# --------------------------------------------------------------------------
CX = 3.7            # die/stack centers at +-CX
DIE_W_MIN, DIE_H = 3.2, 1.6
BND_CX, BND_CY = 0.0, -3.6
BND_W_MIN, BND_H = 3.0, 1.1


def build_2p5d(bnd_name: str, r_lab: str) -> dict:
    """One 2.5D figure's elements: die x2 + boundary, orthogonal edges.

    Edges are orthogonal polylines (no diagonals, v3): vertical_chain =
    die.south down, horizontal across, vertical down to the boundary top;
    face_adjacency stays a horizontal straight line.
    """
    die_txt = "die \u00d7 12 \u00d7 12 mm"
    bnd_txt = f"boundary \u00b7 300 K"
    inner = 2 * 0.333 * SMALL * PT      # TikZ default inner sep both sides (cm)
    n_w = max(DIE_W_MIN, tw(die_txt, SMALL, CHAR_W_SMALL) + inner)
    b_w = max(BND_W_MIN, tw(bnd_txt, SMALL, CHAR_W_SMALL) + inner)

    nodes = {
        "n0": rect(-CX, 0, n_w, DIE_H),
        "n1": rect(CX, 0, n_w, DIE_H),
        "bnd": rect(BND_CX, BND_CY, b_w, BND_H),
    }
    e = n_w / 2                          # die half width -> face_adjacency ends
    bend_y = -2.0                        # horizontal routing level
    bnd_top = BND_CY + BND_H / 2         # boundary top y (ellipse bbox)
    tip_y = bnd_top - 0.05               # vertical segment tip, just at the ellipse top
    edges = {
        "fa": [(-CX + e, 0.0), (CX - e, 0.0)],
        "vc0": [(-CX, -DIE_H / 2), (-CX, bend_y), (-1.0, bend_y), (-1.0, tip_y)],
        "vc1": [(CX, -DIE_H / 2), (CX, bend_y), (1.0, bend_y), (1.0, tip_y)],
    }
    h_lab = th(1, SCRIPTSIZE)
    labels = {
        "fa_type": rect(0.0, h_lab / 2,
                        tw("conduction (Fourier)", SCRIPTSIZE), h_lab),
        "fa_par": rect(0.0, -h_lab / 2,
                       tw("k=150 W/mK \u00b7 t=0.1 mm", SCRIPTSIZE), h_lab),
        # vertical_chain labels (2 lines) on the horizontal routing segments
        "vc0_lab": rect((-CX - 1.0) / 2, bend_y + h_lab,
                        max(tw("conduction", SCRIPTSIZE), tw(r_lab, SCRIPTSIZE)), 2 * h_lab),
        "vc1_lab": rect((CX + 1.0) / 2, bend_y + h_lab,
                        max(tw("conduction", SCRIPTSIZE), tw(r_lab, SCRIPTSIZE)), 2 * h_lab),
        # branch annotation: physical type + value provenance (3 lines)
        "note": rect(0.0, -4.75,
                     max(tw("conduction: k=150 W/mK, t=0.1 mm (interposer, YAML)", SCRIPTSIZE),
                         tw("vertical_chain: conduction (lumped), R_vert=1.5 K/W", SCRIPTSIZE),
                         tw("lumped = \u03bcbump + interposer + C4 + substrate (YAML)", SCRIPTSIZE)),
                     3 * h_lab),
    }
    return {"nodes": nodes, "edges": edges, "labels": labels,
            "own": {"fa": {"fa_type", "fa_par"}, "vc0": {"vc0_lab"}, "vc1": {"vc1_lab"}},
            "seg_ends": {"vc0": {"n0", "bnd"}, "vc1": {"n1", "bnd"}, "fa": {"n0", "n1"}}}


def build_3d() -> dict:
    """3D expanded multi-layer figure (DomainExpert model-ruling XIV):
    two stacks, each expanded into top/bottom die nodes; inter-layer
    TSV/hybrid-bonding vertical edges; per-layer lateral face adjacency;
    bottom-die -> ambient vertical cooling chain; lumped R_vert annotated
    alongside the expanded view (2 layers in series).
    """
    inner = 2 * 0.333 * SMALL * PT
    n_w = max(2.8, tw("stack0 bottom", SMALL, CHAR_W_SMALL) + inner)
    n_h = 1.1
    half = n_w / 2
    cx = 3.4                                  # stack column x
    top_y, bot_y = 1.6, -0.5                  # top / bottom layer centers
    bend_y = -2.2                             # cooling-chain routing level
    b_w = max(BND_W_MIN, tw("boundary \u00b7 300 K", SMALL, CHAR_W_SMALL) + inner)

    nodes = {
        "t0": rect(-cx, top_y, n_w, n_h),
        "t1": rect(cx, top_y, n_w, n_h),
        "b0": rect(-cx, bot_y, n_w, n_h),
        "b1": rect(cx, bot_y, n_w, n_h),
        "bnd": rect(0.0, BND_CY, b_w, BND_H),
    }
    tsv_lab = "TSV/hybrid bonding"
    h_lab = th(1, SCRIPTSIZE)
    edges = {
        "fa_top": [(-cx + half, top_y), (cx - half, top_y)],
        "fa_bot": [(-cx + half, bot_y), (cx - half, bot_y)],
        "tsv0": [(-cx, top_y - n_h / 2), (-cx, bot_y + n_h / 2)],
        "tsv1": [(cx, top_y - n_h / 2), (cx, bot_y + n_h / 2)],
        "vc0": [(-cx, bot_y - n_h / 2), (-cx, bend_y), (-1.0, bend_y), (-1.0, BND_CY + BND_H / 2 - 0.05)],
        "vc1": [(cx, bot_y - n_h / 2), (cx, bend_y), (1.0, bend_y), (1.0, BND_CY + BND_H / 2 - 0.05)],
    }
    labels = {
        "fa_top_type": rect(0.0, top_y + h_lab / 2, tw("conduction (Fourier)", SCRIPTSIZE), h_lab),
        "fa_top_par": rect(0.0, top_y - h_lab / 2, tw("k=150 W/mK \u00b7 t=0.1 mm", SCRIPTSIZE), h_lab),
        "fa_bot_type": rect(0.0, bot_y + h_lab / 2, tw("conduction (Fourier)", SCRIPTSIZE), h_lab),
        "fa_bot_par": rect(0.0, bot_y - h_lab / 2, tw("k=150 W/mK \u00b7 t=0.1 mm", SCRIPTSIZE), h_lab),
        # TSV labels (2 lines) to the inner side of each vertical segment
        "tsv0_lab": rect(-cx + 0.15 + tw(tsv_lab, SCRIPTSIZE) / 2, 0.55,
                         max(tw(tsv_lab, SCRIPTSIZE), tw("conduction", SCRIPTSIZE)), 2 * h_lab),
        "tsv1_lab": rect(cx - 0.15 - tw(tsv_lab, SCRIPTSIZE) / 2, 0.55,
                         max(tw(tsv_lab, SCRIPTSIZE), tw("conduction", SCRIPTSIZE)), 2 * h_lab),
        "vc0_lab": rect(-2.2, bend_y + h_lab, max(tw("conduction", SCRIPTSIZE),
                                                  tw("R=2.4 K/W", SCRIPTSIZE)), 2 * h_lab),
        "vc1_lab": rect(2.2, bend_y + h_lab, max(tw("conduction", SCRIPTSIZE),
                                                 tw("R=2.4 K/W", SCRIPTSIZE)), 2 * h_lab),
        # lumped-summary annotation above the expanded view (one 2-line node)
        "lump": rect(0.0, 2.55,
                     max(tw("stack lumped R_vert = 2.4 K/W", SCRIPTSIZE),
                         tw("2 layers in series", SCRIPTSIZE)),
                     2 * h_lab),
        # branch annotation: physical type + value provenance (3 lines)
        "note": rect(0.0, -4.75,
                     max(tw("tsv/hybrid: conduction, layer-to-layer R (YAML)", SCRIPTSIZE),
                         tw("vertical_chain: conduction (lumped), R=2.4 K/W", SCRIPTSIZE),
                         tw("lumped = 2 layers in series (YAML)", SCRIPTSIZE)),
                     3 * h_lab),
    }
    return {
        "nodes": nodes, "edges": edges, "labels": labels,
        "own": {
            "fa_top": {"fa_top_type", "fa_top_par"},
            "fa_bot": {"fa_bot_type", "fa_bot_par"},
            "tsv0": {"tsv0_lab"}, "tsv1": {"tsv1_lab"},
            "vc0": {"vc0_lab"}, "vc1": {"vc1_lab"},
        },
        "seg_ends": {
            "fa_top": {"t0", "t1"}, "fa_bot": {"b0", "b1"},
            "tsv0": {"t0", "b0"}, "tsv1": {"t1", "b1"},
            "vc0": {"b0", "bnd"}, "vc1": {"b1", "bnd"},
        },
    }


def build_heatsink() -> dict:
    """Heatsink figure (v3.1): the heatsink is an explicit node, not just a
    boundary. Path: die0/die1 ->(vertical chain, TIM/lid segment R=0.8)-> 
    heatsink node ->(vertical chain)-> ambient; heatsink uses a distinct
    rounded-rect shape/color, annotated with its role and temperature.
    All routing orthogonal.
    """
    die_txt = "die \u00d7 12 \u00d7 12 mm"
    bnd_txt = "boundary \u00b7 300 K"
    hs_txt = "cooling \u00b7 300 K"
    inner = 2 * 0.333 * SMALL * PT
    n_w = max(DIE_W_MIN, tw(die_txt, SMALL, CHAR_W_SMALL) + inner)
    b_w = max(BND_W_MIN, tw(bnd_txt, SMALL, CHAR_W_SMALL) + inner)
    hs_w = max(3.6, tw(hs_txt, SMALL, CHAR_W_SMALL) + inner)

    top_y, bend_y, hs_y, hs_h = 1.6, -0.2, -1.5, 1.0
    nodes = {
        "n0": rect(-CX, top_y, n_w, DIE_H),
        "n1": rect(CX, top_y, n_w, DIE_H),
        "hs": rect(0.0, hs_y, hs_w, hs_h),
        "bnd": rect(0.0, BND_CY, b_w, BND_H),
    }
    e = n_w / 2
    tip_y = BND_CY + BND_H / 2 - 0.05
    h_lab = th(1, SCRIPTSIZE)
    edges = {
        "fa": [(-CX + e, top_y), (CX - e, top_y)],
        "vc0": [(-CX, top_y - DIE_H / 2), (-CX, bend_y), (-1.0, bend_y), (-1.0, hs_y + hs_h / 2)],
        "vc1": [(CX, top_y - DIE_H / 2), (CX, bend_y), (1.0, bend_y), (1.0, hs_y + hs_h / 2)],
        "vc2": [(0.0, hs_y - hs_h / 2), (0.0, tip_y)],
    }
    labels = {
        "fa_type": rect(0.0, top_y + h_lab / 2, tw("conduction (Fourier)", SCRIPTSIZE), h_lab),
        "fa_par": rect(0.0, top_y - h_lab / 2, tw("k=150 W/mK \u00b7 t=0.1 mm", SCRIPTSIZE), h_lab),
        # TIM segment labels (2 lines) on the horizontal routing segments
        "vc0_lab": rect(-2.35, bend_y + h_lab, max(tw("conduction", SCRIPTSIZE),
                                                   tw("R=0.3 K/W", SCRIPTSIZE)), 2 * h_lab),
        "vc1_lab": rect(2.35, bend_y + h_lab, max(tw("conduction", SCRIPTSIZE),
                                                  tw("R=0.3 K/W", SCRIPTSIZE)), 2 * h_lab),
        # convection segment label (2 lines) right of the vertical segment
        "vc2_lab": rect(0.12 + tw("R=1/(hA)=0.69 K/W", SCRIPTSIZE) / 2, -2.55,
                        max(tw("convection", SCRIPTSIZE), tw("R=1/(hA)=0.69 K/W", SCRIPTSIZE)),
                        2 * h_lab),
        # branch annotation: physical type + value provenance (3 lines)
        "note": rect(0.0, -4.75,
                     max(tw("tim: conduction, R=0.3 K/W (YAML)", SCRIPTSIZE),
                         tw("heatsink\u2192ambient: convection, R=1/(hA)=0.69 K/W", SCRIPTSIZE),
                         tw("h=100 W/m\u00b2K, A=0.0144 m\u00b2 (YAML)", SCRIPTSIZE)),
                     3 * h_lab),
    }
    return {"nodes": nodes, "edges": edges, "labels": labels,
            "own": {"fa": {"fa_type", "fa_par"},
                    "vc0": {"vc0_lab"}, "vc1": {"vc1_lab"}, "vc2": {"vc2_lab"}},
            "seg_ends": {"fa": {"n0", "n1"},
                         "vc0": {"n0", "hs"}, "vc1": {"n1", "hs"},
                         "vc2": {"hs", "bnd"}}}


def build_3d_explicit() -> dict:
    """3D explicit single-stack figure (config/thermal/3d-two-die-explicit
    .yaml): die_top / die_bottom per-layer nodes, inter-layer TSV vertical
    edge (R_tsv = r_via/n_vias = 5 K/W), top-layer direct cooling chain
    die_top -> ambient (R=1.0 K/W). Every branch annotated with physical
    type + value provenance; all routing orthogonal.
    """
    die_txt = "die \u00d7 12 \u00d7 12 mm"
    bnd_txt = "boundary \u00b7 300 K"
    inner = 2 * 0.333 * SMALL * PT
    n_w = max(2.8, tw(die_txt, SMALL, CHAR_W_SMALL) + inner)
    n_h = 1.1
    b_w = max(BND_W_MIN, tw(bnd_txt, SMALL, CHAR_W_SMALL) + inner)
    h_lab = th(1, SCRIPTSIZE)

    nodes = {
        "t": rect(0.0, 0.8, n_w, n_h),
        "b": rect(0.0, -1.0, n_w, n_h),
        "bnd": rect(0.0, 3.0, b_w, BND_H),
    }
    edges = {
        "tsv": [(0.0, 0.8 - n_h / 2), (0.0, -1.0 + n_h / 2)],
        "vc": [(0.0, 0.8 + n_h / 2), (0.0, 3.0 - BND_H / 2)],
    }
    labels = {
        # TSV label (2 lines) right of the vertical segment
        "tsv_lab": rect(0.12 + max(tw("tsv \u00b7 conduction", SCRIPTSIZE),
                                   tw("R=50/10=5 K/W", SCRIPTSIZE)) / 2, -0.1,
                        max(tw("tsv \u00b7 conduction", SCRIPTSIZE),
                            tw("R=50/10=5 K/W", SCRIPTSIZE)), 2 * h_lab),
        # cooling-chain label (2 lines) left of the vertical segment
        "vc_lab": rect(-0.12 - max(tw("conduction", SCRIPTSIZE),
                                   tw("R=1.0 K/W", SCRIPTSIZE)) / 2, 1.9,
                       max(tw("conduction", SCRIPTSIZE), tw("R=1.0 K/W", SCRIPTSIZE)),
                       2 * h_lab),
        # branch annotation: physical type + value provenance (3 lines)
        "note": rect(0.0, -2.35,
                     max(tw("tsv: conduction, R_tsv = r_via/n_vias = 5 K/W", SCRIPTSIZE),
                         tw("n_vias=10, r_via=50 K/W (YAML)", SCRIPTSIZE),
                         tw("vertical_chain: conduction, R=1.0 K/W (top-layer cooling, YAML)", SCRIPTSIZE)),
                     3 * h_lab),
    }
    return {"nodes": nodes, "edges": edges, "labels": labels,
            "own": {"tsv": {"tsv_lab"}, "vc": {"vc_lab"}},
            "seg_ends": {"tsv": {"t", "b"}, "vc": {"t", "bnd"}}}


def _seg_lab_right(x_anchor: float, y_mid: float, w: float, h: float) -> tuple:
    """Label anchored right of a vertical segment at x_anchor (left edge
    offset 0.12 cm)."""
    return rect(x_anchor + 0.12 + w / 2, y_mid, w, h)


def build_2p5d_complete() -> dict:
    """2.5D complete heat path: die -> ubump -> interposer -> C4 ->
    substrate -> PCB -> ambient, plus heatsink branch die -> TIM ->
    heatsink -> convection -> ambient. Two branches, orthogonal routing.
    """
    inner = 2 * 0.333 * SMALL * PT
    h_lab = th(1, SCRIPTSIZE)
    nodes = {
        "die": rect(0.0, 1.5, max(3.2, tw("12 \u00d7 12 mm", SMALL, CHAR_W_SMALL) + inner), 1.6),
        "interposer": rect(0.0, -0.4, max(5.0, tw("lateral + vertical R", SMALL, CHAR_W_SMALL) + inner), 0.8),
        "substrate": rect(0.0, -1.7, max(5.0, tw("planar spread R", SMALL, CHAR_W_SMALL) + inner), 0.8),
        "pcb": rect(0.0, -3.15, 5.5, 0.7),
        "ambient": rect(0.0, -4.5, 3.0, 1.0),
        "heatsink": rect(0.0, 3.3, max(4.0, tw("R_conv=1/(hA)", SMALL, CHAR_W_SMALL) + inner), 0.8),
        "ambient_hs": rect(0.0, 4.7, 3.0, 1.0),
    }
    edges = {
        "ub": [(0.0, 0.7), (0.0, 0.0)],
        "c4": [(0.0, -0.8), (0.0, -1.3)],
        "pcb": [(0.0, -2.1), (0.0, -2.8)],
        "amb": [(0.0, -3.5), (0.0, -4.0)],
        "tim": [(0.0, 2.3), (0.0, 2.9)],
        "conv": [(0.0, 3.7), (0.0, 4.2)],
    }
    labels = {
        "ub_lab": _seg_lab_right(0.0, 0.35, tw("\u03bcbump \u00b7 conduction", SCRIPTSIZE), h_lab),
        "c4_lab": _seg_lab_right(0.0, -1.05, tw("C4 \u00b7 conduction", SCRIPTSIZE), h_lab),
        "pcb_lab": _seg_lab_right(0.0, -2.45, tw("PCB \u00b7 conduction", SCRIPTSIZE), h_lab),
        "amb_lab": _seg_lab_right(0.0, -3.75, tw("boundary", SCRIPTSIZE), h_lab),
        "tim_lab": _seg_lab_right(0.0, 2.6, tw("TIM \u00b7 R=0.3 K/W", SCRIPTSIZE), h_lab),
        "conv_lab": _seg_lab_right(0.0, 3.95, tw("convection \u00b7 1/(hA)", SCRIPTSIZE), h_lab),
        "note": rect(0.0, -5.9,
                     max(tw("substrate path: R_vert=1.5 K/W lumped = ubump+interposer+C4+substrate (YAML)", SCRIPTSIZE),
                         tw("heatsink path: TIM R=0.3 K/W, convection R=1/(hA)=0.69 K/W (h=100, A=0.0144, YAML)", SCRIPTSIZE),
                         tw("per-segment t/(kA) values: config/params or literature", SCRIPTSIZE)),
                     3 * h_lab),
    }
    return {"nodes": nodes, "edges": edges, "labels": labels,
            "own": {k: {f"{k}_lab"} for k in ("ub", "c4", "pcb", "amb", "tim", "conv")},
            "seg_ends": {"ub": {"die", "interposer"}, "c4": {"interposer", "substrate"},
                         "pcb": {"substrate", "pcb"}, "amb": {"pcb", "ambient"},
                         "tim": {"die", "heatsink"}, "conv": {"heatsink", "ambient_hs"}}}


def build_3d_complete() -> dict:
    """3D complete heat path: die_top / die_bottom (TSV inter-layer) ->
    ubump -> interposer -> C4 -> substrate -> PCB -> ambient, plus heatsink
    branch die_top -> TIM -> heatsink -> convection -> ambient."""
    inner = 2 * 0.333 * SMALL * PT
    h_lab = th(1, SCRIPTSIZE)
    die_w = max(2.8, tw("12 \u00d7 12 mm", SMALL, CHAR_W_SMALL) + inner)
    nodes = {
        "die_top": rect(0.0, 2.0, die_w, 1.1),
        "die_bottom": rect(0.0, 0.4, die_w, 1.1),
        "interposer": rect(0.0, -1.1, max(5.0, tw("lateral + vertical R", SMALL, CHAR_W_SMALL) + inner), 0.8),
        "substrate": rect(0.0, -2.3, max(5.0, tw("planar spread R", SMALL, CHAR_W_SMALL) + inner), 0.8),
        "pcb": rect(0.0, -3.55, 5.5, 0.7),
        "ambient": rect(0.0, -4.95, 3.0, 1.0),
        "heatsink": rect(0.0, 3.5, max(4.0, tw("R_conv=1/(hA)", SMALL, CHAR_W_SMALL) + inner), 0.8),
        "ambient_hs": rect(0.0, 5.0, 3.0, 1.0),
    }
    edges = {
        "tsv": [(0.0, 1.45), (0.0, 0.95)],
        "ub": [(0.0, -0.15), (0.0, -0.7)],
        "c4": [(0.0, -1.5), (0.0, -1.9)],
        "pcb": [(0.0, -2.7), (0.0, -3.2)],
        "amb": [(0.0, -3.9), (0.0, -4.45)],
        "tim": [(0.0, 2.55), (0.0, 3.1)],
        "conv": [(0.0, 3.9), (0.0, 4.5)],
    }
    labels = {
        "tsv_lab": _seg_lab_right(0.0, 1.2, tw("tsv \u00b7 R=5 K/W", SCRIPTSIZE), h_lab),
        "ub_lab": _seg_lab_right(0.0, -0.425, tw("\u03bcbump \u00b7 conduction", SCRIPTSIZE), h_lab),
        "c4_lab": _seg_lab_right(0.0, -1.7, tw("C4 \u00b7 conduction", SCRIPTSIZE), h_lab),
        "pcb_lab": _seg_lab_right(0.0, -2.95, tw("PCB \u00b7 conduction", SCRIPTSIZE), h_lab),
        "amb_lab": _seg_lab_right(0.0, -4.175, tw("boundary", SCRIPTSIZE), h_lab),
        "tim_lab": _seg_lab_right(0.0, 2.825, tw("TIM \u00b7 R=0.3 K/W", SCRIPTSIZE), h_lab),
        "conv_lab": _seg_lab_right(0.0, 4.2, tw("convection \u00b7 1/(hA)", SCRIPTSIZE), h_lab),
        "note": rect(0.0, -6.25,
                     max(tw("3D: tsv R=5 K/W, substrate path R_vert lumped (YAML)", SCRIPTSIZE),
                         tw("heatsink: TIM R=0.3, convection R=1/(hA)=0.69 (YAML)", SCRIPTSIZE),
                         tw("per-segment t/(kA): config/params or literature", SCRIPTSIZE)),
                     3 * h_lab),
    }
    return {"nodes": nodes, "edges": edges, "labels": labels,
            "own": {k: {f"{k}_lab"} for k in ("tsv", "ub", "c4", "pcb", "amb", "tim", "conv")},
            "seg_ends": {"tsv": {"die_top", "die_bottom"}, "ub": {"die_bottom", "interposer"},
                         "c4": {"interposer", "substrate"}, "pcb": {"substrate", "pcb"},
                         "amb": {"pcb", "ambient"},
                         "tim": {"die_top", "heatsink"}, "conv": {"heatsink", "ambient_hs"}}}


def build_wafer() -> dict:
    """Wafer-level heat path: 1x3 die grid + lateral face adjacency +
    backside global cooling (uniform grounded g_vert) to a cold-plate
    ambient."""
    h_lab = th(1, SCRIPTSIZE)
    die_w, die_h = 1.6, 1.0
    nodes = {
        "d0": rect(-2.0, 0.0, die_w, die_h),
        "d1": rect(0.0, 0.0, die_w, die_h),
        "d2": rect(2.0, 0.0, die_w, die_h),
        "coldplate": rect(0.0, -1.6, 4.6, 0.5),
    }
    edges = {
        "lat0": [(-1.2, 0.0), (-0.8, 0.0)],
        "lat1": [(0.8, 0.0), (1.2, 0.0)],
        "gv0": [(-2.0, -0.5), (-2.0, -1.35)],
        "gv1": [(0.0, -0.5), (0.0, -1.35)],
        "gv2": [(2.0, -0.5), (2.0, -1.35)],
    }
    labels = {
        "lat_lab": rect(0.0, 0.9, tw("face_adjacency \u00b7 lateral", SCRIPTSIZE), h_lab),
        "gv_lab": _seg_lab_right(-1.4, -0.95, tw("g_vert", SCRIPTSIZE), h_lab),
        "note": rect(0.0, -2.5,
                     max(tw("backside: convection, g_vert = h_cooling * A_node (water h ~ 1e3-1e4 W/m2K, catalog)", SCRIPTSIZE),
                         tw("lateral: conduction, G = k*A/L through interposer/substrate plane (catalog)", SCRIPTSIZE),
                         tw("uniform grounded g_vert per node: M-matrix diagonal dominance (V5 2.6)", SCRIPTSIZE)),
                     3 * h_lab),
    }
    return {"nodes": nodes, "edges": edges, "labels": labels,
            "own": {"gv0": {"gv_lab"}},
            "seg_ends": {"lat0": {"d0", "d1"}, "lat1": {"d1", "d2"},
                         "gv0": {"d0", "coldplate"}, "gv1": {"d1", "coldplate"},
                         "gv2": {"d2", "coldplate"}}}


def build_fig2_v3() -> dict:
    """Paper Fig. 2 v3 (complete heat path as explicit nodes, model-ruling
    XVI): upper panel = 2.5D chain die->ubump->interposer->C4->substrate->
    ambient + heatsink branch + C1-C4 boxes + envelope box; lower panel =
    3D expanded stacks + lumped R annotation + first-class/triad + note."""
    h_lab = th(1, SCRIPTSIZE)
    nodes = {
        "die": rect(-3.5, 13.5, 3.4, 1.6),
        "heatsink": rect(-3.5, 15.4, 3.6, 0.8),
        "ambient_hs": rect(-3.5, 16.8, 3.0, 1.0),
        "interposer": rect(-3.5, 11.4, 5.0, 1.0),
        "substrate": rect(-3.5, 9.6, 5.0, 1.0),
        "ambient": rect(-3.5, 8.0, 3.0, 1.0),
        "c1": rect(4.0, 13.5, 4.2, 1.0),
        "c2": rect(4.0, 11.4, 4.2, 1.0),
        "c3": rect(4.0, 9.8, 4.2, 1.0),
        "c4": rect(4.0, 8.2, 4.2, 1.0),
        "env": rect(6.8, 16.2, 3.6, 1.8),
        "t0": rect(-2.8, 3.6, 2.8, 1.1),
        "b0": rect(-2.8, 1.9, 2.8, 1.1),
        "t1": rect(2.8, 3.6, 2.8, 1.1),
        "b1": rect(2.8, 1.9, 2.8, 1.1),
        "amb3d": rect(0.0, -0.4, 3.0, 1.0),
    }
    edges = {
        "tim": [(-3.5, 14.3), (-3.5, 15.0)],
        "conv": [(-3.5, 15.8), (-3.5, 16.3)],
        "ub": [(-3.5, 12.7), (-3.5, 11.9)],
        "c4": [(-3.5, 10.9), (-3.5, 10.1)],
        "amb": [(-3.5, 9.1), (-3.5, 8.5)],
        "cpl1": [(1.9, 13.5), (-0.6, 13.5), (-0.6, 12.7), (-3.0, 12.7)],
        "cpl2": [(1.9, 11.4), (-0.6, 11.4), (-3.0, 11.4)],
        "cpl3": [(1.9, 9.8), (-0.6, 9.8), (-0.6, 10.1), (-3.0, 10.1)],
        "cpl4": [(1.9, 8.2), (-0.6, 8.2), (-0.6, 9.1), (-3.0, 9.1)],
        "tsv0": [(-2.8, 3.05), (-2.8, 2.45)],
        "tsv1": [(2.8, 3.05), (2.8, 2.45)],
        "fa_top": [(-1.4, 3.6), (1.4, 3.6)],
        "fa_bot": [(-1.4, 1.9), (1.4, 1.9)],
        "vc0": [(-2.8, 1.35), (-2.8, 0.2), (-0.4, 0.2), (-0.4, -0.35)],
        "vc1": [(2.8, 1.35), (2.8, 0.2), (0.4, 0.2), (0.4, -0.35)],
    }
    labels = {
        "tim_lab": _seg_lab_right(-3.5, 14.65, tw("TIM/lid \u00b7 conduction", SCRIPTSIZE), h_lab),
        "conv_lab": _seg_lab_right(-3.5, 16.05, tw("convection", SCRIPTSIZE), h_lab),
        "ub_lab": _seg_lab_right(-3.5, 12.3, tw("\u03bcbump \u00b7 conduction", SCRIPTSIZE), h_lab),
        "c4_lab": _seg_lab_right(-3.5, 10.5, tw("C4 \u00b7 conduction", SCRIPTSIZE), h_lab),
        "amb_lab": _seg_lab_right(-3.5, 8.8, tw("boundary", SCRIPTSIZE), h_lab),
        "tsv0_lab": rect(-2.68 - tw("tsv/hybrid", SCRIPTSIZE) / 2, 2.75,
                         tw("tsv/hybrid", SCRIPTSIZE), h_lab),
        "tsv1_lab": rect(2.68 + tw("tsv/hybrid", SCRIPTSIZE) / 2, 2.75,
                         tw("tsv/hybrid", SCRIPTSIZE), h_lab),
        "fa_top_lab": rect(0.0, 3.74, tw("face_adjacency", SCRIPTSIZE), h_lab),
        "fa_bot_lab": rect(0.0, 1.76, tw("face_adjacency", SCRIPTSIZE), h_lab),
        "vc0_lab": rect(-1.6, 0.34, tw("R=2.4 K/W", SCRIPTSIZE), h_lab),
        "title3d": rect(0.0, 4.6,
                        tw("3D expanded: per-layer dies + TSV/hybrid, lumped R_vert=2.4 K/W (2 layers in series)",
                           SCRIPTSIZE), h_lab),
        "note": rect(0.0, -1.9,
                     max(tw("values: R_vert=1.5, TIM=0.3, R_conv=1/(hA)=0.69, tsv=5 K/W (YAML)", SCRIPTSIZE),
                         tw("per-segment t/(kA): config/params or literature; no fabricated values", SCRIPTSIZE),
                         tw("first-class: wiring saturation + die-area upper bound (bind before bump budget)", SCRIPTSIZE),
                         tw("triad: P/G routing occupies RDL -> more cooling or lower bandwidth", SCRIPTSIZE)),
                     4 * h_lab),
    }
    return {"nodes": nodes, "edges": edges, "labels": labels,
            "own": {"tim": {"tim_lab"}, "conv": {"conv_lab"}, "ub": {"ub_lab"},
                    "c4": {"c4_lab"}, "amb": {"amb_lab"},
                    "tsv0": {"tsv0_lab"}, "tsv1": {"tsv1_lab"},
                    "fa_top": {"fa_top_lab"}, "fa_bot": {"fa_bot_lab"},
                    "vc0": {"vc0_lab"}},
            "seg_ends": {"tim": {"die", "heatsink"}, "conv": {"heatsink", "ambient_hs"},
                         "ub": {"die", "interposer"}, "c4": {"interposer", "substrate"},
                         "amb": {"substrate", "ambient"},
                         "cpl1": {"c1", "die"}, "cpl2": {"c2", "interposer"},
                         "cpl3": {"c3", "substrate"}, "cpl4": {"c4", "substrate"},
                         "tsv0": {"t0", "b0"}, "tsv1": {"t1", "b1"},
                         "fa_top": {"t0", "t1"}, "fa_bot": {"b0", "b1"},
                         "vc0": {"b0", "amb3d"}, "vc1": {"b1", "amb3d"}}}


FIGS = {
    "2p5d": build_2p5d("ambient", "R=1.5 K/W"),
    "heatsink": build_heatsink(),
    "3d": build_3d(),
    "3d-explicit": build_3d_explicit(),
    "2p5d-complete": build_2p5d_complete(),
    "3d-complete": build_3d_complete(),
    "wafer": build_wafer(),
    "fig2-v3": build_fig2_v3(),
}


def check(fig: dict, name: str) -> list[str]:
    issues: list[str] = []
    nodes, edges, labels = fig["nodes"], fig["edges"], fig["labels"]

    # node x node
    ns = list(nodes)
    for i in range(len(ns)):
        for j in range(i + 1, len(ns)):
            if boxes_overlap(nodes[ns[i]], nodes[ns[j]]):
                issues.append(f"{name}: node x node: {ns[i]} vs {ns[j]}")

    # label x label
    ls = list(labels)
    for i in range(len(ls)):
        for j in range(i + 1, len(ls)):
            if boxes_overlap(labels[ls[i]], labels[ls[j]]):
                issues.append(f"{name}: label x label: {ls[i]} vs {ls[j]}")

    # label x node
    for ln, lb in labels.items():
        for nn, nb in nodes.items():
            if boxes_overlap(lb, nb):
                issues.append(f"{name}: label x node: {ln} vs {nn}")

    # edge x node (exclude the edge's own endpoint nodes)
    for en, poly in edges.items():
        for nn, nb in nodes.items():
            if nn in fig["seg_ends"][en]:
                continue
            if any(seg_rect_intersect(poly[i], poly[i + 1], nb) for i in range(len(poly) - 1)):
                issues.append(f"{name}: edge x node: {en} vs {nn}")

    # edge x edge (segment-wise, orthogonal polylines)
    es = list(edges)
    for i in range(len(es)):
        for j in range(i + 1, len(es)):
            pi, pj = edges[es[i]], edges[es[j]]
            hit = any(seg_intersect(pi[a], pi[a + 1], pj[b], pj[b + 1])
                      for a in range(len(pi) - 1) for b in range(len(pj) - 1))
            if hit:
                issues.append(f"{name}: edge x edge: {es[i]} vs {es[j]}")

    # label x edge (exclude the label's own edge)
    for ln, lb in labels.items():
        for en, poly in edges.items():
            if ln in fig["own"].get(en, set()):
                continue
            if any(seg_rect_intersect(poly[i], poly[i + 1], lb) for i in range(len(poly) - 1)):
                issues.append(f"{name}: label x edge: {ln} vs {en}")

    return issues


def main(argv: list[str]) -> int:
    names = argv[1:] or sorted(FIGS)
    total = 0
    for name in names:
        issues = check(FIGS[name], name)
        total += len(issues)
        print(f"[{name}] collisions: {len(issues)}")
        for i in issues:
            print(f"    {i}")
    print(f"TOTAL: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
