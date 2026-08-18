# 复现对标方案：RapidChiplet 案例分析

**目标**: 制定一个最简复现方案，针对领域内的标杆 DSE 工具/方法（以 RapidChiplet 为例），用 Python 脚本复现其核心判定逻辑。

---

## 1. 对标物选择：RapidChiplet (ICCAD'21)

**选择理由**:
*   **代表性**: ICCAD 顶会论文，是 Chiplet 设计空间探索（DSE）领域的经典工作。
*   **方法清晰**: 论文详细描述了其探索方法，即如何评估不同封装技术和 NoC 拓扑组合下的系统性能与成本。
*   **可复现性**: 其核心逻辑是基于分析模型的计算，而非深度强化学习，便于用 Python 脚本实现。

---

## 2. RapidChiplet 核心方法论解构

通过阅读论文，RapidChiplet 的核心逻辑是一个**三层评估模型**：

1.  **封装层 (Packaging Model)**:
    *   **判定**: 评估给定封装技术（如 2.5D, 3D）下的**最大可布线长度**和**最大凸点（μbump）数量**。
    *   **约束**: 工艺节点的物理限制（如 bump pitch, routing density）。
2.  **网络层 (Network Model)**:
    *   **判定**: 评估给定 NoC 拓扑（如 Mesh, Ring）在满足封装约束下的**最大吞吐量**和**端到端延迟**。
    *   **约束**: 封装层给出的物理边界（如链路长度不能超过最大可布线长度）。
3.  **成本层 (Cost Model)**:
    *   **判定**: 计算每个设计点的**硅片面积开销**、**封装成本**和**良率**。
    *   **约束**: 面积约束、成本约束。

**核心判定逻辑**:
一个设计点（拓扑 + 封装）被判定为**可行**，当且仅当：
1.  所需的总 μbump 数量 ≤ 封装技术提供的最大 μbump 数量。
2.  NoC 的链路总长度 ≤ 封装技术提供的最大布线长度。
3.  系统的带宽需求（Performance Target） ≤ NoC 的最大吞吐量。
4.  总成本 ≤ 预算。

---

## 3. 最简复现方案

我们将编写一个 Python 脚本，`benchmark/replication/rapidchiplet_checker.py`，来复现上述判定逻辑。

### 3.1 输入 (与我们的 Baseline 对齐)

脚本将接收与 `generate_baseline.py` 相同的参数组合：
*   拓扑类型 (mesh, torus) 和规模 (3x3, 4x4)
*   封装/工艺参数 (从 `config/params/*.yaml` 加载)

### 3.2 实现步骤

*   **Step 1: 封装容量计算**
    *   基于封装参数（如 bump pitch, interposer size），计算封装层能提供的：
        *   `max_bumps`: 最大 μbump 数量。
        *   `max_wire_length`: 最大总布线长度。
*   **Step 2: NoC 资源计算**
    *   基于给定拓扑，计算 NoC 需要的：
        *   `required_bumps`: 实现该拓扑所需的 μbump 总数（节点数 * 每节点端口数 * 2）。
        *   `required_wire_length`: 实现该拓扑所需的总布线长度（所有链路的长度之和）。
*   **Step 3: 判定**
    *   执行 `Step 2` 的计算值与 `Step 1` 的容量值对比。
    *   **判定**: 若 `required_bumps <= max_bumps` 且 `required_wire_length <= max_wire_length`，则判定为**可行**。

### 3.3 输出

脚本将输出一个与我们的 Baseline 矩阵结构类似的 CSV 文件：`benchmark/results/rapidchiplet_matrix.csv`。
*   **列**: 拓扑, 规模, 参数, RapidChiplet 判定 (可行/不可行), 失败原因

---

## 4. 下一步

1.  **代码实现**: 根据此方案，编写 `rapidchiplet_checker.py`。
2.  **验证**: 用论文中的一个公开案例（如 3x3 Mesh on 2.5D）验证脚本计算结果是否与论文描述一致。
3.  **对比**: 运行脚本，生成 RapidChiplet 的判定矩阵，并与我们的 `our_baseline_matrix.csv` 进行对比分析。
