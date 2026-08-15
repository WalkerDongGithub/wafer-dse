# 第二章：协议层（Protocol Layer）— 讲义

> 对应文档：UCIe Specification 2.0, Chapter 2.0, p49-55（约7页）
> 定位：理解不同上层协议如何映射到 UCIe 的 Flit 传输格式上

---

## 2.0 协议层概述：核心认知

### 2.0.1 协议层做什么？不做什么？

规范 p49 第一段就给出了关键的原则：

> Protocol-related features are **kept separate from Flit Formats and packetization**. This is because UCIe provides different transport mechanisms that are **not necessarily tied to protocol features**.

翻译：
- **协议层**：负责事务层及以上的协议语义（比如 CXL.cache 的缓存一致性消息、PCIe 的 TLP 格式）
- **Flit 格式**：负责"怎么包装这些内容以便传输"——这是 UCIe 自己的传输机制
- 两者**解耦**——同一个协议可以用不同的 Flit 格式传输

**类比**：
- 协议层 = 你写的信的内容（中文、英文、法语都可以）
- Flit 格式 = 信封的尺寸和格式（标准信封、航空信封）
- UCIe 适配器 = 邮局——它不关心你写的什么语言，只管按信封格式寄送

### 2.0.2 关键术语（规范明确定义，必须记住）

规范 p49 定义了 4 个协议模式术语，它们**不是 UCIe 发明的，而是引用 PCIe/CXL 规范的**：

| 术语 | 来源规范 | 含义 |
|------|---------|------|
| **PCIe Flit Mode** | PCIe Base Spec 6.0+ | PCIe 6.0 引入的新传输模式，使用 Flit 作为基本传输单元 |
| **PCIe non-Flit Mode** | PCIe Base Spec（所有版本） | 传统的 PCIe 传输——使用 TLP/DLLP，不是 Flit |
| **CXL 68B Flit Mode** | CXL Spec（1.0/2.0/3.0） | CXL 使用 68 字节 Flit 的传输模式 |
| **CXL 256B Flit Mode** | CXL Spec 3.0+ | CXL 3.0 引入的 256 字节 Flit 传输模式 |

### 2.0.3 UCIe 上的 6 种协议映射

规范列出了可在 UCIe Mainband 上传输的协议：

| 协议映射 | 必选/可选 | 关键约束 |
|---------|----------|---------|
| **PCIe Flit Mode** | 可选 | 需要 PCIe 6.0+ 协议层 |
| **CXL 68B Flit Mode** | — | CXL.io/CXL.cache/CXL.mem 各自独立协商 |
| **CXL 256B Flit Mode** | — | CXL 3.0+ 协议层 |
| **Streaming Protocol** | 默认（如果不选 PCIe/CXL） | 用户自定义协议 |
| **Management Transport** | 可选 | 管理数据包传输 |
| **PCIe non-Flit Mode** | 见下文 | ⚠️ 不是直接映射，而是通过 CXL.io 68B Flit Format 传输！ |

### 2.0.4 互操作性要求（硬性规则）

规范 p49 底部给了三条铁律：

**规则 1**：
> A Protocol Layer **must** support PCIe non-Flit mode if it is advertising the 68B Flit Mode parameter.

→ 如果你告诉对方"我支持 68B Flit Mode"，你必须同时支持 PCIe non-Flit Mode。因为 68B Flit Format 是从 CXL 借过来的，而 PCIe non-Flit Mode 也需要用这个格式传输。

**规则 2**：
> If a Protocol Layer supports CXL 256B Flit Mode, it **must** support PCIe Flit Mode and 68B Flit Mode as defined in CXL Specification for CXL.io protocol.

→ CXL 256B Flit Mode 是一个"高级"模式，但你必须向下兼容 PCIe Flit Mode 和 68B Flit Mode。这保证了基础互操作性。

**规则 3**：
> A Protocol Layer advertising CXL is permitted to **only** support CXL 68B Flit Mode without supporting CXL 256B Flit Mode or PCIe Flit Mode.

→ 你可以做一个"最小化 CXL 实现"——只支持 68B Flit Mode。这是一种低成本的兼容性方案。

### 2.0.5 规范版本到协议模式映射

Table 2-1（p50）是理解"什么规范对应什么协议"的关键：

| 你的设计支持的规范 | PCIe non-Flit | CXL 68B Flit | CXL 256B Flit | PCIe Flit |
|---|---|---|---|---|
| **PCIe** | **必选** | 不适用 | 不适用 | 可选 |
| **CXL 2.0** | **CXL.io 必选** | **必选** | 不适用 | 不适用 |
| **CXL 3.0** | **CXL.io 必选** | **必选** | **必选** | **CXL.io 必选** |

> 重点：CXL 3.0 的 CXL.io 在 PCIe Flit Mode 下是必选的。这意味着 CXL 3.0 设备必须同时支持传统 PCIe Flit Mode 和 CXL 256B Flit Mode。

### 2.0.6 Flit 格式图例（Figure 2-1）— 读懂所有 Flit 图的前提

```
Color Shading    Description
─────────────────────────────────────────
██ 浅橙色       Some bits populated by Protocol Layer, some by Adapter
██ 深橙色       All bits populated by Adapter
██ 白色         All bits populated by Protocol Layer
```

**这是读懂第 2 章和第 3 章所有 Flit 格式图的基础。** 每一张 Flit 字节图中，你都能看到这三种颜色，它们告诉你"这个字节是谁填的"。

---

## 2.1 PCIe 协议在 UCIe 上的 5 种操作格式（p50-52）

### 核心信息

**PCIe 有两种协议模式**，在 UCIe 上有 5 种操作格式：

```
PCIe 协议
├── PCIe non-Flit Mode（传统 PCIe）
│   └── 通过 CXL.io 68B Flit Format 传输 ← 只有这一种格式！
│
└── PCIe Flit Mode（PCIe 6.0 引入）
    ├── Raw Format
    ├── Standard 256B End Header Flit Format
    ├── 68B Flit Format（这里只用作 PCIe 非标准的 68B 格式）
    ├── Standard 256B Start Header Flit Format
    └── Latency-Optimized 256B with Optional Bytes Flit Format
```

### 2.1.1 Raw Format（PCIe 的 Raw 格式）

**必选/可选**：可选

**所有字节由协议层填充**。适配器不插手 CRC/Retry。

**目的**：给 UCIe Retimer 用——当 CPU 和 I/O 设备在不同机箱，通过 Retimer 连接时，协议层（PCIe 6.0）自带的 FEC+CRC 已经足够。

**规范强烈建议**：Retimer 要利用 PCIe Flit Mode 自带的 6B FEC parity 或 8B CRC 来做错误统计，帮助诊断外部互连的质量。

### 2.1.2 Standard 256B End Header Flit Format（PCIe 标准格式）

**必选/可选**：支持 PCIe Flit Mode 时必选

这是 PCIe Base Spec 定义的标准 Flit 格式。支持它的主要动机是**互操作性**——有些厂商只实现了标准格式。

**关键要求**：
- 协议层在 Adapter 保留字段填 0
- **PM DLLP 和 Link Management DLLP 在 UCIe 上不使用**（因为 UCIe 有自己的功耗管理和链路管理机制）
- 其他 DLLP 和 Flit Status 按 PCIe 规范原样工作

**规范强烈建议**：在协议层设计中优化掉 8b/10b、128b/130b 编码、non-Flit Mode 的 CRC/Retry 逻辑——因为在 UCIe 上这些都没用了，留着浪费面积和功耗。

> ⚠️ **为什么 UCIe 不用 PM 和 Link Management DLLP？**
> 因为 UCIe 的 D2D Adapter 有自己的链路状态管理和功耗管理。PCIe 的 PM DLLP 是为 PCIe 链路设计的——但 UCIe 链路不是 PCIe 链路。UCIe 只是借用了 PCIe 的事务层（TLP），链路层由 UCIe 自己接管。

### 2.1.3 68B Flit Format（PCIe 的 68B 格式）

**必选/可选**：PCIe 或 CXL 协议支持时必选

这是**PCIe non-Flit Mode 的唯一传输方式**。传输机制复用的是 CXL.io 的 68B Flit Format。

**关键理解**——这个格式下，协议层的许多字段被"架空"了：
- LCRC 字节 → 发送端填 0，接收端忽略
- ACK/NAK DLLP → 不使用（因为 UCIe Adapter 做 Retry）
- Sequence Number、DLLP CRC、Frame CRC 等 → 建议发送端填 0，接收端忽略
- 如果检测到 Framing Error → 说明存在内部不可纠正错误（因为 UCIe Adapter 已保证可靠传输）

**本质上**：68B Flit Mode 下，协议层的可靠性机制（CRC、Retry、ACK/NAK）全部被 UCIe Adapter 取代了。协议层只需要处理事务层的内容。

### 2.1.4 Standard 256B Start Header Flit Format

**必选/可选**：可选（需要单独的能力位支持）

这是 256B Flit 的另一个变体——带 Start Header。大多数设计要求和对 End Header 格式相同。

### 2.1.5 Latency-Optimized 256B with Optional Bytes Flit Format

**必选/可选**：可选（需要单独的能力位支持）

延迟优化的 Flit 格式——这是 UCIe 专门为**降低延迟**设计的格式。

**为什么叫"Latency-Optimized"？**
传统 PCIe 6.0 的 256B Flit 需要收齐整个 256 字节才能开始处理。Latency-Optimized 格式把 Flit 内部组织成可以"边收边处理"的结构——这在第 3 章会展开。

**同样要求**：PM 和 Link Management DLLP 不使用，其他 DLLP 和 Flit Status 按 PCIe 规范处理。

---

## 2.2 CXL 256B Flit Mode（p52-53）

CXL 256B Flit Mode 有 4 种操作格式。

### 核心差异：新增了 Adapter 插入的字节

规范强调 CXL 格式中的**浅橙色字节由 Adapter 插入**。在发送端协议层必须填 0，接收端必须忽略。

### 2.2.1 Raw Format（CXL 256B 的 Raw）

**可选**，所有字节由协议层填充。

和 PCIe Raw Format 类似，用于 Retimer 场景。规范建议 Retimer 根据协商的 Flit Format，用 6B FEC parity / 8B CRC / 6B CRC 做错误统计。

⚠️ **CXL 特有要求**：CXL.cachemem 的 Viral/Poison containment 必须在协议层处理。

### 2.2.2 Latency-Optimized 256B Flit Formats（强烈推荐！）

规范**强烈推荐**在 CXL 256B Flit Mode 下使用此格式。

**两个变体**：
- **格式 1**：标准延迟优化（和 CXL 规范定义一致）
- **格式 2**：更高打包效率——给协议层额外字节
  - CXL.io：额外 4B TLP 信息
  - CXL.cachemem：额外 **14B H-slot**（插在 Slot 7 和 8 之间，属于 Group B 和 C）

**延迟优势**：
> The Latency-Optimized formats enable the Protocol Layer to consume the Flit at **128B boundary**, reducing the accumulation latency significantly.

传统 256B Flit 要等 256 字节全部收完才能开始处理。延迟优化格式在 128B 边界就可以开始消费，延迟减半。

**CXL 256B 模式下的额外规则**：
- ACK/NAK/PM/Link Management DLLP **不用于 CXL.io**（UCIe 自己做）
- 其他 DLLP 和 Flit_Marker 按 CXL 规范
- 协议层驱动 DLP 字节中与 Flit_Marker 相关的部分

**CXL.cachemem 的 Viral Containment**：
> FDI provides an `lp_corrupt_crc` signal to help optimize for latency while guaranteeing Viral containment.

这是 CXL 的一个关键故障隔离机制——通过硬件信号传递 CRC 损坏信息，而不是等待协议层超时。第 10 章有详细接口规则。

### 2.2.3 Standard 256B Start Header Flit Format（CXL 标准格式）

**必选**（当 CXL 256B Flit Mode 支持时）

和 CXL 规范定义的标准格式一致。支持它的主要动机：**和只支持标准格式的厂商互通**。

CXL.cachemem 同样使用 `lp_corrupt_crc` 信号优化 Viral containment。

---

## 2.3 CXL 68B Flit Mode（p53-54）

CXL 68B Flit Mode 有 2 种操作格式。

### 2.3.1 Raw Format

**可选**，所有字节由协议层填充。Retimer 场景用。

### 2.3.2 68B Flit Format（基线格式）

**必选**（当 CXL 68B Flit Mode 协商时）

**工作流程**：
```
发送端：
  协议层 → FDI → 64B 数据（不含 Protocol ID 和 CRC）
  适配器 → 插入 2B Flit Header + 2B CRC + 字节移位 → 68B Flit → 物理层

接收端：
  物理层 → 68B Flit → 适配器 → 剥离 Header + CRC → 64B → FDI → 协议层
```

**关键规则**（与 PCIe 68B 类似但更详细）：
- ACK/NAK/PM DLLP 不用于 CXL.io
- Credit 更新和其他 DLLP 按 CXL 规范在 Flit 中传输
- LCRC → 填 0，接收端忽略（适配器做 CRC/Retry）
- Protocol Layer 的 Retry 逻辑 → 不实现

**CXL.cachemem 特有规则**：
- CXL 定义的 "Ak" 字段 → **保留（不使用）**
- Retry Flits → **不使用**
- 链路初始化 → 不等收到的 Flit，直接发送 INIT.Param Flit
- Viral containment → **协议层自己处理**

**重要：为什么 68B Flit Mode 下的 Viral 和 256B 不同？**

规范解释了（p54）：
> CXL-defined Retry Flits (which carry the viral notification for 68B Flits in CXL) **are not used in 68B Flit mode in UCIe**

在原生 CXL 中，Viral（病毒式错误通知）是通过 Retry Flits 携带的。但 UCIe 的 68B Flit Mode 不使用 Retry Flits（因为适配器做 Retry），所以 Viral 的通道断了。

**替代方案**：规范建议依赖 **Error Isolation**（CXL 3.0 引入的机制），而不是传统 Viral。Error Isolation 更精细——Viral 需要整个主机复位，Error Isolation 只需复位虚拟层级中出错的那一部分。

---

## 2.4 Streaming Protocol（流式协议）（p54-55）

### 2.4.0 定位

**Streaming 是"默认协议"**：
> This is the **default protocol** that must be advertised if none of the PCIe or CXL protocols are going to be advertised.

如果你既不是 PCIe 也不是 CXL，你就属于 Streaming。Streaming 支持 5 种操作格式。

**Streaming Flit Format Capability** 是一个大"开关"——如果它关闭，只能用 Raw Format 或厂商自定义扩展。

### 2.4.1 Raw Format（Streaming Raw）

**必选**（当 Adapter 支持 Streaming 时）。

协议层互操作性由**厂商定义**（vendor defined）。所有字节由协议层填充。

→ 这给了最大灵活性——你可以定义完全私有的协议，UCIe 只是一个"透明搬运工"。

### 2.4.2 68B Flit Format（Streaming 68B）

**可选**（需要 Streaming Flit Format Capability 支持）。

和 CXL 68B 一样：协议层给 64B，适配器插 2B Header + 2B CRC。

**这是最有用的模式之一**——你可以用 68B 格式传任何东西（自研协议、DDR 流量、NoC 消息……），同时享受 UCIe 的 Retry/CRC 可靠性保障。

### 2.4.3 Standard 256B Flit Formats

**可选**，支持 Start Header 或 End Header 两种格式。

协议层给 256B，适配器填 Header 和 CRC。

### 2.4.4 Latency-Optimized 256B Flit Formats

**可选**，分"带 Optional Bytes"和"不带 Optional Bytes"两种。

---

## 2.5 Management Transport Protocol（管理传输协议）（p55）

用于在 Mainband 上传送管理网络数据包。

**约束**：68B Flit Format **不允许**用于管理传输协议。只能用 Raw 或任何 256B Flit Format。

**工作方式**：协议层给 256B，适配器填 Header + CRC。接收端 Management Port Gateway 忽略 Adapter 保留的位。

**详细映射**见 8.2.5.2.3 节——这里只是协议层的概述。

---

## 第 2 章核心总结

### 一张图看清全貌

```
协议        Flit 格式                  适配器参与程度
─────────────────────────────────────────────────
PCIe ────→ Raw                      适配器不插手
      ├──→ Standard 256B (End/Start) 适配器填 Header+CRC
      ├──→ 68B                      适配器填 Header+CRC
      └──→ LatOpt 256B+OptBytes     适配器填 Header+CRC

CXL  ────→ Raw                      适配器不插手
  256B├──→ LatOpt 256B (两种)       适配器填 Header+CRC
      └──→ Standard 256B Start      适配器填 Header+CRC

CXL  ────→ Raw                      适配器不插手
  68B └──→ 68B Baseline             适配器填 Header+CRC

Streaming→ Raw (必选)               适配器不插手
      ├──→ 68B (可选)               适配器填 Header+CRC
      ├──→ Standard 256B (可选)     适配器填 Header+CRC
      └──→ LatOpt 256B (可选)       适配器填 Header+CRC

Mgmt  ────→ Raw / 256B (不能用68B)  适配器填 Header+CRC
```

### 5 个核心概念

1. **Flit 格式 ≠ 协议**：同一个协议可以用多种 Flit 格式，同一种 Flit 格式可以承载多种协议。规范刻意解耦。

2. **Raw Format = 适配器不插手**：协议层自己负责可靠传输。其余格式 = 适配器做 CRC/Retry。

3. **UCIe 架空了很多 PCIe/CXL 的链路层机制**：PM DLLP、Link Management DLLP、ACK/NAK 在 UCIe 上都不使用——因为 UCIe 的适配器和物理层有自己的一套。

4. **Streaming = 万能接口**：不懂 PCIe/CXL 也没关系，你可以在 Streaming 模式下传任意自定义协议。

5. **68B Flit Format 是最基础的必选格式**：如果你说"我支持 PCIe 或 CXL"，那你必须支持 68B Flit Format。这是因为 68B Flit Format 来自 CXL 2.0，是最多厂商支持的基线模式。

---

## 讨论问题

1. PCIe non-Flit Mode 在 UCIe 上通过 CXL.io 68B Flit Format 传输——这背后是什么设计考量？为什么不直接映射 PCIe non-Flit 的原生格式？

2. Streaming Protocol 和 Raw Format 在"协议层互操作性"上有什么区别？什么时候选 Streaming，什么时候选 Raw？

3. 为什么 Management Transport Protocol 不能用 68B Flit Format？

4. CXL.cachemem 的 Viral containment 在 68B Flit Mode 和 256B Flit Mode 下处理方式不同——这反映了两者在架构上的什么差异？

5. 本章定义的众多 Flit 格式中，哪些是 PCIe-only，哪些是 CXL-only，哪些是通用的？
