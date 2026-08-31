"""vision.overlap_checker: PDF element overlap detection tool (API).

Usage:
    from vision.overlap_checker import check_pdf_overlap
    report = check_pdf_overlap("figure.pdf", threshold=0.0)
    print(report.summary())
"""
from __future__ import annotations

from .checker import Collision, CollisionReport, check_pdf_overlap

__all__ = ["Collision", "CollisionReport", "check_pdf_overlap"]
__version__ = "0.1.0"
