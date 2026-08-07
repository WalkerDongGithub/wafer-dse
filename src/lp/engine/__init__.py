"""
Engine —— 求解编排层。

Runner 是主入口：model.build → 缓存 → Solver.solve → 存盘。
Solver 和 ResultStore 是 Runner 调用的两个抽象接口，
各自的实现在子目录中：
  solution/  — 求解器（当前: CvxSolver / cvxpy）
  store/     — 持久化（当前: ResultStore / 目录文件）

用法：
    engine = CvxSolver()
    runner = Runner(engine, store="_dse_cache")
    sol = runner.solve(query_id, B=800.0, ctx=ctx, models=models)
"""

from lp.engine.solution import Result, Solver, CvxSolver
from lp.engine.store import ResultStore
from lp.engine._runner import Runner

__all__ = ["Result", "Solver", "CvxSolver",
           "ResultStore", "Runner"]
