# test10 — CLI 入口 (src/main.py)

## 模块定位

`main.py` 是代码作为"基础产品"的入口：读问题定义 YAML（引用物理参数文件）→ 组装模型 → 求解 → 输出结果文档。

两个文件分工：
- **params/\*.yaml** —— 物理参数（实验设置，可复用，对应 ExpParams）
- **problems/\*.yaml** —— 问题定义（实验实例：引用 params + 拓扑 + 场景 + 选择器 + query）

toy 参数组先行：FullMeshTopology(2,1) 的 B* 手算锚点 4500（test09 已验证），main 的完整流程必须落到这个数上。

## 1. 物理参数文件 → ExpParams

```python
import sys; sys.path.insert(0, '../src')
import tempfile, pathlib
import yaml
from physical.params import ExpParams

tmp = pathlib.Path(tempfile.mkdtemp())
params_yaml = """
name: toy
die: {width_mm: 10.0, height_mm: 10.0, static_power_w: 10.0, vdd_v: 1.0}
bump: {name: toy-bump-100μm, pitch_um: 100.0, current_per_bump_ma: 100.0, utilization: 1.0}
link: {name: toy-link-10G, lane_rate_gbps: 10.0, power_per_lane_w: 0.1}
global_link: {name: toy-serdes-100G, lane_rate_gbps: 100.0, power_per_lane_w: 1.0}
c4: {name: toy-c4-200μm, pitch_um: 200.0, current_per_bump_ma: 200.0, utilization: 1.0}
thermal: {r_vert_k_per_w: 1.0, k_interposer: 100.0, t_interposer_mm: 0.1,
          t_ambient_k: 300.0, t_max_k: 400.0}
pkg: {interposer_w_mm: 100.0, interposer_h_mm: 100.0,
      metal_layers: 4, lanes_per_mm: 100.0, c4_pitch_mm: 1.0}
"""
p = tmp / "toy.yaml"
p.write_text(params_yaml)

P = ExpParams.from_dict(yaml.safe_load(params_yaml))
# 手算锚点全部对齐（test09 的准则）
assert P.die.area_mm2 == 100.0
assert P.bump.density_per_mm2 == 100.0
assert P.link.pj_per_bit == 10.0
assert P.thermal.thermal_budget_k == 100.0
print(f"✓ params yaml → ExpParams: {P.name}, 能效 {P.link.pj_per_bit:.0f} pJ/bit")
```

## 2. 完整流程：问题文件 → B* 手算锚点

```python
import sys; sys.path.insert(0, '../src')
import tempfile, pathlib

from main import load_problem, solve_problem

tmp = pathlib.Path(tempfile.mkdtemp())
(tmp / "params").mkdir()
(tmp / "params" / "toy.yaml").write_text("""
name: toy
die: {width_mm: 10.0, height_mm: 10.0, static_power_w: 10.0, vdd_v: 1.0}
bump: {name: toy-bump-100μm, pitch_um: 100.0, current_per_bump_ma: 100.0, utilization: 1.0}
link: {name: toy-link-10G, lane_rate_gbps: 10.0, power_per_lane_w: 0.1}
global_link: {name: toy-serdes-100G, lane_rate_gbps: 100.0, power_per_lane_w: 1.0}
c4: {name: toy-c4-200μm, pitch_um: 200.0, current_per_bump_ma: 200.0, utilization: 1.0}
thermal: {r_vert_k_per_w: 1.0, k_interposer: 100.0, t_interposer_mm: 0.1,
          t_ambient_k: 300.0, t_max_k: 400.0}
pkg: {interposer_w_mm: 100.0, interposer_h_mm: 100.0,
      metal_layers: 4, lanes_per_mm: 100.0, c4_pitch_mm: 1.0}
""", encoding="utf-8")
problem_yaml = f"""
params: {tmp}/params/toy.yaml
topo: {{type: fullmesh, args: [2, 1]}}
scenario: perf+bump+therm
selector: conjugacy
query: {{type: bmax, lo: 100, hi: 20000, step: 100}}
"""
prob_path = tmp / "problem.yaml"
prob_path.write_text(problem_yaml)

spec = load_problem(prob_path)
r = solve_problem(spec)

print(f"B* = {r['B_star']:.0f}  (手算锚点 ~4500)")
assert 4000 <= r['B_star'] <= 6000, f"toy 手算锚点失配: {r['B_star']}"
assert r["scenario"] == "perf+bump+therm"
```

## 3. 错误处理：坏配置必须清晰报错

```python
import sys; sys.path.insert(0, '../src')
import tempfile, pathlib
from main import load_problem

tmp = pathlib.Path(tempfile.mkdtemp())

# 3a. params 文件不存在
bad1 = tmp / "bad1.yaml"
bad1.write_text(f"""
params: {tmp}/no_such_file.yaml
topo: {{type: mesh, args: [2]}}
scenario: perf
query: {{type: bmax}}
""")
try:
    load_problem(bad1)
    assert False, "缺 params 文件应报错"
except (FileNotFoundError, ValueError) as e:
    print(f"✓ 缺 params 文件: {type(e).__name__}: {e}")

# 3b. 坏 scenario
(tmp / "params").mkdir(exist_ok=True)
(tmp / "params" / "toy2.yaml").write_text("""
name: toy
die: {width_mm: 10.0, height_mm: 10.0, static_power_w: 10.0, vdd_v: 1.0}
bump: {name: t, pitch_um: 100.0, current_per_bump_ma: 100.0, utilization: 1.0}
link: {name: t, lane_rate_gbps: 10.0, power_per_lane_w: 0.1}
global_link: {name: t, lane_rate_gbps: 100.0, power_per_lane_w: 1.0}
c4: {name: t, pitch_um: 200.0, current_per_bump_ma: 200.0, utilization: 1.0}
thermal: {r_vert_k_per_w: 1.0, k_interposer: 100.0, t_interposer_mm: 0.1,
          t_ambient_k: 300.0, t_max_k: 400.0}
pkg: {interposer_w_mm: 100.0, interposer_h_mm: 100.0,
      metal_layers: 4, lanes_per_mm: 100.0, c4_pitch_mm: 1.0}
""")
bad2 = tmp / "bad2.yaml"
bad2.write_text(f"""
params: {tmp}/params/toy2.yaml
topo: {{type: mesh, args: [2]}}
scenario: not_a_scenario
query: {{type: bmax}}
""")
try:
    load_problem(bad2)
    assert False, "坏 scenario 应报错"
except ValueError as e:
    print(f"✓ 坏 scenario: {e}")

# 3c. 坏 topo type
bad3 = tmp / "bad3.yaml"
bad3.write_text(f"""
params: {tmp}/params/toy2.yaml
topo: {{type: hypercube, args: [2]}}
scenario: perf+bump+therm
query: {{type: bmax}}
""")
try:
    load_problem(bad3)
    assert False, "坏 topo type 应报错"
except ValueError as e:
    print(f"✓ 坏 topo type: {e}")
```

## 结论

main 的契约：params YAML → ExpParams（字段对齐，toy 锚点全对）；完整流程 B* 落在手算锚点；三类坏配置（缺文件/坏 scenario/坏 topo）当场清晰报错。
