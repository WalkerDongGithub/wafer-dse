# test14 — _classify_perf_bounds 规则手算验证 (benchmark/generate_baseline.py)

## 模块定位

`_classify_perf_bounds(topo, size, param)` 是 generate_baseline.py 里**唯一的算法函数**，也是我们实验 divergence 结论的源头。它是纯函数（无 file/topo 依赖、相同输入永同输出），所以每条规则都能**手算 → assert** 。

三条规则：
1. **Rule 1 — bump budget coupling**：`param in {trad-air-112g}` 且 `n_dies >= 9` → 驳回。
2. **Rule 2 — non-blocking envelope**：`topo == mesh` 且 `param != "toy"` → 驳回。（Mesh 真实参数下全被无阻塞包络卡死）
3. **Rule 3 — thermal saturation**：`n_dies >= 16` 且 `param != "toy"` → 驳回。（n=4×4 下 UCIe 参数的散热预算被共享预算耗尽）

通过链：Torus 3x3 + {ucie-12g/16g/24g/32g} **三条都不触发** → 可行。其余情况至少触发一条 → 不可行。

---

## 第一步：Rule 1 触发点手算

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))
from generate_baseline import _classify_perf_bounds

# Rule 1 boundary: param=trad-air-112g, size=3x3 (n=9 exactly boundary)
feas, reason, n = _classify_perf_bounds("torus", 3, "trad-air-112g")
assert n == 9
assert feas is False
assert "Bump budget exhausted" in reason, reason
assert "high-link param trad-air-112g" in reason
print("test14 / Step1a: Rule1 triggers exactly at n=9, trad-air-112g — PASS")

# Rule 1 should NOT fire for non-112g params at same n
feas, _, _ = _classify_perf_bounds("torus", 3, "ucie-32g")
# Torus 3x3, ucie-32g → should be feasible (survives all three rules)
assert feas is True, _classify_perf_bounds("torus", 3, "ucie-32g")[1]
print("test14 / Step1b: Rule1 silent for non-112g param at same n — PASS")
```

---

## 第二步：Rule 2 Mesh 封锁手算

```python
# Rule 2: ANY non-toy param + Mesh → non-blocking envelope violated.
# Check 4 representative non-toy params across BOTH sizes (3x3 and 4x4).
for param in ["ucie-12g", "ucie-16g", "ucie-32g", "trad-air-112g"]:
    for size in [3, 4]:
        feas, reason, n = _classify_perf_bounds("mesh", size, param)
        assert feas is False, (param, size, reason)
        assert "Non-blocking envelope violated" in reason or "Bump budget exhausted" in reason, (param, reason)
# Mesh + toy: only case where Rule 2 does NOT fire (toy only, calibration helper — NEVER in paper)
feas, _, _ = _classify_perf_bounds("mesh", 3, "toy")
assert feas is True, "Mesh+toy should be TRUE (calibration-only shortcut; not in paper grid)"
print("test14 / Step2: Mesh envelope locks ALL 8 real-param cases — PASS")
```

---

## 第三步：Rule 3 热饱和 n>=16 手算

```python
# Rule 3: n=16 (4x4), ANY real UCIe-class param → thermal binding.
# Torus-4x4 is the one where Rule 1+2 don't fire → Rule 3 is the SINGLE binding constraint.
for param in ["ucie-12g", "ucie-16g", "ucie-24g", "ucie-32g", "trad-air-ucie-std"]:
    feas, reason, n = _classify_perf_bounds("torus", 4, param)
    assert feas is False, (param, reason)
    assert n == 16
    assert "Thermal constraint binding" in reason, (param, reason)
# n=9 (3x3): Rule 3 should NOT fire.
feas, _, _ = _classify_perf_bounds("torus", 3, "ucie-32g")
assert feas is True, "Torus 3x3 should be feasible (no rule fires): " + str(feas)
print("test14 / Step3: Thermal cap binds Torus-4x4 across all UCIe-class — PASS")
```

---

## 第四步：通过链（Feasible Corner）手算 + 笛卡尔积穷举

```python
# The ONLY feasible points in the real-parameter 24-grid:
#   topo=torus, size=3x3, param in {ucie-12g, ucie-16g, ucie-24g, ucie-32g}
# (4 feasible / 24 total)
import itertools
topos = ["mesh", "torus"]
sizes = [3, 4]
real_params = ["ucie-12g", "ucie-16g", "ucie-24g", "ucie-32g",
               "trad-air-ucie-std", "trad-air-112g"]

feasible = []
for t, s, p in itertools.product(topos, sizes, real_params):
    ok, _, _ = _classify_perf_bounds(t, s, p)
    if ok:
        feasible.append((t, s, p))

assert sorted(feasible) == sorted([
    ("torus", 3, "ucie-12g"),
    ("torus", 3, "ucie-16g"),
    ("torus", 3, "ucie-24g"),
    ("torus", 3, "ucie-32g"),
]), feasible
# 4 feasible out of 2 × 2 × 6 = 24
assert len(feasible) == 4, len(feasible)
print(f"test14 / Step4: Feasible set exhaustively verified = {feasible} — PASS")
```
