# test0402 — 翘曲约束 (src/lp/models/phys/therm/_warp_limit.py)

## 问题

相邻 die 之间温差不能太大。硅会翘曲。取 $\Delta T_{max} = 10\ \text{K}$——相邻 die 温度差超过 10 度就有机械应力风险。

数学上，对每一对邻接 die $(i,j)$：

$$|T_i - T_j| \le \Delta T_{max}$$

等价于两条线性不等式：

$$T_i - T_j \le \Delta T_{max},\qquad T_j - T_i \le \Delta T_{max}$$

用矩阵写：$\mathbf{W} \cdot \mathbf{T} \le \Delta T_{max} \cdot \mathbf{1}$，其中 $\mathbf{W}$ 的每行是一个 $(+1, -1)$ 对。

## 和温度约束同样的处理

test04 已经把 $\mathbf{T} = \mathbf{G}^{-1}(\mathbf{P} + \mathbf{b})$ 写成：

$$\mathbf{T} = \underbrace{\mathbf{G}^{-1}(\mathbf{P}_0 + \mathbf{b})}_{\text{常数偏置}} \;+\; B \cdot \underbrace{\mathbf{G}^{-1} \cdot \mathbf{M} \cdot \mathbf{S}_{dyn} \cdot \mathbf{S}_{bw}^{-1}}_{\displaystyle \mathbf{K}} \cdot \mathbf{L}$$

代入 $\mathbf{W} \cdot \mathbf{T} \le \Delta T_{max}$：

$$B \cdot \underbrace{\mathbf{W} \cdot \mathbf{K}}_{warp\_coeff} \cdot \mathbf{L} \;\le\; \underbrace{\Delta T_{max} \cdot \mathbf{1} - \mathbf{W} \cdot \mathbf{G}^{-1}(\mathbf{P}_0 + \mathbf{b})}_{warp\_rhs}$$

和 `SteadyStateModel` 完全同构——只是多乘了一个 $\mathbf{W}$ 矩阵。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from lp.models.phys.therm.network import (
    DiePlacement, MfitStackConfig, ThermalNetworkBuilder, AnalyticNetworkBuilder,
)
from lp.models.phys.therm._steady_state import SteadyStateModel
from lp.models.phys.therm._warp_limit import WarpModel, _are_adjacent
from lp import Ctx
```

---

## 第一步：W 矩阵长什么样

两个 die 水平邻接（中心距 13mm，间隙 1mm）：

```
  [d0] [d1]
```

两 die 面邻接 → $\mathbf{W}$ 有 2 行：

$$\mathbf{W} = \begin{bmatrix} +1 & -1 \\ -1 & +1 \end{bmatrix}$$

第一行：$T_0 - T_1 \le 10$。第二行：$T_1 - T_0 \le 10$。

```python
p = [DiePlacement("d0", 0, 0, 12, 12),
     DiePlacement("d1", 13, 0, 12, 12)]
assert _are_adjacent(p[0], p[1])
print("✓ d0 and d1 are adjacent")
```

---

## 第二步：手算翘曲约束

使用和 test04 相同的物理参数：
$R_{vert}=1.5$，$T_{ambient}=300$，$P_0 = [5, 5]$，$\Delta T_{max}=10$，
一条 UCIe 链路（$S_{bw}=32$，$S_{dyn}=0.016$）连接 die 0。

先构建温度约束的 $\mathbf{K}$ 和 $rhs$，然后乘以 $\mathbf{W}$ 得到翘曲约束。

```python
G, b = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=1.5, T_ambient=300.0))
P0 = np.array([5.0, 5.0])
ppl = np.array([0.016, 0.0])
lr  = np.array([32.0, 1e9])
node_links = {0: [0], 1: []}

# 温度约束的 K 矩阵
temp_net = ThermalNetworkBuilder.precompute(G, b, 358.0, node_links, 2, lr, ppl, P0_vec=P0)

# 翘曲约束: W·G⁻¹(P+b) ≤ ΔT_max
warp = WarpModel(G, b, P0, p, temp_net.link_coeff, delta_T_max=10.0)

print(f"温度 K =\n{temp_net.link_coeff}")
print(f"翘曲 K_warp =\n{warp._link_coeff}")
print(f"温度 rhs = {temp_net.rhs_ambient}")
print(f"翘曲 rhs = {warp._rhs}")
```

**手算验证**：

$\mathbf{K}$（温度）有两个元素：$K_{0,0} = G^{-1}_{00} \cdot 1 \cdot 0.016/32$，$K_{1,0} = G^{-1}_{10} \cdot 1 \cdot 0.016/32$。

$\mathbf{W} \cdot \mathbf{K}$ 的第 0 行 = $K_{0,0} - K_{1,0}$——即 die 0 和 die 1 之间温差对 $L_0$ 的敏感度。

因为 $G^{-1}_{00} > G^{-1}_{10}$（链路直接在 die 0 上），所以 $K_{0,0} > K_{1,0}$，$L_0$ 增大时 $T_0 - T_1 > 0$。

```python
# 验证 W·K = warp link_coeff
W = np.array([[1, -1], [-1, 1]])
expected_lc = W @ temp_net.link_coeff
assert np.allclose(warp._link_coeff, expected_lc, rtol=1e-10)
print("✓ W·K = warp_coeff")

# 验证 rhs
G_inv = np.linalg.inv(G)
expected_rhs = 10.0 - W @ (G_inv @ (P0 + b))
assert np.allclose(warp._rhs, expected_rhs, rtol=1e-10)
print("✓ warp_rhs = ΔT_max − W·G⁻¹(P0+b)")
```

---

## 第三步：LP 里面长什么样

和 `SteadyStateModel` 一样——`WarpModel.build(ctx, B)` 写入两行不等式。

```python
ctx = Ctx(); ctx.vector("L", 2)
warp.build(ctx, B=1000.0)

for i, c in enumerate(ctx.constraints):
    coeff = sum(t.coeff for t in c.terms if t.var == "L")
    print(f"约束 {i}: coeff={coeff:.6f} ≤ rhs={c.rhs:.4f}")

assert len(ctx.constraints) == 2  # 一对邻接 die → 两行
```

---

## 第四步：没有邻接 die 时

如果 die 之间不邻接（距离太远），$\mathbf{W}$ 是空的，翘曲约束不生效。

```python
p2 = [DiePlacement("d0", 0, 0, 12, 12),
      DiePlacement("d1", 50, 0, 12, 12)]  # 远距离
assert not _are_adjacent(p2[0], p2[1])
print("✓ dies 50mm apart are NOT adjacent")

G2, b2 = AnalyticNetworkBuilder.system_of(p2, MfitStackConfig())
temp_net2 = ThermalNetworkBuilder.precompute(G2, b2, 358.0, {0: [], 1: []}, 2,
                                  np.array([32.0, 1e9]),
                                  np.array([0.016, 0.0]),
                                  P0_vec=np.array([5.0, 5.0]))
warp2 = WarpModel(G2, b2, np.array([5.0, 5.0]), p2, temp_net2.link_coeff, 10.0)
# 无邻接 → W 只有 1 行 (dummy)
assert warp2._link_coeff.shape[0] == 1
print("✓ no adjacency → minimal warp model")
```

---

## 总结

翘曲约束和温度约束的数学结构完全相同：

| | 温度 ($T \le T_{max}$) | 翘曲 ($|T_i - T_j| \le \Delta T_{max}$) |
|---|---|---|
| 系数矩阵 | $\mathbf{G}^{-1} \cdot \mathbf{M} \cdot \mathbf{S}_{dyn} \cdot \mathbf{S}_{bw}^{-1}$ | $\mathbf{W} \cdot \mathbf{G}^{-1} \cdot \mathbf{M} \cdot \mathbf{S}_{dyn} \cdot \mathbf{S}_{bw}^{-1}$ |
| RHS | $T_{max} - \mathbf{G}^{-1}(\mathbf{P}_0 + \mathbf{b})$ | $\Delta T_{max} - \mathbf{W} \cdot \mathbf{G}^{-1}(\mathbf{P}_0 + \mathbf{b})$ |
| 约束数 | $|\mathcal{V}|$ | $2 \times$ (邻接对数量) |

都是 $B \cdot coeff \cdot \mathbf{L} \le rhs$ 的形式。如果温度约束已经满足（$T$ 不超 $T_{max}$），翘曲约束通常会先被触发——因为温差限制比绝对温度限制更紧（$10\ \text{K}$ vs $58\ \text{K}$）。
