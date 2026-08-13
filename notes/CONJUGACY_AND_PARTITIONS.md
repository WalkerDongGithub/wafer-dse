# 为什么 S_n 的共轭类 = n 的整数分拆

## 结论

$S_n$ 的两个排列共轭当且仅当它们有相同的 cycle type。因此共轭类和整数分拆一一对应。

---

## 1. 回顾：共轭的定义

$S_n$ 中两个元素 $\sigma, \tau$ **共轭** 当且仅当存在 $\rho \in S_n$ 使得 $\tau = \rho \sigma \rho^{-1}$。

---

## 2. 共轭作用就是"重标号"

把 $\tau = \rho \sigma \rho^{-1}$ 写成映射复合：先 $\rho^{-1}$ 把元素映射到新标签，再 $\sigma$ 作用，最后 $\rho$ 映射回来。

$$\tau(i) = \rho(\sigma(\rho^{-1}(i)))$$

换句话说，$\tau$ 就是**把 $\sigma$ 的 cycle 里的元素用 $\rho$ 重新标号**得到的排列。

---

## 3. 重标号不改变 cycle 结构

考虑 $\sigma$ 的一个 $k$-cycle $(a_1 a_2 \dots a_k)$。在共轭 $\tau = \rho \sigma \rho^{-1}$ 下：

$$\tau(\rho(a_i)) = \rho(\sigma(a_i)) = \rho(a_{i+1})$$

所以 $\tau$ 包含 $k$-cycle $(\rho(a_1) \rho(a_2) \dots \rho(a_k))$。

**结论**：共轭保持 cycle 长度不变，只改变 cycle 中元素的名字。

---

## 4. 反过来：相同 cycle type 一定共轭

任意两个有相同 cycle type 的排列 $\sigma, \tau$：

把 $\sigma$ 的 cycle 写成（任意顺序）：
$$(a_{1,1}\dots a_{1,\ell_1})(a_{2,1}\dots a_{2,\ell_2})\cdots$$

把 $\tau$ 的 cycle 也写成（对应顺序）：
$$(b_{1,1}\dots b_{1,\ell_1})(b_{2,1}\dots b_{2,\ell_2})\cdots$$

定义 $\rho(a_{i,j}) = b_{i,j}$——即把 $\sigma$ 的每个元素映射到 $\tau$ 对应 cycle 的对应位置的元素。则 $\tau = \rho \sigma \rho^{-1}$。

**结论**：相同 cycle type → 共轭。

---

## 5. Cycle type = 整数分拆

一个排列的 **cycle type** 是它的各 cycle 的长度组成的**降序**序列。

$$\text{cycle type}(\sigma) = (\ell_1, \ell_2, \dots, \ell_m)$$

其中 $\ell_1 \ge \ell_2 \ge \dots \ge \ell_m \ge 1$，且 $\sum \ell_i = n$。

这正是 $n$ 的**整数分拆**（integer partition）。

---

## 6. 所以：共轭类 ↔ 分拆

| 概念 | 等价表述 |
|------|---------|
| $S_n$ 的共轭类 | cycle type 相同的排列集合 |
| cycle type | 各 cycle 长度的降序序列 |
| 降序序列 + 和为 $n$ | $n$ 的整数分拆 |

分拆 $p(n)$ 就是 $S_n$ 的共轭类个数。分拆的生成只需要组合数学，不需要群作用计算。

---

## 7. 例子：$S_4$（$p(4)=5$）

| 分拆 | Cycle type | 排列示例 |
|------|-----------|---------|
| `[4]` | 一个 4-cycle | `(0 1 2 3)` |
| `[3,1]` | 一个 3-cycle + 一个 1-cycle | `(0 1 2)(3)` |
| `[2,2]` | 两个 2-cycle | `(0 1)(2 3)` |
| `[2,1,1]` | 一个 2-cycle + 两个 1-cycle | `(0 1)(2)(3)` |
| `[1,1,1,1]` | 四个 1-cycle | `(0)(1)(2)(3)` = identity |

---

## 8. Derangement 过滤

**Derangement** = 没有固定点的排列 = cycle type 中不含 `1`。

在交换网络 DSE 中，1-cycle 表示"节点发给自己"——不产生网络流量，不是有效的最坏情况流量模式。因此我们只保留 cycle type 不含 `1` 的分拆作为排列代表元 $\mathcal{R}$。

$$|\mathcal{R}| = \text{\# partitions of } n \text{ with no part equal to 1}$$

| $n$ | $p(n)$ | 不含 1 的分拆数 $= |\mathcal{R}|$ |
|-----|--------|----------------------|
| 4 | 5 | 2 |
| 6 | 11 | 4 |
| 8 | 22 | 7 |
| 10 | 42 | 12 |
| 16 | 231 | 56 |

---

## 9. 为什么这很重要

计算 $S_n$ 的共轭类不需要遍历 $n!$ 个排列——只需要枚举 $p(n)$ 个整数分拆，对每个分拆构造一个标准代表元。$p(n)$ 的增长远慢于 $n!$（$p(16)=231$ vs $16! \approx 2\times 10^{13}$）。这就是"群论归约"的计算基础。
