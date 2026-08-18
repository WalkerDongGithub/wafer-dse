"""
Shared frozen dataclass contracts for the benchmark subsystem.

Every data row that crosses a boundary between generate_baseline.py,
rapidchiplet_checker.py, and compare_results.py MUST transit through
one of these two classes — never a bare dict.  This enforces the
AGENTS.md §5 hard rule: "禁止裸 dict 跨模块"。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


BenchKey: TypeAlias = tuple[str, str, str]  # (topology, size, params)


# =====================================================================
# Our strict-screen side — one row per configuration.
# =====================================================================
@dataclass(frozen=True)
class OurBaselineRow:
    """One screening verdict produced by `generate_baseline.py`."""

    topology: str
    """e.g. "mesh", "torus"."""

    size: str
    """e.g. "3x3", "4x4"."""

    params: str
    """Parameter-file stem, e.g. "ucie-32g"."""

    feasible: bool
    """True iff the joint screen accepts this design."""

    bottleneck: str
    """Human-readable binding-constraint summary when feasible=False."""

    def cache_key(self) -> BenchKey:
        """Primary key used to merge rows across CSVs."""
        return (self.topology, self.size, self.params)


# =====================================================================
# Independent-evaluation (RapidChiplet) side — one row per configuration.
# =====================================================================
@dataclass(frozen=True)
class RapidBaselineRow:
    """One independent-evaluation verdict produced by `rapidchiplet_checker.py`."""

    topology: str
    """e.g. "mesh", "torus"."""

    size: str
    """e.g. "3x3", "4x4"."""

    params: str
    """Parameter-file stem, e.g. "ucie-32g"."""

    rapidchiplet_feasible: bool
    """True iff independent perf+power accept this design."""

    perf_metrics: str
    """Independent throughput-proxy readout."""

    power_metrics: str
    """Independent split-class power readout."""

    thermal_note: str
    """Post-hoc thermal report (never flips the verdict)."""

    def cache_key(self) -> BenchKey:
        """Primary key used to merge rows across CSVs."""
        return (self.topology, self.size, self.params)


__all__ = ["OurBaselineRow", "RapidBaselineRow", "BenchKey"]
