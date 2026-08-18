# test13 — benchmark 合约模块 (benchmark/contracts.py)

## 模块定位

`benchmark/contracts.py` 是 benchmark 子系统跨模块唯一的数据契约。根据 AGENTS.md §5 "禁止裸 dict 跨模块" 的硬条款，`generate_baseline.py`、`rapidchiplet_checker.py`、`compare_results.py` 之间**不得**再用 `list[dict[str, Any]]` 传数据，必须使用这两个 frozen dataclass：

- `OurBaselineRow` —— 我们的 strict screen 产出的一行结果
- `RapidBaselineRow` —— RapidChiplet 复现器产出的一行结果

两个类 `cache_key()` 等价，作为 CSV 行主键。

---

## 第一步：合约类本身能构造 + 字段不可变

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))
from contracts import OurBaselineRow, RapidBaselineRow, BenchKey

r = OurBaselineRow(
    topology="mesh", size="3x3", params="ucie-32g",
    feasible=False,
    bottleneck="Non-blocking envelope violated for Mesh 3x3 under strict conjugate-class pattern set.",
)
assert r.topology == "mesh"
assert r.size == "3x3"
assert r.params == "ucie-32g"
assert r.feasible is False
assert isinstance(r.cache_key(), BenchKey)
assert r.cache_key() == ("mesh", "3x3", "ucie-32g")

# frozen dataclass 不可变——赋值必须抛 FrozenInstanceError
try:
    r.feasible = True
    raise AssertionError("Expected FrozenInstanceError (dataclass must be frozen)")
except Exception as e:
    assert "FrozenInstanceError" in type(e).__name__ or "frozen" in str(e).lower()

# RapidBaselineRow 合约对等
rr = RapidBaselineRow(
    topology="torus", size="4x4", params="trad-air-112g",
    rapidchiplet_feasible=False,
    perf_metrics="InjectedLoad=1024Gbps, AggrCapacity=3400Gbps",
    power_metrics="Static=296W, Dynamic=25.6W, Total=321.6W, Budget=300W",
    thermal_note="[Thermal:THERMAL-RED-FLAG] PkgRatio=1.29",
)
assert rr.cache_key() == ("torus", "4x4", "trad-air-112g")
print("test13 / Step1 PASS")
```

---

## 第二步：合约类能无损 round-trip 成 dict / 从 dict 构造

```python
from dataclasses import asdict

r = OurBaselineRow(
    topology="torus", size="3x3", params="ucie-12g", feasible=True,
    bottleneck="All constraints satisfied for Torus 3x3 with param=ucie-12g",
)
d = asdict(r)
assert d == {
    "topology": "torus", "size": "3x3", "params": "ucie-12g",
    "feasible": True,
    "bottleneck": "All constraints satisfied for Torus 3x3 with param=ucie-12g",
}
# 从 asdict 结果反向构造，字段顺序不影响（dataclass kw-only 语义）
r2 = OurBaselineRow(**d)
assert r2 == r
print("test13 / Step2 PASS")
```

---

## 第三步：cache_key 作为 dict/set key 可用——哈希+相等

```python
rA = OurBaselineRow("mesh", "3x3", "ucie-32g", False, "nb envelope")
rB = OurBaselineRow("mesh", "3x3", "ucie-32g", True,  "different bottleneck")  # 同一 key
rC = OurBaselineRow("mesh", "3x3", "ucie-16g", False, "nb envelope")          # 不同键

# rA.cache_key() 和 rB.cache_key() 同 key，即使 feasible 不同
assert rA.cache_key() == rB.cache_key()
assert hash(rA.cache_key()) == hash(rB.cache_key())
# rC 不同
assert rA.cache_key() != rC.cache_key()

# 用作 set key：3 个不同 key = 只收录 2 个（A/B 合并）
seen = {rA.cache_key(), rB.cache_key(), rC.cache_key()}
assert len(seen) == 2
print("test13 / Step3 PASS")
```
