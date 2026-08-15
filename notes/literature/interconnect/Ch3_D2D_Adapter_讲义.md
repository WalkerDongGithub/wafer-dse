# 第三章：D2D 适配器 — 课堂讲义

> 对应规范 Chapter 3.0, p56-96（41页）
> **阅读本讲义之前，你不需要先读原文。本讲义是自包含的。**
> 文中所有「原文引用」是证据和参考，不是你必须对照的内容。

---

## 开篇：适配器为什么存在？

在进入具体章节之前，我们先想清楚一个问题：**UCIe 的物理层已经提供了数据传输通道，为什么还需要一个"适配器"？**

这个问题的答案，就藏在 UCIe 试图解决的矛盾里。

### 矛盾：物理链路不够可靠，但协议层期望绝对可靠

从第 1 章我们知道：
- Advanced Package 在 ≥16 GT/s 时，Raw BER 是 **1e-15**——这意味着每传 10¹⁵ 个 bit，平均就有一个 bit 错误
- 在 32 GT/s × 64 Lane 的链路上，这大约相当于**每几分钟就有一个 bit 错误**

如果协议层（PCIe、CXL）直接面对这种链路，它自己的 CRC 也会检测到错误——但代价是：协议层的重传机制是为"偶尔出错"设计的，不是为"底层链路的持续背景噪声"设计的。而且 PCIe/CXL 的可靠性机制有很多假设（比如可变长度 TLP、复杂的 ACK/NAK 协议），在封装内这个场景下，这些假设很多都是多余的。

规范开门见山地定义了适配器的 4 大职责（p56）：

> The Die-to-Die Adapter is responsible for:
> - **Reliable data transfer** (CRC computation and Retry, or parity computation)
> - **Arbitration and Muxing** (in case of multiple Protocol Layers)
> - **Link State Management**
> - **Protocol and Parameter negotiation** with the remote Link partner

这 4 条其实就回答了两个问题：

**问题 1：「链路不可靠怎么办？」→ CRC + Retry（核心职责 1）**

**问题 2：「上面跑什么协议、跑几个、什么时候跑、什么时候停？」→ 参数协商 + 多协议复用 + 状态管理（职责 2/3/4）**

适配器就是**夹在"不完美的物理链路"和"需要完美传输的上层协议"之间的那个翻译官和保镖**。

### 🧠 引申思考：UCIe 的适配器借鉴了 PCIe 的 Data Link Layer，但做了精简

如果你了解 PCIe，你会发现适配器的功能和 PCIe 的 Data Link Layer（DLL）很像——CRC、ACK/NAK、重传。但 UCIe 适配器比 PCIe DLL 简单得多，原因是：

| | PCIe DLL | UCIe Adapter |
|---|---|---|
| 工作环境 | PCB/电缆，BER ~1e-12 | 封装内，BER ~1e-27 ~ 1e-15 |
| CRC 强度 | 4B LCRC (32-bit) | 2B CRC (16-bit) |
| 重传复杂度 | Selective Nak + Rx Retry Buffer | 只做全窗口重传 |
| 序列号宽度 | 10-bit | 8-bit |
| 需要处理的异常 | 大量（链路抖动、均衡器收敛失败...） | 极少 |

所以适配器不是"PCIe DLL 的翻版"，而是"为封装内环境量身定制的极简版可靠性引擎"。

---

有了这个整体认知，我们现在按逻辑顺序重新组织这一章的学习。规范的原始编排（3.0→3.1→3.2→...→3.9）是工程文档的顺序，不是教学的顺序。我们按照**"先理解核心工作，再展开其他功能"**的逻辑来讲。

---

## 第一讲：可靠传输 — 适配器最核心的工作

### 1.1 CRC：适配器怎么发现数据错了？

规范 3.7 节（p91）定义了 CRC 计算。让我们从最基本的开始。

#### 为什么需要 CRC？

物理链路传输的是电信号。即使封装内环境极好，信号仍然可能因为噪声、串扰、电源纹波而翻转。CRC 的作用是：**在接收端独立地重新计算校验值，如果和发送端附在数据里的校验值不一致，就说明数据在传输中损坏了。**

#### UCIe 用的是什么 CRC？

规范 p91 第一段给出了多项式：

> The CRC generator polynomial is **(x+1)*(x¹⁵ + x + 1) = x¹⁶ + x¹⁵ + x² + 1**

这个多项式可以分解为两个因子：

**因子 1：x¹⁵ + x + 1 — 本原多项式**

这是一个"本原多项式"（primitive polynomial）。在 LFSR（线性反馈移位寄存器）理论中，基于本原多项式的 CRC 可以保证：**对于长度不超过 2¹⁵-1 = 32767 bit 的消息，检测到所有 2-bit 错误。**

**因子 2：x + 1 — 奇偶校验因子**

乘以 (x+1) 的效果是：整个 CRC 码字的奇偶性（1 的个数是奇数还是偶数）变成了偶数。这意味着：**任何奇数个 bit 错误必然破坏奇偶性，必然被检测到。**

两个因子叠加的效果：**检测所有 1-bit、2-bit、3-bit 的随机错误，以及所有奇数个 bit 错误。**

#### 为什么是 16-bit 而不是 32-bit？

PCIe 用 32-bit LCRC，UCIe 只用 16-bit。这不是 UCIe 偷工减料——而是物理环境不同。

CRC 的位数选择取决于两个因素：（1）消息长度，（2）预期的错误率。

在 UCIe 的场景下：
- 消息长度：128 字节 = 1024 bit（UCIe 固定以 128B 为 CRC 计算单位）
- 错误率：1e-27（低速）到 1e-15（高速）

16-bit CRC 有 2¹⁶ = 65536 种可能的 CRC 值。CRC 漏检的概率（即数据坏了但 CRC 碰巧也匹配）大约是 2⁻¹⁶ ≈ 1.5×10⁻⁵。在 BER=1e-15 的链路上，漏检发生的概率 = (1e-15 × 1024) × (1.5×10⁻⁵) ≈ **1.5×10⁻¹⁷**——这已经远低于任何工程系统的可接受阈值。

而且 UCIe 还有 Retry 机制——即使 CRC 漏检了，上层协议还有自己的端到端校验。所以 16-bit CRC 在封装内场景下是完全足够的。

#### CRC 总是按 128 字节计算

规范 p91 有一个重要的规定：

> The CRC is always computed over **128 bytes** of the message. For smaller messages, the message is zero extended in the MSB.

无论你的 Flit 是 68 字节还是 256 字节，CRC 始终以 128 字节为单位计算。这不是任意规定——**统一 128B 对齐意味着：硬件 CRC 计算器只需要一种工作模式，面积和延迟都可以优化到极致。**

规范还附带了 Verilog 参考代码（crc_gen.vs）作为 golden reference——这意味着实现者不需要自己推导 LFSR 结构，直接参照就行。

#### 🧠 为什么 CRC 初始值是 0x0000 而不是 0xFFFF？

很多通信协议（比如以太网 CRC-32）用全 1 作为初始值，目的是防止"消息开头有一串 0"导致 CRC 始终为 0。UCIe 选择 0x0000 作为初始值，因为 UCIe 的消息格式是固定的（Flit Header 开头一定有非零的 Protocol ID），不存在"全零数据流"的问题。用 0x0000 初始值简化了硬件复位逻辑。

---

### 1.2 Retry：数据错了怎么恢复？

规范 3.8 节（p92-94）定义了 UCIe 的 Retry 机制。这是适配器最复杂的部分。

#### Retry 的基本逻辑（如果你熟悉计算机网络，这就是一个"停等+滑动窗口"协议）

```
发送端                        接收端
  │                             │
  │── Flit (SeqNum=5) ────────→│  发送第 5 号 Flit
  │                             │  接收端计算 CRC...
  │                             │  CRC 不匹配！数据坏了
  │←── NAK (SeqNum=5) ────────│  接收端请求"重传 5 号"
  │                             │
  │── Flit (SeqNum=5) ────────→│  发送端重传
  │── Flit (SeqNum=6) ────────→│
  │                             │  CRC 正确
  │←── ACK (SeqNum=6) ────────│  确认到 6 号
```

但这个机制有几个关键参数需要考虑：
- 发送端必须保存已发送但未确认的 Flit（Tx Retry Buffer）
- 如果 ACK 丢了怎么办？（发送端会超时重传）
- 序列号能有多大？（决定 Retry Buffer 的大小）

#### UCIe 的 Retry 是 PCIe 6.0 Retry 的"精简版"

规范 p92 明确说了：

> The Retry scheme on UCIe is a **simplified version** of the Retry mechanism for Flit Mode defined in PCIe Base Specification.

**删掉了什么？为什么删？**

**1. Selective Nak（选择性重传）—— 删除**

PCIe 6.0 支持两种 Nak：Nak All（重传所有未确认 Flit）和 Selective Nak（只重传指定的某一个 Flit）。UCIe 只保留了 Nak All。

> Selective Nak and associated rules are **not applicable and must not be implemented.**

为什么？因为 Selective Nak 需要接收端维护 Rx Retry Buffer（保存已收到的后续 Flit，等丢失的那个补上后再重新排序）。这在 UCIe 上不值得——封装内出错概率极低，偶尔触发一次 Nak All 重传几十个 Flit 也无所谓，根本不需要费那么大劲做选择性重传。

**2. Rx Retry Buffer —— 随 Selective Nak 一起删除**

没有 Selective Nak，自然也不需要 Rx Retry Buffer。这省了一大块面积。

**3. 序列号从 10-bit 降到 8-bit**

> All 10-bit retry related counters are replaced with 8-bit counters, and the maximum-permitted sequence number is **255**.

为什么可以降价？因为 UCIe 的链路出错概率极低。PCIe 6.0（PAM4、PCB）可能同时堆积很多未确认 Flit，需要大序列号空间。UCIe 几乎不会有未确认 Flit 堆积，128 个就够用了（上限实际上设为 127）。

#### UCIe 的独有改动：ACK/NAK 必须交替

> Throughout the duration of Link operation, **Explicit Sequence number Flits and Ack/Nak Flits alternate**.

这是 UCIe 对 PCIe Retry 最重要的改动。在 PCIe 6.0 中，ACK/NAK 可以嵌在任何 Flit 的 DLP 字段里，和 Payload Flit 混合发送。UCIe 要求**每发送一个带序列号的 Flit，下一个必须是 ACK/NAK Flit**（除非没有待发送的 ACK/NAK）。

为什么这样设计？**更快 ACK 周转 → 更小的 Retry Buffer。** 发送端知道自己下一个就会收到 ACK/NAK（而不是要等不确定的时间），Retry Buffer 里的 Flit 很快就能被确认释放。

这其实是一个**用带宽换延迟和面积的取舍**：交替规则意味着一半的 Flit 可能是非 Payload 的，带宽利用率降低。但在封装内链路带宽极大（256 GB/s），这点开销无所谓——省下来的 Retry Buffer 面积更有价值。

#### 超时重传：REPLAY_TIMEOUT 的 UCIe 特殊规则

> In addition to incrementing REPLAY_TIMEOUT_FLIT_COUNT as described in PCIe Base Specification, **the count must also be incremented when in Active state and a Flit Time has elapsed since the last flit was sent.**

这是 UCIe 特有的。因为 UCIe 为了省电，空闲时**不发送连续 NOP Flit**（PCIe 6.0 空闲时是不停发 IDLE/NOP Flit 的）。如果不补这个规则，空闲期间 REPLAY_TIMEOUT 永远不会递增，ACK 丢失后就可能永远等不到重传。

当计数达到 **375** 时，触发 Replay Timer Timeout。

#### 序列号握手：每次 Re-train 后必须重做

> Sequence Number Handshake Phase must be performed on **every entry of the RDI to Active state** from Reset or Retrain.

这意味着：物理链路每次重新训练后，两端必须重新协商序列号起点。因为 Re-train 期间链路状态全部刷新，之前"ACK 到哪了"的信息已经不准确了。

128 个 Flit 内完不成握手 → 触发 Link Retrain。

#### 🧠 引申思考：Retry 的工程取舍哲学

UCIe 的 Retry 设计体现了一个重要的工程哲学：**在可靠性极高的物理环境下，可靠性机制应该尽可能简单。**

| 维度 | PCIe 6.0 Retry | UCIe Retry | 取舍逻辑 |
|------|---------------|-----------|---------|
| CRC 宽度 | 8 字节 | 2 字节 | 物理 BER 好 12 个数量级 → 用更短的 CRC |
| 错误频率 | 每分钟 | 每几年 | 出错极少 → 不需要优化重传效率 |
| Selective Nak | 需要 | 不需要 | 重传窗口小（<=127 Flit），全窗口重传足够 |
| ACK 频率 | 不定 | 必须交替 | 用带宽换延迟和面积 |
| 空闲行为 | 连续发 IDLE | 可以停止 | 省电但需要额外的超时机制 |

---

### 1.3 Runtime Parity：链路健康的"心率监测"

规范 3.9 节（p94-95）定义了一个很聪明的机制——它不做纠错，只做监测。

#### CRC 抓的是事故，Parity 看的是趋势

CRC 是"事故检测器"——Flit 坏了，检测到，触发 Retry，日志里记一笔。

Parity 是"健康监控器"——不管 Flit 有没有坏，每隔一段时间就检查一下比特错误率。让 SW 能回答："这条链路今天的 BER 是多少？它是不是在退化？"

#### 工作原理

适配器在**每 256×256×N 字节正常数据**之后，插入 **64×N 字节**的 Parity 信息。N 推荐设为 4（使得 Parity 也是 256B 的整数倍）。

```
正常数据 262,144B → Parity 256B → 正常数据 262,144B → ...
```

每个 Parity 字节只有 bit 0 含信息——它是一组数据字节的 XOR（奇偶校验）结果。如果链路中有奇数个 bit 翻转，Parity 会检测出来。

#### SW 参与的必要性

Parity 不是硬件自动使用的——它是给 SW 看的。SW 通过寄存器使能 Parity，触发 Link Retrain，在 Retrain 期间通过 Sideband 协商，之后每次进入 Active 后自动运行。

SW 可以周期性地读取 Parity 错误计数器，计算 BER，判断链路健康趋势。就像汽车的机油指示灯——不是用来紧急制动的，是用来告诉你"该保养了"。

#### 🧠 引申思考：Parity vs CRC vs FEC — 三层保护各有其用

```
FEC (Forward Error Correction) — 前向纠错
  ├── 在 UCIe 上：不采用（PCIe 6.0 用，因为 PAM4 BER 高）
  └── 代价：占用带宽（每 Flit 额外 6B）

CRC (Cyclic Redundancy Check) — 错误检测
  ├── 在 UCIe 上：2B CRC-16，适配器实现
  └── 代价：极小（每 128B 消息 2B 开销）

Parity — 健康监测
  ├── 在 UCIe 上：周期性插入，SW 采样
  └── 代价：极低（每 256KB 仅 256B 开销）
```

UCIe 的选择是"CRC + Parity"，不选 FEC。因为 FEC 是为 BER ~1e-6 的环境设计的（PCIe 6.0 PAM4），到了 BER ~1e-27 的 UCIe 环境就是纯粹的浪费。

---

## 第二讲：Flit — 适配器的"送货包裹"

理解了适配器怎么保证可靠性之后，我们来看它到底在线上传什么东西。

### 2.1 为什么需要这么多 Flit 格式？

第 2 章讲了协议层支持哪些协议和格式组合。第 3 章 3.3 节（p70-87）把这些格式的**字节级布局**全部画了出来。

在 UCIe 里，适配器和协议层之间传递的是数据（64B 或 256B），适配器在数据前后加上自己的 Header 和 CRC 之后发到物理层。不同协议需要不同的 Header 格式，不同场景需要不同的效率/延迟取舍——这就是多种 Flit 格式的来源。

规范定义了 6 种格式，但本质上可以归为三类：

**类别 1：Raw（格式 1）— 适配器透明模式**

> Raw Format can only be used for scenarios in which Retry support from the Adapter is not required. If Raw Format is negotiated, the Adapter transfers data from Protocol Layer to Physical Layer **without any modification**.

适配器什么都不加，数据原封不动透传。什么时候用？当数据自带 CRC/FEC（比如 PCIe 6.0 原生 Flit 通过 Retimer 传输），或者链路的 Raw BER 已经低到不需要额外保护时。

**类别 2：68B Flit（格式 2）— 最小可行格式**

这是我们详细讲的第一个格式。适配器从协议层收 64B → 加 2B Header + 2B CRC → 发给物理层。总共 68 字节。

它是所有 PCIe/CXL 实现的"最大公约数"——规范要求：只要你说你支持 PCIe 或 CXL，就必须支持 68B Flit Format。

**类别 3：256B Flit（格式 3/4/5/6）— 高性能格式**

256 字节的标准 Flit，和 PCIe 6.0 / CXL 3.0 的原生格式对齐。又分：
- **Standard (格式 3/4)**：和 PCIe/CXL 规范定义的格式完全一致。互操作的基线。
- **Latency-Optimized (格式 5/6)**：UCIe 的"秘密武器"，让接收端在 128B 边界就开始处理，延迟减半。

### 2.2 深入 68B Flit：适配器加了什么？

规范 3.3.2 节（p70-73）详细定义了 68B Flit。适配器插入的 2 字节 Header 长这样：

**无 Retry 的 Header（Table 3-2）**：
```
Byte 0:
  [7:6] Protocol ID: 00=NOP/PDS, 01=CXL.io, 10=CXL.cachemem, 11=ARB/MUX
  [5]   Stack ID: 0=Stack0, 1=Stack1
  [4]   0=Regular Flit, 1=PDS (数据流暂停)
  [3:0] Reserved
Byte 1:
  [7]   0=Regular Flit, 1=PDS
  [6:0] Reserved
```

**有 Retry 的 Header（Table 3-3）**：Byte 0[3:0] 变为 Sequence Number 的高 4 位，Byte 1[5:4] 编码 ACK/NAK 信息，Byte 1[3:0] 为 Sequence Number 低 4 位。

**关键观察**：Protocol ID 字段（2 bit）只能区分 4 种协议——NOP/PDS、CXL.io、CXL.cachemem、ARB/MUX。这就是 Flit Header 的全部"协议感知"——适配器不需要理解 CXL.cache 和 CXL.mem 的区别，它们都走 CXL.cachemem 的 Protocol ID。

### 2.3 PDS（数据流暂停）：68B Flit 的"不定长"问题

68B Flit 有一个麻烦：**4 个连续 68B Flit = 272B ≠ 256B 的整数倍**。这意味着数据流和物理层的 256B 边界不对齐——如果不处理，接收端的 Flit 字节移位会越积越偏。

规范 3.3.2.1 节（p72）定义了一个精巧的解决方案：**Pause of Data Stream (PDS)**。

当没有 Flit 要发（或者需要重对齐）时，适配器插入一个特殊的 PDS Flit Header，后面填充 0 直到下一个 256B 边界。恢复传输时，第一个 Flit 从 256B 对齐的位置开始。

> The Transmitter of PDS drives the following on the Flit header: Bit [4] of Byte 0 as 1, Bit [7] of Byte 1 as 1, Bit [6] of Byte 1 as 1

为什么用 2/3/4 个条件来识别 PDS？规范在 Implementation Note（p73）中解释了——这是防 bit 错误的：

> PDS Flit Header aliasing to a regular Flit Header: Checking for **two out of the four conditions** guarantees that at least three bit errors must occur within the two bytes of the PDS Flit Header for it to alias to a regular Flit Header.

即使是 PDS 这种"辅助信号"，也考虑到了 bit 错误可能导致它被误解为普通 Flit Header。

### 2.4 256B Flit：与 PCIe/CXL 的对齐

256B Flit（格式 3/4/5/6）的设计目标是**和 PCIe 6.0 / CXL 3.0 的原生 Flit 格式保持兼容**。适配器仍然插入自己的 Header 和 CRC，但协议层可以看到的大部分字节布局和 PCIe/CXL 规范定义的完全一样。

**但有一个关键差异**：DLLP（Data Link Layer Payload）的处理。

在 PCIe 6.0 中，DLP 字节（DLP0-5）由 Data Link Layer 填充，包含 Flit Sequence Number、ACK/NAK 命令、Credit Update 等。

在 UCIe 中：

> DLP0 and DLP1 are replaced with the Flit Header for UCIe and are driven by UCIe Adapter.

DLP0/DLP1 被适配器替换成了 UCIe 的 Flit Header。适配器还负责：
- 从协议层收 Update_FC（流控更新）→ 格式化为 Optimized_Update_FC → 填入 DLP 字节
- 在接收端提取 DLLP → 通过 FDI 的专用接口交给协议层

**本质上是：适配器接管了 PCIe DLL 层的"链路管理"功能（Sequence Number、ACK/NAK），但保留了"流控"功能（Update_FC）的通道。**

---

### 🧠 引申思考：为什么有 Format 5 和 Format 6 两种延迟优化格式？

Format 5（Latency-Optimized 256B）把 Flit 按 128B 边界组织，让接收端可以在收到前半时就启动处理。Format 6 在 Format 5 的基础上加了 Optional Bytes——给 CXL 多了 14B H-slot，给 CXL.io 多了 4B TLP 空间。

为什么分开而不是只做一种？因为 Optional Bytes 需要两端都支持，属于"高级功能"。Format 5 更通用——任何支持 CXL 3.0 Latency-Optimized 格式的设备都能用。这又是"最大兼容性"vs"最优性能"的取舍。

---

## 第三讲：链路的生命——从复位到休眠

有了 CRC（检错）、Retry（纠错）、Flit 格式（打包），接下来我们需要理解的是：**链路怎么从断电状态一步步走到可以传输数据的状态？**

这是规范 3.2 节（p60-69）的内容——适配器最核心的流程。

### 3.1 四阶段初始化：一个军事比喻

想象两支军队（两个 Die）需要在一条河的两岸建立通信。他们各自先整队（Stage 0），然后派侦察兵在河面上拉一根细绳（Stage 1，Sideband），再架设一座桥（Stage 2，Mainband 训练），最后两边指挥官坐下来对表——确认用哪种密码、哪种信号（Stage 3，参数交换）。

规范 Figure 3-3（p60）画的就是这个流程。重要的是**Stage 0 是两侧各自独立进行的**——规范特意把两个 Die 的 Stage 0 框画成不同大小，"to denote that different die can take different amount of time to finish Stage 0"。

### 3.2 参数交换：两个陌生人的对话

Stage 3 的 Part 2（3.2.1.2, p61-69）是适配器设计中最"智能"的部分——两端通过交换能力表来决定用什么协议、什么格式。

#### 谁说"我想要什么"？— AdvCap.Adapter

规范 Table 3-1（p61-63）列出了所有需要协商的参数。这个概念很简单：

- 每端列出自己**能做什么**：支持的协议（PCIe/CXL/Streaming）、支持的 Flit 格式（68B/256B Standard/256B LatOpt）、Retry 能力、多栈能力...
- 通过 Sideband 消息 **{AdvCap.Adapter}** 发给对方

#### 谁说"就这么定了"？— FinCap.Adapter

**适配器取两端能力交集**。如果两边都支持 PCIe Flit Mode，就协商为 PCIe Flit Mode。如果一边支持 CXL 256B、另一边不支持，那就只能降到两边都支持的（比如 CXL 68B）。

> Final determination for Protocol parameters: If "68B Flit Mode" is advertised by **both** Link partners, it is set to 1 in the {FinCap.Adapter} message.

这本质上是**取交集**——最低共同能力决定最终配置。

#### 上下行端口的不对称性

规范定义了一个有趣的不对称：对于 PCIe/CXL 协议，**Upstream Port（UP）先等 Downstream Port（DP）发能力，然后基于 DP 的能力调整自己的广告能力，最后再发自己的**。

> the Upstream Port (UP) Adapter must **wait for the first {AdvCap.Adapter} message** from the Downstream Port (DP) Adapter, review the capabilities advertised by DP and **then** send its own.

这是一个"DP 先说，UP 决定"的模式。DP 先摊牌，UP 看了 DP 的牌之后决定怎么回应。这模仿了 PCIe 的 LTSSM 中 Downstream/Upstream 的不对称角色。

对于 Streaming 协议，没有 DP/UP 之分——两端独立发送能力，交集就是最终配置。**Streaming 是对等的，PCIe/CXL 是有主从的。**

#### 超时保护：8ms 必须完成

> The Adapter must implement a timeout of **8 ms** (-0%/+50%) for successful Parameter Exchange completion.

如果 8ms 内参数交换没完成 → 适配器把 RDI 带到 LinkError 状态。这防止了两端永远在等待对方回复的死锁。

Retimer 场景下的额外规则：Retimer 必须和远程 Retimer 完成协商后才能回复本地的 Die。期间必须每 4ms 发一次 **Stall** 消息——"我在忙，别超时"——防止本地 Die 的 8ms 定时器到期。

### 3.3 状态机层次：UCIe 的"指挥链"

规范 3.5 节（p88-89）定义了我认为是 UCIe 最精妙的设计之一——**三层状态机的层次化协调**。

#### 为什么需要层次化？

因为 UCIe 有三个利益相关方：
1. **协议层**——关心"我在传数据还是休眠了"（vLSM / Adapter LSM）
2. **适配器**——关心"链路状态正常吗、需要重训练吗"（Adapter LSM）
3. **物理层**——关心"电气信号对吗、Lane 坏了吗"（RDI SM）

如果它们各自独立管理自己的状态，就会出现"协议层在发数据，但物理层正在重训练"的混乱。

#### 层次结构

```
CXL 协议：                       PCIe/Streaming 协议：
┌──────────┐ ┌──────────┐        ┌──────────────┐
│  vLSM    │ │  vLSM    │        │  Adapter LSM │  ← 协议视角
│(CXL.io)  │ │(CXL.cmem)│        └──────┬───────┘
└────┬─────┘ └────┬─────┘        ┌──────┴───────┐
     └──────┬──────┘              │   RDI SM     │  ← 物理视角
     ┌──────┴──────┐              └──────────────┘
     │ Adapter LSM │
     └──────┬──────┘
     ┌──────┴──────┐
     │   RDI SM    │
     └─────────────┘
```

CXL 有三层（因为 CXL 的 ARB/MUX 引入了额外的虚拟链路概念），PCIe/Streaming 只有两层。

#### 状态转移的方向性

规范 p88-89 定义了严格的状态传播规则。这不是任意的——每一条规则都有物理或逻辑上的必要性。

**Active（激活）：自底向上**

> RDI SM must be in Active before Adapter LSM can begin negotiation to transition to Active. Adapter LSM must be in Active before vLSMs can begin negotiations to transition to Active.

为什么？因为 Active 意味着"可以传输数据"。物理层必须先确保电气通道就绪，适配器才敢把数据流交给它；适配器必须先确保逻辑通道就绪（序列号握手完成），协议层才敢开始发 Flit。

**PM（休眠）：自顶向下**

> Both CXL.io and CXL.cachemem vLSMs (if CXL), must transition to PM before the corresponding Adapter LSM can transition to PM. All Adapter LSMs must be in PM before RDI SM is transitioned to PM.

为什么方向反过来了？因为 PM 意味着"停止传输"。协议层必须先停发数据（清空 Retry Buffer），适配器才能停；适配器停了，物理层才能断电。**如果物理层先断电而协议层还在发数据，数据就丢了。**

**Retrain（重训练）：强制广播**

> RDI SM must be in Retrain before propagating Retrain to Adapter LSMs. If RDI SM is in Retrain, Retrain must be propagated to **all** Adapter LSMs that are in Active state.

物理层出问题（比如 Lane 坏了需要修复）→ 重训练 → 这影响所有人。适配器不能选择性通知——只要在 Active 状态，就必须收到 Retrain 通知。而且适配器必须等所有相关 Adapter LSM 都到达 Retrain 了，才能让 RDI 退出 Retrain。

**LinkError（链路错误）：最高优先级**

> LinkError transition takes priority over LinkReset or Disabled transitions.

无论当前在什么状态，一旦检测到 LinkError，必须优先处理。而且 LinkError 也是自底向上的——物理层检测到错误 → RDI SM 进入 LinkError → 传播到 Adapter LSM → 传播到 vLSM。

#### 🧠 引申思考：这些规则的底层原理是什么？

这本质上是一个**依赖图（Dependency Graph）**的管理问题。

```
依赖关系：
  vLSM.Active      依赖  Adapter_LSM.Active
  Adapter_LSM.Active  依赖  RDI_SM.Active
  RDI_SM.PM         依赖  Adapter_LSM.PM
  Adapter_LSM.PM    依赖  vLSM.PM
```

Active 是"能力提供"，所以依赖方向是 **下层提供能力给上层**（自底向上）。
PM 是"安全停止"，所以依赖方向是 **上层先停止，下层才能停下来**（自顶向下）。

这是一个**非对称的依赖关系**——同一个状态（Active vs PM），依赖方向完全相反。不是因为随意设计，而是因为这两个状态有本质不同的语义：**Active 是"赋能"，PM 是"约束"。赋能从底层开始，约束从顶层开始。**

---

### 3.4 功耗管理：L1 和 L2

规范 3.6 节（p89-91）在状态机层次的基础上，定义了具体的 PM 流程。

L1 和 L2 的区别在物理层实现上（第 4/5 章），适配器这层只需知道：
- L1 = 浅度睡眠，快速恢复
- L2 = 深度睡眠，恢复较慢

**PM 进入流程**（Figure 3-28, p90）：

```
1. vLSM PM entry — CXL 通过 ALMP 在 Mainband 上协商
   (PCIe/Streaming: 协议层基于空闲时间请求 PM)
2. Adapter LSM PM entry — 通过 Sideband 与远程协调
3. RDI PM entry — 所有 Adapter LSM 都 PM 之后
4. Physical Layer PM — Sideband 保持 Active！
```

**为什么 Sideband 必须保持 Active？** 因为唤醒信号通过 Sideband 发送。如果 Sideband 也关电，链路就永远醒不来了。这就是为什么 Sideband 逻辑必须在"Always-On"电源域。

---

## 第四讲：多协议复用

规范 3.1 节（p57-58）是放在最前面的——我现在才讲，是因为需要前面 CRC/Retry/Flit/状态机的全部知识才能理解它为什么这样设计。

### 4.1 核心问题：一条物理链路怎么跑两个协议？

假设你有一条 x64 @ 32 GT/s = 256 GB/s 的 UCIe 链路，但你的 PCIe 协议层只需要 128 GB/s（相当于传统 x16 PCIe 5.0）。链路浪费了一半带宽。解决办法：**在这条链路上再跑一个协议栈。**

但怎么做到？两个栈不能同时发 Flit——物理层一次只能传一个 Flit。适配器需要**仲裁**。

### 4.2 两种模式

| | Multi_Protocol_Enable | Enhanced Multi_Protocol_Enable |
|---|---|---|
| 两个栈的协议 | **必须相同** | **可以不同** |
| 带宽分配 | 各 50%（隐式） | **可配置**：100% 或 50% |
| 仲裁方式 | 禁止连续 Flit | 轮询（100%）或禁止连续 Flit（50%） |
| 用途 | 同协议两实例 | 异协议混合（如 PCIe+Streaming） |

**Multi_Protocol_Enable** 的设计动机在规范的 Implementation Note 中说了：

> The primary motivation is to allow implementations to take advantage of the higher bandwidth provided by the UCIe Link for lower-bandwidth individual Protocol Layers.

翻译：你有一个超快的链路（256 GB/s），但你的协议栈只能吃下 128 GB/s。那就跑两个栈，充分利用带宽。

### 4.3 NOP Flit：仲裁的"填充物"

适配器通过插入 NOP Flit 来保证**不连续发送同一栈的 Flit**：

> Adapter is permitted to insert NOP Flits to guarantee this (these Flits bypass the Tx Retry buffer, and are **not forwarded** to the Protocol Layer on the receiver).

NOP Flit 有三个关键属性：
1. 它旁路 Retry Buffer（NOP 不需要重传——它本来就是"空"的）
2. 接收端不转发给协议层（协议层完全感知不到 NOP）
3. Protocol ID = D2D Adapter（`2'b00`），Flit body 全是 0

**NOP Flit 是适配器内部的"隐身填充物"。**

### 4.4 为什么 Raw Format 和 Multi-Protocol 互斥？

> Multi_Protocol_Enable and Raw Format are **mutually exclusive**.

因为 Raw Format 下，适配器不插手数据——没有 Flit Header，没有 Protocol ID 字段，没有 Stack Identifier。适配器根本无法区分"这个 Flit 是给 Stack 0 还是 Stack 1 的"。**多协议复用需要适配器能识别和标记每个 Flit——这只有在适配器主动插入 Header 的模式下才能做。**

---

## 全章回顾：适配器的"精简哲学"

第三章从头到尾贯穿着同一种设计哲学：**在保证可靠性的前提下，做到极致的精简。**

| 设计决策 | 精简了什么 | 凭什么敢精简 |
|---------|-----------|------------|
| CRC-16 而非 CRC-32 | 6 字节/128B | 封装内 BER 极低 |
| 去 Selective Nak | Rx Retry Buffer 全部逻辑 | 重传极少，全窗口重传足够 |
| 序列号 8-bit 而非 10-bit | 计数器和比较器位宽 | 127 个未确认 Flit 上限足够 |
| ACK/NAK 强制交替 | Retry Buffer 深度 | 链路带宽充裕 |
| 空闲时停止发 NOP | 功耗 | Retry timeout 额外规则补偿 |

**适配器的"灵魂"不在于它做了什么——而在于它敢不做什么。**

---

这就是第三章的全貌。我们现在可以讨论你读完后的问题了。
