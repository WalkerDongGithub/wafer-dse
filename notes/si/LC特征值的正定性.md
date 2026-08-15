# $\mathbf{LC}$ 特征值的正定性 — 物理强制，不是巧合

---

## 1. 特征值的符号决定了传播还是衰减

解耦后的 ODE：

$$\frac{d^2 U_k}{dx^2} = -\omega^2 \lambda_k \cdot U_k$$

传播常数：

$$\gamma_k^2 = -\omega^2 \lambda_k$$

$$\gamma_k = \sqrt{-\omega^2 \lambda_k}$$

- **若 $\lambda_k > 0$**：$\gamma_k^2 < 0$ → $\gamma_k = j \omega\sqrt{\lambda_k} = j\beta_k$ — **纯虚数。** 波可以传播。$e^{-j\beta_k x}$ = 无衰减的正弦振荡。

- **若 $\lambda_k = 0$**：$\gamma_k = 0$ → $U_k'' = 0$ → $U_k$ 是 $x$ 的线性函数。**没有波动——信号退化为直流/静电分布。**

- **若 $\lambda_k < 0$**：$\gamma_k^2 > 0$ → $\gamma_k = \omega\sqrt{|\lambda_k|} \in \mathbb{R}^+$。**纯实数。** $e^{-\gamma_k x}$ = 纯指数衰减。**波不能传播——只在一个趋肤深度内衰减到零。这是倏逝模（evanescent mode）。**

---

## 2. $\lambda_k > 0$ 对所有 $k$ 是物理强制

传输线上能量以电磁波形式传播，要求 $\gamma_k$ 是纯虚数。这等价于 $\lambda_k > 0$ 对所有 $k$。

**这个条件翻译成矩阵语言：$\mathbf{LC}$ 必须是正定矩阵。**

---

## 3. $\mathbf{LC}$ 的正定性可以证明

$$\mathbf{L} \text{ 和 } \mathbf{C} \text{ 各自都是正定的。}$$

**物理原因**：电感矩阵是对称正定的（磁场储能 $\frac{1}{2} \mathbf{I}^T \mathbf{L} \mathbf{I} > 0$ 对所有 $\mathbf{I} \neq 0$）。电容矩阵也是对称正定的（电场储能 $\frac{1}{2} \mathbf{V}^T \mathbf{C} \mathbf{V} > 0$ 对所有 $\mathbf{V} \neq 0$）。这是电磁场能量的正定性强制的——电感储能和电容储能都是非负的，且只有所有电流/电压为零时才是零。

**但两个正定矩阵的乘积不一定是正定的。** $\mathbf{L}$ 和 $\mathbf{C}$ 一般不交换（$\mathbf{LC} \neq \mathbf{CL}$），所以 $\mathbf{LC}$ 不一定是对称的。

**然而**，$\mathbf{L}$ 和 $\mathbf{C}$ 可以同时对角化进行合同变换：存在可逆矩阵 $\mathbf{P}$ 使得 $\mathbf{P}^T \mathbf{L} \mathbf{P}$ 和 $\mathbf{P}^T \mathbf{C} \mathbf{P}$ 同时为对角矩阵（由 $\mathbf{L}$ 和 $\mathbf{C}$ 的对称正定性保证）。在这个基下，$\mathbf{LC}$ 相似于一个对称正定矩阵 → **所有特征值为正实数。**

---

## 4. 两根线的验证

$$\lambda_1 = (L_0 + L_m)(C_0 - C_m), \quad \lambda_2 = (L_0 - L_m)(C_0 + C_m)$$

$\lambda_1 > 0$：需要 $C_0 > C_m$（自电容大于互电容——永远成立，因为信号线对自己回流路径的电容一定大于它对邻线的电容。）

$\lambda_2 > 0$：需要 $L_0 > L_m$（自感大于互电感——永远成立，因为自己回路的磁通一定大于邻线回路漏过来的磁通。）

**耦合系数 $K_L = L_m/L_0 < 1$，$K_C = C_m/C_0 < 1$ — 保证两个特征值都是正的。**

---

## 5. $\lambda_k \to 0$ 可以发生吗

如果某两条线之间的耦合变得极强（$L_m \to L_0$ 或 $C_m \to C_0$），对应的特征值趋近于零 → $\beta_k \to 0$ → $v_k \to \infty$（波速无穷大——物理上不可能）或 $\lambda \to 0$ → $v \to \infty$ 的信号。

实际上 $L_m$ 永远小于 $L_0$（互电感不可能超过自感——你不可能把邻线的全部磁通都耦合过来）。$C_m$ 永远小于 $C_0$（互电容不可能超过自电容——你不可能对邻线的电容大于对自己回流路径的电容）。**物理几何强保特征值远离零。**

---

## 6. 总结

| $\lambda_k$ 的符号 | 物理含义 |
|:---:|------|
| $\lambda_k > 0$ | 波可以传播（$N$ 根线有 $N$ 个传播模） |
| $\lambda_k = 0$ | 波不能传播——退化为静电分布 |
| $\lambda_k < 0$ | 倏逝模——纯指数衰减，波不能传播 |

**所有特征值都是正的因为 $\mathbf{L}$ 和 $\mathbf{C}$ 各自都是正定矩阵——这是电磁场能量正定性在电路层面的表现。** 不是数学巧合，是物理强制的。
