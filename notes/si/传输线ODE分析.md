# $V'' = \gamma^2 V$ — 传输线 ODE 的完整分析

---

## 1. ODE 的来源

电报方程在频域解耦后得到：

$$\frac{d^2 V}{dx^2} = \gamma^2 V$$

其中：

$$\gamma^2 = (R + j\omega L)(G + j\omega C) \in \mathbb{C}$$

这是标准的二阶线性齐次常微分方程。形式如 $y'' = Ay$，含零一阶导数项。

---

## 2. 为什么没有 $y'$ 项？

一般二阶线性 ODE 为 $y'' + p(x)y' + q(x)y = 0$。此处 $p(x) \equiv 0$。

**$y'$ 项代表系统中的耗散或增益不对称性。** $y' = 0$ 意味着正向波与反向波完全对称——同一传输线，从哪端注入信号的传播规律相同。物理上这要求 $R, L, C, G$ 沿 $x$ 均匀分布且各向同性，UCIe 封装走线满足此条件。

---

## 3. 标量情况：$A = \gamma^2 \in \mathbb{C}$

### 3.1 特征方程与通解

特征方程：

$$\lambda^2 = \gamma^2 \quad \Rightarrow \quad \lambda = \pm \gamma$$

通解（$\gamma \neq 0$ 时）：

$$V(x) = C_1 e^{\gamma x} + C_2 e^{-\gamma x}$$

$C_1, C_2 \in \mathbb{C}$ 由边界条件确定。

若 $\gamma = 0$（退化情况，$R = G = 0$ 且 $\omega = 0$，即直流无损），则 $\lambda^2 = 0$，二重根 $\lambda = 0$，通解 $V(x) = C_1 + C_2 x$。无物理意义，不讨论。

---

### 3.2 三类定性行为 — 看 $\gamma^2$ 落在复平面何处

设 $A = \gamma^2$。

#### 情况 I：$A > 0$（纯实数正）

$$\gamma = \sqrt{A} \in \mathbb{R}^+$$

$$V(x) = C_1 e^{\sqrt{A}x} + C_2 e^{-\sqrt{A}x}$$

纯指数增长/衰减。无振荡。

物理场景：极低频下 $R \gg \omega L$，$\gamma^2 \approx RG$（两实数乘积为正）。

---

#### 情况 II：$A < 0$（纯实数负）

$$\gamma = j\sqrt{|A|} \in \text{纯虚数}$$

$$V(x) = C_1 e^{j\beta x} + C_2 e^{-j\beta x}, \quad \beta = \sqrt{|A|}$$

或用实三角函数：

$$V(x) = D_1 \cos(\beta x) + D_2 \sin(\beta x)$$

纯正弦振荡，无衰减。

物理场景：无损传输线 $R = G = 0$：

$$A = -\omega^2 LC < 0 \quad \Rightarrow \quad \beta = \omega\sqrt{LC}$$

---

#### 情况 III：$A \in \mathbb{C}$（复数，虚部为主）

$$\gamma = \sqrt{A} = \alpha + j\beta \quad (\alpha, \beta \in \mathbb{R}^+)$$

$$V(x) = C_1 e^{\alpha x} e^{j\beta x} + C_2 e^{-\alpha x} e^{-j\beta x}$$

衰减的正弦波。

物理场景：有损传输线，$R, G > 0$。这是 **UCIe 的场景**。

---

### 3.3 物理形式：正向波 + 反向波

约定波的传播方向（$+x$ 从发送端指向接收端）：

$$V(x) = V_+ e^{-\gamma x} + V_- e^{+\gamma x}$$

分解为：

$$V(x) = \underbrace{V_+ e^{-\alpha x} e^{-j\beta x}}*{\text{正向（发送端 → 接收端）}} + \underbrace{V*- e^{+\alpha x} e^{+j\beta x}}_{\text{反向（反射，接收端 → 发送端）}}$$

**物理含义**：

$$
\begin{array}{c|c}
\text{传播距离 } L & \text{正向波的状态} \\
\hline
x = 0 & |V_+|,\; \angle V_+ \\
x = L & |V_+| \cdot e^{-\alpha L},\; \angle V_+ - \beta L
\end{array}
$$

---

### 3.4 $\gamma$ 的两个特征长度

| 参数 | 含义 | 特征长度 |
|------|------|---------|
| $\alpha = \Re\{\gamma\}$ | 衰减率（Np/m） | $\ell_\alpha = 1/\alpha$ = 幅度衰减到 $1/e$ 的距离 |
| $\beta = \Im\{\gamma\}$ | 相位旋转率（rad/m） | $\lambda = 2\pi/\beta$ = 波长 |

相速度：

$$v_p = \frac{\omega}{\beta}, \quad \lambda = \frac{v_p}{f}$$

**数值示例 — 铜走线 @ 16 GHz**：

对于 Advanced Package 走线（典型 $\alpha \approx 0.02\text{ Np/mm}$，$\beta \approx 0.4\text{ rad/mm}$）：

$$
\begin{aligned}
\ell_\alpha &= 1/0.02 = 50\text{ mm} &&\text{（需要 50mm 才衰减到 }1/e\text{）} \\
\lambda     &= 2\pi/0.4 \approx 15.7\text{ mm} &&\text{（一个波长的距离）}
\end{aligned}
$$

Advanced Package 走线仅 2 mm → $e^{-\alpha L} \approx e^{-0.04} \approx 0.96$，幅度还剩 96%。相位旋转 $\beta L \approx 0.8\text{ rad} \approx 46°$。几乎无损、几乎无畸变。

---

### 3.5 从 $\gamma^2$ 显式计算 $\alpha, \beta$

$$\gamma = \sqrt{u + jw}, \quad u = RG - \omega^2 LC,\; w = \omega(RC + LG)$$

$$\alpha = \sqrt{\frac{\sqrt{u^2 + w^2} + u}{2}}, \quad \beta = \sqrt{\frac{\sqrt{u^2 + w^2} - u}{2}}$$

若 $u < 0$（常见，因 $-\omega^2 LC$ 主导），则有 $\alpha < |u|$ 且 $\beta > 0$——信号主呈波特征，伴轻微衰减。

---

### 3.6 不需求解即知的定性判据 — $\gamma$ 在复平面的位置

在复平面上标记 $\gamma = \alpha + j\beta$：

```
Im(γ) = β
  ↑
  │   ×  无损 (α = 0, γ = jω√(LC))
  │  ×   低损 (α ≪ β, UCIe Advanced)
  │
  │   ×  中等损耗 (α ~ β/2, Standard 25mm)
  │
  │      ×  强损 (α = β, RC 扩散方程)
  │
  └────────────────────→ Re(γ) = α
```

**判据**：

$$\begin{aligned}
\alpha \ll \beta &\;\longrightarrow\; \text{波主导，衰减很小} \\
\alpha \approx \beta &\;\longrightarrow\; \text{扩散主导，波特征消失} \\
\alpha \gg \beta &\;\longrightarrow\; \text{信号在极短距离内被吸收}
\end{aligned}$$

---

### 3.7 边界条件

传输线长度 $L$，发送端阻抗 $Z_S$，接收端阻抗 $Z_L$。

发送端（$x = 0$）条件：

$$V(0) = V_S \cdot \frac{Z_{in}(0)}{Z_S + Z_{in}(0)}$$

其中 $Z_{in}(0) = Z_0 \cdot \frac{Z_L + Z_0 \tanh(\gamma L)}{Z_0 + Z_L \tanh(\gamma L)}$。

接收端（$x = L$）条件：

$$\frac{V(L)}{I(L)} = Z_L$$

由此解得反射系数：

$$\boxed{\Gamma_L = \frac{Z_L - Z_0}{Z_L + Z_0}}$$

$$\boxed{\Gamma_S = \frac{Z_S - Z_0}{Z_S + Z_0}}$$

全解在 $x = 0$ 处的形式：

$$V(x) = V_{inc} \cdot e^{-\gamma x} \cdot \left[1 + \Gamma_L \cdot e^{-2\gamma(L - x)}\right]$$

---

## 4. 矩阵情况：两根耦合传输线

### 4.1 方程

$$\frac{d^2}{dx^2} \begin{bmatrix} V_1 \\ V_2 \end{bmatrix} = \underbrace{(\mathbf{R} + j\omega\mathbf{L})(\mathbf{G} + j\omega\mathbf{C})}_{\mathbf{A} \in \mathbb{C}^{2\times2}} \begin{bmatrix} V_1 \\ V_2 \end{bmatrix}$$

即：

$$\boxed{\mathbf{V}'' = \mathbf{A} \mathbf{V}}$$

$\mathbf{A} \in \mathbb{C}^{2\times2}$，一般为满矩阵（含非对角元）。

---

### 4.2 对角化

设 $\mathbf{A}$ 可对角化：

$$\mathbf{A} = \mathbf{T} \begin{bmatrix} \gamma_1^2 & 0 \\ 0 & \gamma_2^2 \end{bmatrix} \mathbf{T}^{-1}$$

- $\gamma_1^2, \gamma_2^2$ = $\mathbf{A}$ 的两个特征值
- $\mathbf{T}$ 的列 = 对应的两个特征向量

即存在基变换 $\mathbf{W} = \mathbf{T}^{-1}\mathbf{V}$ 使得耦合方程解耦：

$$\frac{d^2\mathbf{W}}{dx^2} = \begin{bmatrix} \gamma_1^2 & 0 \\ 0 & \gamma_2^2 \end{bmatrix} \mathbf{W}$$

两个独立的标量 ODE，各自求解。

---

### 4.3 特征向量的物理含义：偶模与奇模

对于两根对称传输线（$L_{11} = L_{22}$, $C_{11} = C_{22}$），特征向量对应**偶模**与**奇模**：

**偶模**：$V_1 = V_2$（两线同相驱动）

$$\gamma_e^2 = \big(R + j\omega(L_{11} + L_{12})\big)\big(G + j\omega(C_{11} + C_{12})\big)$$

$$Z_{0e} = \sqrt{\frac{L_{11} + L_{12}}{C_{11} + C_{12}}}$$

**奇模**：$V_1 = -V_2$（两线反相驱动）

$$\gamma_o^2 = \big(R + j\omega(L_{11} - L_{12})\big)\big(G + j\omega(C_{11} - C_{12})\big)$$

$$Z_{0o} = \sqrt{\frac{L_{11} - L_{12}}{C_{11} - C_{12}}}$$

---

### 4.4 什么是 $e^{-\sqrt{\mathbf{A}}x}$？

标量下解为 $e^{\pm \gamma x}$。矩阵下形式完全一致，但需定义**矩阵指数**：

$$e^{-\sqrt{\mathbf{A}}x} = \mathbf{T} \begin{bmatrix} e^{-\gamma_1 x} & 0 \\ 0 & e^{-\gamma_2 x} \end{bmatrix} \mathbf{T}^{-1}$$

通解：

$$\mathbf{V}(x) = e^{-\sqrt{\mathbf{A}}x} \cdot \mathbf{V}_+ + e^{+\sqrt{\mathbf{A}}x} \cdot \mathbf{V}_-$$

在特征向量基下，耦合的矩阵方程组解耦为两个独立的标量方程——每个模式独立传播，各有自己的 $\gamma$ 和 $Z_0$。

---

### 4.5 串扰从这里出来

特征基变换矩阵 $\mathbf{T}$ 将"物理电压"（$V_1, V_2$，每根线上的电压）与"模式电压"（偶模、奇模的独立传播解）联系起来。

**若偶模与奇模的传播速度不同**（$v_e \neq v_o$），两个模式到达远端的时间不同 → 在物理电压 $V_1, V_2$ 上产生远端串扰（FEXT）。

**若偶模阻抗与奇模阻抗不同**（$Z_{0e} \neq Z_{0o}$），两个模式的反射特性不同 → 对近端和远端均产生串扰贡献。

**这就是串扰的数学根源——$\mathbf{A}$ 矩阵的非对角元使两个特征向量（偶/奇模）的传播特性不同，物理线上的电压不再独立传播。**

---

## 5. 整体结构

```
标量:  y'' = γ² y
         │
         ├── 特征值 γ²
         ├── 解结构: 指数函数 e^(±γx)
         ├── γ ∈ ℂ → α, β → 衰减 + 相位旋转
         └── 边界条件 → Γ 反射系数

矩阵:  Y'' = A Y
         │
         ├── 对角化 A → T diag(γ₁², γ₂²) T⁻¹
         ├── 特征值 → 各自模式的 γ₁, γ₂
         ├── 特征向量 → 偶模与奇模
         ├── 解结构: 矩阵指数 e^(±√A x)
         └── 偶/奇模速度差 → FEXT ≠ 0
```
