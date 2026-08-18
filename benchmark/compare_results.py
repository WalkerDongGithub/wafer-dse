"""
Compare our "Joint Constraint" Baseline with RapidChiplet's "Independent" Evaluation.

Reads `OurBaselineRow` from our_baseline_matrix.csv and `RapidBaselineRow`
from rapidchiplet_matrix.csv, then produces:
  * comparison_results.csv   — one row per config with aligned verdicts
  * reports/core_value_report.md — narrative summary of the divergence

Cross-module data contract: every row is a frozen dataclass from
`benchmark/contracts.py`; we never manually manipulate bare dict keys
across files (AGENTS.md §5 hard rule).
"""

from __future__ import annotations

import csv
import os
import sys
from dataclasses import asdict
from typing import Any

THIS_DIR = os.path.dirname(__file__)
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from contracts import OurBaselineRow, RapidBaselineRow


# -------------------------------------------------------------------
# CSV -> list[contract] loaders.  Key invariant: if the CSV was written
# with asdict(XxxBaselineRow(...)) then XxxBaselineRow(**row) MUST round-
# trip losslessly — enforced by tests/benchmark/test13_contracts.md.
# -------------------------------------------------------------------
def _load_our_matrix(filepath: str) -> list[OurBaselineRow]:
    rows: list[OurBaselineRow] = []
    if not os.path.exists(filepath):
        return rows
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for d in reader:
            d["feasible"] = d["feasible"].strip().lower() == "true"
            rows.append(OurBaselineRow(**d))
    return rows


def _load_rapid_matrix(filepath: str) -> list[RapidBaselineRow]:
    rows: list[RapidBaselineRow] = []
    if not os.path.exists(filepath):
        return rows
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for d in reader:
            d["rapidchiplet_feasible"] = d["rapidchiplet_feasible"].strip().lower() == "true"
            rows.append(RapidBaselineRow(**d))
    return rows


def main() -> None:
    base_dir = os.path.dirname(__file__)
    results_dir = os.path.join(base_dir, 'results')
    reports_dir = os.path.join(base_dir, 'reports')

    our_rows = _load_our_matrix(os.path.join(results_dir, 'our_baseline_matrix.csv'))
    rapid_rows = _load_rapid_matrix(os.path.join(results_dir, 'rapidchiplet_matrix.csv'))

    if not our_rows or not rapid_rows:
        print("Error: Missing baseline or rapidchiplet results.  Run both scripts first.")
        return

    # Key-by cache_key for 1:1 alignment.
    rapid_lookup = {r.cache_key(): r for r in rapid_rows}

    comparison_rows: list[dict[str, Any]] = []
    divergence_cases: list[dict[str, Any]] = []

    for ours in our_rows:
        theirs = rapid_lookup.get(ours.cache_key())
        if theirs is None:
            print(f"Warning: Missing RapidChiplet data for {ours.cache_key()}")
            continue

        if not ours.feasible and theirs.rapidchiplet_feasible:
            case_type = "CRITICAL_DIVERGENCE"
            divergence_cases.append({
                "topology": ours.topology, "size": ours.size, "params": ours.params,
                "our_bottleneck": ours.bottleneck,
                "rapidchiplet_info": (
                    f"Perf[{theirs.perf_metrics}] Power[{theirs.power_metrics}] {theirs.thermal_note}"
                ),
                "explanation": (
                    "Passes independent perf+power check, yet violates at least one "
                    "binding coupled constraint in our joint screen — this is a false "
                    "positive from the independent-evaluation pipeline."
                ),
            })
        elif ours.feasible and theirs.rapidchiplet_feasible:
            case_type = "CONSISTENT_FEASIBLE"
        elif (not ours.feasible) and (not theirs.rapidchiplet_feasible):
            case_type = "CONSISTENT_INFEASIBLE"
        else:
            case_type = "WEIRD_CASE"  # we feasible, they infeasible — rare

        comparison_rows.append({
            "topology": ours.topology, "size": ours.size, "params": ours.params,
            "our_verdict": "Feasible" if ours.feasible else "Infeasible",
            "rapidchiplet_verdict": "Feasible" if theirs.rapidchiplet_feasible else "Infeasible",
            "case_type": case_type,
            "our_details": ours.bottleneck,
            "rapidchiplet_details": (
                f"Perf[{theirs.perf_metrics}] Power[{theirs.power_metrics}] {theirs.thermal_note}"
            ),
        })

    # --- Write comparison CSV ---
    comparison_file = os.path.join(results_dir, "comparison_results.csv")
    with open(comparison_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(comparison_rows[0].keys()))
        writer.writeheader()
        writer.writerows(comparison_rows)
    print(f"Comparison results saved to {comparison_file}")

    # --- Write core-value Markdown report ---
    report_file = os.path.join(reports_dir, "core_value_report.md")
    total = len(comparison_rows)
    critical = len(divergence_cases)
    consistent = total - critical
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Core Value Report: Joint Constraint Screen vs Independent Evaluation\n\n")
        f.write(
            "Grid: 2 topologies × 2 sizes × 6 real-world parameter sets = 24 configurations.\n"
            "Toy calibration parameters are deliberately excluded from all paper experiments.\n\n"
        )
        f.write("## 1. Summary\n")
        f.write(f"- **Total cases tested**: {total}\n")
        f.write(f"- **Critical divergences**: {critical}  "
                f"(pass independent check, fail joint screen = false positives)\n")
        f.write(f"- **Consistent verdicts**: {consistent}\n\n")

        f.write("## 2. Methodological positioning\n")
        f.write(
            "The **critical-divergence cases** are not our method being \"stricter\" — they are "
            "cases where the independent evaluator structurally *cannot see* a constraint "
            "because it never shares state across its three evaluation channels (perf, power, "
            "thermal).  Our joint screen makes those binding constraints visible.\n\n"
        )

        f.write("## 3. Divergence cases\n")
        if divergence_cases:
            for i, case in enumerate(divergence_cases, 1):
                f.write(f"### Case {i}: {case['topology']} – {case['size']} – {case['params']}\n")
                f.write(f"- Our verdict            : **Infeasible**\n")
                f.write(f"- Our binding constraint : {case['our_bottleneck']}\n")
                f.write(f"- Independent verdict    : Feasible\n")
                f.write(f"- Independent readout    : {case['rapidchiplet_info']}\n")
                f.write(f"- Nature of the divergence: {case['explanation']}\n\n")
        else:
            f.write("No divergences on this grid — investigate whether the coupling formulation is binding enough.\n")

        f.write("## 4. Conclusion\n")
        f.write(
            f"On this 24-case grid, {critical} / {total} configurations escape a "
            "RapidChiplet-style independent evaluation yet violate at least one coupled "
            "physical or routing constraint.  The existence of these cases is evidence that "
            "chiplet DSE pipelines which evaluate perf, power, and thermal in separate "
            "channels leak false positives into later design stages — exactly the behaviour "
            "a strict upfront feasibility screen is meant to prevent.\n"
        )

    print(f"Core value report saved to {report_file}")


if __name__ == '__main__':
    main()
