# CodeEngineer 开工前咨询记录（2026-08-20，G2 双旋钮 + v5.21 布线/面积）

> 本文件是 CodeEngineer 会话的 consult-team 记录与交付备忘（会话重建可依此续跑）。

## 一、咨询摘要（全部收齐验收）

| 成员 | qid | 问题 | 结论 |
|---|---|---|---|
| DomainExpert | q-12856a16 | G2 双旋钮模型语义 | R_peak=单对包络（原次随机定案后作废）；C_rated=β_P:=0；4 档正交；V5 由 DomainExpert 改 v5.22 |
| EvalDesigner | q-83fdd68d | E2 场景命名/判据/输出 | 4 档字符串定稿；拓扑子集 7 个；M1/M2/M3 判据；E4 共用 C_rated；knob_matrix 列归 EvalDesigner |
| DataSteward | q-81b7de6e | exp 分工/缓存口径 | src 层归我、exp 归 DataSteward；回归锚点 B*=11211；跑前清 .cache；ucie 谱系即可 |
| master | q-1fa22b41 | 任务边界 | ①布线/面积接入（先行，V5 v5.21）②G2 双旋钮（次之）；C4/sub 热不接入；只动 src/ 层 |
| DomainExpert | q-85e8c02c | R_peak 重裁决 | 次随机≡双随机（我独立发现，Hall 补全论证）；最终定案=单对包络 L_e*=max c_ij^e（V5 §7.3b） |

## 二、交付清单（git 已提交）

1. **459a6ed feat: 布线 (2d) 与 die 面积上界 (2f) 接入 build_scenario（V5 v5.21）**
   - `src/problem/builder/_scenario.py`：token 解析（perf+bump+therm+wiring / +area / +wiring+area）
   - `src/problem/models/phys/area/_die_area.py`（新 DieAreaModel，V5 §2(2f)）
   - `src/diagnostics.py` 加 area 家族；`src/main.py` 场景白名单
   - 测试：`tests/routing/test16_wiring_scenario.md`、`tests/die_scaling/test17_die_area.md`
2. **5008ed0 feat: 双旋钮场景参数化（V5 v5.22 要求 R × 约束 C 四档）**
   - `_oblivious.py`：ObliviousValiantModel requirement 参数（qos/peak）
   - `_scenario.py`：egress_peak → R_peak；rated → β_P:=0
   - 测试：`tests/perf/test18_dual_knobs.md`
   - run_all 19/19 全绿

## 三、关键事实（给 DataSteward/EvalDesigner 的判据预期）

- 回归锚点 Mesh(2)/ucie-32g/perf+bump+therm B*=11211 数值不变（实测）
- 默认 β_P=0：C 旋钮（rated）与 C_peak 无差异（EvalDesigner 已警示）→ E2 C 旋钮需 β_P>0 档
- R 旋钮默认有区分度：Mesh(2)/ucie-32g B* 11211 → 33627（perf+egress_peak+bump+therm）
- 默认参数 wiring/area 不绑定（B*=11211 不变）；E3B v2 C3'/C4' 可能需 α_d>0 档位触发面积绑定
  （perf+area 在 α_d=0.001 时闭式上界 28000 已验证精确生效）
- 次随机包络 ≡ 双随机包络（数学事实 + 10 拓扑数值），已作废；最终 R_peak=单对包络

## 四、边界与纪律

- 我（CodeEngineer）只动 src/ 层（build_scenario + models + tests）；V5 归 DomainExpert；
  exp 编排归 DataSteward；实验设计文档归 EvalDesigner
- 测试先行：先写 .md 测试 → 确认 → 再写实现；run_all.py 全绿才提交
- 大实验走 ssh walker 远机（DataSteward 执行侧）
