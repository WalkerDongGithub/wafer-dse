# Floorplan —— 物理布局层（待实现）

热模型需要物理位置才能构建 G 矩阵。当前缺失的链路：

```
Topology → TopoStructure    逻辑：链路 + die 归属
Floorplan                   物理：die 位置、基板尺寸、冷却方案  ← 缺失
    ↓
_hierarchical.py            G 矩阵（热传导网络）
    ↓
build_thermal_network()     G⁻¹ + 链路系数 → ThermalNetwork
    ↓
NetworkModel                温度约束进 LP
```

Floorplan 需要提供：
- die 的 (x, y) 位置（mm）
- 基板整体尺寸（mm）
- interposer 间距（mm）
- 冷却方案

默认可用等距网格 + 统一冷却占位。
