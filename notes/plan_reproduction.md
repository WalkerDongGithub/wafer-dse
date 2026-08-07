# 对标复现计划

## 重要前提

`vendor/congestion` 子模块未 checkout（空目录）—— Dragonfly 仿真复现依赖它（或 BookSim2）。
Feng & Ma 的 venue 在 ref.bib/LITERATURE_SURVEY 中写 SC 2024，DOWNLOAD_LIST 写 ATC 2024——届时核实。

---

## A. 对标文章与复现目标

### A1. Kim et al. — Dragonfly Topology (ISCA 2008) ⭐

**内容**：定义 Dragonfly (a,p,h,g)，平衡条件 a=2p, h=p。minimal 路由 uniform 流量 ~95% 吞吐，Valiant ~50%，对抗 bit-complement 流量 minimal 坍缩到 ~1.38% 而 Valiant 保持 ~50%。

**与我们的关系**：我们用的主要拓扑。我们的 worst-case LP 说平衡 Dragonfly 下 t*=1（Valiant）；论文仿真说是 ~50% 平均吞吐。比较的要点：我们给出的是确定性上界，他们是平均仿真结果。

**复现指标**：(a) ~95%/~50%/~1.38% 吞吐三元组（BookSim2 或 vendor/congestion）；(b) 平衡条件 a=2p, h=p ↔ 我们 LP t*=1。

**可行性**：高（BookSim2 开源，子模块需 checkout）。

### A2. FPIA — Jiao et al. (TCAS-I 2024) ⭐ PDF 在手

**内容**：Tile-based field-programmable 互联 fabric（TOB/COB/平行 track），自动 chiplet placement（QP + SA）+ maze routing。94.5% 峰值利用率保证可布线性，2.2 ns 延迟，1.18 pJ/bit，256 GB/s 最大带宽，IO block 达 256 端口（11.8× prior art）。

**与我们的关系**：我们 L2 grid-capacity 约束 `A·ℓ ≤ c` 的来源。他们的 fabric 参数是我们的路由容量层天然物理常数。

**复现指标**：(a) 从 fabric 算术重算 94.5% 利用率和 256 GB/s；(b) 用他们的参数化我们的 L2 约束，比较 9 个 scenario 的可布线性判定。

**可行性**：高（资源算术复现，无需他们的 router）。

### A3. Chen, Pal, Kumar — Waferscale Network Switches (ISCA 2024)

**内容**：自上而下的 radix 缩放分析。仅面积约束下 ~32× 传统芯片交换机 radix；实际天花板是内部带宽、外部 IO 和功率密度。

**与我们的关系**：最接近的架构比较。他们问"晶圆级交换机最大能做多大"，我们问"这个配置可行吗、什么绑定了"。

**复现指标**：(a) 面积约束下 32× radix；(b) 我们的 B_max_geom 和 B_max_thermal 在他们平台参数上的曲线交叉点。

**可行性**：中等（需论文参数表）。

### A4. MFIT — Zhang et al. (ACM TACO 2025) ⭐ 源在 repo

**内容**：多精度 2.5D/3D chiplet 热 RC/DSS 模型，vs ANSYS Fluent FEM 验证（~5% 误差）。`MFIT/` 下有完整代码和 3 个示例配置。

**复现指标**：(a) 跑通 3 个示例，确认与论文结果一致；(b) 在相同 4-chiplet 2.5D 几何上比较我们的 lumped G-matrix 稳态温度 vs MFIT RC——量化 lumping error。

**可行性**：高（全部本地代码，需 SuperLU 动态库）。

### A5. Ngo et al. — Nonblocking via LP Duality (INFOCOM 2010)

**内容**：统一 Clos/Banyan/multirate 无阻塞分析。Primal LP 最大化 blocked middle module；dual LP 给出普适上界。

**与我们的关系**：LP 作为分析器的直接方法论先驱。完美的"sanity check"目标。

**复现指标**：从他们的 dual LP 恢复 Clos SNB (m≥2n−1)、Benes WSNB (m≥⌊3n/2⌋)、Slepian-Duguid RNB (m≥n)。

**可行性**：高（纯数学，无外部依赖，arXiv 有）。

### A6. 其他对标（Tier 2-3）

| 文章 | 点 | 可行性 |
|------|-----|--------|
| Feng & Ma, SC 2024 — Switch-Less Dragonfly | 评价其 (a,p,h) + 无交换机前提在我们的框架中是否可行 | 中低（需仿真器，但参数检查可行） |
| Wan et al., TVLSI 2024 — BFT on Mesh | 392 dies / 896 ports 在我们的几何+热约束下的物理可行性 | 中低 |
| Yang et al., ISCA 2025 — TickTock | 采纳其 50mm D2D 上限约束 | 低（核心指标不具可比性） |
| RapidChiplet, CF 2025 | 同样分析代理工具的精度-速度对比 | 中高（开源） |
| Tesla Dojo / Cerebras WSE-2 | 参数校准——把公开参数过我们的 Power/Bump 模型 | 中高 |
| UCIe 2.0 / OIF-CEI-5.1 | 参数审计——hardcoded 数字必须可追溯到 spec 行 | 高 |

---

## B. 优先级

**Tier 1 — 验证数学核心（不依赖外部、必须通过）：**
1. 无阻塞理论验证套件（Ngo dual LP + 经典条件枚举）
2. Dragonfly 仿真复现（~95%/~50%/~1.38% 三元组）
3. MFIT 热交叉验证（lumped G-matrix vs MFIT RC vs FEM）

**Tier 2 — 主要对比：**
4. FPIA 参数复现 + L2 约束参数化
5. Chen et al. 32× radix 交叉检查
6. 工业平台校准（Dojo, WSE-2）

**Tier 3 — 更深入/更长周期：**
7. Feng & Ma + RapidChiplet + TickTock + Wan et al.

---

## C. 推荐目录结构

```
repro/
├── README.md
├── common/published.py          # 所有手抄的论文常数（唯一来源）
├── common/tables.py             # CSV + LaTeX 表格生成
├── theory/                      # Tier 1: 无阻塞理论
│   ├── clos_conditions.py
│   └── ngo_dual.py
├── dragonfly/                   # Tier 1: Dragonfly 仿真
│   ├── run_sweep.py
│   └── balance_condition.py
├── thermal/                     # Tier 1: MFIT 交叉验证
│   ├── run_mfit_examples.py
│   ├── build_lumped.py
│   └── compare.py
├── fpia/                        # Tier 2
│   ├── fabric_params.py
│   ├── routability_ceiling.py
│   └── l2_compare.py
├── chen2024/                    # Tier 2
│   └── radix_curve.py
├── industry/                    # Tier 2
│   ├── dojo_cal.py
│   └── wse2_cal.py
├── data/published/  data/results/  data/figures/
└── reports/
    ├── validation_matrix.md
    └── gaps.md
```

---

## E. 写代码前需要精读的论文

1. **Kim et al., ISCA 2008 (Dragonfly)** — 仿真配置、平衡条件、被比较的具体图。最高杠杆的深度阅读。
2. **Ngo et al., INFOCOM 2010 / arXiv:1204.3180** — LP 对偶的方法论先驱，必须逐行理解。
3. **FPIA (Jiao et al. 2024)** — §IV（fabric 架构）和 §V（实验，Fig. 11 利用率图）需在转录参数前精确读。
4. **MFIT (Zhang et al. 2025)** — 需要论文以了解示例应该复现什么结果，验证协议需对齐。
5. **Chen et al., ISCA 2024** — 参数表和 32× 推导。
6. **Berman & Plemmons** — M-矩阵章节（G⁻¹≥0），如需超越经验的正式化。
