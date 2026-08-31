# FigureArtist 工作汇报（2026-08-21）

## ① 为什么做

论文要讲"晶圆级交换机两层 DSE + 多因素耦合"的故事，需要图把框架和物理图像讲清楚——尤其作者点名的"散热路径要看得见"（散热板是显式环节、完整链可见）；图出不好，审稿人看不懂，论证就白写了。

## ② 做了什么

- **论文概念图两张**（`docs/paper/Img/`）：
  - 图 1 两层 DSE 框架：外层离散枚举（复用 chiplet DSE）+ 物理参数接口 + 内层可行性模型 → 输出额定带宽 B\*；聚焦"一个 interposer 的设计"。
  - 图 2 三层实体 + 完整散热链：die→μbump→interposer→C4→substrate→ambient（interposer/substrate 是显式节点，不是一根线）+ heatsink 支路（die→TIM→散热板→对流）+ C1-C4 跨层耦合 + 3D 展开形态（每层 die + TSV）。
- **传热网络图 8 张**（`vision/examples/`）：把 config/thermal 的 YAML 配置画成图——2.5D 两 die、heatsink 显式版、3D 集总/展开、2.5D 完整链、3D 完整链、晶圆级（大网格 die + 背面整体冷却）。全部横平竖直、无衬线字体、每个支路标注物理类型（传导/对流）+ 热阻值来源（来自配置 YAML，不编造）。
- **遮盖检测工具**（`vision/overlap_checker/`）：用 PyMuPDF 从编译好的 PDF 里提取每个文字/方框/线段的真实位置，两两检查是否重叠（shapely 计算）。一条命令：`python3 -m vision.overlap_checker.cli xxx.pdf`。

## ③ 达到什么效果

- **交付物**：图 1/2 PDF（`docs/paper/Img/fig01_two_level_dse.pdf`、`fig02_three_layer_coupling_v3.pdf`）；传热图 8 张 PDF（`vision/examples/*.pdf`）；检测工具（含测试）。
- **质量数据**：全部图"零遮盖"——声明式检查 8 图 0 碰撞；工具实测三张 PDF 真重叠 = 0（仅标签在框内、折线拐点相接这类正常构造，报告里已分类）。测试 14 个用例 + 合成 PDF 全绿。
- **对论文的意义**：图 1/2 支撑"两层 DSE + 单 interposer 聚焦 + 耦合"的论证主线；传热图让"散热路径"（作者要求的 heatsink 显式环节、完整链）肉眼可见；检测工具保证后续任何图都能一条命令验收，不再靠猜。
