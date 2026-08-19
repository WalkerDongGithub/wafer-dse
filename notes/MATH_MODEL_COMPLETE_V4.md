# v4 符号表（V5 前置）

> **v4（2026-08-13，符号表版）**：本文件现仅承担**符号表**职能——为 V5
> （`MATH_MODEL_V5_JOINT_SENSITIVITY.md`）提供 §0 基础符号定义。
> 约束模型本体见 V5；V5 §1 增补符号表在本表之外新增。
> 缺什么符号就补什么，本表随 V5 演进。

---

## 0. 符号表

| 符号 | 含义 |
|------|------|
| $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ | 逻辑拓扑图（端口为节点，链路为有向边） |
| $\mathcal{E}_{\text{on-die}}$ | die 内链路（零物理代价） |
| $\mathcal{E}_{\text{UCIe}}$ | UCIe 链路（die 间，距离 ≤ UCIe 可达范围） |
| $\mathcal{E}_{\text{SerDes}}$ | SerDes 链路（组间，经 C4 出 interposer） |
| $B$ | 端口带宽（二分搜索确定 $B^*$） |
| $\mathbf{L}$ | 链路负载向量（包络，共享变量；V5 细分为 $\mathbf{L}_{\text{D2D}}, \mathbf{L}_{\text{I2I}}$） |
| $\boldsymbol{\ell}$ | 物理 lane 数：$\boldsymbol{\ell} = B \cdot \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ |
| $\mathbf{S}_{\text{bw}}$ | 每 lane 带宽对角阵（on-die 取 $\infty$） |
| $\mathbf{S}_{\text{dyn}}$ | 每 lane 动态功耗对角阵（on-die 取 0） |
| $\mathbf{M}$ | **die-链路 incidence**：$M_{v,e}=1 \iff$ 链路 $e$ 的源或宿是 die $v$（有向链路两端 die 各记一次；on-die 两端同 die 只记一次） |
| $V_{dd}, I_{bump}$ | 供电电压；单 bump 载流能力 |
| $p, \eta$ | bump pitch；阵列面积利用率 |
| $\mathbf{N}^{\text{total}}(B)$ | μbump 总数：$N_v^{\text{total}} = \eta \cdot A_{die}(B)/p^2$ |
| $\mathbf{S}_{\text{in}}$ | 功率-bump 换算对角阵：$[\mathbf{S}_{\text{in}}]_{vv} = V_{dd} \cdot I_{bump}$ |
| $P_{peak}(B)$ | die 峰值功耗：$P_{peak}(B) = P_0 + \beta_P \cdot B$ |
| $\mathbf{P}$ | die 功耗向量：$\mathbf{P} = \mathbf{P}_{peak}(B) + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}$ |
| $\mathbf{G}, \mathbf{b}$ | 热导矩阵（对角占优 M-矩阵，$\mathbf{G}^{-1}\ge 0$）；环境温度贡献向量 |
| $\mathbf{T}, T_{\max}$ | die 温度：$\mathbf{G}\cdot\mathbf{T} = \mathbf{P} + \mathbf{b}$；结温上限 |
| $\mathbf{x}$ | 布线分配变量（链路 × 候选路径） |
| $\mathbf{A}, \mathbf{R}$ | 布线 incidence：$\mathbf{A}\mathbf{x} = \boldsymbol{\ell}$（需求）；$\mathbf{R}\mathbf{x} \le \mathbf{C}$（容量） |
| $N_{C4}^{\text{SerDes}}$ | C4 信号焊球中分配给 SerDes 的份额 |
