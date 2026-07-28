"""DSE 汇总写入器 — 机器可读的 JSON 输出。

每设计一行，直接:
    import pandas as pd
    df = pd.read_json("dse_results/summary.json")
    df.plot.scatter(x="cost_index", y="nonblock_bw_gbps")
"""

from __future__ import annotations

import json
import os
from typing import Any


class SummaryWriter:
    """收集所有设计点，最后 dump 一个 summary.json。"""

    def __init__(self, output_dir: str = "dse_results"):
        self._output_dir = output_dir
        self._designs: list[dict[str, Any]] = []
        self._config: dict[str, Any] = {}

    def set_config(self, cfg: dict) -> None:
        self._config = dict(cfg)

    def add(self, record: dict[str, Any]) -> None:
        self._designs.append(record)

    def dump(self) -> str:
        os.makedirs(self._output_dir, exist_ok=True)
        path = os.path.join(self._output_dir, "summary.json")
        data = {
            "config": self._config,
            "designs": self._designs,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path
