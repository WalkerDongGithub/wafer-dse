### 5.2 完整问题形式（L1 精度，max $B$）

$$\boxed{
\begin{aligned}
\max_{B,\; \mathbf{D},\; \mathbf{f},\; \mathbf{L},\; \boldsymbol{\ell},\; \mathbf{P},\; \mathbf{N}^{\text{sig}},\; \mathbf{T}} \quad & B \\[8pt]
\text{s.t.} \quad
& \mathbf{D} \in \mathcal{D}, \quad
\sum_k f_{ij}^k = D_{ij}, \quad
L_e = \sum_{(i,j,k):\, e \in \text{path}} f_{ij}^k
&& \text{（流量模型：BvN + Valiant 分流）} \\[4pt]
& \max_{e} {L_e} \le 1
&& \text{（性能：广义无阻塞）} \\[8pt]
& \boldsymbol{\ell} = B \, \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}
&& \text{（归一化负载 → 物理 lane 数）} \\[8pt]
& \mathbf{P} = \mathbf{P}_0 + \mathbf{M} \cdot \mathbf{S}_{\text{dyn}} \cdot \boldsymbol{\ell}
&& \text{（功耗模型：静态 + 拓扑 × 标准 × lane 数）} \\[4pt]
& \mathbf{N}^{\text{pwr}} = \mathbf{S}_{\text{in}} \cdot \mathbf{P}
&& \text{（电源 bump 需求）} \\[4pt]
& \mathbf{N}^{\text{sig}} = \mathbf{M} \cdot \boldsymbol{\ell}
&& \text{（信号 bump 需求）} \\[4pt]
& \mathbf{N}^{\text{sig}} + \mathbf{N}^{\text{pwr}} \le \mathbf{N}^{\text{total}}
&& \text{（几何：bump 核心约束）} \\[8pt]
& \mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}
&& \text{（热网络：稳态热传导）} \\[4pt]
& \mathbf{T} \le T_{\max} \cdot \mathbf{1}
&& \text{（温度上限约束）} \\[4pt]
& \mathbf{W} \cdot \mathbf{T} \le \Delta T_{\max} \cdot \mathbf{1}
&& \text{（翘曲约束：相邻温差 $\le \Delta T_{\max}$）} \\[8pt]
& \mathbf{D} \ge 0,\; \mathbf{f} \ge 0,\; \mathbf{L} \ge 0,\; \boldsymbol{\ell} \ge 0,\; B \ge 0
\end{aligned}
}$$

其中 $\mathbf{P}_0$、$\mathbf{M}$、$\mathbf{S}_{\text{bw}}$、$\mathbf{S}_{\text{dyn}}$、$\mathbf{S}_{\text{in}}$、$\mathbf{G}$、$\mathbf{W}$、$\mathbf{N}^{\text{total}}$、$T_{\max}$、$\Delta T_{\max}$、$\mathbf{b}$ 均由外层技术选型决定，为常数。

以上为 L1 精度，包含全部三族约束的完整形式。L0 精度将性能替换为 $\sum_{e \in C} L_e \ge N/4$、几何替换为 $\sum_e \ell_e \le \sum_v N_v^{\text{total}}$、功耗替换为 $\mathbf{1}^T \mathbf{P} \le A \cdot q_{\max}$，详见 §5.1。

$\boldsymbol{\ell} = B \, \mathbf{S}_{\text{bw}}^{-1} \cdot \mathbf{L}$ 含 $B \cdot \mathbf{L}$ 双线性项。令 $\beta = 1/B$ 可将所有约束转化为 $(\beta, \mathbf{L}, \boldsymbol{\ell}, \mathbf{P}, \mathbf{N}^{\text{sig}}, \mathbf{T})$ 上的标准线性不等式（求解细节见 §7）。

### 5.3 解的判据
