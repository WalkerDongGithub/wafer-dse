"""诊断原语 —— 给定 B，解 min ΣL，返回 L* + margin + binding。

存在意义：
  这是 sensitivity 的计算基础（闭式 λ_j = 1/(A_j·L*)）。在固定 B 下解
  min ΣL 拿到真实包络负载 L*，再对每条物理约束报 margin（rhs − lhs）与
  绑定约束（物理约束 margin≈0 优先 + duals 非零辅助，按约束名前缀归到
  模型家族）。不重解 LP 之外的任何东西——这是瓶颈诊断（B 增长时谁先碰壁）
  的数据源。

用法：
    diag = solve_diagnostic(models, B)
    diag.L_star    # 包络负载 {link_idx: load}
    diag.margins   # 物理约束 {constraint_name: rhs - lhs}
    diag.binding   # 绑定约束 [(name, family, dual, meaning), ...]

读者指南：
  - 核心原语 → 读 solve_diagnostic（本文件唯一求解入口）。
  - 约束名前缀归类 → 读 constraint_family。
  - 账本打印（full_ledger / print_ledger / *_ledger）→ 实验编排用，可跳过。

关键坑（test08 三个）：
  1. 无目标求解的 duals 不可靠——绑定诊断必须用 min ΣL 解，本原语固定用
     objective=sum(L), maximize=False。
  2. infeasible 时 duals 是 Farkas 证书、不是绑定约束——binding 只在
     feasible=True 时有语义，infeasible 时返回空。
  3. binding 不是光秃秃的 duals key 列表——每条都带模型家族归类。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from problem import Ctx, CvxSolver

if TYPE_CHECKING:
    from problem.ctx import LinearC

# 物理约束家族 = 约束名前缀 → 模型家族。顺序无关（各前缀互不重叠），
# 但 route 放在 c4 之前是防御性的：route_c4pad_* 属于布线家族，不属于 C4。
_PHYS_FAMILIES = ("bump", "therm", "route", "c4")

_FEASIBLE = ("optimal", "optimal_inaccurate")

# margin ≈ 0 的绝对容差：物理约束 rhs−lhs 的绝对值小于它就算"取等"。
_MARGIN_EPS = 1e-6


# ========================================================================
# 这部分是什么？
#   诊断原语的结构化返回值。BindingInfo 是一条绑定约束的完整语义，
#   DiagnosticResult 是一问一答：给定 B，min ΣL 解出了什么。
# ========================================================================

@dataclass(frozen=True)
class BindingInfo:
    """一条绑定约束：名字 + 模型家族 + 对偶值 + 物理含义。"""

    name: str
    family: str
    dual: float
    meaning: str


@dataclass(frozen=True)
class DiagnosticResult:
    """诊断原语的一问一答。

    L_star   — 包络负载 {link_idx: load}，infeasible 时为空。
    margins  — 物理约束余量 {constraint_name: rhs − lhs}，infeasible 时为空。
    binding  — 绑定约束（按 |dual| 降序），infeasible 时为空。
    """

    B: float
    feasible: bool
    L_star: dict[int, float]
    margins: dict[str, float]
    binding: tuple[BindingInfo, ...]


# ========================================================================
# 这部分是什么？
#   诊断原语本体：build → min ΣL 求解 → 提取 L* / margin / binding。
#   不走 Runner——缓存 key 不含 objective，会被无目标可行性解污染。
# ========================================================================

def solve_diagnostic(models, B: float) -> DiagnosticResult:
    """诊断原语：给定 (models, B)，解 min ΣL，返回结构化诊断结果。

    models 里必须有一个模型声明变量 L（通常由 perf 模型负责）。
    """
    ctx = Ctx()
    for m in models:
        m.build(ctx, float(B))

    sol = CvxSolver().solve(ctx, objective=sum(ctx["L"]), maximize=False)
    feasible = sol.status in _FEASIBLE

    # L* —— 真实包络（min ΣL），非 feasibility 的任意可行解
    L_star: dict[int, float] = {}
    if sol.variables and "L" in sol.variables:
        L_star = {i: v for i, v in enumerate(sol.variables["L"])}

    # margins —— 仅物理约束，infeasible 时无变量解、无意义
    margins: dict[str, float] = {}
    if feasible and sol.variables:
        for c in ctx.constraints:
            if constraint_family(c.name) not in _PHYS_FAMILIES:
                continue
            margins[c.name] = _margin(c, _lhs_value(c, sol.variables))

    # binding —— 只在 feasible 时有语义（infeasible 的 duals 是 Farkas 证书）。
    # margin ≈ 0 优先：物理约束取等即绑定，即使 dual=0（退化点会被 duals 漏掉）。
    # duals 非零作为辅助：补齐 margin 非零但求解器仍报 dual 的数值噪声项。
    binding: tuple[BindingInfo, ...] = ()
    if feasible and sol.variables:
        by_name = {c.name: c for c in ctx.constraints}
        duals = sol.duals or {}
        names = set(duals)
        for cname, m in margins.items():
            if abs(m) <= _MARGIN_EPS:
                names.add(cname)
        items = [
            BindingInfo(
                name=n,
                family=constraint_family(n),
                dual=duals.get(n, 0.0),
                meaning=by_name[n].meaning if n in by_name else "",
            )
            for n in names
        ]
        items.sort(key=lambda b: -abs(b.dual))
        binding = tuple(items)

    return DiagnosticResult(
        B=float(B), feasible=feasible,
        L_star=L_star, margins=margins, binding=binding,
    )


# ========================================================================
# 这部分是什么？
#   约束名前缀 → 模型家族 的归类，以及 margin 的数值求值。
#   binding 的"哪个模型家族"和 margins 的 rhs−lhs 都在这里算。
# ========================================================================

def constraint_family(name: str) -> str:
    """按约束名前缀归到模型家族：bump / therm / c4 / route，其余 other。"""
    for prefix in _PHYS_FAMILIES:
        if name.startswith(prefix):
            return prefix
    return "other"


def _lhs_value(c: LinearC, var_values: dict[str, list[float]]) -> float:
    """约束左端 Σ coeff·x[idx] 在给定变量值下的数值。"""
    total = 0.0
    for t in c.terms:
        total += t.coeff * var_values[t.var][t.idx]
    return total


def _margin(c: LinearC, lhs: float) -> float:
    """约束离取等的余量：<= 用 rhs−lhs，>= 用 lhs−rhs，== 恒为 0。"""
    if c.sense == "<=":
        return c.rhs - lhs
    if c.sense == ">=":
        return lhs - c.rhs
    return 0.0


# ========================================================================
# 这部分是什么？
#   约束账本（ledger）——实验编排的打印辅助，不是诊断原语本体，可跳过。
#   每约束家族用 __init__ 预计算系数 + L 值，解析利用率 / 余量。
# ========================================================================

def perf_ledger(L_vals: dict[int, float]) -> dict:
    """包络负载：max L 与最热链路。"""
    if not L_vals:
        return {"max_L": float("inf"), "argmax_link": None}
    am = max(L_vals, key=L_vals.get)
    return {"max_L": float(L_vals[am]), "argmax_link": am}


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
        rhs = float(bump._budgets[k].available_at(B))
        rows.append({
            "die": die_labels[k] if die_labels and k < len(die_labels) else f"#{k}",
            "used": used,
            "rhs": rhs,
            "util": used / rhs if rhs else float("inf"),
        })
    return rows


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
        rhs = float(therm._rhs0[i] - therm._beta_p[i] * B * therm._peak_coeff[i])
        margin = rhs - used
        rows.append({
            "die": i,
            "T": None if T_max is None else T_max - margin,
            "margin": margin,
            "rhs": rhs,
        })
    return rows


def full_ledger(models, L_vals: dict[int, float], B: float,
                T_max: float = 358.15) -> dict:
    """对一组模型出汇总账本：每约束家族的紧张程度。"""
    out: dict = {"perf": None, "bump": None, "therm": None}
    for m in models:
        name = type(m).__name__
        if name == "OptimalValiantModel":
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
