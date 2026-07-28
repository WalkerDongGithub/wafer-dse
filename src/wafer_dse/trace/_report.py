"""Per-design report logger — 一个方案一个 .dse 文件。"""

from __future__ import annotations

import os
from typing import Any

from ._base import DseLogger


class ReportDseLogger(DseLogger):
    """每个设计方案输出一个独立的 .dse 报告文件。

    格式: 约束分类表格
      ════════════════════
       Constraint Category
      ════════════════════
      Parameter     Value        Unit    Status
      ─────────     ─────        ────    ──────
      ...
    """

    def __init__(self, output_dir: str = "dse_results"):
        self._output_dir = output_dir
        self._f = None
        self._design_label = ""

    # ------------------------------------------------------------------
    # 设计生命周期
    # ------------------------------------------------------------------

    def start_design(self, label: str) -> None:
        os.makedirs(self._output_dir, exist_ok=True)
        path = os.path.join(self._output_dir, f"{label}.dse")
        self._f = open(path, "w")
        self._design_label = label
        self._write(f"═══════════════════════════════════════════\n")
        self._write(f"  DSE Report: {label}\n")
        self._write(f"═══════════════════════════════════════════\n\n")

    def finish_design(self) -> None:
        if self._f:
            self._f.close()
            self._f = None

    # ------------------------------------------------------------------
    # 约束表格
    # ------------------------------------------------------------------

    def constraint_table(self, title: str, rows: list[tuple[str, str, str, str]]) -> None:
        """写入一个约束分类表格。

        rows: [(parameter, value, unit, status), ...]
        status: "✓" / "✗" / "—"
        """
        if not self._f:
            return

        self._write(f"── {title} ──\n")
        # compute widths
        col_widths = [12, 14, 8, 6]
        header = ("Parameter", "Value", "Unit", "")
        self._write(
            f"  {header[0]:<{col_widths[0]}}  "
            f"{header[1]:<{col_widths[1]}}  "
            f"{header[2]:<{col_widths[2]}}  "
            f"{header[3]}\n"
        )
        self._write(
            f"  {'─'*col_widths[0]}  "
            f"{'─'*col_widths[1]}  "
            f"{'─'*col_widths[2]}  "
            f"{'─'*col_widths[3]}\n"
        )

        for param, val, unit, status in rows:
            self._write(
                f"  {param:<{col_widths[0]}}  "
                f"{val:<{col_widths[1]}}  "
                f"{unit:<{col_widths[2]}}  "
                f"{status}\n"
            )
        self._write("\n")

    # ------------------------------------------------------------------
    # 兼容 DseLogger ABC
    # ------------------------------------------------------------------

    def section(self, title: str) -> None:
        self._write(f"\n{'='*50}\n  {title}\n{'='*50}\n\n")

    def check(self, name: str, passed: bool, **kv: Any) -> None:
        rows = []
        for k, v in kv.items():
            rows.append((k, str(v), "", "✓" if passed else "✗"))
        self.constraint_table(name, rows)

    def info(self, message: str) -> None:
        self._write(f"  {message}\n")

    def table(self, headers: list[str], rows: list[list[Any]]) -> None:
        widths = [max(len(h), max((len(str(c)) for c in col))) for h, col in zip(headers, zip(*rows))]
        header_line = "  ".join(f"{h:<{w}}" for h, w in zip(headers, widths))
        self._write(f"  {header_line}\n")
        self._write(f"  {'─' * sum(widths)}\n")
        for row in rows:
            self._write(f"  {'  '.join(str(c).ljust(w) for c, w in zip(row, widths))}\n")
        self._write("\n")

    def result(self, total: int, feasible: int, frontier: int) -> None:
        self._write(f"\n  {total} designs, {feasible} feasible, {frontier} on frontier\n")

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _write(self, text: str) -> None:
        if self._f:
            self._f.write(text)
