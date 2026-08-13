# Rent's Rule 与 I/O 密度文献整理

> 用途：支撑"bump 供给结构性过剩"与"die 内部复杂度是真正瓶颈"两条论断。
> 来源标注：[可靠] = 原始学术文献 / 行业规范；[中等] = 行业杂志/综述；[待确认] = 需下载原文核对页码与数字。

---

## 1. Rent's Rule —— pin 数随内部复杂度亚线性增长

**论断**：芯片的 I/O 需求 T 与内部逻辑量 g 满足 T = t·g^p，p < 1（典型 0.5~0.75）。内部复杂度增长快于 I/O 需求——die 越复杂，I/O 相对越富余。

| 文献 | 信息 | 状态 |
|------|------|------|
| **Landman & Russo 1971**（原始文献） | B. S. Landman and R. L. Russo, "On a Pin Versus Block Relationship For Partitions of Logic Graphs," *IEEE Transactions on Computers*, vol. C-20, no. 12, pp. 1469–1479, 1971. doi:10.1109/T-C.1971.223159 | [可靠] 需下载原文 |
| Lanzerotti, Fiorenza, Rand 2005 | Rent 的 IBM 内部备忘录首次公开（*IBM Journal of Research and Development*） | [可靠] 需确认卷号页码 |
| Stroobandt（Region III） | Rent's rule 在小规模分区的偏离（Region III） | [待确认] 搜索提及，需定位原文 |
| [Wikipedia: Rent's rule](https://en.wikipedia.org/wiki/Rent%27s_rule) | 综述索引：p 的范围、Region II 偏离、现代功能分区电路 P = 7·G^0.21 | [中等] 用作索引，引用时用原文 |

**为什么可信**：1971 年 IEEE Trans. Computers 的原始论文 + 半个世纪的验证。p < 1 的物理根源是 2D 平面电路的邻居局部性。

**与我们的关系**：交换机 die 的 crossbar 复杂度 ~O(N²)（内部逻辑），I/O 需求 ~O(N)（端口数）。Rent 直接支持"die 越大，bump/布线相对越富"——bump 结构性过剩的论据。

---

## 2. pad-limited → area-array：封装演进让 I/O 供给变成面积性

**论断**：传统 flip-chip 是 perimeter-limited（焊盘沿 die 边缘排列，I/O 受周长限制）；先进封装（fan-out / interposer / EMIB）把它变成 area-array（bump 铺满底面），I/O 供给随面积平方增长。

| 文献 | 信息 | 状态 |
|------|------|------|
| Patsnap 技术博客: [Wafer-level fan-out vs flip-chip BGA](https://www.patsnap.com/de/resources/blog/articles/wafer-level-fan-out-vs-flip-chip-bga-for-ai-chips-2/) | perimeter-limited 概念与 area-array 对比，"I/O 密度是 AI 加速器封装的决定性架构因素" | [中等] 商业博客，**需找更权威出处替换**（候选：ITRS 封装章节、IDTechEx Advanced Packaging 2025） |
| Chip Scale Review（行业杂志） | RDL pitch 翻译功能：die 级 μbump（10–40μm）→ RDL（2–5μm L/S）→ substrate 焊球（100–500μm） | [中等] 行业杂志 |

**为什么可信**：perimeter-limited / pad-limited 是封装工程的标准术语，行业共识级。但引用时建议配 ITRS 或 IDTechEx 的正式报告。

**与我们的关系**：修正过时说法——"lane 是周长资源"只对传统封装成立；我们的 wafer-scale 场景是 area-array，bump 和 RDL 都是面积资源。

---

## 3. Bump pitch 阶梯与面密度

**论断**：焊料类互连的 pitch 是 die I/O 密度的主要约束，密度 ∝ 1/pitch²。

| Pitch | 技术 | 密度（mm⁻²） | 来源 |
|-------|------|--------------|------|
| 100–150 μm | C4 焊球（FC-BGA） | ~59（130μm） | [中等] 与 UCIe 2.0 / 我们 tsmc_profiles.py 一致 |
| ~80 μm | 标准 Cu pillar | ~156 | [中等] |
| 55 μm | TSMC InFO | **314** | [待确认] 数字来自搜索摘要，原始出处待核对 |
| 45 μm | Intel EMIB | **492** | [待确认] 同上 |
| 30/60 μm（交错） | 精细 Cu pillar | — | [中等] |
| 10–40 μm | RDL/chiplet 接口 μbump | — | [中等] |
| ~20–25 μm | Cu–Cu hybrid bonding | **2518**（20μm） | [待确认] Gen-2 M-Series 数字，出处待核对 |

**为什么可信**：pitch 数字与 UCIe 2.0 规范（36–55μm）和我们的 bump.py 预设（UBUMP_45UM/25UM、C4_130UM）交叉一致；密度换算 1/pitch² 是几何事实。

**与我们的关系**：12×12mm die @ 45μm = ~49.4 万/mm² × 144mm² × 利用率 ≈ 6.4 万个 bump——数字落在 EMIB 与 InFO 之间，参数选择合理。

---

## 4. RDL 布线密度

**论断**：interposer RDL 的线密度比 bump pitch 细一个数量级——布线供给比 bump 供给更富，不是更缺。

| 技术 | L/S | 层数 | 来源 |
|------|-----|------|------|
| Cu damascene RDL | <2 μm（≈500 lines/mm/层） | 1–6 | [中等] Chip Scale Review / 行业综述 |
| 聚合物 RDL（BCB/PBO/PI） | ~5 μm | 1–4（FOWLP 2–5，最多 10+） | [中等] 同上 |

**为什么可信**：RDL 的 pitch 翻译角色是行业共识——它就是用来在细 bump 和粗焊球之间过渡的，密度必须显著高于两侧。

**与我们的关系**：⚠️ **修正实验参数**——exp 里 lanes_per_mm = 10/50/200 全是保守假设，真实 RDL 单层就有 ~500 lines/mm。用真实参数重跑布线约束实验（B* 预计回到热墙量级）。

---

## 5. 待办（引用前必须做）

1. 下载 Landman & Russo 1971 原文，核对公式与页码
2. InFO 314 / EMIB 492 / hybrid bonding 2518 三个密度数字的原始出处（搜索摘要不可引用）
3. pad-limited 论述找比 Patsnap 博客更权威的出处（ITRS / IDTechEx / 学术综述）
4. 确认 Lanzerotti 2005 的完整引文信息
5. 用真实 RDL 参数（~500 lines/mm/层）重跑 exp 布线实验，修正 B* 数字

## 6. BibTeX 草稿

```bibtex
@article{landman1971pin,
  author  = {Landman, B. S. and Russo, R. L.},
  title   = {On a Pin Versus Block Relationship for Partitions of Logic Graphs},
  journal = {IEEE Transactions on Computers},
  volume  = {C-20},
  number  = {12},
  pages   = {1469--1479},
  year    = {1971},
  doi     = {10.1109/T-C.1971.223159}
}
```
