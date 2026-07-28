"""Console DSE Logger — 带颜色和缩进的终端输出。"""

from __future__ import annotations

import sys
from typing import Any

from ._base import DseLogger


# ANSI
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"

_CHECK = "✓"
_CROSS = "✗"
_INDENT = "  "


class ConsoleDseLogger(DseLogger):
    """终端日志器。

    输出格式:
      ── Phase N: Description ──
        ✓ item   key=val key=val
        ✗ item   key=val → reason
      ── Result ──
      total | feasible | frontier
    """

    def __init__(self, stream=None):
        self._stream = stream or sys.stdout
        self._depth = 0

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def section(self, title: str) -> None:
        self._writeln("")
        self._writeln(f"{_BOLD}── {title} ──{_RESET}")

    def check(self, name: str, passed: bool, **kv: Any) -> None:
        mark = f"{_GREEN}{_CHECK}{_RESET}" if passed else f"{_RED}{_CROSS}{_RESET}"
        details = "  ".join(f"{_DIM}{k}={v}{_RESET}" for k, v in kv.items())
        self._writeln(f"{_INDENT}{mark} {name}  {details}")

    def info(self, message: str) -> None:
        self._writeln(f"{_INDENT}{_DIM}{message}{_RESET}")

    def table(self, headers: list[str], rows: list[list[Any]]) -> None:
        # compute column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))

        # header
        header_line = "  ".join(
            f"{_BOLD}{h:<{w}}{_RESET}" for h, w in zip(headers, widths)
        )
        self._writeln("")
        self._writeln(f"{_INDENT}{header_line}")
        self._writeln(f"{_INDENT}{_DIM}{'-' * sum(widths)}{_RESET}")

        # rows
        for row in rows:
            line = "  ".join(
                str(cell).ljust(widths[i]) for i, cell in enumerate(row)
            )
            self._writeln(f"{_INDENT}{line}")

    def result(self, total: int, feasible: int, frontier: int) -> None:
        self._writeln("")
        self._writeln(
            f"{_BOLD}  {total}{_RESET} designs enumerated, "
            f"{_GREEN}{feasible}{_RESET} feasible, "
            f"{_YELLOW}{frontier}{_RESET} on Pareto frontier"
        )
        self._writeln("")

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _writeln(self, text: str) -> None:
        self._stream.write(text + "\n")
        self._stream.flush()
