# 第一章：引论（Introduction）— 讲义

> 对应文档：UCIe Specification 2.0, Chapter 1.0, p35-48（约14页）
> 定位：建立 UCIe 全局认知框架，回答"UCIe 是什么、为什么需要它、它怎么工作"

---

## 1.0 引言：UCIe 的核心定位（p35-36）

### 1.0.1 一句话定义

**UCIe 是一个开放的、多协议支持的、封装级（on-package）互连标准**，用于在同一封装内连接多个芯片（Die/芯粒）。

### 1.0.2 关键概念拆解

#### "开放"（Open）意味着什么？

- UCIe 由 **Universal Chiplet Interconnect Express, Inc.**（一个 Delaware 非营利公司/联盟）管理
- 任何人都可以通过签署评估协议（Evaluation Copy Agreement）获取规范
- 联盟成员享有完整的知识产权保护
- 对标标准：PCIe 由 PCI-SIG 管理，CXL 由 CXL Consortium 管理

#### "多协议支持"（Multi-protocol Capable）

UCIe 不是为某一种协议设计的，而是提供了一套**通用传输层**，可以在上面承载多种上层协议：

| 协议 | 用途 |
|------|------|
| **PCIe** | 传统 I/O 互连：从 PCIe Base Spec 6.2 映射 |
| **CXL** | 缓存/内存/一致性互连：从 CXL 3.1 映射（注意：不支持 RCD/RCH/eRCD/eRCH） |
| **Streaming** | 用户自定义协议：可利用 UCIe 的 CRC/Retry 获得可靠传输 |
| **Raw Format** | 协议无关透传：可以承载任意协议（如 Ethernet），但可靠性由上层负责 |
| **Management Transport** | UCIe 内置管理协议：端到端的管理通信 |

#### "封装级"（On-Package）意味着什么？

这是 UCIe 与 PCIe/SERDES 最本质的区别：

```
传统 SERDES（片外）：  Die A → SERDES PHY → PCB走线 → SERDES PHY → Die B
                        (长距离, 高损耗, BER ~1e-12, 需要复杂均衡)

UCIe（封装内）：        Die A → UCIe PHY → 封装基板/中介层走线 → UCIe PHY → Die B
                        (短距离, 低损耗, BER ~1e-27, 可以省去大量电路)
```

因为封装内的环境远好于 PCB，UCIe 可以：
- 省去复杂的 SerDes 均衡器 → 功耗更低
- 使用转发时钟而不是时钟恢复 → 延迟更低
- 获得极低的原始误码率 → 减少纠错开销

### 1.0.3 UCIe 解决的核心问题：解耦式架构

传统 SoC 把所有功能（CPU、GPU、内存控制器、I/O）做到一块大芯片上：

```
传统单芯片 SoC：
┌──────────────────────────────┐
│  CPU | GPU | MemCtrl | I/O  │  ← 一块大芯片，良率低、成本高
└──────────────────────────────┘

解耦式（Disaggregated）架构：
┌─────┐  ┌─────┐  ┌──────────┐
│ CPU │  │ GPU │  │ I/O Tile │    ← 每块分别制造（更好的工艺/更小的面积）
└──┬──┘  └──┬──┘  └────┬─────┘
   │        │          │
   └────────┼──────────┘
          UCIe（封装内互连）
```

解耦的好处：
- **良率**：小芯片的良率远高于大芯片
- **工艺灵活性**：CPU 用最先进工艺，I/O 用成熟工艺
- **IP 复用**：不同产品组合不同芯粒
- **成本分摊**：同一芯粒可用于多个产品

### 1.0.4 UCIe 2.0 的两个新增子系统

UCIe 2.0 相比 1.1 版本新增了两大块：

1. **UCIe Manageability Architecture**（可选）：提供管理 SiP 的通用架构和软硬件基础设施
2. **UCIe DFx Architecture (UDA)**：利用可管理性架构提供标准化的测试和调试基础设施

**思考**：为什么需要内置管理架构？
> 在解耦式 SiP 中，多个不同供应商的芯粒共存，需要一个统一的管理框架来处理配置、安全、错误报告等。否则每个供应商自己搞一套，集成起来很困难。

---

## 三大封装选项（p37-39）

UCIe 覆盖了从低成本到极致性能的全谱系，这是其设计哲学的重要体现：

```
        成本 ↓                              性能 ↑
Standard 2D  ←────  Advanced 2.5D  ───→  UCIe-3D
(有机基板)      (硅中介层/硅桥)        (垂直堆叠)
10-25mm         <2mm                 3D垂直
```

### Standard Package（2D 封装）— 低成本长距离

| 参数 | 数值 | 解读 |
|------|------|------|
| 速率 | 4/8/12/16/24/32 GT/s | 全速率支持 |
| Bump 间距 | 100-130 um | 较大间距，成本低 |
| 传输距离 | 10mm（短距）/ 25mm（长距） | 可覆盖整个封装 |
| Raw BER（≤8GT/s） | **1e-27** | 极低，几乎不需要纠错 |
| Raw BER（≥12GT/s） | **1e-15** | 仍远好于传统 SERDES（~1e-12） |
| 走线介质 | 有机封装基板（Organic Substrate） | 传统封装工艺 |
| 模块宽度 | x16 或 x8（含 Sideband） | 适中带宽 |

**使用场景**：成本敏感的通用计算方案

### Advanced Package（2.5D 封装）— 高性能短距离

| 参数 | 数值 | 解读 |
|------|------|------|
| 速率 | 4/8/12/16/24/32 GT/s | 全速率支持 |
| Bump 间距 | 25-55 um | 高密度互连 |
| 传输距离 | < 2mm | 极短距离 |
| Raw BER（≤12GT/s） | **1e-27** | 超低误码 |
| Raw BER（≥16GT/s） | **1e-15** | 仍然很好 |
| 模块宽度 | x64 或 x32（含冗余修复） | 高带宽 |
| 走线介质 | 硅中介层（Interposer）、硅桥（EMIB）、扇出有机中介层（FO CoS-B） | 需要高级封装 |

**三种典型实现**：

```
EMIB（硅桥）：                CoWoS（硅中介层）：           FO CoS-B（扇出有机）：
┌───┐    ┌───┐               ┌───┐ ┌───┐               ┌───┐ ┌───┐
│Die│    │Die│               │Die│ │Die│               │Die│ │Die│
└─┬─┘    └─┬─┘               └─┬─┘ └─┬─┘               └─┬─┘ └─┬─┘
──┴────────┴──                ───┴─────┴───                ───┴─────┴───
  硅桥(Silicon Bridge)         硅中介层(Interposer)        扇出有机中介层
────────────────              ───────────────              ──────────────
  封装基板                       封装基板                       封装基板
```

### UCIe-3D（3D 堆叠）— 极致性能

| 参数 | 数值 | 解读 |
|------|------|------|
| 速率 | up to 4 GT/s | 速率不高但... |
| Bump 间距 | <10 um（优化）/ 10-25 um（功能） | 极小间距 |
| 互连方向 | 3D 垂直 | Die on Die |
| Raw BER | **1e-27** | 极低 |
| 带宽密度 | **4000 GB/s/mm²** | 比 2.5D 高 ~200 倍！ |
| 能效 | 0.05 pJ/bit | 比 2.5D 好 ~5-10 倍 |
| 延迟 | ≤125 ps | 比 2.5D 好 ~16 倍 |

**为什么 3D 速率低但带宽更高？**
- 2D/2.5D 只在芯片边缘放置 bump（1D 线性排列）
- 3D 在整个芯片面积上放置 bump（2D 阵列）
- 所以即使每 lane 速率低，总 lane 数极高 → 总带宽极高

---

## 1.1 UCIe 组件（p40-42）★ 核心架构

这是 UCIe 最重要的分层架构图（Figure 1-8）：

```
┌─────────────────────────────────────────────────┐
│                                                 │
│               协议层 (Protocol Layer)             │
│        PCIe / CXL / Streaming / Raw              │
│                                                 │
│        Flit-aware D2D Interface (FDI)            │  ← 第 10 章定义
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│            D2D 适配器 (D2D Adapter)               │
│   ┌──────────┐  ┌───────────┐  ┌──────────┐     │
│   │ ARB/MUX  │  │ CRC/Retry │  │  链路状态  │     │
│   │ (多协议)  │  │ (可靠性)   │  │  管理/    │     │
│   │          │  │           │  │ 参数协商  │     │
│   └──────────┘  └───────────┘  └──────────┘     │
│                                                 │
│        Raw D2D Interface (RDI)                   │  ← 第 10 章定义
│                                                 │
├────────┬────────────────────┬───────────────────┤
│        │    物理层 (PHY)     │                   │
│  ┌─────┴──────────────────┐ │                   │
│  │      PHY Logic          │ │                   │
│  │  - Link Training        │ │  ┌───────────────┤
│  │  - Lane Repair/Reversal │ │  │ 电气/AFE      │
│  │  - Scrambling           │ │  │ (k个Slice)    │
│  │  - Sideband Init/Trans  │ │  │ - Clock FWD   │
│  └─────────────────────────┘ │  │ - 模拟前端     │
│                              │  └───────────────┤
│  ┌──────────────────────────┐│                  │
│  │ Sideband / Global         ││                  │
│  └──────────────────────────┘│                  │
└─────────────────────────────────────────────────┘
```

### 1.1.1 协议层（Protocol Layer）

**本质**：协议层是"内容生产者/消费者"，它不关心数据怎么传输，只关心传什么。

**协议层负责**：
- 构造协议特定的 Transaction/Data 内容
- 以 Flit 格式交付给 D2D 适配器

**5 种协议全解析**：

1. **PCIe**：来源于 PCIe Base Spec 6.2
   - Flit Mode：PCIe 6.0 引入的 Flit 模式
   - Non-Flit Mode：传统 PCIe 模式（通过 CXL 68B Flit 格式传输）

2. **CXL**：来源于 CXL Spec 3.1
   - **CXL.io**：基于 PCIe 的发现/配置/IO 协议
   - **CXL.cache**：主机对设备缓存的访问
   - **CXL.mem**：主机对设备内存的访问
   - ⚠️ **RCD/RCH/eRCD/eRCH** 不支持（这些是 CXL 设备类型子集）

3. **Streaming**：用户自定义协议
   - 提供通用传输模式
   - 可以利用 UCIe Adapter 的 CRC/Retry 获得可靠传输！

4. **Management Transport**（2.0 新增）
   - 端到端的媒体无关管理协议
   - 可通过 sideband 或 mainband 传输

5. **Raw Format**
   - 协议无关，所有 Flit 字节由协议层填充
   - 用途：集成独立 SERDES/收发器 tile（如 Ethernet）
   - ⚠️ Raw Format 下，可靠传输由协议层自己负责（Adapter 不提供 CRC/Retry）

### 1.1.2 D2D 适配器（Die-to-Die Adapter）

**本质**：适配器是 UCIe 最核心的创新——它是夹在协议层和物理层之间的"智能胶水层"。

**适配器负责**：

| 功能 | 说明 |
|------|------|
| **ARB/MUX**（多协议场景） | 当使用 CXL 时，对 CXL.io/CXL.cache/CXL.mem 进行仲裁和多路复用 |
| **CRC/Retry** | 当 Raw BER > 1e-27 时，提供链路级可靠性保障 |
| **链路状态管理（LSM）** | 协调高层的链路状态机（比 PHY 的训练状态机层级更高） |
| **参数协商** | 与远端 Link Partner 交换并协商协议选项、能力 |

**设计理念**：最小化主数据路径上的逻辑，保证低延迟。

**CRC/Retry 的启用条件**：只有 Raw Format 模式且 Raw BER <= 1e-27 时才可以省略 CRC/Retry，其他所有情况都启用。

### 1.1.3 物理层（Physical Layer）

物理层有三个子组件：

**（1）PHY Logic（逻辑物理层）**

负责数字端的控制和数据处理：
- 链路训练（Link Training）
- Lane 修复（Lane Repair）— 当部分物理 Lane 损坏时
- Lane 反转（Lane Reversal）— 物理布线优化
- 扰码/解扰（Scrambling/De-scrambling）
- Sideband 初始化和传输
- 多模块 PHY（MMPL）— 多模块间的同步

**（2）Analog Front End（模拟前端/AFE）**

负责物理信号的生成和接收：
- 时钟转发（Clock Forwarding）
- 信号驱动/接收
- 均衡

**（3）Sideband / Global**

独立于数据路径的管理通道。

### 物理链路的两类连接

| 特性 | **Sideband** | **Mainband** |
|------|-------------|-------------|
| **用途** | 参数交换、寄存器访问、链路训练协调、debug | 主数据传输 |
| **组成** | 1 时钟 pin + 1 数据 pin（双向） | 1 转发时钟 + 1 Valid pin + 1 Track pin + N 数据 Lane |
| **时钟频率** | **固定 800 MHz**（与主数据速率无关） | 随数据速率变化 |
| **电源域** | 辅助电源、**Always-On** | 正常运行域 |
| **每模块数量** | 1 组 | x64/x32（Advanced）或 x16/x8（Standard） |
| **冗余** | Advanced Package 有冗余对 | 4 个额外 pin 用于 Advanced Package 修复 |

**Sideband "Always-On" 的意义**：
- 即使 Mainband 完全断电，Sideband 也可以工作
- 用于链路唤醒、功耗管理转换（L1→L2→Active）
- 类似 PCIe 的 Aux Power 概念

**Module（模块）概念**：
> UCIe 主数据路径在物理 bump 上组织为一个 Lane 组，称为一个 Module。Module 是 UCIe AFE 的**原子设计粒度**。
> - Advanced Package：1 Module = 64 Lanes（x64）或 32 Lanes（x32）
> - Standard Package：1 Module = 16 Lanes（x16）或 8 Lanes（x8）
> - 需要更高带宽时，可以聚合多个 Module

### 1.1.4 接口（Interfaces）

UCIe 定义了两个标准化接口，目的是实现**IP 混搭**：

```
协议层 (Vendor A)
    ↕  FDI — Flit-aware Die-to-Die Interface（第 10 章定义）
D2D 适配器 (Vendor B)
    ↕  RDI — Raw Die-to-Die Interface（第 10 章定义）
物理层 (Vendor C)
```

**FDI vs RDI 的关键区别**：

| 特性 | FDI | RDI |
|------|-----|-----|
| 位置 | 协议层 ↔ 适配器 | 适配器 ↔ 物理层 |
| 数据格式 | 已封装的 Flit（含 CRC/FEC 位） | 原始字节流 |
| 流控信息 | 协议级流控 | 适配器级流控 |
| 时钟域 | 与 LCLK 同步 | 与 LCLK 同步 |

**为什么要标准化这两个接口？**

1. **IP 混搭**：不同供应商的不同层可以自由组合 → 加速生态发展
2. **降低验证成本**：Post-silicon 互操作测试成本高，标准化接口+BFM 可以前期做更多验证
3. **加速上市时间**

---

## 1.2 UCIe 配置（p42-44）

### 1.2.1 单模块配置

```
Advanced Package：               Standard Package：
┌──────────┐                     ┌──────────┐
│  Adapter │                     │  Adapter │
├──────────┤                     ├──────────┤
│PHY Logic │                     │PHY Logic │
├──────────┤                     ├──────────┤
│   AFE    │                     │   AFE    │
│  x64/x32 │                     │  x16/x8  │
│ + SB/Val │                     │ + SB/Val │
│ + Trk/Clk│                     │ + Trk/Clk│
└──────────┘                     └──────────┘
```

- x8 Standard Package 模式**仅允许单模块**，主要用于 pre-bond 测试
- 多个单模块可以独立操作（不同速率、不同宽度）

### 1.2.2 多模块配置（2 模块、4 模块）

**关键规则**：当多个模块共用同一个 Adapter 时，**所有模块必须工作在相同的数据速率和宽度**。

```
两模块 Standard Package：        四模块 Standard Package：
┌──────────┐                     ┌──────────┐
│  Adapter │                     │  Adapter │
├──────────┤                     ├──────────┤
│  MMPL    │                     │  MMPL    │
├────┬─────┤                     ├──┬──┬──┬─┤
│PHY │ PHY │                     │PH│PH│PH│PH│
│Log │ Log │                     │Y │Y │Y │Y │
├────┼─────┤                     ├──┼──┼──┼─┤
│AFE │ AFE │                     │AF│AF│AF│AF│
│x16 │ x16 │                     │E │E │E │E │
└────┴─────┘                     └──┴──┴──┴─┘
                                 x16 x16 x16 x16
```

**MMPL（Multi-Module PHY Logic）**：负责多个模块之间的同步和协调，包括：
- 宽度退化（某些模块的部分 Lane 故障）
- 速度退化（某些模块无法达到目标速率）
- 模块禁用（整个模块不可用）

### 1.2.3 Sideband-only 配置

仅使用 Sideband 通道的配置，用于：
- **测试目的**（pre-bond 测试）
- **管理目的**（仅需管理通信）

支持 1、2、4 个 Sideband-only 端口。

---

## 1.3 UCIe Retimers（p45-46）

### 为什么需要 Retimers？

UCIe 本质是封装级互连（<2mm 或 <25mm），但如果想将其扩展到**封装外**（如机架级、集群级），就需要 Retimer。

```
Package 0                     Package 1
┌──────────┐                  ┌──────────┐
│ UCIe Die │                  │ UCIe Die │
│    0     │                  │    1     │
└────┬─────┘                  └────┬─────┘
     │ UCIe Link 0                │ UCIe Link 1
┌────┴────────────────────────────┴────┐
│  Retimer 0    Off-Package    Retimer 1│
│  ┌────┐   Interconnect (光/电)  ┌────┐│
│  │Buf │◄══════════════════════►│Buf ││
│  └────┘                       └────┘│
└──────────────────────────────────────┘
```

**典型应用**：Figure 1-2 展示的 Rack/Pod 级别 CXL 解耦：
- 多个计算抽屉通过 CXL 交换机连接加速器/内存池
- 每个抽屉内部用 UCIe，跨抽屉用 Retimer + 外部互连

### Retimer 的 5 大职责

**1. 可靠 Flit 传输**（三种方案可选）：

| 方案 | 谁提供 FEC/CRC/Retry | 何时用 |
|------|---------------------|--------|
| A | 利用 PCIe/CXL 原生的 FEC+CRC | 外部互连符合原生 BER 模型，UCIe Link 用 Raw Format |
| B | Retimer 自己提供完整的 FEC+CRC+Retry | 三跳独立链路，每跳有自己的 ACK/NAK |
| C | Retimer 替换/增加 FEC，用原生 CRC+Replay | 需要额外 FEC，但利用已有重试机制 |

**2. 链路和协议参数解析**：
- Retimer 可以强制两端用相同的宽度、速度、协议、Flit 格式
- 引入 "Stall" 响应来避免外部互连延迟导致的不必要超时

**3. 链路状态协调**：Retimer 协调 LSM 和 RDI 状态在两端之间的一致性

**4. 流控和反压**：
- **Die → Retimer**：基于信用（Credit），1 Credit = 256B
- **Retimer → Die**：不设适配器级流控
- 信用在 RDI 离开 ACTIVE 状态后重置
- Retimer 重新进入 ACTIVE 前必须排空/丢弃接收缓冲

---

## 1.4 关键性能指标（p47）

### 2D/2.5D 性能指标

| 指标 | Advanced Package (x64) | Standard Package (x16) |
|------|----------------------|----------------------|
| **边沿带宽密度** @ 32GT/s | **1317 GB/s/mm** | 224 GB/s/mm |
| **能效** @ 0.5V | 0.25 pJ/bit (≤12 GT/s) | 0.5 pJ/bit (≤16 GT/s) |
| **延迟目标** @ 16GT/s | **≤ 2ns** | ≤ 2ns |

**边沿带宽密度怎么理解？**
> 在芯片边缘每毫米能挤出多少带宽。这是芯片设计者最关心的物理约束——芯片面积是有限的，能放 I/O bump 的周长也是有限的。Advanced Package 因为 bump 间距小（45um vs 110um），每毫米能放更多 bump → 带宽密度高。

### UCIe-3D 性能指标

| 指标 | 数值 | 相比 2.5D |
|------|------|-----------|
| 面积带宽密度 | **4000 GB/s/mm²** | ~200 倍提升 |
| 能效 @ 0.65V | **0.05 pJ/bit** | ~5-10 倍提升 |
| 延迟 | **≤ 125 ps** | ~16 倍提升 |

> 注意：3D 用面积密度（/mm²），2D/2.5D 用边沿密度（/mm）。因为 3D 在整个芯片面积上互连。

---

## 1.5 互操作性（p48）

### 4 组 Bump Pitch

规范把所有可能的 bump pitch 分成 4 组，保证**组内**和**跨组**的互操作性：

| 分组 | Bump Pitch (um) | 最低频率 | 预期最高频率 |
|------|----------------|----------|-------------|
| Group 1 | 25 - 30 | 4 GT/s | 12 GT/s |
| Group 2 | 31 - 37 | 4 GT/s | 16 GT/s |
| Group 3 | 38 - 44 | 4 GT/s | 24 GT/s |
| Group 4 | 45 - 55 | 4 GT/s | **32 GT/s** |

**关键规律**：
- bump pitch 越大 → 可以支持的频率越高（物理间隙更大 → 串扰更小）
- bump pitch 越小 → 虽然频率受限，但密度更高（单位面积带宽不低）
- 所有组都支持最高 32GT/s 只是**能力上限**，实际设计可能在较低频率优化面积/功耗
- 互操作性在组内和跨组都保证

### 推荐发送器电压

规范**强烈建议** Die 采用 **< 0.85V** 的发送器电压，以便与广泛的工艺节点互操作。

---

## 第一章核心总结

### 需要记住的 5 个关键概念

1. **UCIe = 封装级互连**：利用封装内的优等物理环境，省去复杂 SerDes，获得极低功耗和延迟

2. **分层结构**：Protocol → Adapter → PHY Logic → AFE，FDI 和 RDI 保证每一层可以来自不同供应商

3. **三种封装形态**：Standard（2D/成本优先）→ Advanced（2.5D/性能优先）→ UCIe-3D（极致密度/能效）

4. **Module 是物理原子粒度**：x64/x32/x16/x8，多模块聚合实现带宽扩展

5. **Retimer 把 UCIe 延伸到封装外**：三步可靠性方案（原生 FEC / Retimer FEC+CRC / 混合）

### 贯穿全书的线索

- Sideband：低速管理通道，Always-On，是链路训练和管理的"生命线"
- CRC/Retry：UCIe 可靠性的核心机制，适配器层实现
- 参数协商：两端如何"对上话"并达成一致——这是第 3 章的核心

---

## 讨论问题

1. 为什么 UCIe 的 Sideband 时钟要固定 800MHz，而不是随主数据速率变化？
2. 三种封装方案中，为什么 UCIe-3D 的 BER 统一为 1e-27，而 Standard/Advanced Package 分两档？
3. Retimer 方案 B（三跳独立链路）和方案 A（Raw 透传）各有什么利弊？
4. 为什么要定义 FDI 和 RDI 两个接口，而不是只定义一个？
5. 如果我们想把一块 Ethernet MAC IP 用 UCIe 连接到交换机 Die，应该用哪种协议模式？为什么？
