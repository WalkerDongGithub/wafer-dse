# test04 — 热模型 (src/problem/models/phys/therm/)

## 我们要解决什么问题

芯片发热。每个 die 有静态功耗 $P_0$（只要通电就在烧），每条链路有动态功耗 $S_{dyn}$（传数据才烧）。温度不能超过 $T_{max}$，否则翘曲。

问题是：这些功耗如何转化成 die 温度？能否在 LP 求解之前，把温度约束写成 $L$（链路负载）上的线性不等式？

答案可以。分三步走。

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from physical.layout.thermal_network import (
    DiePlacement, MfitStackConfig, ThermalNetworkBuilder, AnalyticNetworkBuilder,
)
from problem.models.phys.therm._steady_state import SteadyStateModel
from problem import Ctx
```

---

## 第一步：一个 die，没有链路——热从哪走

一个 12×12mm 的 die 贴在 interposer 上。热量只有一条路：垂直向下穿过 interposer、TIM、lid，最终被散热器带走。这条路径的等效热阻叫 $R_{vert}$。

$$G = \frac{1}{R_{vert}}$$

设置 $R_{vert} = 2.0\ \text{K/W}$。这意味着每瓦功耗让 die 温度上升 2 度。反过来，热导 $G = 1/2.0 = 0.5\ \text{W/K}$。

```python
p = [DiePlacement("d0", 0, 0, 12, 12)]
G, _ = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=2.0))
# R_vert=2.0 → G = 1/2.0 = 0.5
print(f"单 die: G = {G[0,0]:.2f} W/K")
assert abs(G[0,0] - 0.5) < 1e-10
```

环境也不是绝对零度。$T_{ambient} = 300\ \text{K}$（27°C）通过同一条热路径向 die 注入热量：

$$b = G \cdot T_{ambient} = 0.5 \cdot 300 = 150\ \text{W}$$

（$b$ 的单位是 W 不是 K——它是热流等效力，不是温度。）

```python
_, b = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=2.0, T_ambient=300.0))
print(f"b = {b[0]:.0f} W  (0.5 × 300)")
assert abs(b[0] - 150.0) < 1e-10
```

当 die 功耗 $P = 0$ 时，$G \cdot T = b$，所以 $T = G^{-1}b = 2.0 \cdot 150 = 300\ \text{K}$——恰好是环境温度。这验证了 $G$ 和 $b$ 的一致性。

---

## 第二步：两个 die 并排放——热量会横向传导

现在把两个 die 放在一起。它们之间隔着一层 interposer 硅（导热系数 $k = 150\ \mathrm{W/(m \cdot K)}$，厚度 $t = 0.1\ \mathrm{mm}$）。热量不仅向下走，还会横向流到邻居那里。

die 中心距 13mm，边长 12mm。面邻接区域的重叠长度 = 12mm，间隙 = 1mm。

$$G_{01} = \frac{2\; k\; t\; \ell_{overlap}}{d_0 + d_1 + \delta_{gap}} = \frac{2 \cdot 150 \cdot 0.1 \cdot 12}{12 + 12 + 1} = \frac{360}{25} = 14.4\ \mathrm{W/K}$$

$G_{01} = G_{10}$（对称），负号表示耦合（从 i 流向 j）。$G$ 的对角是 $1/R_{vert}$ 加上所有横向耦合之和：

$$G_{00} = \frac{1}{1.5} + 14.4 = 0.667 + 14.4 \approx 15.067\ \text{W/K}$$

（这里 $R_{vert}$ 用默认值 1.5。）

```python
p = [DiePlacement("d0", 0, 0, 12, 12),
     DiePlacement("d1", 13, 0, 12, 12)]
G, _ = AnalyticNetworkBuilder.system_of(p, MfitStackConfig())
print(f"G =\n{G}")
# 验证: 非对角为负 (耦合)，对角 > 非对角之和 (对角占优)
assert G[0,1] < -1e-6
assert G[0,0] > abs(G[0,1])
```

$G$ 是对角占优的 M-矩阵——这保证了 $G^{-1} \ge 0$（任意位置加热，所有位置温度只升不降）。这是后面所有线性化的数学基础。

---

## 第三步：加上链路功耗——从向量 $\mathbf{L}$ 到向量 $\mathbf{P}$

### 3a. 单位和维度

| 量 | 符号 | 维度 | 单位 |
|----|------|------|------|
| 链路负载包络 | $\mathbf{L}$ | $|\mathcal{E}| \times 1$ 向量 | dimensionless |
| 端口带宽 | $B$ | 标量 | Gbps |
| 每 lane 带宽 | $\mathbf{S}_{bw}$ | $|\mathcal{E}| \times |\mathcal{E}|$ **对角阵** | Gbps/lane |
| 每 lane 功耗 | $\mathbf{S}_{dyn}$ | $|\mathcal{E}| \times |\mathcal{E}|$ **对角阵** | W/lane |
| die-链路 incidence | $\mathbf{M}$ | $|\mathcal{V}| \times |\mathcal{E}|$ | $\{0,1\}$ |

物理 lane 数向量 $\boldsymbol{\ell}$（$|\mathcal{E}| \times 1$）：

$$\boldsymbol{\ell} = B \cdot \mathbf{S}_{bw}^{-1} \cdot \mathbf{L}$$

逐分量：$\ell_e = B \cdot L_e / S_{bw,e}$。单位：$\text{Gbps} \cdot 1 \;/\; (\text{Gbps/lane}) = \text{lane}$。

### 3b. 从 lane 到功耗

动态功耗向量 $\mathbf{P}_{dyn}$（$|\mathcal{V}| \times 1$）：

$$\mathbf{P}_{dyn} = \mathbf{M} \cdot \mathbf{S}_{dyn} \cdot \boldsymbol{\ell}$$

展开：$P_{dyn,v} = \sum_{e \in \delta(v)} S_{dyn,e} \cdot \ell_e$，单位 $\text{W} = \text{W/lane} \times \text{lane}$。

总功耗：

$$\mathbf{P} = \mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{dyn} \cdot \boldsymbol{\ell}$$

### 3c. 具体数值

一条 UCIe 链路 $e=0$ 连接 die 0。$S_{bw,0} = 32\ \text{Gbps/lane}$，$S_{dyn,0} = 16\ \text{mW/lane}$。$B = 1000\ \text{Gbps}$，$L_0 = 1.0$：

$$\ell_0 = 1000 \cdot 1.0 \;/\; 32 = 31.25\ \text{lane}$$
$$P_{dyn,0} = 1 \cdot 0.016 \cdot 31.25 = 0.5\ \text{W}$$
$$P_0 = 5.0 + 0.5 = 5.5\ \text{W}$$

（$\mathbf{M}$ 只有 $M_{0,0}=1$；$\mathbf{S}_{bw}$ 和 $\mathbf{S}_{dyn}$ 只有第 0 个对角元非零。）

### 3d. 消去 $\mathbf{T}$ 和 $\mathbf{P}$，写成 $\mathbf{L}$ 上的线性不等式

$$\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b} \quad\Longrightarrow\quad \mathbf{G}^{-1}(\mathbf{P} + \mathbf{b}) \le T_{max} \cdot \mathbf{1}$$

展开 $\mathbf{P}$，代入 $\boldsymbol{\ell} = B \cdot \mathbf{S}_{bw}^{-1} \cdot \mathbf{L}$：

$$\mathbf{G}^{-1}(\mathbf{P}_0 + \mathbf{b}) + B \cdot \underbrace{\mathbf{G}^{-1} \cdot \mathbf{M} \cdot \mathbf{S}_{dyn} \cdot \mathbf{S}_{bw}^{-1}}_{\displaystyle \mathbf{K}} \cdot \mathbf{L} \le T_{max} \cdot \mathbf{1}$$

其中 $\mathbf{K}$（$|\mathcal{V}| \times |\mathcal{E}|$）就是代码里的 `link_coeff`：

$$K_{v,e} = \sum_{u} G^{-1}_{v,u} \cdot M_{u,e} \cdot \frac{S_{dyn,e}}{S_{bw,e}}$$

单位：$\text{K/W} \times 1 \times (\text{W/lane}) / (\text{Gbps/lane}) = \text{K/Gbps}$。

每个 die $v$ 一条约束：

$$B \cdot \sum_{e} K_{v,e} \cdot L_e \;\le\; \underbrace{T_{max} - \bigl[\mathbf{G}^{-1}(\mathbf{P}_0 + \mathbf{b})\bigr]_v}_{\displaystyle rhs_v}$$

### 3e. 单 die 手工验算

$R_{vert}=2.0$，$T_{ambient}=300$，$P_0=5$，$T_{max}=358$：

$$\mathbf{G} = [0.5],\quad \mathbf{G}^{-1} = [2.0]$$
$$[\mathbf{G}^{-1}(\mathbf{P}_0 + \mathbf{b})]_0 = 2.0 \cdot (5 + 150) = 310\ \text{K}$$
$$rhs_0 = 358 - 310 = 48\ \text{K}$$

```python
p = [DiePlacement("d0", 0, 0, 12, 12)]
G, b = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=2.0, T_ambient=300.0))
# G=[[0.5]], b=[150], P0=[5] → G⁻¹(P0+b)=2.0×155=310 → rhs=358-310=48
net = ThermalNetworkBuilder.precompute(G, b, 358.0, {0: []}, 0, P0_vec=np.array([5.0]))
print(f"rhs = {net.rhs_ambient[0]:.1f} K  (expected 48)")
assert abs(net.rhs_ambient[0] - 48.0) < 1e-10
```

现在加上那条链路。$\mathbf{K}$ 矩阵的计算：

$$\mathbf{K} = \mathbf{G}^{-1} \cdot \mathbf{M} \cdot \mathbf{S}_{dyn} \cdot \mathbf{S}_{bw}^{-1}$$

单 die 场景下全是 $1\times1$ 矩阵：

$$K_{0,0} = 2.0 \cdot 1 \cdot 0.016 \cdot (1/32) = 2.0 \cdot 0.0005 = 0.001\ \text{K/Gbps}$$

```python
net = ThermalNetworkBuilder.precompute(G, b, 358.0, {0: [0]}, 1,
                            np.array([32.0]), np.array([0.016]),
                            P0_vec=np.array([5.0]))
# M = [[0.016/32]] = [[0.0005]], link_coeff = 2.0 × 0.0005 = 0.001
# rhs = 358 - 2.0×(150+5) = 48 (和上一步一致)
print(f"link_coeff = {net.link_coeff[0,0]:.4f} K/Gbps")
print(f"rhs = {net.rhs_ambient[0]:.1f} K")
assert abs(net.link_coeff[0,0] - 0.001) < 1e-10
assert abs(net.rhs_ambient[0] - 48.0) < 1e-10
```

---

## 第四步：LP 里面长什么样

一切就绪。`SteadyStateModel.build(ctx, B)` 写的就是这条不等式：

$$B \cdot link\_coeff \cdot L \le rhs\_ambient$$

代入 $B=1000$：$1000 \cdot 0.001 \cdot L[0] \le 48$，即 $L[0] \le 48$。

也就是说，在 $B=1000\ \text{Gbps}$ 时，这条 UCIe 链路的负载 $L$ 不能超过 48。如果 LP 中的排列代表元要求 $L$ 更大，热约束就会 infeasible。

```python
model = SteadyStateModel(net)
ctx = Ctx(); ctx.vector("L", 1)
model.build(ctx, B=1000.0)

c = ctx.constraints[0]
coeff = sum(t.coeff for t in c.terms if t.var == "L")
# B × link_coeff = 1000 × 0.001 = 1.0
# rhs = 48.0 (从上面 net 带下来)
print(f"约束: {coeff:.2f} × L[0] ≤ {c.rhs:.1f}")
assert abs(coeff - 1.0) < 1e-10
assert abs(c.rhs - 48.0) < 1e-10
```

---

## 一个完整数值案例

来一个具体场景，把所有数字串起来。

**设置**：2 个 die 水平邻接（中心距 13mm，间隙 1mm），$R_{vert}=1.5$，$T_{ambient}=300$，$P_0=5$W/die。die 0 有一条 UCIe 链路（32Gbps, 16mW/lane），$B=1000$，$L_0=1.0$。

**G 矩阵**（手算验证）：

| 项 | 公式 | 数值 |
|----|------|------|
| $G_{vert}$ | $1/R_{vert}$ | 0.667 W/K |
| $G_{01}$（横向） | $2kt\ell_{overlap}/(d_0+d_1+\delta)$ | $-14.4$ W/K |
| $G_{00}$ | $G_{vert} + |G_{01}|$ | 15.07 W/K |
| $G^{-1}_{00}$ | $(G^{-1})_{00} = G_{00}/\det(G)$ | 0.765 K/W |
| $G^{-1}_{01}$（耦合） | $(G^{-1})_{01} = |G_{01}|/\det(G)$ | 0.731 K/W |

注意：$G^{-1}$ 的元素只有 ~0.76，远小于 $1/G_{vert}=1.5$。这是因为横向耦合提供了第二条散热路径——die 0 的热量不仅向下走，还通过邻居 die 1 散出去。两路并行，等效热阻更低。

```python
p = [DiePlacement("d0", 0, 0, 12, 12),
     DiePlacement("d1", 13, 0, 12, 12)]
G, b = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=1.5, T_ambient=300.0))
G_inv = np.linalg.inv(G)
print(f"G =\n{G}")
print(f"G⁻¹ =\n{G_inv}")
# 手算验证 G⁻¹
detG = G[0,0]*G[1,1] - G[0,1]*G[1,0]
assert abs(G_inv[0,0] - G[0,0]/detG) < 1e-10
assert abs(G_inv[0,1] - (-G[0,1])/detG) < 1e-10
```

**功耗流**（$B=1000$, $L_0=1.0$, UCIe 参数）：

| 步骤 | 公式 | 数值 |
|------|------|------|
| lane 数 | $\ell = B L / S_{bw}$ | $1000 \times 1.0 / 32 = 31.25$ |
| 动态功耗 | $P_{dyn} = \ell \cdot S_{dyn}$ | $31.25 \times 0.016 = 0.5$ W |
| die 0 总功耗 | $P_0 + P_{dyn}$ | $5.0 + 0.5 = 5.5$ W |
| die 1 总功耗 | $P_0$（无链路） | $5.0$ W |

```python
ell = 1000 * 1.0 / 32.0
P = np.array([5.0 + ell * 0.016, 5.0])
print(f"ell={ell:.1f} lanes, P={P}")
```

**温度**（$T = G^{-1}(P + b)$，$b=G_{vert}\cdot T_{amb}=200$）：

| die | $P$ (W) | $b$ (W) | $P+b$ (W) | $T$ (K) | 距 $T_{max}$=358K |
|-----|---------|---------|-----------|---------|-------------------|
| die 0 | 5.5 | 200 | 205.5 | 307.9 | +50.1K |
| die 1 | 5.0 | 200 | 205.0 | 307.9 | +50.1K |

两个 die 温度几乎相同——横向热耦合（$G_{01}=-14.4$）远强于垂直散热（$G_{vert}=0.667$），所以功耗差异被邻居抹平了。这是好的散热设计。

```python
T = G_inv @ (P + b)
print(f"T = [{T[0]:.1f}, {T[1]:.1f}] K")
assert abs(T[0] - T[1]) < 1.0, "强耦合下温差应很小"
```

**LP 约束**（预计算 $\mathbf{K} = \mathbf{G}^{-1} \cdot \mathbf{M} \cdot \mathbf{S}_{dyn} \cdot \mathbf{S}_{bw}^{-1}$）：

| die $v$ | $K_{v,0}$ (K/Gbps) | $rhs_v$ (K) | 约束 |
|---------|---------------------|-------------|------|
| die 0 | $G^{-1}_{00} \cdot 1 \cdot 0.016/32 = 0.00038$ | $358 - [\mathbf{G}^{-1}(\mathbf{P}_0+\mathbf{b})]_0 = 201.1$ | $B \cdot K_{0,0} \cdot L_0 \le 201.1$ |
| die 1 | $G^{-1}_{10} \cdot 1 \cdot 0.016/32 = 0.00037$ | $201.1$ | $B \cdot K_{1,0} \cdot L_0 \le 201.1$ |

两个 die 的约束几乎相同（强耦合的结果）。在 $B=1000$ 时 $L_0 \le 201.1 / 0.38 \approx 529$——比单 die 的 48 大一个数量级。这就是横向散热的威力。

```python
ppl = np.array([0.016, 0.0]); lr = np.array([32.0, 1e9])
node_links = {0: [0], 1: []}
P0 = np.array([5.0, 5.0])
net = ThermalNetworkBuilder.precompute(G, b, 358.0, node_links, 2, lr, ppl, P0_vec=P0)
print(f"rhs = {net.rhs_ambient}")
print(f"link_coeff =\n{net.link_coeff}")
# die 0 系数略大于 die 1 (链路更直接影响 die 0)
assert net.link_coeff[0,0] > net.link_coeff[1,0]
# 强耦合下 rhs 几乎相等
assert abs(net.rhs_ambient[0] - net.rhs_ambient[1]) < 0.1
```

---

## 回顾整条链路

```
layout → G, b  (Layer A: AnalyticNetworkBuilder.system_of)
G, b, P0, Sdyn, Sbw → link_coeff, rhs  (Layer B: ThermalNetworkBuilder.precompute)
B × link_coeff × L ≤ rhs  (Layer C: SteadyStateModel.build)
```

每层都是输入→预计算→输出的纯函数。LP 求解时只跑 Layer C——`build()` 只做 B 缩放，所有系数已经算好了。

这也是为什么热约束是凸的：$T = G^{-1}(P+b)$ 是 $P$ 的线性函数，$P$ 是 $L$ 的线性函数，所以 $T$ 是 $L$ 的线性函数。$T \le T_{max}$ 是线性不等式。无论离散化多细（die 级、sub-die 级、全 3D），只要稳态热传导是线性 PDE，这个性质永远成立。

---

## 热网络构建器接口

"placement → 热网络"这层留接口：`ThermalNetworkBuilder(ABC)`，输入布局，输出 `ThermalNetwork`。model 层（`SteadyStateModel`）不关心 G/b 怎么来的——将来换 MFIT 仿真标定、hierarchical 标定网络，只是加一个子类。

```python
from physical.layout.thermal_network import ThermalNetworkBuilder, AnalyticNetworkBuilder

# ABC 不可实例化
try:
    ThermalNetworkBuilder()
    assert False, "抽象类应抛 TypeError"
except TypeError:
    pass

# 自包含场景：2 die 邻接，1 条链路
placements = [DiePlacement("d0", 0, 0, 12, 12),
              DiePlacement("d1", 13, 0, 12, 12)]
d2l = {0: [0], 1: [0]}          # 链路 0 两端都算
n_links = 1
lane_rate = np.array([32.0])
ppl = np.array([0.016])
P0_vec = np.array([5.0, 5.0])
stack = MfitStackConfig(R_vert=2.0, T_ambient=300.0)
T_MAX = 358.0

# AnalyticNetworkBuilder 与手工两步构建必须产出完全一致的网络
builder = AnalyticNetworkBuilder(stack=stack, T_max=T_MAX)
net_auto = builder.build(placements, d2l, n_links, lane_rate, ppl, P0_vec)

G2, b2 = AnalyticNetworkBuilder.system_of(placements, stack)
net_manual = ThermalNetworkBuilder.precompute(G2, b2, T_MAX, d2l, n_links, lane_rate, ppl, P0_vec=P0_vec)

assert np.allclose(net_auto.G_inv, net_manual.G_inv)
assert np.allclose(net_auto.rhs_ambient, net_manual.rhs_ambient)
assert np.allclose(net_auto.link_coeff, net_manual.link_coeff)
print(f"✓ {builder.name} 构建器: 与手工两步构建逐矩阵一致")
```

---

## ThermalNetwork 禁止私自构造

`ThermalNetwork` 是纯数据容器，但 G⁻¹ 和 link_coeff 之间有数学关系（M-矩阵非负、维度一致）——私自构造可能造出不合法的网络。所以：

- `@dataclass(frozen=True, init=False)`：直接 `ThermalNetwork(...)` 是 TypeError
- 合法构造只有 `ThermalNetwork.from_system(...)` 类方法，构造时校验不变量

```python
from physical.layout.thermal_network._net import ThermalNetwork

# 直接构造被禁
try:
    ThermalNetwork(np.eye(2), np.zeros(2), np.zeros((2, 1)))
    assert False, "直接构造应 TypeError"
except TypeError:
    print("✓ 直接构造被禁止 (init=False)")

# 类上没有任何工厂——from_system 不存在（Builder 是唯一生产者）
assert not hasattr(ThermalNetwork, "from_system")
print("✓ ThermalNetwork 类上无工厂，唯一入口是 ThermalNetworkBuilder")

# 不变量校验在 Builder._make_network：喂非 M-矩阵的 G → G_inv 负值 → ValueError
G_bad = np.array([[-1.0, 0.0], [0.0, -1.0]])
try:
    ThermalNetworkBuilder.precompute(
        G_bad, np.zeros(2), 358.0, {0: [], 1: []}, 0)
    assert False, "非 M-矩阵应 ValueError"
except ValueError as e:
    print(f"✓ 不变量校验生效: {e}")

# 合法入口 = Builder.precompute
net_ok = ThermalNetworkBuilder.precompute(
    np.eye(2), np.zeros(2), 358.0, {0: [], 1: []}, 0)
print(f"✓ 唯一入口构造: rhs={net_ok.rhs_ambient}")
```
