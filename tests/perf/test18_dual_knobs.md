# test18 — 双旋钮场景：要求 R（qos/peak）× 约束 C（peak/rated）(V5 §0.1/v5.22)

## 模块定位

V5 v5.22（DomainExpert 落盘）定义双旋钮档位——$B$ 是要求与约束的单调函数
（insight 3）的具体化，四档正交可组合：

| 档位 | 要求旋钮 R | 约束旋钮 C | 场景字符串（EvalDesigner 定稿） |
|---|---|---|---|
| 参考档（最严） | R_qos（双随机包络，置换最坏情形） | C_peak（$P_0+\beta_P B$） | `perf+bump+therm`（回归锚点） |
| 约束放宽 | R_qos | C_rated（$\beta_P:=0$） | `perf+bump+therm+rated` |
| 要求放宽 | R_peak（单对包络 $\max c_{ij}^{e}$） | C_peak | `perf+egress_peak+bump+therm` |
| 双放宽（最松） | R_peak | C_rated | `perf+egress_peak+bump+therm+rated` |

- R 只作用于性能包络（V5 §7.3b）：R_peak 闭式 $L_e^* = \max_{(i,j)} c_{ij}^{e} \le 1$；
- C 只作用于物理 rhs（V5 §2.8）：C_rated 峰值项 $\beta_P B$ 置 0，$P_0$ 保留。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from problem.builder import build_scenario
from problem.models.perf import ObliviousValiantModel
from problem.models.phys.bumps import BumpModel
from problem.models.phys.therm import SteadyStateModel
from physical.params import TOY, UCIE_32G
from topology import MeshTopology
from layout import place
```

---

## 1. 要求旋钮 R：ObliviousValiantModel(requirement="peak") 闭式单对包络

R_peak 包络 = 逐链路取路由系数最大值（V5 §7.3b 闭式解，O(|E|·N²)），
替代 Birkhoff 子 LP。手算 Mesh(2) 链路 e0=(0,1)：

- OD (0,1)：valiant 返回 2 条路径 [[0,1],[0,2,3,1]]，含 e0 的 1 条 → c=1/2；
- OD (0,2)：[[0,2],[0,1,3,2]]？——总之 max c 需要逐 OD 算，这里直接验证
  L*_peak ≤ L*_qos（V5 §7.3b 严格更松）与闭式公式实现。

```python
topo = MeshTopology(2)
qos = ObliviousValiantModel(topo, requirement="qos")
peak = ObliviousValiantModel(topo, requirement="peak")

L_qos = qos.solve_envelope()
L_peak = peak.solve_envelope()
print(f"L*_qos  = {[round(x,4) for x in L_qos]}")
print(f"L*_peak = {[round(x,4) for x in L_peak]}")
assert len(L_peak) == topo.n_links
assert all(0.0 < p <= 1.0 + 1e-9 for p in L_peak), "单对包络 ≤ 1（V5 §7.3b）"
assert all(p <= q + 1e-9 for p, q in zip(L_peak, L_qos)), \
    "R_peak 包络必须逐链路 ≤ R_qos（严格更松，旋钮有区分度）"
assert any(p < q - 1e-6 for p, q in zip(L_peak, L_qos)), \
    "至少一条链路严格更松（否则旋钮无区分度）"
print("✓ R_peak 单对包络：0 < L*_peak ≤ L*_qos，逐链路成立")
```

---

## 2. 约束旋钮 C：C_rated 的 β_P := 0

C_rated 档（V5 §2.8 v5.22）：BumpModel rhs 的电源 bump 数
$N_{\text{pwr}} = \lceil P_0/(V_{dd} I) \rceil$ 常数；SteadyStateModel rhs
去掉 $\beta_P B$ 项。用 ucie-32g（β_P 默认 0 时两档相同）与 toy+β_P>0
对比验证：β_P>0 时 C_rated 的 rhs 更大（更松）。

```python
from physical.config.spec_bump import DieBumpBudget, BumpSpec

# β_P=0.2 的 die：P_peak(B) = P0 + 0.2B
s = BumpSpec("t", 100.0, 100.0)
b_peak = DieBumpBudget("d0", s, 10, 10, 10.0, 1.0, 1.0, beta_p=0.2)
# C_rated 语义：beta_p 传 0（build_scenario 对 rated 档做 beta_p:=0 程序化覆盖）
b_rated = DieBumpBudget("d0", s, 10, 10, 10.0, 1.0, 1.0, beta_p=0.0)

# B=100：P_peak(100)=30W → N_pwr=300；C_rated 恒 10W → N_pwr=100
assert b_peak.power_bumps_at(100.0) == 300
assert b_rated.power_bumps_at(100.0) == 100
print(f"N_pwr(C_peak, B=100) = {b_peak.power_bumps_at(100.0)}, "
      f"N_pwr(C_rated, B=100) = {b_rated.power_bumps_at(100.0)}")
assert b_rated.power_bumps_at(100.0) == b_rated.power_bumps_at(0.0), \
    "C_rated 电源 bump 数不随 B 变（常数）"
print("✓ C_rated：β_P B 项置 0 → 电源 bump 数常数，rhs 更松")
```

---

## 3. 四档场景可构造 + 模型列表

build_scenario 支持 4 档字符串（token 解析：`egress_peak` → R_peak 包络；
`rated` → β_P:=0）。

```python
topo = MeshTopology(2)
P = UCIE_32G
layout = place(topo, P)

scenarios = {
    "perf+bump+therm":                  "ObliviousValiantModel,BumpModel,SteadyStateModel",
    "perf+bump+therm+rated":            "ObliviousValiantModel,BumpModel,SteadyStateModel",
    "perf+egress_peak+bump+therm":      "ObliviousValiantModel,BumpModel,SteadyStateModel",
    "perf+egress_peak+bump+therm+rated":"ObliviousValiantModel,BumpModel,SteadyStateModel",
}
for sc, expect in scenarios.items():
    models, meta = build_scenario(topo, sc, P, layout)
    types = ",".join(type(m).__name__ for m in models)
    assert types == expect, f"{sc}: {types}"
    print(f"{sc:<36} → {types}")
print("✓ 四档场景全部可构造")
```

---

## 4. R 旋钮可测：perf+egress_peak 档约束确实更松

关键契约（DomainExpert 重裁决 + EvalDesigner 结构性断言）：
同 C 档下 R_peak 场景的可行性不劣于 R_qos——包络约束 L ≥ L*_peak 比
L ≥ L*_qos 松（第 1 节逐链路证明），因此固定 B 下 R_peak 档可行 ⇒
R_qos 档不一定；B* 上 R_qos ≤ R_peak（M1 判据方向）。

这里验证**约束系数层面**（不依赖 solver）：同 B 下 R_peak 档写出的
oblivious_env 约束 rhs（= L*_peak）≤ R_qos 档 rhs（= L*_qos）。

```python
from problem import Ctx

models_qos, _ = build_scenario(topo, "perf+egress_peak+bump+therm+rated", P, layout)
models_ref, _ = build_scenario(topo, "perf+bump+therm+rated", P, layout)

# 每个模型列表独立 ctx（perf 模型自己声明 L，勿预声明）
ctx_p = Ctx()
for m in models_qos: m.build(ctx_p, B=100.0)
ctx_q = Ctx()
for m in models_ref: m.build(ctx_q, B=100.0)

def env_rhs(ctx):
    return {c.name: c.rhs for c in ctx.constraints if c.name.startswith("oblivious_env_")}

rhs_peak = env_rhs(ctx_p)
rhs_qos = env_rhs(ctx_q)
assert set(rhs_peak) == set(rhs_qos)
for k in rhs_qos:
    assert rhs_peak[k] <= rhs_qos[k] + 1e-9, f"{k}: L*_peak {rhs_peak[k]} > L*_qos {rhs_qos[k]}"
print(f"perf+egress_peak 档 oblivious_env rhs（L*_peak）≤ 参考档 rhs（L*_qos）✓")
print(f"  例: e0  L*_peak={rhs_peak['oblivious_env_e0']:.3f}  L*_qos={rhs_qos['oblivious_env_e0']:.3f}")
```

---

## 5. C 旋钮可测：rated 档 rhs 更松（β_P>0 时）

用 β_P>0 的参数组（toy + replace）验证：同 R 档下 `+rated` 档的
bump/therm rhs 更大（更松）。默认 ucie 系列 β_P=0 → 两档 rhs 相同
（退化档，如实报告——EvalDesigner M2 警示）。

```python
from dataclasses import replace

Ptoy = replace(TOY, die=replace(TOY.die, beta_p=0.2, alpha_d=0.0))
layout_t = place(topo, Ptoy)

m_cpeak, _ = build_scenario(topo, "perf+bump+therm", Ptoy, layout_t)
m_crated, _ = build_scenario(topo, "perf+bump+therm+rated", Ptoy, layout_t)

ctx_a = Ctx()
for m in m_cpeak: m.build(ctx_a, B=100.0)
ctx_b = Ctx()
for m in m_crated: m.build(ctx_b, B=100.0)

def phys_rhs(ctx):
    return {c.name: c.rhs for c in ctx.constraints
            if c.name.startswith(("bump_", "therm_"))}

ra, rb = phys_rhs(ctx_a), phys_rhs(ctx_b)
assert set(ra) == set(rb)
assert any(rb[k] > ra[k] + 1e-6 for k in ra), \
    "β_P>0 时 rated 档应有至少一个 rhs 更松"
for k in ra:
    rel = ">" if rb[k] > ra[k] + 1e-6 else "="
    print(f"  {k:<12} C_peak rhs={ra[k]:>9.1f}  C_rated rhs={rb[k]:>9.1f}  {rel}")
print("✓ C_rated（β_P>0 时）bump/therm rhs 更松，旋钮有区分度")
```

---

## 6. cache_key 区分档位

```python
k_qos = ObliviousValiantModel(topo, requirement="qos").cache_key()
k_peak = ObliviousValiantModel(topo, requirement="peak").cache_key()
assert k_qos != k_peak, "requirement 必须进 cache_key（不同档位不同缓存）"
assert k_qos == ObliviousValiantModel(topo, requirement="qos").cache_key()
print("✓ cache_key 区分 R 档位")
```

---

## 结论

双旋钮场景实现完成（V5 v5.22 权威依据）：

- **R 旋钮**：`ObliviousValiantModel(requirement="peak")` 闭式单对包络
  $L_e^*=\max c_{ij}^{e} \le 1$，逐链路严格不劣于 R_qos（M1 方向）；
- **C 旋钮**：`rated` 档 β_P:=0，电源 bump 数变常数、热 rhs 去 β_P B 项；
- **场景**：4 档字符串可构造，参考档 `perf+bump+therm` 回归锚点不变；
- 结构性断言（约束系数层）不依赖 solver，run_all 全绿可提交。
