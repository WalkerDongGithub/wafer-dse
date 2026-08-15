# RLCG 有损传输线模型 — 完整求解

> 基于 Eric Bogatin, *Signal and Power Integrity — Simplified*, 2nd Ed., Ch7 & Ch9

---

## 1. 物理结构与支配方程

取一段无穷小长度 $dx$：

```
  i(x,t)    R·dx     L·dx      i(x+dx,t)
  ────────∕\/\/\────((((───────┬─────────
  v(x,t)                       │
                               ├── C·dx
                               ├── G·dx
  ─────────────────────────────┴─────────  (回流路径)
```

对这一段用基尔霍夫定律：

**KVL — 串联支路：**

$$v(x,t) - v(x+dx,t) = R \cdot dx \cdot i(x,t) + L \cdot dx \cdot \frac{\partial i}{\partial t}$$

除以 $dx$，取 $dx \to 0$：

$$\boxed{\frac{\partial v}{\partial x} = -R \cdot i - L \cdot \frac{\partial i}{\partial t}}\tag{1}$$

**KCL — 并联支路：**

$$i(x,t) - i(x+dx,t) = G \cdot dx \cdot v(x,t) + C \cdot dx \cdot \frac{\partial v}{\partial t}$$

除以 $dx$，取 $dx \to 0$：

$$\boxed{\frac{\partial i}{\partial x} = -G \cdot v - C \cdot \frac{\partial v}{\partial t}}\tag{2}$$

(1)(2) 就是**电报方程（Telegrapher's Equations）**。

---

## 2. 频域化

对正弦稳态，设：

$$v(x,t) = \Re\{V(x) \cdot e^{j\omega t}\}, \quad i(x,t) = \Re\{I(x) \cdot e^{j\omega t}\}$$

其中 $V(x), I(x)$ 是 x 的复值函数（phasor）。

代入 (1)(2)，消去 $e^{j\omega t}$：

$$\boxed{\frac{dV}{dx} = -(R + j\omega L) \cdot I}\tag{3}$$

$$\boxed{\frac{dI}{dx} = -(G + j\omega C) \cdot V}\tag{4}$$

**PDE 已化为 ODE。**

---

## 3. 解耦 — 二阶传播方程

对 (3) 再对 $x$ 求导：

$$\frac{d^2V}{dx^2} = -(R + j\omega L) \cdot \frac{dI}{dx}$$

代入 (4) 消去 $\frac{dI}{dx}$：

$$\frac{d^2V}{dx^2} = (R + j\omega L)(G + j\omega C) \cdot V$$

定义**传播常数** $\gamma$：

$$\boxed{\gamma^2 = (R + j\omega L)(G + j\omega C)}\tag{5}$$

$$\boxed{\gamma = \sqrt{(R + j\omega L)(G + j\omega C)}}\tag{6}$$

得到：

$$\boxed{\frac{d^2V}{dx^2} - \gamma^2 V = 0}\tag{7}$$

---

## 4. 求解 V(x)

(7) 是常系数齐次二阶线性 ODE。特征方程 $\lambda^2 - \gamma^2 = 0$，$\lambda = \pm\gamma$。

通解：

$$\boxed{V(x) = A \cdot e^{-\gamma x} + B \cdot e^{+\gamma x}}\tag{8}$$

$A, B$ 为两个复常数，由边界条件确定。

**物理含义**：

$$
\begin{aligned}
A \cdot e^{-\gamma x} &\quad\text{— 正向传播波（沿 }+x\text{，发送端 → 接收端）} \\
B \cdot e^{+\gamma x} &\quad\text{— 反向传播波（沿 }-x\text{，反射波）}
\end{aligned}
$$

---

## 5. 求 I(x) 与特性阻抗 $Z_0$

由 (3) 和 (8)：

$$
\begin{aligned}
I(x) &= -\frac{1}{R+j\omega L} \cdot \frac{dV}{dx} \\
     &= -\frac{1}{R+j\omega L} \cdot \left[-\gamma A e^{-\gamma x} + \gamma B e^{+\gamma x}\right] \\
     &= \frac{\gamma}{R+j\omega L} \cdot \left[A e^{-\gamma x} - B e^{+\gamma x}\right]
\end{aligned}
$$

定义**特性阻抗**：

$$\boxed{Z_0 = \frac{R + j\omega L}{\gamma} = \sqrt{\frac{R + j\omega L}{G + j\omega C}}}\tag{9}$$

则：

$$\boxed{I(x) = \frac{A e^{-\gamma x} - B e^{+\gamma x}}{Z_0}}\tag{10}$$

**物理含义**：对于纯正向波（$B=0$），$V/I = Z_0$ —— 信号在任何位置看到的"瞬时阻抗"就是这个常数。

---

## 6. 分解 $\gamma$ — 衰减与相位

$\gamma$ 为复数，写为：

$$\boxed{\gamma = \alpha + j\beta}$$

$$
\begin{aligned}
\alpha &= \Re\{\gamma\} = \text{衰减常数（Np/m）} \\
\beta  &= \Im\{\gamma\} = \text{相位常数（rad/m）}
\end{aligned}
$$

代入 (8)：

$$V(x) = A \cdot e^{-\alpha x} \cdot e^{-j\beta x} + B \cdot e^{+\alpha x} \cdot e^{+j\beta x}\tag{11}$$

**正向波的演化**：

$$
\begin{aligned}
x = 0 &: \quad |V| = |A|,\quad \angle V = \arg(A) \\
x = L &: \quad |V| = |A| \cdot e^{-\alpha L},\quad \angle V = \arg(A) - \beta L
\end{aligned}
$$

传播速度与波长：

$$v_p = \frac{\omega}{\beta}, \quad \lambda = \frac{2\pi}{\beta}$$

---

## 7. 边界条件 — 反射系数

传输线长度 $L$，终端接负载 $Z_L$。在 $x = L$ 处：

$$\frac{V(L)}{I(L)} = Z_L\tag{12}$$

由 (8)(10)：

$$\frac{A e^{-\gamma L} + B e^{+\gamma L}}{(A e^{-\gamma L} - B e^{+\gamma L})/Z_0} = Z_L$$

整理得：

$$\frac{B e^{+\gamma L}}{A e^{-\gamma L}} = \frac{Z_L - Z_0}{Z_L + Z_0}$$

定义**反射系数** $\Gamma$：

$$\boxed{\Gamma = \frac{Z_L - Z_0}{Z_L + Z_0}}\tag{13}$$

则全解可写为：

$$V(x) = A e^{-\gamma x} \cdot \left[1 + \Gamma \cdot e^{2\gamma(x-L)}\right]\tag{14}$$

输入阻抗（$x = 0$）：

$$Z_{in}(0) = \frac{V(0)}{I(0)} = Z_0 \cdot \frac{Z_L + Z_0 \tanh(\gamma L)}{Z_0 + Z_L \tanh(\gamma L)}\tag{15}$$

**三种特殊情况**：

$$
\begin{aligned}
Z_L = Z_0   &\Rightarrow \Gamma = 0      &&\text{匹配，无反射} \\
Z_L = \infty &\Rightarrow \Gamma = +1     &&\text{开路，全反射，同相} \\
Z_L = 0     &\Rightarrow \Gamma = -1     &&\text{短路，全反射，反相}
\end{aligned}
$$

---

## 8. $\gamma$ 的精确表达式

从 (6)：

$$\gamma = \sqrt{(R + j\omega L)(G + j\omega C)} = \sqrt{(RG - \omega^2 LC) + j\omega(RC + LG)}$$

设：

$$u = RG - \omega^2 LC, \quad w = \omega(RC + LG)$$

则：

$$\gamma = \sqrt{u + jw} = \sqrt[4]{u^2 + w^2} \cdot e^{j\theta/2}, \quad \theta = \arctan(w/u)$$

$$
\begin{aligned}
\alpha &= \sqrt[4]{u^2 + w^2} \cdot \cos\left(\frac{\theta}{2}\right) = \sqrt[4]{u^2 + w^2} \cdot \sqrt{\frac{1 + \frac{u}{\sqrt{u^2 + w^2}}}{2}}\tag{16} \\[4pt]
\beta  &= \sqrt[4]{u^2 + w^2} \cdot \sin\left(\frac{\theta}{2}\right) = \sqrt[4]{u^2 + w^2} \cdot \sqrt{\frac{1 - \frac{u}{\sqrt{u^2 + w^2}}}{2}}\tag{17}
\end{aligned}
$$

---

## 9. 低损近似 — UCIe 的工程公式

当 $R \ll \omega L$ 且 $G \ll \omega C$ 时：

令 $\varepsilon_1 = \frac{R}{\omega L} \ll 1$，$\varepsilon_2 = \frac{G}{\omega C} \ll 1$：

$$
\begin{aligned}
\gamma &= \sqrt{(R + j\omega L)(G + j\omega C)} \\
       &= \sqrt{j\omega L(1 - j\varepsilon_1) \cdot j\omega C(1 - j\varepsilon_2)} \\
       &= \sqrt{-\omega^2 LC \cdot (1 - j\varepsilon_1)(1 - j\varepsilon_2)} \\
       &= j\omega\sqrt{LC} \cdot \sqrt{(1 - j\varepsilon_1)(1 - j\varepsilon_2)} \\
       &= j\omega\sqrt{LC} \cdot \sqrt{1 - j(\varepsilon_1 + \varepsilon_2) - \varepsilon_1\varepsilon_2}
\end{aligned}
$$

展开 $\sqrt{1 + \delta} \approx 1 + \frac{\delta}{2} - \frac{\delta^2}{8} + \cdots$，忽略 $\varepsilon_1\varepsilon_2$（二阶小量）：

$$
\begin{aligned}
\gamma &\approx j\omega\sqrt{LC} \cdot \left[1 - j\frac{\varepsilon_1 + \varepsilon_2}{2}\right] \\
       &= j\omega\sqrt{LC} + \frac{\omega\sqrt{LC}}{2}(\varepsilon_1 + \varepsilon_2) \\
       &= j\omega\sqrt{LC} + \frac{R}{2\sqrt{L/C}} + \frac{G}{2}\sqrt{\frac{L}{C}}
\end{aligned}
$$

代入 $Z_0 \approx \sqrt{L/C}$：

$$\boxed{\alpha \approx \frac{R}{2Z_0} + \frac{G \cdot Z_0}{2}}\tag{18}$$

$$\boxed{\beta \approx \omega\sqrt{LC}}\tag{19}$$

$$\boxed{Z_0 \approx \sqrt{\frac{L}{C}}}\tag{20}$$

---

## 10. $\alpha$ 的频率依赖

$R$ 和 $G$ 各自有自己的频率依赖：

$$
\begin{aligned}
R(\omega) &= R_{DC} + k_1\sqrt{\omega} \quad &\text{（趋肤效应，Bogatin §9.3）} \\
G(\omega) &= \omega \cdot C \cdot \tan\delta \quad &\text{（介质耗散，Bogatin §9.4）}
\end{aligned}
$$

其中 $\tan\delta = D_f$（耗散因子，材料属性，无量纲）。

代入 (18)：

$$\boxed{\alpha(f) \approx \frac{R_{DC}}{2Z_0} + \underbrace{\frac{k_1}{2Z_0} \cdot \sqrt{2\pi f}}_{\text{趋肤效应 } \propto \sqrt{f}} + \underbrace{\frac{\pi \cdot C \cdot D_f \cdot Z_0}{1} \cdot f}_{\text{介质损耗 } \propto f}}\tag{21}$$

**关键**：$f \to \infty$ 时，介质损耗项（$\propto f$）主导趋肤效应项（$\propto \sqrt{f}$）。

---

## 11. 总损耗 — 代入 UCIe 参数

长度 $L$ 的通道总损耗：

$$IL(dB) = 20 \log_{10}\left|\frac{V(L)}{V(0)}\right| = 20 \log_{10}\left(e^{-\alpha L}\right) = -\frac{20}{\ln 10} \cdot \alpha \cdot L$$

$$\boxed{IL(dB) \approx -8.686 \cdot \alpha \cdot L}\tag{22}$$

UCIe Table 5-11 规定在 Nyquist 频率 $f_N = \frac{\text{Data Rate}}{2}$ 处：

$$
\begin{aligned}
\text{4–16 GT/s Advanced:}&\quad IL(f_N) > -3\text{ dB} \\
\text{24–32 GT/s Advanced:}&\quad IL(f_N) > -5\text{ dB}
\end{aligned}
$$

代入 (18)：

$$|IL(f_N)| = 8.686 \cdot \left[\frac{R(f_N)}{2Z_0} + \frac{G(f_N) \cdot Z_0}{2}\right] \cdot L < 3 \text{（或 }5\text{）dB}$$

**这个不等式是通道设计的硬约束。**

---

## 12. 线性掩模的额外含义

UCIe 还规定损耗掩模从 DC 到 $f_N$ 是**线性的**。数学上：

$$IL(f) \geq \frac{f}{f_N} \cdot IL(f_N), \quad \forall f \in [0, f_N]$$

这不是多余的——它防止了中间频率出现谐振坑（resonance dip）。如果通道在某个 $f < f_N$ 处有明显的阻抗不连续，该频率会有一个额外的损耗峰，违反线性掩模。**这是一个"平滑性"约束——等效于要求没有严重的阻抗不连续。**

---

## 13. 去加重 — 对 $\alpha(f)$ 不平的预补偿

因为 $\alpha(f)$ 随频率增加，通道相当于一个低通滤波器——高频衰减更多。

**去加重**：在发送端降低低频分量幅度，使得经通道衰减后所有频率分量幅度均匀。

一阶 FIR 滤波器（UCIe Table 5-4, p188）：

$$V_{out}(n) = C_0 \cdot V_{in}(n) + C_{+1} \cdot V_{in}(n-1)$$

$$|C_0| + |C_{+1}| = 1 \quad \text{（恒定峰值功率约束）}$$

去加重值：

$$\text{De-emphasis (dB)} = 20 \log_{10}\left(\frac{V_b}{V_a}\right)$$

其中 $V_a$ 为峰值幅度，$V_b = V_a - |C_{+1}| \cdot V_a$ 为去加重后的低频幅度。

---

## 14. 总结：从电报方程到 UCIe 每个参数

$$\boxed{\frac{d^2V}{dx^2} - \gamma^2 V = 0}$$

$$
\begin{aligned}
\gamma &= \sqrt{(R + j\omega L)(G + j\omega C)} = \alpha + j\beta \\[4pt]
\alpha &\approx \frac{R}{2Z_0} + \frac{GZ_0}{2}
    \begin{cases}
        R \propto \sqrt{f} &\text{（趋肤效应）} &\longrightarrow& \text{约束导线截面} \\
        G \propto f        &\text{（介质损耗）} &\longrightarrow& \text{约束介质 } D_f
    \end{cases} \\[4pt]
\beta &\approx \omega\sqrt{LC} \quad\longrightarrow\quad v = 1/\sqrt{LC} \\[4pt]
Z_0 &\approx \sqrt{L/C} \quad\longrightarrow\quad \text{驱动器阻抗 22–28 Ω 匹配目标} \\[4pt]
\Gamma &= \frac{Z_L - Z_0}{Z_L + Z_0} \quad\longrightarrow\quad \text{端接策略}
\end{aligned}
$$
