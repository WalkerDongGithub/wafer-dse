"""
Runner —— model.build → 缓存 → engine.solve → 存盘。

Solver 只管求解。Runner 管求解之外的所有事情。
内建日志——每次求解事件（命中/求解/错误）一行记录。
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

from lp.engine.store import ResultStore

_SOLVE = "solution.pkl"


class Runner:
    """编排求解 + L1/L2 缓存 + 日志。

    runner = Runner(engine, store="_dse_cache")
    sol = runner.solve(query_id, B=800.0, ctx=ctx, models=models)
    """

    def __init__(self, engine, store: ResultStore | str | Path | None = None,
                 log: bool = True):
        self._engine = engine
        self._mem: dict[tuple, object] = {}
        self._hits = 0
        self._log = log
        if isinstance(store, ResultStore):
            self._store = store
        elif store is not None:
            self._store = ResultStore(store)
        else:
            self._store = None

    @property
    def hits(self) -> int:
        return self._hits

    # ==================================================================
    # 求解（查 L1 → L2 → 求解 → 存盘）
    # ==================================================================

    def solve(self, query_id: str, B: float, ctx, models: Sequence = (),
              objective=None, maximize: bool = False):
        """带缓存的求解。key = (query_id, B, model_keys...)。"""
        key = self._ckey(query_id, B, models)
        nm = len(models)

        # L1
        if key is not None and key in self._mem:
            self._hits += 1
            self._log_event(query_id, B, nm, "L1")
            return self._mem[key]

        # L2
        if key is not None and self._store is not None:
            r = self._store.get(key, _SOLVE)
            if r is not None:
                self._mem[key] = r
                self._hits += 1
                self._log_event(query_id, B, nm, "L2")
                return r

        # 求解
        t0 = time.perf_counter()
        for m in models:
            m.build(ctx, B)
        result = self._engine.solve(ctx, objective=objective, maximize=maximize)
        dt = time.perf_counter() - t0
        self._log_event(query_id, B, nm, result.status, dt)

        # 存盘
        if key is not None:
            self._mem[key] = result
            if self._store is not None:
                self._store.put(key, _SOLVE, result)
        return result

    # ==================================================================
    # 额外数据存取
    # ==================================================================

    def put(self, query_id: str, B: float, ctx, models: Sequence,
            name: str, data) -> None:
        key = self._ckey(query_id, B, models)
        if key is None or self._store is None:
            raise RuntimeError("需要 model 实现 cache_key() 且 runner 有 store")
        self._store.put(key, name, data)

    def get(self, query_id: str, B: float, ctx, models: Sequence, name: str):
        if self._store is None:
            return None
        key = self._ckey(query_id, B, models)
        return self._store.get(key, name) if key else None

    # ==================================================================
    # 内部
    # ==================================================================

    def _log_event(self, qid: str, B: float, n_models: int,
                   event: str, dt: float = 0.0):
        if not self._log:
            return
        ts = time.strftime("%H:%M:%S")
        if event in ("L1", "L2"):
            print(f"[{ts}] {qid} B={B:.0f} hit:{event}")
        else:
            print(f"[{ts}] {qid} B={B:.0f} {event} {dt:.3f}s ({n_models} models)")

    @staticmethod
    def _ckey(query_id: str, B: float, models: Sequence) -> tuple | None:
        parts = [query_id, B]
        for m in models:
            k = m.cache_key()
            if k is None:
                return None
            parts.append(k)
        return tuple(parts)
