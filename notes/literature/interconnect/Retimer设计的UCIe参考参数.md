# Retimer 设计需要参考的 UCIe 电气参数

---

## 1. 核心认知：Retimer 的 UCIe 侧就是一个标准的 UCIe 接收器

规范没有"Retimer 专用接收器规范"——因为不需要。**Retimer 面对 UCIe 链路的那一侧，就是标准的 UCIe PHY。** 所有第 5 章的接收器电气参数，Retimer 都必须满足。

---

## 2. 从 UCIe 链路进入 Retimer 的信号——Retimer 接收器必须能处理的

### 发送器侧（对端 Die 发出来的——Retimer 收到的就是这个）

规范 §5.3, Table 5-3（p186-187）：

| 参数 | Advanced | Standard | 含义 |
|------|:---:|:---:|------|
| 数据 Lane 摆幅 | **0.4 V** | **0.4 V** | Retimer 接收器的最小输入灵敏度必须覆盖这个 |
| 1-UI 总抖动 | **≤ 96/113 mUI pk-pk** | 同 | Retimer 接收器必须能容忍这个抖动 |
| 确定性抖动 | **≤ 48 mUI pk-pk** | 同 | Retimer 的时钟恢复必须在这个抖动下工作 |
| Lane 间偏移（校正后）| **≤ ±0.02 UI** | ≤ ±0.14 UI | Retimer 必须做 per-lane deskew 来补偿 |
| 时钟到数据训练精度 | **≤ ±0.07 UI** | 同 | Retimer 接收器的采样点定位精度 |

**所以 Retimer 收到的信号不是"胡吊传"的——发送端必须符合这些参数。Retimer 接收器必须在这些参数定义的信号质量下正确工作。**

### 接收器侧（Retimer 自己的接收器电气要求）

规范 §5.4, Table 5-5（p190）：

| 参数 | 值 | 含义 |
|------|:---:|------|
| RX 输入阻抗（Standard，含端接） | **45–55 Ω** | Retimer 在 Standard Package 下必须端接 |
| RX 电压灵敏度 | **≤ 40 mV** | Retimer 接收器必须能分辨 ≥ 40mV 的眼图开口 |
| 数据/时钟总差分抖动 | **≤ 60 mUI pk-pk** | Retimer 自己的接收器不能引入超过这个的抖动 |
| Lane 间偏移容限（≤16 GT/s）| **±0.07 UI** | Retimer 必须容忍线间偏移 |
| Lane 间偏移容限（>16 GT/s）| **±0.12 UI** | 高速下更宽 |
| RX Pad 电容（Advanced, 24-32 GT/s）| **≤ 125 fF** | Retimer 的 bump/pad 不能有大电容 |

---

## 3. 通道质量——Retimer 本地 UCIe 链路必须满足的

Retimer 和本地 Die 之间的 UCIe 链路，和其他 UCIe 链路一样，必须满足第 5 章的通道规范。

### 通道损耗（§5.7, p201, Table 5-11）

| 数据速率 | Advanced | Standard |
|---------|:---:|:---:|
| 4–16 GT/s | $IL(f_N) > -3\text{ dB}$ | 同 |
| 24–32 GT/s | $IL(f_N) > -5\text{ dB}$ | 同 |

**Retimer 和 Die 之间的封装走线必须满足这个损耗掩模。** 如果 Retimer 放在离 Die 很远的位置，超过了 Standard Package 的 25mm 距离——这条链路本身就不是 UCIe 合规的。Retimer 必须放在 UCIe 合规距离内。

### 串扰掩模（§5.7, p201, Table 5-11）

$$XT(f_N) < 1.5 \cdot IL(f_N) - 21.5\quad\text{且}\quad XT(f_N) < -23\text{ dB}$$

Retimer 和多条 UCIe 链路共存时，每条链路之间的串扰必须满足此掩模。

---

## 4. BER —— Retimer 必须在此误码率下工作

规范 §5.10, p236 + Table 1-1/1-2：

| 封装 | 低速 | 高速 |
|------|:---:|:---:|
| Advanced | 1e-27 (≤12 GT/s) | **1e-15** (≥16 GT/s) |
| Standard | 1e-27 (≤8 GT/s) | **1e-15** (≥12 GT/s) |

**Retimer 的 UCIe 接收器必须在这个 BER 下正确工作。** 如果 Retimer 收到的信号质量差到 BER > 1e-15，本地的 UCIe 链路不是合规的——需要对端 Die 检查自己的发送器、或检查封装走线。

**如果外部互连导致的端到端 BER 不满足要求——那是 Retimer 方案 B 或 C 的责任（Retimer 自己做额外纠错）。本地 UCIe 链路的 BER 必须独立满足。**

---

## 5. 均衡 —— Retimer 的发送器和接收器

### Retimer 向 Die 发送时

Retimer 的 UCIe 发送器**必须**满足和普通 Die 一样的发送器规范。24/32 GT/s 下**必须**支持去加重（§5.3.3, p187）。

### Retimer 从 Die 接收时

Retimer 的 UCIe 接收器**可以**选做 CTLE/DFE（§5.4.3, p193），和普通 Die 一样的可选条款。

---

## 6. 时钟 —— Retimer 的特殊之处

规范 §5.1.1（p180）专门区分了 Retimer 的两种时钟场景：

> For the retimer use case, the **"Local UCIe Link connection"** shall use common REFCLK, while the **"Off-Package Link connection"** is not required to use or share the common REFCLK.

| 链路侧 | REFCLK 要求 |
|--------|-----------|
| UCIe 链路侧（Retimer ↔ Die） | **必须共享公共 REFCLK**，传输延迟差 < 5ns |
| 外部互连侧（Retimer ↔ Retimer） | **不需要共享 REFCLK** |

**UCIe 侧 REFCLK 必须是同一个时钟源。外部互连侧不需要。**

---

## 7. 总结：Retimer 设计者需要从 UCIe 规范中提取的电气参数

| 类别 | 关键参数 | 规范位置 |
|------|---------|---------|
| Retimer 的 RX 电气 | 输入灵敏度 40mV，抖动容限，端接阻抗 | Table 5-3, 5-5 |
| 对端 Die 的 TX 信号质量 | 摆幅 0.4V，抖动 ≤ 96/113 mUI | Table 5-3 |
| 本地通道合规 | $IL(f_N) > -3$ / $-5$ dB，XT 掩模 | Table 5-11 |
| BER | 1e-27 / 1e-15（取决于速率和封装） | Table 1-1/1-2 |
| 均衡 | TX 去加重必须（24/32 GT/s），RX CTLE 可选 | §5.3.3, §5.4.3 |
| 时钟 | UCIe 侧共享 REFCLK，外部侧自由 | §5.1.1 |

**Retimer 的 UCIe 侧——无论是物理层、通道、BER、均衡还是时钟——完全等同于一个标准的 UCIe Die。规范没有给 Retimer "放宽条件"。** Retimer 必须和任何其他 UCIe 芯片一样满足 Chapter 5 的全部电气合规要求。
