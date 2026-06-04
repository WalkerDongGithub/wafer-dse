"""轻量配置读取器。

输入：JSON 或本项目 YAML 子集。
输出：Python dict。
目的：避免额外依赖，用户指令和封装工艺文件都走同一个读取入口。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _parse_scalar(value: str) -> Any:
    """把 YAML 字符串标量转换成 bool/int/float/list/str。"""
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [] if not inner else [_parse_scalar(x) for x in inner.split(",")]
    try:
        return float(value) if any(ch in value for ch in [".", "e", "E"]) else int(value)
    except ValueError:
        return value


def _minimal_yaml_load(text: str) -> dict[str, Any]:
    """读取缩进字典和行内 list；足够覆盖当前 DSE 配置。"""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, value = line.strip().split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if not value.strip():
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            parent[key] = _parse_scalar(value)
    return root


def load_config(path: str | Path) -> dict[str, Any]:
    """读取配置文件路径，返回 dict。"""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else _minimal_yaml_load(text)
