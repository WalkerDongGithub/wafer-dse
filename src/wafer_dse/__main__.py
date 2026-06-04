"""命令行入口。

输入：--config 指向用户需求配置。
输出：在配置指定目录下生成 JSON/CSV/Markdown 可视化报告。
目的：提供一个最小可运行的 DSE 用户界面。
"""

from __future__ import annotations

import argparse
import json

from wafer_dse.user_interface.driver import reports_as_dicts, run


def main() -> None:
    """解析配置路径并运行 DSE。"""
    parser = argparse.ArgumentParser(description="晶圆级交换机：体系结构级 + 封装级耦合初筛")
    parser.add_argument("--config", default="configs/example_user_request.yaml")
    args = parser.parse_args()
    reports = run(args.config)
    summary = {
        "candidate_count": len(reports),
        "feasible_count": sum(1 for r in reports if r.feasible_potential),
        "best": reports_as_dicts([reports[0]])[0] if reports else None,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
