"""DSE 追踪日志器 — ABC 驱动的结构化日志。

用法:
    from wafer_dse.trace import get_logger
    log = get_logger("report", output_dir="dse_results")
    log.start_design("DF_a2_p2_h1_g3")
    log.constraint_table("Architecture", [...])
    log.finish_design()
"""

from ._base import DseLogger
from ._console import ConsoleDseLogger
from ._report import ReportDseLogger
from ._summary import SummaryWriter


def get_logger(kind: str = "console", **kwargs) -> DseLogger:
    if kind == "console":
        return ConsoleDseLogger(**kwargs)
    if kind == "report":
        return ReportDseLogger(**kwargs)
    raise ValueError(f"unknown logger kind: {kind!r}")


__all__ = ["DseLogger", "ConsoleDseLogger", "ReportDseLogger", "get_logger"]
