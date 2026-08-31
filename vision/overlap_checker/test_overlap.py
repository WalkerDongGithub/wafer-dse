"""Synthetic + end-to-end tests for the PDF overlap checker.

Run:
    python3 -m vision.overlap_checker.test_overlap
    # or directly: python3 vision/overlap_checker/test_overlap.py
Exits 0 only if every assertion passes and the acceptance PDFs
(vision/examples/2p5d, heatsink, 3d) report zero overlaps.
"""
from __future__ import annotations

import os
import sys

import fitz
from shapely.geometry import LineString, Point, Polygon, box

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vision.overlap_checker.checker import check_pdf_overlap, detect_overlaps

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        FAILS.append(f"{name}: {detail}")
        print(f"  FAIL {name}  {detail}")
    else:
        print(f"  ok   {name}")


def test_geometry_cases() -> None:
    print("[geometry] synthetic pairwise cases")
    # 1. two overlapping rectangles -> 1 overlap
    els = [("a", "rect", box(0, 0, 2, 2)), ("b", "rect", box(1, 1, 3, 3))]
    cols = detect_overlaps(els)
    check("rect-rect overlap", len(cols) == 1 and cols[0].relation == "overlap"
          and cols[0].overlap_area > 0, f"got {len(cols)}")

    # 2. two separated rectangles -> 0
    cols = detect_overlaps([("a", "rect", box(0, 0, 1, 1)), ("b", "rect", box(2, 2, 3, 3))])
    check("rect-rect separated", len(cols) == 0, f"got {len(cols)}")

    # 3. exactly touching rectangles -> 1 touch (threshold=0)
    cols = detect_overlaps([("a", "rect", box(0, 0, 1, 1)), ("b", "rect", box(1, 0, 2, 1))])
    check("rect-rect touch", len(cols) == 1 and cols[0].relation == "touch"
          and cols[0].overlap_area == 0, f"got {cols}")

    # 4. text x text (two overlapping line bboxes) -> 1 overlap
    cols = detect_overlaps([("t1", "text", box(0, 0, 2, 1)), ("t2", "text", box(1, 0.5, 3, 1.5))])
    check("text-text overlap", len(cols) == 1 and cols[0].relation == "overlap", f"got {len(cols)}")

    # 5. text x rect -> 1
    cols = detect_overlaps([("t", "text", box(0, 0, 2, 1)), ("r", "rect", box(1, 0.5, 3, 2))])
    check("text-rect overlap", len(cols) == 1, f"got {len(cols)}")

    # 6. segment x rect (crossing) -> 1 collision (line-rect intersection
    #    area is 0, so relation is "touch"; the pair is still detected)
    cols = detect_overlaps([("s", "segment", LineString([(0, 1), (3, 1)])),
                            ("r", "rect", box(1, 0.5, 2, 1.5))])
    check("segment-rect crossing", len(cols) == 1, f"got {len(cols)}")

    # 7. label inside a node box -> "contain", NOT an occlusion
    cols = detect_overlaps([("label", "text", box(1, 1, 3, 2)),
                            ("node", "rect", box(0, 0, 4, 3))])
    check("label-in-node contain", len(cols) == 1 and cols[0].relation == "contain"
          and cols[0].a_kind == "text", f"got {cols}")

    # 8. degenerate zero-area: point inside rect; zero-length segment
    cols = detect_overlaps([("p", "segment", Point(1, 1)), ("r", "rect", box(0, 0, 2, 2))])
    check("point-in-rect", len(cols) == 1, f"got {len(cols)}")
    cols = detect_overlaps([("s", "segment", LineString([(1, 1), (1, 1)])),
                            ("r", "rect", box(0, 0, 2, 2))])
    check("zero-length-segment", len(cols) == 1, f"got {len(cols)}")

    # 9. circle x circle (buffered points) -> 1 overlap
    cols = detect_overlaps([("c1", "polygon", Point(0, 0).buffer(1.0)),
                            ("c2", "polygon", Point(1.5, 0).buffer(1.0))])
    check("circle-circle overlap", len(cols) == 1 and cols[0].relation == "overlap", f"got {len(cols)}")

    # 10. threshold distinguishes overlap vs touch: tiny overlap below threshold
    cols = detect_overlaps([("a", "rect", box(0, 0, 2, 2)), ("b", "rect", box(1.99, 0, 3, 2))],
                           threshold=0.05)
    check("threshold->touch", len(cols) == 1 and cols[0].relation == "touch", f"got {cols}")
    cols = detect_overlaps([("a", "rect", box(0, 0, 2, 2)), ("b", "rect", box(1.5, 0, 3, 2))],
                           threshold=0.05)
    check("threshold->overlap", len(cols) == 1 and cols[0].relation == "overlap", f"got {cols}")

    # 11. adjacent text lines (same block, index diff 1) -> touch, not overlap
    cols = detect_overlaps([("text:0:0", "text", box(0, 0, 4, 1)),
                            ("text:0:1", "text", box(0, 0.9, 4, 1.9))])
    check("adjacent-lines touch", len(cols) == 1 and cols[0].relation == "touch", f"got {cols}")
    # separate blocks, overlapping -> real overlap
    cols = detect_overlaps([("text:0:0", "text", box(0, 0, 4, 1)),
                            ("text:1:0", "text", box(2, 0.5, 6, 1.5))])
    check("cross-block text overlap", len(cols) == 1 and cols[0].relation == "overlap", f"got {cols}")


def test_end_to_end_pdf() -> None:
    print("[e2e] synthetic PDF via fitz")
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.draw_rect(fitz.Rect(10, 10, 100, 60), color=(0, 0, 1), width=1)      # overlap pair
    page.draw_rect(fitz.Rect(60, 30, 150, 80), color=(0, 0, 1), width=1)
    page.draw_rect(fitz.Rect(200, 150, 260, 190), color=(0, 0, 1), width=1)   # separated
    page.insert_text((70, 45), "overlapping text", fontsize=8)
    path = os.path.join(os.path.dirname(__file__), "_synth_test.pdf")
    doc.save(path)
    doc.close()
    rep = check_pdf_overlap(path)
    os.remove(path)
    check("e2e overlap found", rep.overlap_count >= 1,
          f"expected >=1 overlap, got {rep.overlap_count}")


def test_acceptance() -> None:
    print("[acceptance] every figure PDF, span-level (real glyph bboxes)")
    here = os.path.dirname(os.path.abspath(__file__))
    pdfs = sorted(os.path.join(here, "..", "examples", f)
                  for f in os.listdir(os.path.join(here, "..", "examples")) if f.endswith(".pdf"))
    pdfs += [os.path.join(here, "..", "..", "docs", "paper", "Img", "python",
                          "fig02_three_layer_coupling_v3.pdf")]
    for path in pdfs:
        rep = check_pdf_overlap(path, text_granularity="span")
        name = os.path.basename(path)
        print(f"    {name:38s} overlap={rep.overlap_count} "
              f"touch={rep.touch_count} contain={rep.contain_count}")
        check(f"acceptance {name} overlap==0", rep.overlap_count == 0,
              f"got {rep.overlap_count} spans/rects overlapping")


def main() -> int:
    test_geometry_cases()
    test_end_to_end_pdf()
    test_acceptance()
    if FAILS:
        print(f"\n{len(FAILS)} FAILURE(S)")
        return 1
    print("\nALL TESTS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
