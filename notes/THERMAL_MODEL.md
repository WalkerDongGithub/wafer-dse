# 晶圆级热约束：从零开始的推导

## 0. 类比：热 = 水流

热从高温流到低温，跟电流从高电压流到低电压一模一样。

| 热 | 电 | 水 |
|---|---|---|
| 温差 $\Delta T$ [K] | 电压 $V$ [V] | 水压差 |
| 热流 $P$ [W] | 电流 $I$ [A] | 水流 |
| 热阻 $R$ [K/W] | 电阻 $R$ [Ω] | 管道阻力 |

**欧姆定律的热学版本**：$P = \Delta T / R$。温差越大、热阻越小，热流越大。

## 1. 单 die：最简单的情况

一颗 die 发热 $P$ 瓦，上面扣着 heatsink。热从 die → TIM → lid → heatsink → ambient。

$$P = \frac{T - T_{\text{amb}}}{R} \quad\Longrightarrow\quad T = T_{\text{amb}} + P \cdot R$$

给定功率和热阻，温度就定了。要 $T \le 85°\text{C}$？等价于 $P \le (85 - T_{\text{amb}}) / R$。

为方便，用**热导** $g = 1/R$ 代替热阻：

$$P = g \cdot (T - T_{\text{amb}})$$

## 2. 模型假设

1. **一个 interposer = 一个热节点**。同一 interposer 上所有 die 温度一致，因为它们之间距离短（几 mm）、interposer 是硅（导热好）。一个节点功率 $P_v = \sum_{\text{dies}} P_{\text{die}}$。

2. **只建模 interposer 之间的横向导热**。die 之间的局部温差被 lumped 掉。横向热流通过 substrate（硅 wafer）传导。

3. **稳态**。不考虑温度随时间变化（$dT/dt = 0$）。DSE 可行性只关心最坏稳态温度是否超标。

4. **$g_{\text{vert}}$ 由 MFIT 一次标定**。单 interposer 的 3D 堆叠热阻（TIM + lid + heatsink）被压缩成一个等效热导 $g_{\text{vert}}$，不参与逐节点求解。

## 3. wafer：多了一个维度

wafer 上有 $n$ 个 interposer 并排。每个有自己的 heatsink（向上散热），但 wafer substrate（硅基板）是**连通的**——一个 interposer 特别烫，热量会通过基板横向流到邻居，把它们也加热。

两个相邻 interposer 为例：

```
   heatsink (T_amb)          heatsink (T_amb)
        ↑                          ↑
     g_vert                     g_vert
        │                          │
   ┌─────────┐    g_lat     ┌─────────┐
   │ inter1  │←───────────→│ inter2  │
   │  T₁, P₁ │             │  T₂, P₂ │
   └─────────┘             └─────────┘
```

稳态热平衡——每个 interposer 的产热 = 向上走的 + 横向走的：

$$P_1 = g_{\text{vert}}(T_1 - T_{\text{amb}}) + g_{\text{lat}}(T_1 - T_2)$$

$$P_2 = g_{\text{vert}}(T_2 - T_{\text{amb}}) + g_{\text{lat}}(T_2 - T_1)$$

如果 $T_1 > T_2$，$T_1 - T_2$ 为正 → 热从 1 流向 2。如果反过来，就从 2 流向 1。

## 3. 矩阵形式

整理——未知温度归左，已知量归右：

$$(g_{\text{vert}} + g_{\text{lat}})T_1 - g_{\text{lat}}T_2 = P_1 + g_{\text{vert}}T_{\text{amb}}$$

$$-g_{\text{lat}}T_1 + (g_{\text{vert}} + g_{\text{lat}})T_2 = P_2 + g_{\text{vert}}T_{\text{amb}}$$

写成矩阵：

$$\begin{bmatrix} g_{\text{vert}}+g_{\text{lat}} & -g_{\text{lat}} \\ -g_{\text{lat}} & g_{\text{vert}}+g_{\text{lat}} \end{bmatrix} \begin{bmatrix} T_1 \\ T_2 \end{bmatrix} = \begin{bmatrix} P_1 \\ P_2 \end{bmatrix} + \begin{bmatrix} g_{\text{vert}}T_{\text{amb}} \\ g_{\text{vert}}T_{\text{amb}} \end{bmatrix}$$

$$\boxed{\mathbf{G} \cdot \mathbf{T} = \mathbf{P} + \mathbf{b}}$$

推广到 $n$ 个节点（4×4 网格 = 16 个）：

$$\begin{aligned}
G_{ii} &= g_{\text{vert}} + |\mathcal{N}(i)| \cdot g_{\text{lat}} \quad &\text{(对角：自己到环境 + 到所有邻居)} \\
G_{ij} &= -g_{\text{lat}} \quad (j \in \mathcal{N}(i)) \quad &\text{(非对角：邻居之间的热耦合)} \\
b_i &= g_{\text{vert}} \cdot T_{\text{amb}}
\end{aligned}$$

$\mathbf{G}$ 是一个**M-矩阵**：对角全是正的，非对角全是负的或零，每行的对角 $\ge$ 非对角绝对值之和。稀疏（每个节点最多连 4 个邻居），对称正定。

## 4. 关键数学性质：$\mathbf{G}^{-1} \ge 0$

M-矩阵的逆矩阵所有元素都 $\ge 0$。物理含义：

> **任何一个节点的功率增加，所有节点的温度只升不降。功率减少，温度只降不升。**

这就是热传导的因果性——没人能"偷"你的热量让你的温度反而降低。

## 5. 温度约束 → 线性不等式

要求所有节点温度 $\le T_{\text{max}}$：

$$\mathbf{T} = \mathbf{G}^{-1}(\mathbf{P} + \mathbf{b}) \le T_{\text{max}} \cdot \mathbf{1}$$

因为 $\mathbf{G}^{-1} \ge 0$，这是一个**保序映射**——两边同时左乘 $\mathbf{G}$，不等号方向不变：

$$\mathbf{G} \cdot (T_{\text{max}} \cdot \mathbf{1}) \ge \mathbf{P} + \mathbf{b}$$

右边 $\mathbf{P} + \mathbf{b}$ 是实际功率加环境贡献，左边 $\mathbf{G} \cdot (T_{\text{max}}\mathbf{1})$ 是**热网络在 $T_{\text{max}}$ 下能带走的最大功率**。不等式意味着：实际功率不能超过这个上限。

代入 $\mathbf{P} = \mathbf{P}_0 + \mathbf{C} \cdot \mathbf{L}$：

$$\boxed{\mathbf{C} \cdot \mathbf{L} \le \mathbf{G} \cdot (T_{\text{max}} \cdot \mathbf{1}) - \mathbf{b} - \mathbf{P}_0}$$

**热约束 = 关于 $\mathbf{L}$ 的线性不等式。** 整条推导链上唯一的"数学"就是 $\mathbf{G}^{-1} \ge 0$。写成代码只需构造 $\mathbf{G}$（5 行）、算右边常数、检查 $\mathbf{C} \cdot \mathbf{L} \le \text{常数}$。
