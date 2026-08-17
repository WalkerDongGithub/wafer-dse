# Do 报告 — 领域专家分身（03a）数学完善

日期：2026-08-17
任务：三层热网络 G_joint 构造 + §2.8 数量关系 + 多约束退化 λ 排序

## 一、三层垂直热网络的 G_joint 显式构造

记号：G_intra（die 层热导）、G_inter（substrate 层热导）、G_vert^intra（die→interposer 底面垂直热导对角阵）、G_vert^inter（substrate→ambient 垂直热导对角阵）。

**单向耦合（任务给定）**：T_bottom=T_substrate，得

```
[ G_intra   -G_vert^intra ] [T_die]   [ P_die                    ]
[ 0           G_inter      ] [T_sub] = [ P_sub + G_vert^inter·T_amb ]
```

分块下三角矩阵，显式逆：

```
T_die = G_intra^{-1}·P_die + G_intra^{-1}·G_vert^intra·G_inter^{-1}·P_sub + (环境项)
```

**双向耦合（物理严格，推荐）**：把 die 流入 substrate 的热加回，得对称不可约 M-矩阵，逆严格正。Schur 补形式：

```
T_die = (G_intra − G_vert^intra·B^{-1}·G_vert^intra)^{-1}·(P_die + G_vert^intra·B^{-1}·P_sub + ...),  B=G_inter+G_vert^intra
```

**结论**：两版都保持 G_joint^{-1} ≥ 0，V4 §4 热约束线性化「T≤T_max ⟺ G·T_max·1 ≥ P+b」在联合模型下原样成立，只需 G→G_joint、P→(P_die,P_sub)。推荐双向对称形式（物理严格、对称正定、逆严格正）。

## 二、§2.8 数量关系（α_d、β_P 物理依据）

**α_d（die 边长随 B）**：端口数 N=B/r，lane 数 =B/s（工业事实），PHY/IO 面积 A_io=a_lane·(B/s)=a_io·B（线性）。A_die(B)=A_core+a_io·B，d(B)=√(A_core+a_io·B)，一阶展开：

```
α_d = a_io/(2·d_0) = a_lane/(2·s·d_0)
```

两种极限：perimeter-limited α_d=1/(s·σ)（严格线性）；area-array α_d=1/(2·s·ρ·d_0)（sqrt 线性化）。
量级：SerDes perimeter α_d~1e-4 mm/Gbps；UCIe area-array α_d~1e-6 mm/Gbps。
标定来源：TH5（750mm²/51.2T/512×112G，唯一面积+功耗齐全锚点）、Dojo D1、UCIe shoreline 28–224 GB/s/mm。
**待核实**：a_lane 精确值、TH3/TH4 die 面积（TechInsights 付费）。

**β_P（峰值功耗随 B）**：线性项 = 每 Gbps 链路功耗斜率（pJ/bit）。1 W/Tbps = 1 pJ/bit，故 β_P（W/Tbps）= pJ/bit 数值。
量级：长距 SerDes 2–4、UCIe 0.25–0.5、UCIe-3D 0.2 pJ/bit。
标定：TH5 p_IO=2 pJ/bit（Chen thesis：100W÷51.2T）。
**待核实**：S_dyn 与 β_P 的精确拆分。

**一致性警示**：A_die(B)=(d_0+α_d·B)² 是 B 的二次函数，N_total(B) 二次，μbump 约束变凸二次——固定 B 仍是线性 LP，但「B 作变量」升级为 QCQP/SOCP（论文卖点而非缺陷）。

## 三、多约束绑定退化 λ 排序

固定 L*，B*(b)=min_i b_i/a_i（a_i=A_i·L*），凹，绑定集 J=argmin_i b_i/a_i，次微分 ∂B*=conv{e_i/a_i : i∈J}。
退化验证：单松任一绑定约束方向导数 = 0。
联合松弛收益 = min_i ε_i/a_i，瓶颈 = a_i 最大者。

**推荐三层唯一排序**：
1. 主序（瓶颈优先）：按 a_i=A_i·L* **降序**（松它才抬升 min 下界）。
2. tie-break：物理优先级字典序 热 > 布线 > bump > C4。
3. 辅助（归一化投资效率）：按 1/a_i 降序（「谁值钱」，仅作比较，非实际边际收益）。

区分两个量：a_i 降序回答「谁挡路」，1/a_i 降序回答「谁值钱」。

## 待核实汇总

① 单向/双向耦合选择（推荐双向）；② a_lane 与 S_dyn/β_P 拆分；③ interposer 底面与 substrate 顶面网格对齐（或 Π 映射）；④ α_d 的 perimeter vs area-array 极限取哪个（取决于 SerDes 出片走 C4 还是 UCIe 并口）。
