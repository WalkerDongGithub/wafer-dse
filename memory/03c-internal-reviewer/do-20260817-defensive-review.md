# Do 报告 — 内部审查员（03c）防御性审查

日期：2026-08-17
对象：design_sensitivity.md、design_joint_model.md、MATH_MODEL_COMPLETE_V4.md、NONBLOCKING_CONDITIONS.md、paper_outline_v0.md

## 可攻击点清单

### 高危（H1–H3）

**H1｜定理 1「最差模式=置换矩阵」证明有数学错误**（已修复 2026-08-17）
- 位置：SYMMETRY_REDUCTION.md §2；被 NONBLOCKING_CONDITIONS.md §2 引用。
- 问题：假设 1 只约束行和=1（行随机多面体，顶点 nⁿ 个函数矩阵含 all-to-one），证明却引用 Birkhoff 多面体（需行+列和=1，顶点 n! 置换）。归约从 n! 崩到 nⁿ。
- 修复：补「每列和=1」双随机假设（每端口发1收1，物理正确）。

**H2｜B* 是上界还是下界未钉死；「保证」vs「潜能」矛盾**（语义已定，待全文统一）
- B* = 「最优路由 + 保守物理供给」下带宽。(a) 相对次优路由是上界（真实≤B*）；(b) 相对非保守物理是下界（真实≥B*）。筛选（淘汰 B*<目标）安全，落在保守侧。全文删「保证」，统一「无阻塞潜能/保守判定」。

**H3｜sensitivity 的 KKT 在非凸双线性上不严谨**（已修复 2026-08-17）
- 问题：max_B B s.t. B·(A_i·L)≤b_i 是双线性非凸，KKT 仅必要条件。
- 修复：B* 用二分求（不依赖非凸 max），λ 事后闭式 λ_j=1/(A_j·L*)，挂 Milgrom–Segal (2002) envelope theorem（不要求凸性）。已写入 design_sensitivity.md §2.1。

### 中危（M1–M8）

- **M1**：sensitivity 符号约定不统一（surplus vs 占用形式），§8 缺内层变量消去说明。修：统一 surplus 形式 g_i=b_i−B·A_i·L≥0，注明包络定理消去内层 B*/L* 对 θ 的一阶响应。
- **M2**：三套求解框架并存（NONBLOCKING 二分 vs sensitivity max-B vs CLOS 构造），主从关系未声明。修：声明主线=组内对称 LP + 组间 RNB/Clos，sensitivity 只作二分后的绑定闭式。
- **M3**：§2.8 接入后 N_total(B) 平方增破坏二分单调性。→ 已论证（α_d≤12/B 充分条件，物理范围成立）。
- **M4**：「B*_joint ≤ min(intra,inter)」无证明、无前提。修：补两前提（共享同标量 B + 联合约束=超集）+ 可行域单调性论证。
- **M5**：「T_bottom=T_substrate」理想接触，低估 die 温度（偏乐观）。修：参数化 T_bottom=T_substrate+R_if·Q_if，声明 R_if=0 为理想特例。
- **M6**：Dragonfly 是否 vertex-transitive 存疑；「轨道数远小于 231」无计算依据。**修：对称 LP 只用于组内 FullMesh（K_a 完全图，vertex-transitive ✓）；组间 Dragonfly 走 RNB/Clos 路径，不依赖对称假设。**（本条最关键，决定方法适用范围）
- **M7**：「假阴性不可接受」缺完备性背书。修：绑定 permutation traffic + 对称拓扑假设。
- **M8**：对标断言无引用（「要么…要么…要么」「只会做小 DSE」）。修：加「据我们所知」+ 逐条引用。

### 低危（L1–L5）

- L1「bump 一一对应」忽略布线 → 改为「资源归属层面一一对应，走线拥塞由 V4 §2.4 单独约束」。
- L2 退化时「由绑定演化序列回答」空承诺 → 给算法（a_i 降序）。
- L3 结果式断言 → 改将来时/示例语气。
- L4「必要且充分」强声明 → 依赖 H1 修复。
- L5「无可争议」过度自信 → 删。

## 完整性检查结论

- 难点→策略段：闭合良好。
- 策略→效果段：**4 个断点**（群论归约地基 H1、判读规则 H2、sensitivity 实现 H3、二分正确性 M3），现已全部修复。
- 效果段硬缺口：最小可行实验数据、Aut(H) 轨道数实算、对标复现、三层热阻标定（已对标）。

## 总体评估

论证骨架健康（双向保守夹逼、早筛定位、对称性=方法边界等自我设限式诚实是加分项）。H1 是最高优先（群论归约地基），已修复。补齐 H1/H2/H3/M3 + 一行最小实验数据后，论文具备外审竞争力。
