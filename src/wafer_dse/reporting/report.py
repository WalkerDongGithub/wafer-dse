"""运行结果报告生成。

输入：FeasibilityReport 列表。
输出：results.json、results.csv、report.md。
目的：让用户同时看到机器可读结果和带图的人工审查报告。
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from wafer_dse.models import FeasibilityReport


def write_reports(out_dir: str | Path, reports: list[FeasibilityReport]) -> None:
    """输入输出目录和报告列表，写出 JSON/CSV/Markdown。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = [_flat_row(r) for r in reports]

    # JSON 保留完整嵌套结构，方便后续程序读取。
    (out / "results.json").write_text(json.dumps([asdict(r) for r in reports], indent=2, ensure_ascii=False), encoding="utf-8")

    # CSV 保留关键字段，方便表格排序。
    if rows:
        with (out / "results.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    # Markdown 用 Mermaid 图和表格解释两关耦合过程。
    (out / "report.md").write_text(_markdown_report(reports, rows), encoding="utf-8")


def _flat_row(r: FeasibilityReport) -> dict:
    """把嵌套报告压平成 CSV 行。"""
    return {
        "feasible": r.feasible_potential,
        "topology": r.network.topology_name,
        "route": r.network.route,
        "ports": r.requirement.port_count or r.network.terminal_count,
        "target_gbps_per_port": r.requirement.target_nonblocking_gbps_per_port,
        "network_nonblocking_gbps_per_port": round(r.network.nonblocking_gbps_per_port, 3),
        "required_speedup": r.network.required_internal_speedup,
        "required_internal_800g_links": r.network.required_internal_800g_links,
        "internal_800g_link_budget": round(r.packaging.internal_800g_link_budget, 3),
        "external_800g_port_budget": round(r.packaging.external_800g_port_budget, 3),
        "die_area_mm2": round(r.packaging.die_area_mm2, 3),
        "power_w": round(r.packaging.power_w, 3),
        "certificate": r.network.certificate_status,
        "fail_reasons": ";".join(r.fail_reasons),
        "recommendation": r.recommendation,
    }


def _markdown_report(reports: list[FeasibilityReport], rows: list[dict]) -> str:
    """生成带 Mermaid 可视化的人工审查报告。"""
    feasible = sum(1 for r in reports if r.feasible_potential)
    lines = [
        "# DSE 运行结果报告",
        "",
        "## 1. 总览",
        "",
        f"- 候选数量：{len(reports)}",
        f"- 通过数量：{feasible}",
        "",
        "## 2. 两关耦合逻辑图",
        "",
        "```mermaid",
        "flowchart LR",
        "    A[用户需求<br/>带宽/功耗/严格程度/封装配置] --> B[体系结构级初筛<br/>拓扑无阻塞潜能]",
        "    B --> C[required speedup<br/>required internal links]",
        "    A --> D[封装级初筛<br/>面积/功耗/lane预算]",
        "    C --> E[耦合判断]",
        "    D --> E",
        "    E --> F[可行潜力 / 瓶颈原因]",
        "```",
        "",
        "## 3. 候选结果表",
        "",
    ]
    if not rows:
        return "\n".join(lines + ["无结果。"])

    headers = ["feasible", "topology", "route", "required_speedup", "required_internal_800g_links", "internal_800g_link_budget", "die_area_mm2", "power_w", "fail_reasons"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")

    lines += ["", "## 4. 候选瓶颈解释", ""]
    for row in rows:
        status = "通过" if row["feasible"] else "失败"
        lines.append(f"### {row['topology']} / {row['route']}：{status}")
        lines.append("")
        lines.append(f"- 网络需要 speedup：{row['required_speedup']}")
        lines.append(f"- 需要内部 800G-equivalent links：{row['required_internal_800g_links']}")
        lines.append(f"- 封装内部 link 预算：{row['internal_800g_link_budget']}")
        lines.append(f"- 估计面积/功耗：{row['die_area_mm2']} mm² / {row['power_w']} W")
        lines.append(f"- 失败原因：{row['fail_reasons'] or '无'}")
        lines.append(f"- 建议：{row['recommendation']}")
        lines.append("")
    return "\n".join(lines)
