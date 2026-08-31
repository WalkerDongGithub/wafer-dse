"""PDF element overlap detection.

Extract every element's real geometry from a compiled PDF (PyMuPDF:
text lines as bbox rectangles, vector rects/lines/curves/quadrilaterals/
fills) and pairwise-intersect them (shapely, O(n^2)). Text widths are
measured from the rendered PDF, not estimated.

API:
    report = check_pdf_overlap("figure.pdf", threshold=0.0)
    report.overlap_count / report.touch_count / report.collisions
    report.save("report.txt")
"""
from __future__ import annotations

from dataclasses import dataclass, field

import fitz
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.base import BaseGeometry

TEXT, RECT, SEG, CURVE, POLY = "text", "rect", "segment", "curve", "polygon"


def _bezier_polyline(p0, p1, p2, p3, n: int = 8) -> list[tuple[float, float]]:
    """Sample a cubic Bezier (control points p0..p3) into an n-segment polyline."""
    pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        x = u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y
        pts.append((x, y))
    return pts


def _valid(g: BaseGeometry) -> BaseGeometry:
    """Repair degenerate geometries (zero area / self-touch) for safe
    predicate tests; shapely handles points/zero-length lines natively."""
    return g.buffer(0) if not g.is_valid else g


def extract_page_elements(page, text_granularity: str = "line") -> list[tuple[str, str, BaseGeometry]]:
    """Return [(name, kind, geometry)] for every element on one page.

    text_granularity: "line" (one bbox per text line, coarser) or "span"
    (one bbox per text span/glyph run -- exposes in-line overlaps such as
    math sub/superscripts and adjacent label text).
    """
    elems: list[tuple[str, str, BaseGeometry]] = []

    for bi, blk in enumerate(page.get_text("dict").get("blocks", [])):
        if blk.get("type") != 0:
            continue
        for li, line in enumerate(blk.get("lines", [])):
            if text_granularity == "span":
                for si, span in enumerate(line.get("spans", [])):
                    r = span["bbox"]
                    elems.append((f"text:{bi}:{li}:{si}", TEXT,
                                  _valid(box(r[0], r[1], r[2], r[3]))))
            else:
                r = line["bbox"]
                elems.append((f"text:{bi}:{li}", TEXT, _valid(box(r[0], r[1], r[2], r[3]))))

    for di, dr in enumerate(page.get_drawings()):
        for ii, item in enumerate(dr["items"]):
            kind = item[0]
            if kind == "re":
                r = item[1]
                elems.append((f"rect:{di}:{ii}", RECT,
                              _valid(box(r.x0, r.y0, r.x1, r.y1))))
            elif kind == "l":
                p1, p2 = item[1], item[2]
                elems.append((f"seg:{di}:{ii}", SEG,
                              _valid(LineString([(p1.x, p1.y), (p2.x, p2.y)]))))
            elif kind == "c":
                pts = _bezier_polyline(*item[1:])
                elems.append((f"curve:{di}:{ii}", CURVE, _valid(LineString(pts))))
            elif kind == "qu":
                pts = [(p.x, p.y) for p in item[1:]]
                elems.append((f"quad:{di}:{ii}", POLY, _valid(Polygon(pts))))
            elif kind == "f":
                try:
                    pts = [(p.x, p.y) for p in item[1]]
                except (TypeError, AttributeError):
                    continue
                if len(pts) >= 3:
                    elems.append((f"fill:{di}:{ii}", POLY, _valid(Polygon(pts))))
    return elems


@dataclass(frozen=True)
class Collision:
    """One intersecting element pair.

    relation: "overlap" (partial overlap, intersection area > threshold,
    a real occlusion), "touch" (contact only, area <= threshold, or two
    adjacent text lines whose glyph bboxes overlap at normal line
    spacing), or "contain" (one element fully contains the other, e.g. a
    label inside its node box -- normal, not an occlusion).
    overlap_area: intersection area (PDF points^2); distance: 0 for
    intersecting pairs.
    """
    a: str
    b: str
    a_kind: str
    b_kind: str
    relation: str
    overlap_area: float
    distance: float


@dataclass
class CollisionReport:
    pdf_path: str
    threshold: float
    collisions: list[Collision] = field(default_factory=list)

    @property
    def overlap_count(self) -> int:
        return sum(1 for c in self.collisions if c.relation == "overlap")

    @property
    def touch_count(self) -> int:
        return sum(1 for c in self.collisions if c.relation == "touch")

    @property
    def contain_count(self) -> int:
        return sum(1 for c in self.collisions if c.relation == "contain")

    def summary(self) -> str:
        return (f"{self.pdf_path}: {self.overlap_count} overlap(s), "
                f"{self.touch_count} touch(es), {self.contain_count} contain(s) "
                f"[threshold={self.threshold}]")

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"pdf: {self.pdf_path}\n")
            f.write(f"threshold: {self.threshold}\n")
            f.write(f"overlap: {self.overlap_count}, touch: {self.touch_count}, "
                    f"contain: {self.contain_count}\n\n")
            for c in self.collisions:
                f.write(f"{c.relation:7s} {c.a} ({c.a_kind}) x {c.b} ({c.b_kind}) "
                        f"area={c.overlap_area:.3f} dist={c.distance:.3f}\n")


def _text_loc(name: str):
    """(block, line, span) for a text element name; span may be None."""
    if not name.startswith("text:"):
        return None
    parts = name.split(":")
    if len(parts) == 3:
        return int(parts[1]), int(parts[2]), None
    if len(parts) == 4:
        return int(parts[1]), int(parts[2]), int(parts[3])
    return None


def _adjacent_text_lines(a: str, b: str) -> bool:
    """True for two text lines in the same block with adjacent indices
    (normal line spacing makes glyph bboxes overlap slightly), or two
    spans of the same line (a math group: subscript/superscript glyph
    bboxes overlap the base glyph)."""
    pa, pb = _text_loc(a), _text_loc(b)
    if pa is None or pb is None:
        return False
    if pa[0] != pb[0]:
        return False
    if pa[1] == pb[1]:           # same line: math group spans
        return pa[2] is not None and pb[2] is not None and abs(pa[2] - pb[2]) <= 1
    return abs(pa[1] - pb[1]) == 1


def detect_overlaps(elements: list[tuple[str, str, BaseGeometry]],
                    threshold: float = 0.0) -> list[Collision]:
    """O(n^2) pairwise intersection test over element geometries.

    Containment (a label inside its node box) is reported as "contain"
    and does not count as an occlusion; adjacent text lines in the same
    block are reported as "touch" (normal glyph-bbox overlap).
    """
    out: list[Collision] = []
    n = len(elements)
    for i in range(n):
        na, ka, ga = elements[i]
        for j in range(i + 1, n):
            nb, kb, gb = elements[j]
            if not ga.intersects(gb):
                continue
            area = ga.intersection(gb).area
            if ga.contains(gb) or gb.contains(ga):
                rel = "contain"
            elif ka == TEXT and kb == TEXT and _adjacent_text_lines(na, nb):
                rel = "touch"
            else:
                rel = "overlap" if area > threshold else "touch"
            out.append(Collision(na, nb, ka, kb, rel, area, ga.distance(gb)))
    return out


def check_pdf_overlap(pdf_path: str, threshold: float = 0.0,
                      text_granularity: str = "line") -> CollisionReport:
    """Extract all page elements from a PDF and pairwise-intersect them."""
    doc = fitz.open(pdf_path)
    elements: list[tuple[str, str, BaseGeometry]] = []
    try:
        for page in doc:
            elements += extract_page_elements(page, text_granularity)
    finally:
        doc.close()
    return CollisionReport(pdf_path, threshold, detect_overlaps(elements, threshold))
