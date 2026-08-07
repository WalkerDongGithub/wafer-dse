"""
bmax query —— 在给定构型下，能支撑的最大端口带宽 B* 是多少？

这是一个复合查询——内部多次调用 feasibility query 做二分。
feasibility 的中间结果缓存在它自己的 query_id 下，各 query 共享。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lp.queries import Query
from lp.queries.feasibility import FeasibilityQuery

if TYPE_CHECKING:
    from lp.ctx import Ctx
    from lp.engine import Result

_FEAS = FeasibilityQuery.query_id


@dataclass
class BmaxResult:
    """一问一答：最大可行 B 是多少？"""

    B_star: float
    lo: float = 0.0
    hi: float = 0.0
    iterations: int = 0
    notes: list[str] = field(default_factory=list)


class BmaxQuery(Query):
    """二分 partition B 轴，找最大可行带宽。"""

    query_id = "bmax"

    def objective(self, ctx: Ctx):
        return None

    def interpret(self, sol: Result, ctx: Ctx, B: float):
        raise NotImplementedError("bmax 用 solve() 而非 interpret()")

    # ==================================================================
    # 求解
    # ==================================================================

    def solve(self, runner,
              ctx_factory,
              lo: float = 100.0,
              hi: float = 10000.0,
              step: float = 50.0,
              ) -> BmaxResult:
        """二分 partition，返回 B*。ctx_factory(B) → (Ctx, list[Model])。"""

        def _ok(b: float) -> bool:
            out = ctx_factory(b)
            ctx, models = out if isinstance(out, tuple) else (out, ())
            return runner.solve(_FEAS, b, ctx, models).status in (
                "optimal", "optimal_inaccurate",
            )

        if not _ok(lo):
            print(f"[bmax] lo={lo:.0f} infeasible — abort")
            return BmaxResult(B_star=0.0, lo=lo, hi=hi,
                              notes=["lo 不可行"])

        while _ok(hi):
            print(f"[bmax] hi={hi:.0f} feasible → expand")
            lo, hi = hi, hi * 2

        print(f"[bmax] search [{lo:.0f}, {hi:.0f}] step={step:.0f}")
        iters = 0
        while hi - lo > step:
            mid = (lo + hi) / 2.0
            iters += 1
            ok = _ok(mid)
            status = "✓" if ok else "✗"
            print(f"[bmax]   iter{iters}: lo={lo:.0f} hi={hi:.0f} mid={mid:.0f} {status}")
            if ok:
                lo = mid
            else:
                hi = mid

        print(f"[bmax] B* = {lo:.0f} Gbps ({iters} LP solves)")
        return BmaxResult(B_star=lo, lo=lo, hi=hi, iterations=iters)


partition_bmax = BmaxQuery().solve
