"""Rust 求解器后端 —— 自动探测 wafer-solve 二进制并提供透明回退。

架构：
    - 模块级函数 `batch_derangement()` 和 `hungarian_min_cost()`
      对外与纯 Python 版本的签名完全兼容。
    - 优先使用 Rust 二进制（如果可用），否则静默回退到纯 Python。
    - 二进制路径缓存在模块级变量，避免重复查找。

二进制查找顺序：
    1. `WAFER_SOLVE_BIN` 环境变量（显式指定路径）
    2. `rust-solvers/target/release/wafer-solve`（相对于项目根）
    3. `rust-solvers/target/debug/wafer-solve`
    4. `PATH` 中的 `wafer-solve`

用法：
    from wafer_dse.architecture_model.solver.rust_backend import batch_derangement

    results = batch_derangement([matrix1, matrix2, ...])
    # results: list[tuple[float, list[int]]]
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 二进制发现
# ---------------------------------------------------------------------------

_SOLVER_BINARY: Optional[str] = None  # None=未查找, ""=没找到, str=路径


def _find_binary() -> Optional[str]:
    """查找 wafer-solve 二进制，结果缓存到 _SOLVER_BINARY。

    Returns:
        二进制路径字符串，如果未找到则返回 None。
    """
    global _SOLVER_BINARY

    # 已查找过
    if _SOLVER_BINARY is not None:
        return _SOLVER_BINARY if _SOLVER_BINARY else None

    # 1. 环境变量覆盖
    env_path = os.environ.get("WAFER_SOLVE_BIN")
    if env_path and Path(env_path).exists():
        _SOLVER_BINARY = env_path
        return env_path

    # 2. 开发路径（相对于本文件向上查找 rust-solvers/）
    this_dir = Path(__file__).resolve().parent
    for ancestor in [this_dir] + list(this_dir.parents):
        release = ancestor / "rust-solvers" / "target" / "release" / "wafer-solve"
        debug = ancestor / "rust-solvers" / "target" / "debug" / "wafer-solve"
        if release.exists():
            _SOLVER_BINARY = str(release)
            return str(release)
        if debug.exists():
            _SOLVER_BINARY = str(debug)
            return str(debug)

    # 3. PATH 查找
    for dirpath in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(dirpath) / "wafer-solve"
        if candidate.exists():
            _SOLVER_BINARY = str(candidate)
            return str(candidate)

    # 未找到
    _SOLVER_BINARY = ""
    return None


def is_rust_available() -> bool:
    """检查 Rust 二进制是否可用（供测试和诊断使用）。"""
    return _find_binary() is not None


# ---------------------------------------------------------------------------
# Rust 调用
# ---------------------------------------------------------------------------

def _call_rust(request: dict) -> dict:
    """发送 JSON 请求到 wafer-solve 二进制，返回解析后的响应字典。

    Raises:
        RuntimeError: 二进制不可用、调用失败或求解器返回错误。
    """
    binary = _find_binary()
    if binary is None:
        raise RuntimeError("wafer-solve binary not found")

    proc = subprocess.run(
        [binary],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=300,  # 大规模拓扑的宽松超时
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"wafer-solve 退出码={proc.returncode}: {proc.stderr.strip()}"
        )

    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError("wafer-solve 返回空输出")

    result = json.loads(stdout)

    if result.get("status") == "error":
        raise RuntimeError(f"求解器错误: {result.get('error')}")

    return result


# ---------------------------------------------------------------------------
# 公开 API —— 与纯 Python 版本签名兼容
# ---------------------------------------------------------------------------

def batch_derangement(
    matrices: list[list[list[float]]],
) -> list[tuple[float, list[int]]]:
    """对多个权重矩阵批量求解 max-weight derangement。

    优先使用 Rust 批量求解（一次子进程调用），不可用时逐个使用纯 Python。

    Args:
        matrices: 权重矩阵列表，每个矩阵为 N×N 的 list[list[float]]。

    Returns:
        list of (max_weight, assignment)，与输入矩阵一一对应。

    Raises:
        ValueError: 某个矩阵无效。
        RuntimeError: 无有效 derangement（例如 N=1）。
    """
    # --- Rust 路径 ---
    if is_rust_available():
        try:
            result = _call_rust({
                "command": "batch_derangement",
                "matrices": matrices,
            })
            if "results" not in result:
                raise RuntimeError(f"响应中缺少 'results' 字段: {result}")
            return [
                (r["max_weight"], r["assignment"])
                for r in result["results"]
            ]
        except (RuntimeError, KeyError, json.JSONDecodeError):
            # Rust 调用失败 → 回退到纯 Python
            pass

    # --- 纯 Python 回退 ---
    from wafer_dse.architecture_model.solver.algorithm.derangement import (
        max_weight_derangement,
    )
    return [max_weight_derangement(m) for m in matrices]


def hungarian_min_cost(
    matrix: list[list[float]],
) -> tuple[float, list[int]]:
    """求 N×N 方阵的最小成本完美匹配。

    优先使用 Rust，不可用时使用纯 Python。

    Args:
        matrix: N×N 成本矩阵。

    Returns:
        (min_total_cost, assignment)。
    """
    if is_rust_available():
        try:
            result = _call_rust({
                "command": "hungarian",
                "matrix": matrix,
            })
            return result["total_cost"], result["assignment"]
        except (RuntimeError, KeyError, json.JSONDecodeError):
            pass

    from wafer_dse.architecture_model.solver.algorithm.hungarian import (
        hungarian_min_cost,
    )
    return hungarian_min_cost(matrix)
