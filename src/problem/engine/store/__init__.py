"""
ResultStore —— 基于目录的持久化结果存储。

每个 cache key → 一个目录，目录内必须包含 meta.json：
  {
    "version": 1,
    "backend": "dir",          // "dir" | "sqlite" | ...
    "files": {
      "solve.pkl": {"sha256": "abc123", "size": 1234},
      ...
    }
  }

目录内的实际文件由 backend 管理——默认 "dir" 就是平铺文件。
换 backend 只需实现 _Backend 子类并注册。
"""

from __future__ import annotations

import hashlib
import json
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

META_FILE = "meta.json"
META_VERSION = 1


# ========================================================================
# 后端抽象
# ========================================================================


class _Backend(ABC):
    """存储后端。负责具体读写。"""

    @abstractmethod
    def put(self, dir_: Path, name: str, data: Any) -> None: ...

    @abstractmethod
    def get(self, dir_: Path, name: str) -> Any | None: ...

    @abstractmethod
    def exists(self, dir_: Path, name: str) -> bool: ...

    @abstractmethod
    def list(self, dir_: Path) -> list[str]: ...

    @abstractmethod
    def remove(self, dir_: Path, name: str) -> None: ...


class _DirBackend(_Backend):
    """默认后端——目录平铺文件。序列化由后缀决定。"""

    _ENCODERS = {
        ".pkl": lambda d: pickle.dumps(d),
        ".json": lambda d: json.dumps(d, indent=2).encode(),
    }
    _DECODERS = {
        ".pkl": lambda r: pickle.loads(r),
        ".json": lambda r: json.loads(r.decode()),
    }

    def put(self, dir_: Path, name: str, data: Any) -> None:
        dir_.mkdir(parents=True, exist_ok=True)
        ext = Path(name).suffix
        encode = self._ENCODERS.get(ext, pickle.dumps)
        dir_.joinpath(name).write_bytes(encode(data))

    def get(self, dir_: Path, name: str) -> Any | None:
        p = dir_ / name
        if not p.exists():
            return None
        ext = Path(name).suffix
        decode = self._DECODERS.get(ext, pickle.loads)
        return decode(p.read_bytes())

    def exists(self, dir_: Path, name: str) -> bool:
        return (dir_ / name).exists()

    def list(self, dir_: Path) -> list[str]:
        if not dir_.exists():
            return []
        return [p.name for p in dir_.iterdir() if p.is_file() and p.name != META_FILE]

    def remove(self, dir_: Path, name: str) -> None:
        p = dir_ / name
        if p.exists():
            p.unlink()


# ========================================================================
# Store
# ========================================================================


class ResultStore:
    """基于目录的结果存储。

    生命周期：
      store = ResultStore("_dse_cache")
      store.put(key, "solve.pkl", result)      # 写 meta + 数据
      r = store.get(key, "solve.pkl")          # 读 meta → 选后端 → 加载
    """

    _BACKENDS: dict[str, _Backend] = {
        "dir": _DirBackend(),
    }

    def __init__(self, root: str | Path):
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    # ---- 读写 ----

    def put(self, key: tuple, name: str, data: Any, backend: str = "dir") -> None:
        """存储一份结果。会自动创建/更新 meta.json。"""
        dir_ = self._dir(key)
        be = self._BACKENDS[backend]
        be.put(dir_, name, data)
        self._update_meta(dir_, backend)

    def get(self, key: tuple, name: str) -> Any | None:
        """读取一份结果。使用 meta 中记录的后端。"""
        dir_ = self._dir(key)
        meta = self._read_meta(dir_)
        if meta is None:
            return None
        if name not in (meta.get("files") or {}):
            return None
        be = self._BACKENDS.get(meta.get("backend", "dir"), self._BACKENDS["dir"])
        return be.get(dir_, name)

    def has(self, key: tuple, name: str) -> bool:
        dir_ = self._dir(key)
        meta = self._read_meta(dir_)
        if meta is None:
            return False
        return name in (meta.get("files") or {})

    def list(self, key: tuple) -> list[str]:
        meta = self._read_meta(self._dir(key))
        if meta is None:
            return []
        return list((meta.get("files") or {}).keys())

    def remove(self, key: tuple, name: str) -> None:
        dir_ = self._dir(key)
        meta = self._read_meta(dir_)
        if meta is None:
            return
        be = self._BACKENDS.get(meta.get("backend", "dir"), self._BACKENDS["dir"])
        be.remove(dir_, name)
        self._update_meta(dir_, meta["backend"])

    # ---- 内部 ----

    def _dir(self, key: tuple) -> Path:
        h = hashlib.sha256(str(key).encode()).hexdigest()[:12]
        return self._root / h

    # ---- meta 管理 ----

    def _update_meta(self, dir_: Path, backend: str) -> None:
        dir_.mkdir(parents=True, exist_ok=True)
        be = self._BACKENDS[backend]
        files: dict[str, dict] = {}
        for fname in be.list(dir_):
            p = dir_ / fname
            raw = p.read_bytes()
            files[fname] = {
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        meta = {
            "version": META_VERSION,
            "backend": backend,
            "files": files,
        }
        dir_.joinpath(META_FILE).write_text(json.dumps(meta, indent=2))

    def _read_meta(self, dir_: Path) -> dict | None:
        mp = dir_ / META_FILE
        if not mp.exists():
            return None
        try:
            meta = json.loads(mp.read_text())
        except (json.JSONDecodeError, OSError):
            return None
        if meta.get("version") != META_VERSION:
            return None
        # 完整性校验：文件存在 + 大小 + sha256
        be = self._BACKENDS.get(meta.get("backend", "dir"), self._BACKENDS["dir"])
        for fname, info in (meta.get("files") or {}).items():
            p = dir_ / fname
            if not p.exists():
                return None
            if p.stat().st_size != info.get("size", -1):
                return None
            expected = info.get("sha256", "")
            if expected:
                actual = hashlib.sha256(p.read_bytes()).hexdigest()
                if actual != expected:
                    return None
        return meta
