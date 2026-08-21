"""Shared helpers for wafer-dse paper concept figures (FigureArtist).

Engineering discipline (old prompt/04-figure-artist.md): every aesthetic
decision must land on a computable, reproducible numeric check — WCAG
contrast, golden-ratio divisions, text-overlap and canvas-overflow audits.
"""
from __future__ import annotations

import math
from typing import Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from matplotlib.text import Text

# --------------------------------------------------------------------------
# Palette (restrained: neutral + signal + accent).
# Every saturated fill below passes WCAG >= 4.5:1 against white text
# (verified by contrast_report, not by eye).
# --------------------------------------------------------------------------
INK = "#202124"    # primary text (on light fills, ratio > 10:1)
INK2 = "#5F6368"   # secondary text (on white, ratio 6.07:1)
BLUE = "#1A73E8"   # outer layer / C1   (white 4.51:1)
AMBER = "#B45309"  # inner layer / C4   (white 5.02:1)
GREEN = "#188038"  # output / C3        (white 5.00:1)
PURPLE = "#9334E6" # C2                 (white 5.41:1)
GRAY = "#5F6368"   # interface / structure (white 6.07:1)
BLUE_L = "#E8F0FE"
AMBER_L = "#FFF4E5"
GREEN_L = "#E6F4EA"
PURPLE_L = "#F3E8FD"
GRAY_L = "#F1F3F4"

GOLDEN = 1.618033988749895


def setup_rc() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
        "svg.fonttype": "none",           # editable text in SVG
        "pdf.fonttype": 42,               # editable TrueType text in PDF
        "font.size": 8,
        "mathtext.fontset": "dejavusans",
        "axes.linewidth": 0.8,
    })


def new_fig(w: float, h: float) -> tuple[Figure, Axes]:
    """Figure where 1 data unit == 1 inch (axes fill the canvas exactly)."""
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


# --------------------------------------------------------------------------
# Computed aesthetics: WCAG contrast, golden ratio.
# --------------------------------------------------------------------------
def _chan(s: float) -> float:
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def luminance(color_spec: str) -> float:
    r, g, b = mpl.colors.to_rgb(color_spec)
    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


def contrast(fg: str, bg: str) -> float:
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def contrast_report(pairs: Sequence[tuple[str, str, str]]) -> None:
    for name, fg, bg in pairs:
        c = contrast(fg, bg)
        flag = "OK  " if c >= 4.5 else ("WARN" if c >= 3.0 else "FAIL")
        print(f"  contrast[{name:<28}] {fg} on {bg}: {c:5.2f}  [{flag}]")


def golden_split(length: float) -> tuple[float, float]:
    """Golden-section split: returns (short, long) = (0.382L, 0.618L)."""
    return length / GOLDEN ** 2, length / GOLDEN


def golden_report(name: str, ratio: float) -> None:
    dev = abs(ratio - GOLDEN) / GOLDEN
    flag = "OK  " if dev <= 0.02 else ("WARN" if dev <= 0.05 else "FAIL")
    print(f"  golden[{name:<28}] ratio={ratio:5.3f} vs 1.618 (dev {dev*100:4.1f}%) [{flag}]")


# --------------------------------------------------------------------------
# Primitive drawing helpers (coordinates computed, never eyeballed).
# --------------------------------------------------------------------------
def rbox(ax: Axes, x: float, y: float, w: float, h: float, *,
         fc: str, ec: str, lw: float = 1.0, r: float = 0.06,
         ls: str = "-") -> FancyBboxPatch:
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       fc=fc, ec=ec, lw=lw, linestyle=ls, zorder=2)
    ax.add_patch(p)
    return p


def arrow(ax: Axes, x0: float, y0: float, x1: float, y1: float, *,
          color: str = INK, lw: float = 1.4, style: str = "-|>",
          ms: float = 10, ls: str = "-", z: int = 3) -> FancyArrowPatch:
    a = FancyArrowPatch((x0, y0), (x1, y1),
                        arrowstyle=style, mutation_scale=ms,
                        color=color, lw=lw, linestyle=ls, zorder=z,
                        shrinkA=0, shrinkB=0)
    ax.add_patch(a)
    return a


def txt(ax: Axes, x: float, y: float, s: str, *, size: float = 8,
        color: str = INK, ha: str = "center", va: str = "center",
        weight: str = "normal", style: str = "normal", z: int = 4) -> Text:
    t = ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
                fontweight=weight, fontstyle=style, zorder=z)
    return t


# --------------------------------------------------------------------------
# QA: computed text extents -> overlap / overflow / containment audits.
# --------------------------------------------------------------------------
def text_data_bbox(t: Text, ax: Axes) -> tuple[float, float, float, float]:
    fig = ax.figure
    fig.canvas.draw()
    ext = t.get_window_extent(renderer=fig.canvas.get_renderer())
    inv = ax.transData.inverted()
    (x0, y0) = inv.transform((ext.x0, ext.y0))
    (x1, y1) = inv.transform((ext.x1, ext.y1))
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def _overlap(a: tuple[float, float, float, float],
             b: tuple[float, float, float, float], tol: float) -> bool:
    return not (a[2] <= b[0] + tol or b[2] <= a[0] + tol
                or a[3] <= b[1] + tol or b[3] <= a[1] + tol)


def check_text_overlaps(ax: Axes, texts: Sequence[tuple[str, Text]],
                        tol: float = 0.006) -> list[str]:
    """Pairwise text-bbox overlap audit (all text must be disjoint)."""
    boxes = {name: text_data_bbox(t, ax) for name, t in texts}
    issues: list[str] = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            na, nb = texts[i][0], texts[j][0]
            if _overlap(boxes[na], boxes[nb], tol):
                a, b = boxes[na], boxes[nb]
                issues.append(
                    f"  overlap: '{na}' {tuple(round(v, 3) for v in a)}"
                    f" vs '{nb}' {tuple(round(v, 3) for v in b)}")
    return issues


def check_canvas_overflow(ax: Axes, texts: Sequence[tuple[str, Text]],
                          canvas: tuple[float, float, float, float],
                          margin: float = 0.06) -> list[str]:
    issues: list[str] = []
    for name, t in texts:
        x0, y0, x1, y1 = text_data_bbox(t, ax)
        if (x0 < canvas[0] + margin or y0 < canvas[1] + margin
                or x1 > canvas[2] - margin or y1 > canvas[3] - margin):
            issues.append(
                f"  overflow: '{name}' bbox=({x0:.3f},{y0:.3f},{x1:.3f},{y1:.3f})")
    return issues


def check_text_in_boxes(ax: Axes, pairs: Sequence[tuple[str, Text, str, tuple[float, float, float, float]]],
                        pad: float = 0.03) -> list[str]:
    """Each (text, container box) pair: text bbox must sit inside box + pad."""
    issues: list[str] = []
    for tname, t, bname, (bx0, by0, bx1, by1) in pairs:
        x0, y0, x1, y1 = text_data_bbox(t, ax)
        if (x0 < bx0 - pad or y0 < by0 - pad or x1 > bx1 + pad or y1 > by1 + pad):
            issues.append(
                f"  text '{tname}' escapes box '{bname}': "
                f"text=({x0:.3f},{y0:.3f},{x1:.3f},{y1:.3f}) "
                f"box=({bx0:.3f},{by0:.3f},{bx1:.3f},{by1:.3f})")
    return issues


def run_qa(name: str, ax: Axes, texts: Sequence[tuple[str, Text]],
           canvas: tuple[float, float, float, float],
           containers: Sequence[tuple[str, Text, str, tuple[float, float, float, float]]] = ()) -> None:
    issues: list[str] = []
    issues += check_text_overlaps(ax, texts)
    issues += check_canvas_overflow(ax, texts, canvas)
    issues += check_text_in_boxes(ax, containers)
    print(f"QA[{name}]:")
    if issues:
        for i in issues:
            print(i)
        print(f"QA[{name}]: {len(issues)} issue(s) -> FIX")
    else:
        print(f"QA[{name}]: all text disjoint, in-canvas, contained. PASS")


def save_pub(fig: Figure, out: str) -> None:
    fig.savefig(f"{out}.pdf", bbox_inches="tight")
    fig.savefig(f"{out}.svg", bbox_inches="tight")
    print(f"saved {out}.pdf / {out}.svg")


def golden_width_for(height: float) -> float:
    return height * GOLDEN
