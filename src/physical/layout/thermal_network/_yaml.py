"""YAML 热网络组装器 —— config/thermal/*.yaml → ThermalNetwork（schema v1）.

存在意义：
  把"传热路径"写成配置文件（用户层一眼看懂散热逻辑），组装器翻译成
  G·T = P + b 的 (G, b)。3D/2.5D 同一 schema——nodes（die/stack/boundary）
  + edges（face_adjacency / vertical_chain / tsv / hybrid / ground），
  差异只在节点/边类型，结构同一。

怎么用：
  net = build_thermal_from_yaml("config/thermal/2p5d-two-die.yaml")
  # → ThermalNetwork（G_inv / rhs_ambient / link_coeff 已预计算）

读者指南：
  - 想理解 schema 字段 → 读 config/thermal/*.yaml 示例（本模块 docstring 下）
  - 想理解边类型 → 热阻公式库 → 读 _EDGE_BUILDERS
  - 想理解 M-矩阵校验 → ThermalNetworkBuilder.precompute/_make_network
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

from physical.config.spec_thermal import T_JUNCTION_MAX_K
from physical.layout.thermal_network._mfit_system import DiePlacement
from physical.layout.thermal_network.builder import ThermalNetworkBuilder


def build_thermal_from_yaml(path: str | Path) -> "ThermalNetwork":
    """读 YAML 热配置 → 组装 G/b → 预计算 ThermalNetwork.

    Args:
        path: config/thermal/*.yaml 路径。

    Returns:
        ThermalNetwork（G_inv ≥ 0，M-矩阵不变量已校验）。

    Raises:
        ValueError: 未知节点/边类型、无散热路径（G 非对角占优）、
            边引用不存在的节点。
    """
    d = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    # -- 节点：自由节点（die/stack/heatsink，进 G）与边界节点（boundary，固定温度）--
    free_ids: list[str] = []          # die/stack/heatsink，按声明顺序 → G 索引
    free_geom: list[DiePlacement] = []  # 面邻接几何（x/y/w/h）
    free_layers: dict[str, int] = {}  # stack 层数（3D 集总，v1 仅记录）
    boundary_t: dict[str, float] = {}  # boundary 节点温度

    for node in d.get("nodes", []):
        nid = node["id"]
        ntype = node["type"]
        if ntype in ("die", "stack", "heatsink"):
            g = node.get("geometry", {})
            free_ids.append(nid)
            free_geom.append(DiePlacement(nid,
                                          float(g.get("x_mm", 0.0)),
                                          float(g.get("y_mm", 0.0)),
                                          float(g.get("w_mm", 12.0)),
                                          float(g.get("h_mm", 12.0))))
            if ntype == "stack":
                free_layers[nid] = int(node.get("layers", 1))
        elif ntype == "boundary":
            boundary_t[nid] = float(node["temperature_k"])
        else:
            raise ValueError(
                f"未知节点类型 '{ntype}'（可选 die/stack/heatsink/boundary）")

    n = len(free_ids)
    if n == 0:
        raise ValueError("至少需要一个 die/stack 节点")
    idx = {nid: i for i, nid in enumerate(free_ids)}

    G = np.zeros((n, n))
    b = np.zeros(n)

    # -- 边：类型 → 热阻公式库 --
    for edge in d.get("edges", []):
        etype = edge["type"]
        if etype == "face_adjacency":
            a, bb = edge["between"]
            if a not in idx or bb not in idx:
                raise ValueError(f"face_adjacency 引用未知节点 {a}/{bb}")
            g_lat = _face_adjacency(free_geom[idx[a]], free_geom[idx[bb]],
                                    edge.get("k_interposer_w_mk", 150.0),
                                    edge.get("t_interposer_mm", 0.1))
            if g_lat > 0:
                _connect(G, idx, a, bb, g_lat)
        elif etype in ("vertical_chain", "ground"):
            # 纵向集总：g = 1/R_vert（或直接 g），进对角；边界温度进 b
            src = edge["from"] if "from" in edge else edge.get("at")
            if src not in idx:
                raise ValueError(f"{etype} 引用未知节点 '{src}'")
            i = idx[src]
            if "r_vert_k_per_w" in edge:
                g = 1.0 / float(edge["r_vert_k_per_w"])
            else:
                g = float(edge["g_w_per_k"])
            G[i, i] += g
            dst = edge.get("to")
            t_amb = boundary_t.get(dst, d.get("t_ambient_k", 300.0))
            b[i] += g * t_amb
        elif etype in ("tsv", "hybrid"):
            # 3D 层间纵向（§十四 展开形态）：两自由节点间并联
            # R = r_via/n_vias（或直接 r_tsv_k_per_w），g = 1/R
            a, bb = edge["between"]
            if a not in idx or bb not in idx:
                raise ValueError(f"{etype} 引用未知节点 {a}/{bb}")
            if "r_tsv_k_per_w" in edge:
                g = 1.0 / float(edge["r_tsv_k_per_w"])
            else:
                g = float(edge["n_vias"]) / float(edge["r_via_k_per_w"])
            _connect(G, idx, a, bb, g)
        elif etype in ("tim", "lid", "heatsink_ambient"):
            # 散热链显式（§十五）：tim/lid = die→heatsink 段（1/R），
            # heatsink_ambient = heatsink→环境（r_sink 或 h·A）。to 自由/边界。
            a = edge["from"]
            if a not in idx:
                raise ValueError(f"{etype} 引用未知节点 '{a}'")
            i = idx[a]
            dst = edge.get("to")

            def _g(edge) -> float:
                if "r_tim_k_per_w" in edge:
                    return 1.0 / float(edge["r_tim_k_per_w"])
                if "r_sink_k_per_w" in edge:
                    return 1.0 / float(edge["r_sink_k_per_w"])
                if "h_w_per_m2k" in edge:
                    return float(edge["h_w_per_m2k"]) * float(edge["area_m2"])
                return float(edge["g_w_per_k"])

            g = _g(edge)
            if dst in idx:
                # 两自由节点间（die→heatsink）
                _connect(G, idx, a, dst, g)
            else:
                # 到边界（heatsink→ambient）：进对角 + b 贡献
                G[i, i] += g
                t_amb = boundary_t.get(dst, d.get("t_ambient_k", 300.0))
                b[i] += g * t_amb
        else:
            raise ValueError(
                f"未知边类型 '{etype}'（可选 face_adjacency/vertical_chain/"
                f"ground/tsv/hybrid/tim/lid/heatsink_ambient）")

    # -- M-矩阵校验：每节点必须有散热路径（对角元 > 0）--
    if np.any(np.diag(G) <= 0):
        bad = [free_ids[i] for i in range(n) if G[i, i] <= 0]
        raise ValueError(f"节点 {bad} 无散热路径（G 对角非正）——检查 vertical_chain")

    # -- 预计算 ThermalNetwork（G⁻¹ ≥ 0 校验在 _make_network）--
    t_max = float(d.get("t_max_k", T_JUNCTION_MAX_K))
    return ThermalNetworkBuilder.precompute(G, b, t_max, {}, 0)


def _connect(G: np.ndarray, idx: dict[str, int],
             a: str, b: str, g: float) -> None:
    """两自由节点间热导装配：进对角 + 非对角（M-矩阵结构）。"""
    i, j = idx[a], idx[b]
    G[i, i] += g
    G[j, j] += g
    G[i, j] -= g
    G[j, i] -= g


def _face_adjacency(a: DiePlacement, bb: DiePlacement,
                    k_interposer: float, t_interposer_mm: float) -> float:
    """面邻接热导：k·overlap·t / (d_a/2 + d_b/2 + gap)（MFIT 式半单元串联）.

    与 AnalyticNetworkBuilder._lateral_conductance 同公式；单位换算
    mm → m（k 用 W/mK）。
    """
    k = float(k_interposer)
    t = float(t_interposer_mm) * 1e-3
    tol = 1e-4

    def overlap(lo1, hi1, lo2, hi2) -> float:
        return max(0.0, min(hi1, hi2) - max(lo1, lo2))

    # y 方向相邻（共享水平边）→ 用 x 向 overlap
    ov_x = overlap(a.x, a.x + a.w, bb.x, bb.x + bb.w)
    if ov_x > tol:
        gap = bb.y - (a.y + a.h)
        if gap >= -tol:
            return k * ov_x * t / (a.h / 2 + bb.h / 2 + max(gap, 0.0))
        gap = a.y - (bb.y + bb.h)
        if gap >= -tol:
            return k * ov_x * t / (a.h / 2 + bb.h / 2 + max(gap, 0.0))

    # x 方向相邻 → 用 y 向 overlap
    ov_y = overlap(a.y, a.y + a.h, bb.y, bb.y + bb.h)
    if ov_y > tol:
        gap = bb.x - (a.x + a.w)
        if gap >= -tol:
            return k * ov_y * t / (a.w / 2 + bb.w / 2 + max(gap, 0.0))
        gap = a.x - (bb.x + bb.w)
        if gap >= -tol:
            return k * ov_y * t / (a.w / 2 + bb.w / 2 + max(gap, 0.0))

    return 0.0
