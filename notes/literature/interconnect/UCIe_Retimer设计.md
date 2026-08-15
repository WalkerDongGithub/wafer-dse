# UCIe Retimer 设计 — 规范要求与架构决策

---

## 1. Retimer 的物理位置

```
  Package 0                        Package 1
  ┌──────────────┐                ┌──────────────┐
  │ UCIe Die 0   │                │ UCIe Die 1   │
  │  (CPU chiplet)│                │ (Accelerator) │
  └──────┬───────┘                └──────┬───────┘
         │ UCIe Link 0                   │ UCIe Link 1
         │ (封装内，≤25mm)               │ (封装内，≤25mm)
  ┌──────┴────────────────────────────────┴───────┐
  │ Retimer 0  ←── Off-Package Interconnect ──→ Retimer 1 │
  │            (光缆/电缆/背板，可达数米到数百米)         │
  └────────────────────────────────────────────────┘
```

Retimer 一侧面对 UCIe 链路（封装内，≤25mm），另一侧面对外部互连（任意距离，任意介质）。**两侧的物理环境完全不同——Retimer 必须在两者之间做协议和数据格式的桥接。**

---

## 2. 规范规定的 Retimer 核心职责（§1.3, p45-46）

### 职责 1：可靠 Flit 传输 — 三种方案

| 方案 | UCIe 链路侧 Flit 格式 | 外部互连的可靠性 | Retimer 自己做什么 |
|------|:---:|------|------|
| **A** | Raw Format | 依赖 PCIe/CXL 原生 FEC + CRC | 只做错误统计（parity bits），不做纠错 |
| **B** | 任意 Flit 格式 | Retimer 自己做 FEC + CRC + ACK/NAK | **三跳独立链路**，每跳独立重传 |
| **C** | — | Retimer 替换/追加 FEC，用原生 CRC + Replay | 只加 FEC，不碰重传机制 |

**方案 B 是最完整的——它把端到端拆成三段独立可靠链路：**

```
Die 0 → Retimer 0   : UCIe 链路，Retimer 0 做 ACK/NAK
Retimer 0 → Retimer 1 : 外部互连，Retimer 自己做 ACK/NAK
Retimer 1 → Die 1   : UCIe 链路，Retimer 1 做 ACK/NAK
```

每段链路独立管理重传缓冲、独立做序列号和确认。**这是一种"防火墙"架构——外部互连的 BER 问题不会穿透到 UCIe 链路侧。**

---

### 职责 2：参数协商 — 保证端到端一致

> Retimers are permitted to **force the same Link width, speed, protocol, and Flit Formats** on both Package 0 and Package 1.

Retimer 和远端 Retimer 协商完毕后，强制两边的 UCIe 链路使用相同参数。协商机制本身是**实现特定**的——规范不规定 Retimer 到 Retimer 之间通过什么协议协商，只规定了它们必须保证结果一致。

**Stall 机制**：外部互连可能需要几百毫秒才能建立连接。如果 Retimer 不回应本地 Die 的 Sideband 消息，Die 的 8ms 超时会触发 LinkError。Retimer 每 4ms 发一次 Stall 响应——"我在忙，别超时"。

---

### 职责 3：状态机协调

> It is the responsibility of the Retimer die to **negotiate state transitions with the remote Retimer partner** and make sure the different UCIe Die are in sync.

如果 Die 0 想要进入 Active，Retimer 0 必须确认：
1. Retimer 1 已经转发了这个请求
2. Die 1 已经响应了
3. 整个链路两端的状态一致
4. **然后**才能向 Die 0 回复 Active Status

> The Off Package Interconnect **cannot** be taken to a low power state unless all the relevant states on UCIe Die 0 **AND** UCIe Die 1 have reached the low power state.

---

### 职责 4：流控 — Retimer 特有的信用机制

**方向 1：Die → Retimer（有信用流控）**

> Data transmitted from a UCIe Die to a UCIe Retimer is **flow-controlled using credits**. One credit corresponds to **256B** of data.

Retimer 必须有一个**接收缓冲（Receiver Buffer）**。缓冲的大小（以 256B 为单位）作为 credits 在参数交换时广告给本地 Die。Die 如果没有 credit 就不能发送。

> Credit returns are **overloaded on the Valid framing**.

不是单独的消息——credit 归还嵌在 Valid 信号的编码中。

**方向 2：Retimer → Die（无适配器级流控）**

> Data transmitted from a UCIe Retimer to a UCIe die is **not** flow-controlled at the D2D adapter level.

Retimer 直接发送，不管理 credit。假设 Die 的接收能力足够强。Retimer 之间的流控由 Retimer 自己实现，规范不约束。

**Credit 重置**：RDI 离开 Active 状态时，Die 侧的 credit 计数器复位到初始值。Retimer 在重新进入 Active 之前必须**排空或丢弃**接收缓冲中的数据。

---

## 3. 规范对 Retimer 的其他具体要求

### Valid Framing for Retimers（§4.1.2.1, p100）

| 8-bit Valid 编码 | 含义 |
|:---:|------|
| `00000000` | 无数据传输 + 无 credit 归还 |
| `00001111` | 有数据传输 + 无 credit 归还 |
| `11110000` | 无数据传输 + **归还 1 个 credit** |
| `11111111` | 有数据传输 + **归还 1 个 credit** |

编码选择了极端值（全 0、前半 0 后半 1、前半 1 后半 0、全 1）——确保即使 3 个 bit 同时翻转也能区分。单 bit 错误可以通过这个编码纠正。

### 参数交换中的 Retimer 字段（§3.2.1.2, p62）

- **DP / UP 位**：Retimer 用这两 bit 识别它连接的是下行端口还是上行端口（PCIe/CXL 拓扑用）
- **Retimer 本身设 DP=0, UP=0**——它既不是下行端口也不是上行端口
- **Retimer Receiver Buffer credits**：在参数交换阶段广告

### 管理传输（§8.2.6, p363）

Retimer **可选**支持管理传输。如果支持，Retimer 成为 UCIe 管理网络中的一个可寻址节点——可以被发现、配置，可以在 UCIe 接口和外部接口之间转发管理包。

---

## 4. Retimer 设计中的架构决策

### 决策 1：外部互连用什么物理层？

规范完全不规定。你的选择：
- **电气电缆**：直接铜线，几十米内可行
- **光模块 + 光纤**：几百米到几公里
- **背板走线**：机箱内互连
- **其他**：规范说 "any other technology"

**外部互连的 PHY 不属于 UCIe 规范的范围。** Retimer 在外部互连侧（"Off-Package Link connection"）不需要共享 REFCLK——和 UCIe 链路侧的要求不同。

### 决策 2：接收缓冲多大？

取决于外部互连的往返延迟和带宽。$BufferSize = RTT \times Bandwidth$。光互连几百纳秒、高带宽 → 缓冲需求大。Retimer 在参数交换时把这个大小广告给 Die。

### 决策 3：选方案 A、B 还是 C？

| 外部互连质量 | 推荐方案 | 原因 |
|------------|:---:|------|
| 极好（BER < 1e-15，光模块） | A | 原生 FEC 够用，Retimer 最简 |
| 一般到良好 | B | Retimer 自己做可靠性，外部互连不用操心 |
| 需要额外 FEC 但不想独立做重传 | C | 混合方案 |

---

## 5. Retimer 的简化架构

```
               UCIe Link 侧                Off-Package 侧
          ┌─────────────────────┐    ┌──────────────────┐
  UCIe    │  UCIe PHY           │    │ 外部 SerDes/PHY   │
  Die ───→│  (≤25mm)            │    │ (任意距离)         │──→ 远端
          │       ↓              │    │        ↑          │
          │  UCIe 适配器逻辑      │    │ 外部互连控制器     │
          │  (CRC/Retry/信用)    │    │ (FEC/Retry/流控)   │
          │       ↓              │    │        ↑          │
          │  ┌──────────────┐   │    │  ┌──────────────┐ │
          │  │ 接收缓冲      │───┼────→│ 发送缓冲       │ │
          │  │ (256B credits)│   │    │ │              │ │
          │  └──────────────┘   │    │  └──────────────┘ │
          │  ┌──────────────┐   │    │  ┌──────────────┐ │
          │  │ 发送缓冲      │←──┼─────│ 接收缓冲       │ │
          │  └──────────────┘   │    │  └──────────────┘ │
          └─────────────────────┘    └──────────────────┘
```

两侧各有独立的 PHY。中间是 Retimer 的逻辑核心——缓冲 + 可靠性 + 协议转换。UCIe 侧走 UCIe 协议栈（适配器+PHY）；外部侧走任意协议栈。

---

## 6. 规范没规定的事

- 外部互连的物理层协议（光模块的型号、电缆的规格）
- Retimer 到 Retimer 的参数协商协议
- 接收缓冲的具体大小（只规定按 256B 粒度广告）
- 外部互连的 flow control 机制
- 外部互连侧的均衡方案

**这些是 Retimer 实现者的设计空间。** UCIe 只规定了 Retimer 和本地 Die 之间的接口行为——确保 UCIe 链路侧的一致性。
