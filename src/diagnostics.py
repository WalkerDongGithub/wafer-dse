"""约束账本 —— 给定 B 的解（L 值），逐约束报告关键值.

每个模型 __init__ 预计算的系数 + L 值，即可解析出每个约束家族的
利用率 / 余量。不重解 LP。这是瓶颈诊断（B 增长时谁先碰壁）的数据源。

注意：L 值必须来自 min ΣL 的解（真实包络），feasibility 的任意可行解
会高估负载。
"""

from __future__ import annotations

import numpy as np


def solve_diagnostic(models, B: float):
    """直调 engine 解 min ΣL（真实包络），返回 (ctx, sol, L_vals)。

    不走 Runner——缓存 key 不含 objective，会被无目标的可行性解污染。
    且无目标求解 CLARABEL 不返回 duals，绑定诊断必须用本解。
    """
    from lp import Ctx, CvxSolver

    ctx = Ctx()
    for m in models:
        m.build(ctx, float(B))
    sol = CvxSolver().solve(ctx, objective=sum(ctx["L"]), maximize=False)
    if sol.variables is None or "L" not in sol.variables:
        return ctx, sol, {}
    return ctx, sol, {i: v for i, v in enumerate(sol.variables["L"])}


def solve_min_L(models, B: float) -> dict[int, float]:
    return solve_diagnostic(models, B)[2]


def binding_with_meaning(ctx, duals: dict[str, float],
                         top_k: int = 5) -> list[tuple[str, float, str]]:
    """绑定约束按 |dual| 降序，附 meaning。"""
    by_name = {c.name: c for c in ctx.constraints}
    items = []
    for n, v in duals.items():
        c = by_name.get(n)
        items.append((n, v, c.meaning if c else ""))
    items.sort(key=lambda t: -abs(t[1]))
    return items[:top_k]


# ── 性能包络 ──────────────────────────────────────────────────────

def perf_ledger(L_vals: dict[int, float]) -> dict:
    """包络负载：max L 与最热链路。"""
    if not L_vals:
        return {"max_L": float("inf"), "argmax_link": None}
    am = max(L_vals, key=L_vals.get)
    return {"max_L": float(L_vals[am]), "argmax_link": am}


# ── μbump ─────────────────────────────────────────────────────────

def bump_ledger(bump, L_vals: dict[int, float], B: float,
                die_labels: list[str] | None = None) -> list[dict]:
    """每 die 一条账：信号 bump / 功率 bump / 可用数 / 占用率.

    coeff[e] = (1/lr_e)·(1 + ppl/(V·I))
    信号部分 = B·Σ(1/lr)·L，功率部分 = B·Σ(1/lr)(ppl/(V·I))·L
    """
    rows = []
    for k, links in enumerate(bump._incid):
        coeffs = bump._coeffs[k]
        used = B * sum(coeffs[e] * L_vals.get(e, 0.0) for e in links)
        rows.append({
            "die": die_labels[k] if die_labels and k < len(die_labels) else f"#{k}",
            "used": used,
            "rhs": bump._rhs[k],
            "util": used / bump._rhs[k] if bump._rhs[k] else float("inf"),
        })
    return rows


# ── 热网络 ────────────────────────────────────────────────────────

def thermal_ledger(therm, L_vals: dict[int, float], B: float,
                   T_max: float | None = None) -> list[dict]:
    """每 die 一条账：T_i 与 margin_i.

    T_i = T_max − (rhs_i − used_i)，used_i = B·Σ link_coeff[i,e]·L[e]
    （link_coeff 单位 K/Gbps，scale 恒为 B）
    """
    net = therm._net
    rows = []
    for i in range(net.G_inv.shape[0]):
        used = B * sum(
            net.link_coeff[i, e] * L_vals.get(e, 0.0)
            for e in range(net.link_coeff.shape[1]))
        rhs = float(net.rhs_ambient[i])
        margin = rhs - used
        rows.append({
            "die": i,
            "T": None if T_max is None else T_max - margin,
            "margin": margin,
            "rhs": rhs,
        })
    return rows


# ── 汇总 ──────────────────────────────────────────────────────────

def full_ledger(models, L_vals: dict[int, float], B: float,
                T_max: float = 358.15) -> dict:
    """对一组模型出汇总账本：每约束家族的紧张程度。"""
    out: dict = {"perf": None, "bump": None, "therm": None}
    for m in models:
        name = type(m).__name__
        if name == "EnvelopeModel":
            out["perf"] = perf_ledger(L_vals)
        elif name == "BumpModel":
            out["bump"] = bump_ledger(m, L_vals, B)
        elif name == "SteadyStateModel":
            out["therm"] = thermal_ledger(m, L_vals, B, T_max)
    return out


def print_ledger(ledger: dict, B: float, title: str = "") -> None:
    """控制台打印账本摘要。"""
    print(f"\n── 约束账本 @ B={B:.0f} Gbps {title} ──")
    if ledger.get("perf"):
        p = ledger["perf"]
        print(f"  性能:  max L = {p['max_L']:.2f} (链路 {p['argmax_link']})")
    if ledger.get("bump"):
        rows = ledger["bump"]
        worst = max(rows, key=lambda r: r["util"])
        print(f"  μbump: {len(rows)} 条约束, 最紧 die {worst['die']}: "
              f"{worst['used']:.0f}/{worst['rhs']:.0f} bumps "
              f"(占用 {worst['util']*100:.1f}%)")
    if ledger.get("therm"):
        rows = ledger["therm"]
        worst = min(rows, key=lambda r: r["margin"])
        print(f"  热:    {len(rows)} 个 die, 最热 die {worst['die']}: "
              f"T={worst['T']:.1f}K (margin {worst['margin']:+.1f}K)")
