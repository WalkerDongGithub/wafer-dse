# UCIe 合规测试方法 — 规范给了什么、没给什么

---

## 1. 规范本身给了什么

### 硬性边界（基础规范 Chapter 5）

- 损耗掩模和串扰掩模的数值（Table 5-11）
- 发送器和接收器电气参数（Table 5-3, 5-4, 5-5）
- Bump Map——物理布局的精确坐标
- PHY 物理尺寸的参考值（Table 5-2，informative）

### 合规测试框架（Chapter 11）

- **Golden Die 方法**：用一个已知合规的参考 UCIe 芯片（Golden Die）和被测芯片（DUT）对接，通过已知合规的硅桥或中介层连接
- **Timing margining**：在采样点附近前后微调，看多偏还能正确接收 → 眼宽余量
- **Voltage margining**：调整接收器参考电压，看多偏还能正确接收 → 眼高余量
- **BER measurement**：在裕度边界处测量实际的 bit 错误率
- **Tx Equalization**：通过寄存器测试去加重功能

---

## 2. 规范没给什么 — 需要单独的合规文档

Chapter 11（p508）明确说：

> A separate document will be published later to describe the following:
> - Compliance test setup, including **the channel model and package level details**
> - Test details
> - Golden Die details including form factor and system-level behavior

**通道模型、测试细节、Golden Die 规格——这些都在另一个文档里，不在基础规范中。** 基础规范给了电气掩模的数值，但合规测试用的具体通道模型（比如参考走线的 S 参数文件）需要额外的合规文档。

---

## 3. 参考数据 — 规范已经给了什么

### PHY 物理尺寸参考值（Table 5-2, p184）

这些是 **informative**（参考信息），不是硬性要求。但对通道设计是重要的起点：

| 封装类型 | 宽度/模块 | 深度（45μm pitch） |
|---------|:---:|:---:|
| Advanced x64 | 388.8 μm | ~1043 μm |
| Standard x16 | 571.5 μm | ~1320 μm |

### Bump Map

规范给了精确的 bump 位置矩阵（§5.7.2.2–5.7.3.2）。**这是物理上唯一强制的东西**——两个 Die 的 bump 必须按这个坐标对齐。

### 模块命名规则（§5.7.2.5, 5.7.3.4）

命名包含 bump pitch、列数、模块数、旋转方向。两个不同的模块配置能不能对接——名字告诉你。

---

## 4. 测试方法的核心：裕度测试

UCIe 合规不测"眼图长什么样"——它测**"信号离出错还有多远"**。

### Timing margining

Golden Die 发送已知模式 → DUT 接收。DUT 的采样点在正常位置周围扫描 → 测量"采样点偏移多大时 BER 开始超标"→ 眼宽。

### Voltage margining

同上，但扫的是接收器参考电压 → 眼高。

**规范不规定眼宽/眼高的最小绝对值——它要求 DUT 在裕度测试中展示"足够的余量"，具体阈值在合规文档中定义。**

---

## 5. 对于通道设计的实际帮助

| 你需要做的事 | UCIe 给了什么 |
|------------|-------------|
| 确定走线截面和材料 | 无——你自行设计 |
| 验证走线是否合规 | 损耗/串扰掩模（Table 5-11） |
| 参考一个可行的走线设计 | PHY 尺寸参考值（Table 5-2）+ Bump Map |
| 测试做出来的走线 | Golden Die + 裕度测试（Chapter 11） |
| 了解合规测试用的参考通道 | 合规文档（另行发布） |

---

## 6. 总结

**UCIe 规范给出了"目标"（掩模数值）和"验证方法"（Golden Die + 裕度测试），但把"怎么做到"留给设计者。**

这和 PCIe 合规的逻辑一样——PCIe 规范给了眼图掩模和抖动容限，但不会教你"用什么材料和截面去做 PCB 走线"。**标准只管验收标准，不管实现路径。** UCIe 额外给的是 Bump Map——因为那是两个 Die 物理对接时唯一共同的坐标参考，必须强制。
