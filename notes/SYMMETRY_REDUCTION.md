# 对称图最差流量下界的群论归约

## 1. 问题定义

设物理拓扑为无向图 $H = (V, E)$，$|V| = n$。每个节点可向所有其他节点通信，边容量无限。负载均衡策略 $L$ 给定：对任意端到端流量需求矩阵 $T = (t_{ij})_{n \times n}$，$L$ 决定每条边的负载分布，所得**网络流图**记为 $G(T) = L(H, T)$。对 $G(T)$ 取最大边负载，得该策略下的瓶颈负载。

**假设 1（单位总发出量）** 每个节点恰好发出总计 1 单位流量，即 $\sum_j t_{ij} = 1$，$\forall i$。

**假设 2（最差流量模式）** 我们不知 $T$，需求得在最差的 $T$ 下瓶颈负载的上界。即求

$$
\Phi(T) := \max_{e \in E} \; \ell_e(G(T)), \qquad T^* = \arg\max_{T \in \mathcal{T}} \Phi(T)
$$

其中 $\mathcal{T} = \{T \in [0,1]^{n \times n} : \sum_j t_{ij} = 1,\; \forall i\}$。

若负载均衡为**最优**（adaptive / 最优多商品流），则 $\Phi(T)$ 本身是一个凸优化（并发流）的最优值，而外层的 $\max_T \Phi(T)$ 是**凸函数最大化问题**。一般情况下凸函数最大化无多项式保证。

---

## 2. 定理一：最差模式为置换

**定理 1** 设 $H$ 顶点传递（vertex-transitive）且 $L$ 在 $\text{Aut}(H)$ 作用下不变，则存在最差流量模式 $T^*$ 使得每行恰有一个元素非零（即 $T^*$ 为置换矩阵）。

*证明思路*：$\Phi: \mathcal{T} \to \mathbb{R}^+$ 为凸函数。$\mathcal{T}$ 为 Birkhoff 多面体，其顶点恰为置换矩阵。凸函数在有界多面体上的最大值必在某个顶点处取到。由顶点传递性和 $L$ 的对称性可证 $\Phi$ 的定义域限制到 $\mathcal{T}$ 上后确为凸。$\square$

**推论** 只需考虑 $\sigma \in S_n$ 对应的流量模式：

$$
t_{ij}^{(\sigma)} = \begin{cases} 1 & j = \sigma(i) \\ 0 & \text{otherwise} \end{cases}
$$

至此搜索空间从 $n^2$ 维连续多面体降为 $n!$ 个离散点。

---

## 3. 定理二：Aut(H)-共轭归约

设负载均衡策略 $L$ 是 $\text{Aut}(H)$-不变的，即：

$$
\forall \phi \in \text{Aut}(H), \quad L(H,\; \phi \circ T \circ \phi^{-1}) = \phi \cdot L(H, T)
\tag{A1}
$$

其中 $(\phi \circ T \circ \phi^{-1})_{ij} = T_{\phi^{-1}(i),\;\phi^{-1}(j)}$。

**引理 1（节点重标号 = 置换共轭）** 对 $\sigma \in S_n$ 和 $\phi \in \text{Aut}(H)$，按 $\phi$ 对节点重标号后，置换 $\sigma$ 变为 $\phi \sigma \phi^{-1}$。

*证明*：原流量 $i \to \sigma(i)$，重标号为 $\phi(i) \to \phi(\sigma(i))$。对新标号 $j = \phi(i)$，有 $j \mapsto \phi(\sigma(\phi^{-1}(j))) = (\phi \sigma \phi^{-1})(j)$。$\square$

**引理 2（流图同构 = 置换共轭）** 在 (A1) 下，若 $\sigma \mapsto G_\sigma$ 为单射，则：

$$
\exists \phi \in \text{Aut}(H),\; \phi(G_{\sigma_1}) = G_{\sigma_2} \iff \sigma_2 = \phi \sigma_1 \phi^{-1}
$$

*证明*：由 (A1), $\phi(G_{\sigma_1}) = L(H, \phi \sigma_1 \phi^{-1}) = G_{\phi \sigma_1 \phi^{-1}}$。由单射性即得。$\square$

**定理 2** 在引理 2 条件下，等价类为 $\text{Aut}(H)$ 在 $S_n$ 上的共轭轨道：

$$
\sigma_1 \sim \sigma_2 \iff \exists \phi \in \text{Aut}(H),\; \sigma_2 = \phi \sigma_1 \phi^{-1}
$$

**注**：共轭不是额外假设——它是"在对称图上做节点重标号"这一操作的代数表达。$L$ 的单射性若放宽（如策略忽略流向），等价仅会变粗，共轭结构不变。

---

## 4. 轨道计数

**命题 1（轨道大小）** 对 $\sigma \in S_n$，其在 $\text{Aut}(H)$ 共轭下的轨道大小为：

$$
|\text{orb}(\sigma)| = \frac{|\text{Aut}(H)|}{|\text{Aut}(H) \cap C_{S_n}(\sigma)|}
$$

其中 $C_{S_n}(\sigma) = \{\tau \in S_n : \tau\sigma = \sigma\tau\}$ 为 $\sigma$ 在 $S_n$ 中的中心化子。

**命题 2（共轭类内轨道数）** 对 cycle type $\lambda \vdash n$，该 $S_n$ 共轭类内的 $G$-轨道数（$G = \text{Aut}(H)$）为：

$$
N_\lambda(G) = \frac{n!}{|G|} \cdot \frac{|G \cap C_{S_n}(\sigma_\lambda)|}{|C_{S_n}(\sigma_\lambda)|}
$$

其中 $\sigma_\lambda$ 为 cycle type $\lambda$ 的任一代表元。

**命题 3（总轨道数，Burnside 引理）**

$$
\text{总轨道数} = \frac{1}{|G|} \sum_{g \in G} |C_{S_n}(g)|
$$

其中对 $g$ 的 cycle type $1^{m_1}2^{m_2}\cdots n^{m_n}$：

$$
|C_{S_n}(g)| = \prod_{k=1}^n k^{m_k} \cdot m_k!
$$

---

## 5. 常见拓扑的自同构群

| 物理拓扑 $H$ | $\text{Aut}(H)$ | 阶 | 备注 |
|---|---|---|---|
| $K_n$（完全图） | $S_n$ | $n!$ | 轨道 = $S_n$ 共轭类 = $n$ 的分拆，$p(10)=42$ |
| $C_n$（环） | $D_n$ | $2n$ | 二面体群 |
| $\text{Mesh}(k)$（$k \times k$ 网格） | $D_4$ | 8 | 矩形二面体 |
| $\text{Torus}(k)$（$k \times k$ 环面） | $(C_k \times C_k) \rtimes C_2$ | $2k^2$（一般）或 $8k^2$（$D_k \times D_k$ 情形） | 取决于维度对称性 |
| $\text{Dragonfly}(a,p,h)$ | 取决于布线 | — | 正则布线时接近 $S_a \wr S_p$ 类型 |
| $Q_d$（超立方，$n=2^d$） | 超正八面体群 | $d! \cdot 2^d$ | 轨道接近 $S_n$ 共轭类 |
| $K_{m,m}$（完全二分图） | $S_m \times S_m \rtimes C_2$ | $2(m!)^2$ | |

$n \leq 10$ 时，对称图的 $\text{Aut}(H)$ 族有限，均可手工给出。不规则的 $H$ 可用 nauty 在毫秒内求解。

---

## 6. 算法

**输入**：物理拓扑 $H$（$|V| = n$）、负载均衡策略 $L$、$\text{Aut}(H)$（已知或由 nauty 给出）

**输出**：最差瓶颈负载 $\Phi_{\max}$ 及对应流量模式 $\sigma^*$

```
G = Aut(H)
representatives = []

若 G = S_n:
    representatives = {S_n 共轭类代表元（p(n) 个）}
否则：
    生成 S_n 共轭类代表元集合 C
    for each σ in C:
        for each φ in G:
            τ = φ σ φ^(-1)
            visited.add(τ)          # 标记 σ 的 G-轨道中所有元
        for each τ in G·σ:          # 轨道内未取代表元的
            representatives.append(τ)
            break                    # 每个轨道一个代表元

for each σ in representatives:
    G_σ = L(H, σ)                   # 多项式计算流图
    Φ(G_σ) = max_{e∈E} load(e)     # 瓶颈负载
    记录 max

return Φ_max, σ*
```

**复杂度**：$O(p(n) \cdot |G| \cdot n \log n)$（轨道生成）+ $O(|\text{representatives}| \cdot \text{poly}(n))$（流图计算）

---

## 7. 可行性

对 $n \leq 10$，$p(n) \leq 42$。非 $S_n$ 的对称群阶均不超过 $2 \cdot (5!)^2 = 28800$（$K_{5,5}$），或约 $d! \cdot 2^d$（$Q_d$，$d \leq 3$ 时 $n \leq 8$）。

$n$ 到 12–15 时，$p(n)$ 仍可控（$p(12)=77$, $p(15)=176$），但若 $\text{Aut}(H)$ 退化为 $\{e\}$，轨道数退化为 $15! \approx 1.3 \times 10^{12}$——此时需要更强的归约或启发式。对于实际物理拓扑（Mesh/Torus/Dragonfly），$\text{Aut}(H)$ 非平凡，轨道数远小于 $n!$。
