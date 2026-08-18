import sys; sys.path.insert(0, '../src')
import sys; sys.path.insert(0, '../src')
import numpy as np
from physical.layout.thermal_network import (
    DiePlacement, MfitStackConfig, ThermalNetworkBuilder, AnalyticNetworkBuilder,
)
from problem.models.phys.therm._steady_state import SteadyStateModel
from problem import Ctx

p = [DiePlacement("d0", 0, 0, 12, 12)]
G, _ = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=2.0))
# R_vert=2.0 → G = 1/2.0 = 0.5
print(f"单 die: G = {G[0,0]:.2f} W/K")
assert abs(G[0,0] - 0.5) < 1e-10

_, b = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=2.0, T_ambient=300.0))
print(f"b = {b[0]:.0f} W  (0.5 × 300)")
assert abs(b[0] - 150.0) < 1e-10

p = [DiePlacement("d0", 0, 0, 12, 12),
     DiePlacement("d1", 13, 0, 12, 12)]
G, _ = AnalyticNetworkBuilder.system_of(p, MfitStackConfig())
print(f"G =\n{G}")
# 验证: 非对角为负 (耦合)，对角 > 非对角之和 (对角占优)
assert G[0,1] < -1e-6
assert G[0,0] > abs(G[0,1])

p = [DiePlacement("d0", 0, 0, 12, 12)]
G, b = AnalyticNetworkBuilder.system_of(p, MfitStackConfig(R_vert=2.0, T_ambient=300.0))
# G=[[0.5]], b=[150], P0=[5] → G⁻¹(P0+b)=2.0×155=310 → rhs=358-310=48
net = ThermalNetworkBuilder.precompute(G, b, 358.0, {0: []}, 0, P0_vec=np.array([5.0]))
print(f"rhs = {net.rhs_ambient[0]:.1f} K  (expected 48)")
assert abs(net.rhs_ambient[0] - 48.0) < 1e-10

net = ThermalNetworkBuilder.precompute(G, b, 358.0, {0: [0]}, 1,
                            np.array([32.0]), np.array([0.016]),
                            P0_vec=np.array([5.0]))
# M = [[0.016/32]] = [[0.0005]], link_coeff = 2.0 × 0.0005 = 0.001
# rhs = 358 - 2.0×(150+5) = 48 (和上一步一致)
print(f"link_coeff = {net.link_coeff[0,0]:.4f} K/Gbps")
print(f"rhs = {net.rhs_ambient[0]:.1f} K")
assert abs(net.link_coeff[0,0] - 0.001) < 1e-10
assert abs(net.rhs_ambient[0] - 48.0) < 1e-10

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

ell = 1000 * 1.0 / 32.0
P = np.array([5.0 + ell * 0.016, 5.0])
print(f"ell={ell:.1f} lanes, P={P}")

T = G_inv @ (P + b)
print(f"T = [{T[0]:.1f}, {T[1]:.1f}] K")
assert abs(T[0] - T[1]) < 1.0, "强耦合下温差应很小"

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
