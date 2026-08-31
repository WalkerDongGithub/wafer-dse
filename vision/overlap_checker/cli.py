"""CLI for the PDF overlap checker.

Usage:
    python3 -m vision.overlap_checker.cli figure.pdf [more.pdf ...] [--threshold T] [--report DIR]
    python3 -m vision.overlap_checker.cli vision/examples/*.pdf   # one command, all results
"""
from __future__ import annotations

import argparse
import os
import sys

from .checker import check_pdf_overlap


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="PDF element overlap detection")
    p.add_argument("pdfs", nargs="+", help="PDF files to check")
    p.add_argument("--threshold", type=float, default=0.0,
                   help="min intersection area (pt^2) to count as overlap (below = touch)")
    p.add_argument("--report", metavar="DIR", default=None,
                   help="write per-PDF report files into DIR")
    p.add_argument("--granularity", choices=["line", "span"], default="line",
                   help="text granularity: line (coarse) or span (glyph-run, "
                        "exposes in-line overlaps like math subscripts)")
    p.add_argument("-v", "--verbose", action="store_true", help="print every collision")
    args = p.parse_args(argv)

    rc = 0
    for path in args.pdfs:
        report = check_pdf_overlap(path, threshold=args.threshold,
                                   text_granularity=args.granularity)
        print(report.summary())
        if report.overlap_count:
            rc = 1
        if args.verbose:
            for c in report.collisions:
                print(f"    {c.relation:7s} {c.a} ({c.a_kind}) x {c.b} ({c.b_kind}) "
                      f"area={c.overlap_area:.3f} dist={c.distance:.3f}")
        if args.report:
            os.makedirs(args.report, exist_ok=True)
            stem = os.path.splitext(os.path.basename(path))[0]
            report.save(os.path.join(args.report, f"{stem}.overlap.txt"))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
