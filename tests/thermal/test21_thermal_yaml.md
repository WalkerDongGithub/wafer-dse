# test21 — YAML 热网络组装器 (config/thermal/*.yaml → ThermalNetwork)

## 模块定位

master 指令：一个能翻译成 G·T = P + b 的配置工具。物理配置在
`config/thermal/*.yaml`，`build_thermal_from_yaml(path)` 组装 ThermalNetwork。

- **schema v1**：nodes（die/stack/boundary）+ edges（face_adjacency /
  vertical_chain / tsv / hybrid / ground）；3D/2.5D 同一结构；
- **边界**：boundary 节点 → b = g·T_amb；vertical_chain → 纵向集总 g = 1/R_vert
  （对角项 + b 贡献）；face_adjacency → 横向面邻接（非对角 + 对角）；
- **M-矩阵校验保留**（ThermalNetworkBuilder._make_network：G⁻¹ ≥ 0）；
- **不接 build_scenario/Model**——纯 ThermalNetwork 构造。

公式（thermal-g-construction.md 已核验）：
- 面邻接：$G_{\text{lat}} = k \cdot \text{overlap} \cdot t / (\frac{d_i}{2}+\frac{d_j}{2}+\text{gap})$
- 纵向：$g_{\text{vert}} = 1/R_{\text{vert}}$，$b = g_{\text{vert}} \cdot T_{\text{amb}}$

```python
import sys; sys.path.insert(0, '../src')
import numpy as np
from physical.layout.thermal_network import (
    build_thermal_from_yaml, ThermalNetwork,
)
```

---

## 1. 2.5D 两 die + ambient：手算 G/b

`config/thermal/2p5d-two-die.yaml`：die0(0,0,12,12)、die1(13,0,12,12)、
k=150 W/mK、t=0.1mm、gap=1mm、R_vert=1.5、T_amb=300。

### 手算

- **面邻接**（die0↔die1，y 方向相邻，overlap = 共享边长 = 12mm = 0.012m）：
  $$
  G_{\text{lat}} = \frac{150 \times 0.012 \times 0.0001}{\frac{0.012}{2}+\frac{0.012}{2}+0.001}
                 = \frac{1.8\times10^{-4}}{0.013} = 0.013846\ \text{W/K}
  $$
- **纵向**（每 die）：$g_{\text{vert}} = 1/1.5 = 0.666667$ W/K
- **G**（2×2）：
  $$
  G = \begin{bmatrix} 0.666667+0.013846 & -0.013846 \\ -0.013846 & 0.666667+0.013846 \end{bmatrix}
  $$
- **b** = g_vert·T_amb = 0.666667 × 300 = 200.0（每 die）
- M-矩阵校验：G 严格对角占优（对角 0.6805 > 行非对角和 0.0138）→ G⁻¹ ≥ 0

```python
net = build_thermal_from_yaml("../config/thermal/2p5d-two-die.yaml")
assert isinstance(net, ThermalNetwork)
G_inv = net.G_inv
assert G_inv.shape == (2, 2)
# 手算 G（由 G⁻¹ 反推验证：G = inv(G_inv)）
G = np.linalg.inv(G_inv)
g_lat = 150.0 * 0.012 * 0.0001 / (0.012/2 + 0.012/2 + 0.001)
g_vert = 1.0 / 1.5
G_expect = np.array([[g_vert + g_lat, -g_lat],
                     [-g_lat, g_vert + g_lat]])
print(f"G_lat = {g_lat:.6f}, G = {G.round(6).tolist()}")
assert np.allclose(G, G_expect, atol=1e-9), "G 应与手算一致"
assert np.all(G_inv >= 0), "G⁻¹ 必须非负（M-矩阵）"
print("✓ 2.5D 两 die：G 与手算逐位一致，M-矩阵校验通过")
```

---

## 2. 散热板变体：R_vert 更小 → b 同源、G 对角更大

`config/thermal/2p5d-two-die-heatsink.yaml`：同一布局，vertical_chain 走
heatsink（R_vert=0.8），T_coolant=300。

### 手算

- 面邻接不变：G_lat = 0.013846
- 纵向：g_vert = 1/0.8 = 1.25（比 1.5 档大 → 散热能力更强）
- G 对角 = 1.25 + 0.013846 = 1.263846；b = 1.25 × 300 = 375

```python
net_hs = build_thermal_from_yaml("../config/thermal/2p5d-two-die-heatsink.yaml")
G_hs = np.linalg.inv(net_hs.G_inv)
g_vert_hs = 1.0 / 0.8
G_hs_expect = np.array([[g_vert_hs + g_lat, -g_lat],
                        [-g_lat, g_vert_hs + g_lat]])
assert np.allclose(G_hs, G_hs_expect, atol=1e-9)
# 散热板档 vs 默认档：同 P 下结温更低（G 对角更大 = 更易散热）
assert G_hs[0, 0] > G[0, 0], "散热板 R_vert 小 → G 对角大 → 结温低"
print(f"✓ 散热板变体：G 对角 {G_hs[0,0]:.4f} > 默认 {G[0,0]:.4f}（散热更强）")
```

---

## 3. 3D 集总：每 stack 一个节点，R_vert = 层串联和

`config/thermal/3d-stack-two-lumped.yaml`：stack 类型（layers=2），
R_vert=2.4（=1.2+1.2 串联）。

### 手算

- 面邻接（stack0↔stack1，层聚合横向）：G_lat = 0.013846（同 2.5D）
- 纵向：g_vert = 1/2.4 = 0.416667
- G 对角 = 0.416667 + 0.013846 = 0.430513

```python
net_3d = build_thermal_from_yaml("../config/thermal/3d-stack-two-lumped.yaml")
assert net_3d.G_inv.shape == (2, 2), "3D 集总 = 每 stack 一个节点 → 2×2"
G_3d = np.linalg.inv(net_3d.G_inv)
g_vert_3d = 1.0 / 2.4
G_3d_expect = np.array([[g_vert_3d + g_lat, -g_lat],
                        [-g_lat, g_vert_3d + g_lat]])
assert np.allclose(G_3d, G_3d_expect, atol=1e-9)
assert np.all(net_3d.G_inv >= 0)
print(f"✓ 3D 集总：2 节点（每 stack），G 与手算一致（g_vert={g_vert_3d:.6f}）")
```

---

## 4. schema 统一性：3D/2.5D 同一结构（节点类型不同，edges 结构同一）

```python
import yaml
for path in ["../config/thermal/2p5d-two-die.yaml",
             "../config/thermal/3d-stack-two-lumped.yaml"]:
    d = yaml.safe_load(open(path))
    assert set(d) >= {"name", "t_max_k", "nodes", "edges"}
    assert all({"id", "type"} <= set(n) for n in d["nodes"])
    assert all("type" in e for e in d["edges"])
print("✓ 2.5D/3D 同一 schema：name/t_max_k/nodes/edges 结构一致")
```

---

## 5. 边界校验：无散热路径 → M-矩阵破坏 → 报错

没有 boundary/vertical 边的 die 无散热路径 → G 对角为 0 → 非对角占优 →
ThermalNetwork 构造必须拒绝（G⁻¹ 非非负）。

```python
import tempfile, pathlib
bad_yaml = """
name: bad
t_max_k: 358.15
nodes:
  - {id: die0, type: die, geometry: {x_mm: 0, y_mm: 0, w_mm: 12, h_mm: 12}}
edges:
  - {type: face_adjacency, between: [die0], k_interposer_w_mk: 150.0,
     t_interposer_mm: 0.1}
"""
p = pathlib.Path(tempfile.mkdtemp()) / "bad.yaml"
p.write_text(bad_yaml)
try:
    build_thermal_from_yaml(str(p))
    print("FAIL: 无散热路径应报错")
    assert False
except (ValueError, RuntimeError) as e:
    print(f"✓ 无散热路径 → 拒绝: {type(e).__name__}")
```

---

## 6. 纯 ThermalNetwork 构造（不接 build_scenario/Model）

组装器返回 ThermalNetwork（含 G_inv/rhs_ambient/link_coeff），可被
SteadyStateModel 消费（若后续接入），但本模块自身不 import problem.models。

```python
import inspect
src = inspect.getsource(build_thermal_from_yaml)
assert "build_scenario" not in src and "problem.models" not in src, \
    "组装器不接 build_scenario/Model（纯 ThermalNetwork 构造）"
print("✓ 组装器纯 ThermalNetwork 构造，不依赖 problem.models")
```

---

## 7. 3D 展开形态：每层 die 节点 + 层间 tsv 边（schema 双形态）

`config/thermal/3d-two-die-explicit.yaml`：stack 展开为每层一个 die 节点，
层间纵向用 tsv 边（R_tsv = r_via/n_vias 并联），顶层 vertical_chain 到 ambient。

### 手算

两 die 上下堆叠（同 x/y 位置）：die_bottom（层 0，几何 0,0,12,12）、
die_top（层 1，同位置），tsv 连接两者：n_vias=10、r_via=50 → R_tsv=5、
g_tsv=0.2。die_top → ambient vertical_chain R=1.0（g=1.0）。
die_bottom 无直接散热路径（热量经 tsv 到 top 再到 ambient）——G 2×2：

$$
G = \begin{bmatrix} g_{\text{tsv}} & -g_{\text{tsv}} \\ -g_{\text{tsv}} & g_{\text{tsv}}+g_{\text{vert}} \end{bmatrix}
  = \begin{bmatrix} 0.2 & -0.2 \\ -0.2 & 1.2 \end{bmatrix}
$$

b = [0, g_vert·T_amb] = [0, 300]。

```python
net_x = build_thermal_from_yaml("../config/thermal/3d-two-die-explicit.yaml")
G_x = np.linalg.inv(net_x.G_inv)
g_tsv = 1.0 / 5.0
G_x_expect = np.array([[g_tsv, -g_tsv],
                       [-g_tsv, g_tsv + 1.0]])
assert G_x.shape == (2, 2), "展开形态 = 每层 die 节点"
assert np.allclose(G_x, G_x_expect, atol=1e-9), "G 应与手算一致"
assert np.all(net_x.G_inv >= 0), "M-矩阵校验"
print(f"✓ 3D 展开（tsv 层间纵向）：G={G_x.round(4).tolist()} 与手算一致")
```

---

## 8. schema 双形态统一：集总 stack 与显式展开共用同一结构

集总（stack.layers 记录）与展开（每层 die + tsv 边）都是
nodes+edges 结构，仅节点/边类型不同——同一 schema。

```python
d_lump = yaml.safe_load(open("../config/thermal/3d-stack-two-lumped.yaml"))
d_expl = yaml.safe_load(open("../config/thermal/3d-two-die-explicit.yaml"))
assert set(d_lump) == set(d_expl) == {"name", "t_max_k", "nodes", "edges"}
assert d_expl["nodes"][0]["type"] == "die" and d_expl["nodes"][1]["type"] == "die"
tsv_edges = [e for e in d_expl["edges"] if e["type"] == "tsv"]
assert len(tsv_edges) == 1, "展开形态应有 tsv 层间边"
print("✓ 双形态同一 schema：集总（stack+layers）与展开（每层 die+tsv）")
```

---

## 9. heatsink 显式化（§十五）：die→TIM→heatsink→ambient 三段链

`config/thermal/2p5d-two-die-heatsink-explicit.yaml`：heatsink 是**显式节点**
（非 boundary）——die 经 tim 边到 heatsink，heatsink 经 heatsink_ambient 边
到 ambient（环境）。作者要求看完整散热链。

### 手算（两 die + heatsink，3 自由节点，r_sink 字段）

- 面邻接（die0↔die1）：G_lat = 0.013846（同 §1）
- tim 边（die→heatsink）：r_tim=0.3 → g_tim = 1/0.3 = 3.3333
- heatsink_ambient：r_sink=0.5 → g_sink = 1/0.5 = 2.0
- G（3×3：die0, die1, heatsink）：
  $$
  G = \begin{bmatrix}
      g_{\text{lat}}+g_{\text{tim}} & -g_{\text{lat}} & -g_{\text{tim}} \\
      -g_{\text{lat}} & g_{\text{lat}}+g_{\text{tim}} & -g_{\text{tim}} \\
      -g_{\text{tim}} & -g_{\text{tim}} & 2g_{\text{tim}}+g_{\text{sink}}
  \end{bmatrix}
  $$
- b = [0, 0, g_sink·T_amb] = [0, 0, 600]

```python
net_h = build_thermal_from_yaml("../config/thermal/2p5d-two-die-heatsink-explicit.yaml")
G_h = np.linalg.inv(net_h.G_inv)
g_tim = 1.0 / 0.3
g_sink = 1.0 / 0.5
G_h_expect = np.array([
    [g_lat + g_tim, -g_lat, -g_tim],
    [-g_lat, g_lat + g_tim, -g_tim],
    [-g_tim, -g_tim, 2*g_tim + g_sink],
])
assert G_h.shape == (3, 3), "heatsink 显式 = 两 die + heatsink 三个自由节点"
assert np.allclose(G_h, G_h_expect, atol=1e-9), "G 应与手算一致"
assert np.all(net_h.G_inv >= 0), "M-矩阵校验"
print(f"✓ heatsink 显式：G={G_h.round(4).tolist()} 与手算一致（tim 3.3333 + sink 2.0）")
```

---

## 10. 边类型完整性：tsv/hybrid/tim/heatsink_ambient 全解析

```python
import yaml as _y
for path, etypes in [
    ("../config/thermal/3d-two-die-explicit.yaml", {"tsv", "vertical_chain"}),
    ("../config/thermal/2p5d-two-die-heatsink-explicit.yaml",
     {"tim", "heatsink_ambient"}),
]:
    d = _y.safe_load(open(path))
    got = {e["type"] for e in d["edges"]}
    assert etypes <= got, f"{path}: 应含 {etypes}，实际 {got}"
print("✓ 边类型齐全：face_adjacency/vertical_chain/ground/tsv/hybrid/tim/heatsink_ambient")
```

---

## 11. heatsink_ambient 用 r_sink_k_per_w（§十五 定案字段）

定案（model-ruling §十五）heatsink_ambient 字段 = `r_sink_k_per_w`
（散热板自身到环境的总热阻，含 R_spread + R_conv 集总），非 h·A 对流。
物理等价（r_sink = 1/(h·A)），但 schema 与定案一致。

### 手算（单 die 链 die0 → tim → heatsink → heatsink_ambient → ambient）

- tim：r_tim=0.3 → g_tim = 3.3333
- heatsink_ambient：r_sink=0.5 → g_sink = 1/0.5 = 2.0
- G（2×2：die0, heatsink）：
  $$
  G = \begin{bmatrix} g_{\text{tim}} & -g_{\text{tim}} \\ -g_{\text{tim}} & g_{\text{tim}}+g_{\text{sink}} \end{bmatrix}
    = \begin{bmatrix} 3.3333 & -3.3333 \\ -3.3333 & 5.3333 \end{bmatrix}
  $$
- b = [0, g_sink·T_amb] = [0, 600]

```python
d_r = """
name: hs-r-sink
t_max_k: 358.15
nodes:
  - {id: die0, type: die, geometry: {x_mm: 0, y_mm: 0, w_mm: 12, h_mm: 12}}
  - {id: hs, type: heatsink}
  - {id: amb, type: boundary, temperature_k: 300.0}
edges:
  - {type: tim, from: die0, to: hs, r_tim_k_per_w: 0.3}
  - {type: heatsink_ambient, from: hs, to: amb, r_sink_k_per_w: 0.5}
"""
p2 = pathlib.Path(tempfile.mkdtemp()) / "hs_r.yaml"
p2.write_text(d_r)
net_r = build_thermal_from_yaml(str(p2))
G_r = np.linalg.inv(net_r.G_inv)
g_tim_r = 1.0 / 0.3
g_sink = 1.0 / 0.5
G_r_expect = np.array([[g_tim_r, -g_tim_r],
                       [-g_tim_r, g_tim_r + g_sink]])
assert np.allclose(G_r, G_r_expect, atol=1e-9), "r_sink 字段应与手算一致"
assert np.all(net_r.G_inv >= 0)
print(f"✓ heatsink_ambient r_sink_k_per_w：G={G_r.round(4).tolist()}（g_tim 3.3333 + g_sink 2.0）")
```

---

## 12. 全链显式：die→ubump→interposer→c4→substrate→ambient（§十六）

`config/thermal/2p5d-full-chain.yaml`：interposer/substrate 为显式节点
（有自身温升），链段边 ubump/c4/substrate_ambient（1/R）。

### 手算（两 die + interposer + substrate，4 自由节点）

- 面邻接（die0↔die1）：G_lat = 0.013846
- ubump（die→interposer）：r_ubump=0.2 → g_ub = 5.0
- c4（interposer→substrate）：r_c4=0.3 → g_c4 = 3.3333
- substrate_ambient：r_sub=0.5 → g_sub = 2.0
- G（4×4：die0, die1, interposer, substrate）：
  $$
  G = \begin{bmatrix}
      g_{\text{lat}}+g_{\text{ub}} & -g_{\text{lat}} & -g_{\text{ub}} & 0 \\
      -g_{\text{lat}} & g_{\text{lat}}+g_{\text{ub}} & -g_{\text{ub}} & 0 \\
      -g_{\text{ub}} & -g_{\text{ub}} & 2g_{\text{ub}}+g_{\text{c4}} & -g_{\text{c4}} \\
      0 & 0 & -g_{\text{c4}} & g_{\text{c4}}+g_{\text{sub}}
  \end{bmatrix}
  $$
- b = [0, 0, 0, g_sub·T_amb] = [0, 0, 0, 600]

```python
net_f = build_thermal_from_yaml("../config/thermal/2p5d-full-chain.yaml")
G_f = np.linalg.inv(net_f.G_inv)
g_ub = 1.0 / 0.2
g_c4 = 1.0 / 0.3
g_sub = 1.0 / 0.5
G_f_expect = np.array([
    [g_lat + g_ub, -g_lat, -g_ub, 0.0],
    [-g_lat, g_lat + g_ub, -g_ub, 0.0],
    [-g_ub, -g_ub, 2*g_ub + g_c4, -g_c4],
    [0.0, 0.0, -g_c4, g_c4 + g_sub],
])
assert G_f.shape == (4, 4), "全链 = 两 die + interposer + substrate 四个自由节点"
assert np.allclose(G_f, G_f_expect, atol=1e-9), "全链 G 应与手算一致"
assert np.all(net_f.G_inv >= 0), "M-矩阵校验"
print(f"✓ 全链显式：G={G_f.round(4).tolist()}（ubump 5.0 + c4 3.3333 + sub 2.0）")
```

---

## 13. v1.2 节点/边类型：interposer/substrate + ubump/c4/substrate_ambient

```python
d_full = yaml.safe_load(open("../config/thermal/2p5d-full-chain.yaml"))
types = {n["type"] for n in d_full["nodes"]}
assert {"die", "interposer", "substrate", "boundary"} <= types, \
    f"应含 die/interposer/substrate/boundary，实际 {types}"
etypes = {e["type"] for e in d_full["edges"]}
assert {"ubump", "c4", "substrate_ambient"} <= etypes, \
    f"应含 ubump/c4/substrate_ambient，实际 {etypes}"
print("✓ v1.2 节点/边类型齐全（interposer/substrate + ubump/c4/substrate_ambient）")
```

---

## 结论

YAML 热网络组装器（schema v1.2）实现：

- `config/thermal/*.yaml`：nodes（die/stack/heatsink/interposer/substrate/
  boundary）+ edges（face_adjacency/vertical_chain/tsv/hybrid/ground/tim/lid/
  heatsink_ambient/ubump/c4/substrate_ambient），3D/2.5D 同一结构；
- `build_thermal_from_yaml(path) -> ThermalNetwork`：边类型公式库（面邻接、
  纵向 1/R_vert、tsv 并联、链段边 1/R）→ G/b → M-矩阵校验 → ThermalNetwork；
- **双形态**（§十四）+ **heatsink 显式**（§十五）+ **全链显式**（§十六：
  interposer/substrate 节点 + ubump/c4/substrate_ambient 链段）；
- 手算锚点：2.5D、散热板、3D 集总、3D 展开、heatsink 三段链、r_sink 字段、
  全链三段；
- 无散热路径 → 拒绝；不接 build_scenario/Model。
