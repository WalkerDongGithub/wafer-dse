# $N$ 线耦合的数学结构 — $\mathbf{LC}$ 矩阵的特征谱

---

## 1. $N$ 根对称线的 $\mathbf{LC}$ 矩阵

$N$ 根完全相同的传输线。每线自感 $L_0$，自容 $C_0$。任意两根线之间有互感和互容。

最简单、最常用的模型：**间距相等、耦合随距离衰减**。此时 $\mathbf{L}$ 和 $\mathbf{C}$ 是 **Toeplitz 矩阵**（每条对角线上的元素相等）：

$$\mathbf{L} = \begin{bmatrix}
L_0 & L_1 & L_2 & \cdots & L_{N-1} \\
L_1 & L_0 & L_1 & \cdots & L_{N-2} \\
L_2 & L_1 & L_0 & \cdots & L_{N-3} \\
\vdots & \vdots & \vdots & \ddots & \vdots \\
L_{N-1} & L_{N-2} & L_{N-3} & \cdots & L_0
\end{bmatrix}$$

$L_k$ = 间距为 $k$ 步的互电感（$k=0$ → 自感，$k=1$ → 相邻，$k=2$ → 隔一条线）。

$\mathbf{C}$ 结构相同（符号约定：互电容项带负号）。

$$\mathbf{LC} \text{ 是 Toeplitz 矩阵的乘积——不一定是 Toeplitz，但保留了大量对称性。}$$

---

## 2. 极限情况：只有相邻耦合

$L_k = 0$ 对所有 $k \geq 2$。$\mathbf{L}$ 退化为三对角 Toeplitz：

$$\mathbf{L} = \begin{bmatrix}
L_0 & L_1 & 0 & \cdots & 0 \\
L_1 & L_0 & L_1 & \cdots & 0 \\
0 & L_1 & L_0 & \cdots & 0 \\
\vdots & \vdots & \vdots & \ddots & L_1 \\
0 & 0 & 0 & L_1 & L_0
\end{bmatrix}$$

$\mathbf{C}$ 同样结构。$\mathbf{LC}$ 变为**五对角**（两个三对角的乘积）。

**这类矩阵的特征值和特征向量是已知的。**

---

## 3. 特征向量：离散正弦模式

对于只有相邻耦合的对称三对角或五对角 Toeplitz 矩阵，特征向量是**离散正弦函数**：

$$\mathbf{v}_k = \begin{bmatrix}
\sin\!\left(\frac{k\pi}{N+1}\right) \\
\sin\!\left(\frac{2k\pi}{N+1}\right) \\
\sin\!\left(\frac{3k\pi}{N+1}\right) \\
\vdots \\
\sin\!\left(\frac{Nk\pi}{N+1}\right)
\end{bmatrix}, \quad k = 1, 2, \ldots, N$$

**$k=1$：基模 — 所有线同相（偶模在 $N$ 维的推广）。**

**$k=N$：最高阶模 — 相邻线反相（奇模在 $N$ 维的推广）。**

特征值近似（弱耦合展开）：

$$\lambda_k \approx L_0 C_0 \cdot \left[1 - 2\left(\frac{L_1}{L_0} - \frac{C_1}{C_0}\right) \cdot \cos\!\left(\frac{k\pi}{N+1}\right)\right]$$

---

## 4. 特征值 → $N$ 个传播速度

传播常数：

$$\gamma_k = j\omega\sqrt{\lambda_k}, \quad \beta_k = \omega\sqrt{\lambda_k}, \quad v_k = \frac{1}{\sqrt{\lambda_k}}$$

**$N$ 个特征值 → $N$ 个模 → $N$ 个不同的传播速度。**

最高阶模（$k = N$，相邻线反相）对应的 $\lambda_N$ 最小 → $v_N$ 最大（如果 $L_1/L_0 < C_1/C_0$）。

---

## 5. 任意激励 → 模分解

线 $m$ 在 $x = 0$ 被驱动，其他线安静。把物理激励分解到特征模上：

$$\mathbf{V}(0) = [0,\ldots,0,V_S,0,\ldots,0]^T = \sum_{k=1}^{N} c_k \mathbf{v}_k$$

系数 $c_k = \mathbf{v}_k \cdot \mathbf{V}(0) / \|\mathbf{v}_k\|^2 = V_S \cdot \sin(mk\pi/(N+1))$。

每个模以各自速度 $v_k$ 独立传播。在 $x = d$ 处：

$$V_{\ell}(d,t) = \sum_{k=1}^{N} c_k \cdot v_{k,\ell} \cdot s\!\left(t - \frac{d}{v_k}\right)$$

其中 $v_{k,\ell}$ 是第 $k$ 个特征向量的第 $\ell$ 个分量。

**$N$ 个到达时间 $\tau_k = d/v_k$ → 信号在接收端展宽为 $N$ 个时间上错开的副本。这是串扰在 $N$ 根线中的一般形式。**

---

## 6. 串扰消除的条件

让串扰在所有远端线消失：所有 $V_{\ell}(d,t) = 0$ 对 $\ell \neq$ 驱动线。

充要条件：**所有模的速度相等。** $v_1 = v_2 = \cdots = v_N$。

$\Longleftrightarrow$ 所有特征值相等 $\Longleftrightarrow$ $\mathbf{LC} = \lambda \mathbf{I}$（$\mathbf{LC}$ 是单位矩阵的标量倍数）。

$\Longleftrightarrow$ $\mathbf{LC}$ 的非对角元全部为零。$\Longleftrightarrow$ **没有耦合。**

对于 Toeplitz 耦合矩阵，这要求 $L_k = 0$ 且 $C_k = 0$ 对所有 $k \geq 1$——即没有互感和互容。在非均匀介质中，即使 $L_k \neq 0$、$C_k \neq 0$，只要 $L_k/L_0 = C_k/C_0$ 对所有 $k$ 成立（$N$ 维的"均匀介质条件"），所有特征值相等——所有模同速——所有远端串扰同时消失。这是两根线条件的直接推广。

---

## 7. 总结

| $N=2$ | 一般 $N$ |
|-------|---------|
| 特征向量：$[1,1]$、$[1,-1]$ | 离散正弦模式 $\sin(k m \pi/(N+1))$ |
| 两个模、两个速度 | $N$ 个模、$N$ 个速度 |
| FEXT = 一个到达时间差 | FEXT = $N$ 个时间错开的副本 |
| $L_1/L_0 = C_1/C_0$ → 串扰消失 | $L_k/L_0 = C_k/C_0$ 对所有 $k$ → 串扰消失 |

**$2 \times 2$ 是特例，$N \times N$ 的结构完全由 Toeplitz 矩阵的特征谱决定。特征向量从两个变成一族离散正弦模式，串扰从"两个波的到达时间差"变成"$N$ 个波的时间离散"。**
