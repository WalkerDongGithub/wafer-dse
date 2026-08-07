"""
CvxSolver —— cvxpy 实现的 Solver。

存在意义：
  这是框架中**唯一**引入 cvxpy 的文件。换求解器只改这一处。
  编译流程：1.变量 2.约束 3.目标 4.求解 5.提取——五步标注。

用法（通过 Runner，不直接调用）：
    engine = CvxSolver()
    sol = engine.solve(ctx)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lp.engine.solution import Solver

if TYPE_CHECKING:
    from lp.ctx import Ctx, LinExpr
    from lp.engine.solution import Result


class CvxSolver(Solver):
    """cvxpy 求解器。"""

    def __init__(self, solver: str = "CLARABEL", verbose: bool = False):
        self._solver = solver
        self._verbose = verbose

    def solve(self, ctx: Ctx,
              objective: LinExpr | None = None,
              maximize: bool = False,
              ) -> Result:
        """编译 ctx → cvxpy → 求解。"""
        return self._compile_and_solve(ctx, objective, maximize)

    # ------------------------------------------------------------------
    # 编译主流程（1.变量 2.约束 3.目标 4.求解 5.提取）
    # ------------------------------------------------------------------

    def _compile_and_solve(self, ctx, objective, maximize) -> Result:
        import time, cvxpy as cvx
        from lp.engine.solution import Result

        t0 = time.perf_counter()

        # 1. 变量
        cvx_vars = {}
        for name, spec in ctx.variables.items():
            cvx_vars[name] = (
                cvx.Variable(nonneg=spec.nonneg) if spec.shape == 1
                else cvx.Variable(spec.shape, nonneg=spec.nonneg)
            )

        # 2. 约束
        cvx_cons = []
        for c in ctx.constraints:
            e = self._build_expr(c.terms, cvx_vars)
            cvx_cons.append(
                e <= c.rhs if c.sense == "<=" else
                e >= c.rhs if c.sense == ">=" else
                e == c.rhs
            )

        # 3. 目标
        if objective is None:
            obj = cvx.Minimize(0)
        else:
            o = self._build_expr(objective._to_terms(), cvx_vars)
            obj = cvx.Maximize(o) if maximize else cvx.Minimize(o)

        # 4. 求解
        prob = cvx.Problem(obj, cvx_cons)
        name = self._solver
        try:
            prob.solve(verbose=self._verbose, solver=self._solver)
        except cvx.error.SolverError:
            try:
                prob.solve(verbose=self._verbose)
                name = "default"
            except Exception:
                return Result(status="error",
                                   solve_time_s=time.perf_counter() - t0)

        dt = time.perf_counter() - t0

        # 5. 提取
        var_vals = {}
        for vn, var in cvx_vars.items():
            v = var.value
            if v is not None:
                var_vals[vn] = v.tolist() if hasattr(v, "tolist") else [float(v)]

        duals = {}
        try:
            for i, c in enumerate(prob.constraints):
                dv = c.dual_value
                if dv is not None and abs(float(dv)) > 1e-9:
                    dn = ctx.constraints[i].name if i < len(ctx.constraints) else f"c{i}"
                    duals[dn] = float(dv)
        except Exception:
            pass

        return Result(
            status=prob.status, solve_time_s=dt,
            objective=float(prob.value) if prob.value is not None else None,
            variables=var_vals, duals=duals,
        )

    @staticmethod
    def _build_expr(terms, cvx_vars):
        import cvxpy as cvx
        from lp.ctx import Term
        e: cvx.Expression = 0
        for t in terms:
            if not isinstance(t, Term):
                continue
            v = cvx_vars[t.var]
            e = e + t.coeff * (v if v.shape == () else v[t.idx])
        return e
