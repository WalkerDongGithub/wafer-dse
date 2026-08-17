# notes/literature/ PDF 文献清单

> **重要**：本目录下的 PDF 原文**不进入 git**（`.gitignore` 已忽略 `*.pdf`），clone 后不会自动存在。
> **获取方式**：这些 PDF 都在 **walker-server 机器**的 `~/wafer-dse/notes/literature/`（及项目根目录）下。其他机子 clone 后，按需从 walker-server 拉取（scp / rsync / 直接访问），**需要什么下什么，不必全量**。

```bash
# 示例：从 walker-server 按需拉取某篇
scp walker-server:~/wafer-dse/notes/literature/textbooks/Harchol_Balter_Performance_Modeling_Queueing_Theory.pdf .
```

## 清单（按目录）

### 项目根目录（3 个，散落）
- `FPIA_Communication-Aware_Multi-Chiplet_Integration_With_Field-Programmable_Interconnect_Fabric_on_Reusable_Silicon_Interposer.pdf`
- `packaging.pdf`
- `fundamentals of heat and mass transfer.pdf`

### notes/literature/perf_evaluation/papers/（7 个，性能建模原始论文）
- `Mandal_2019_Priority_NoC.pdf`
- `Fischer_2012_Queueing_NoC.pdf`
- `ZhangShen_McKeown_2008_VLB_FaultTolerant.pdf`
- `Yuan_2009_Oblivious_Routing_FatTree.pdf`
- `Kiasari_2013_Analytical_Latency_NoC.pdf`
- `Chang_1999_Birkhoff_Service_Guarantees.pdf`
- `McKeown_1996_100pct_Throughput_InputQueued.pdf`

### notes/literature/textbooks/（6 个，权威教材）
- `Harchol_Balter_Performance_Modeling_Queueing_Theory.pdf`
- `Le_Boudec_Thiran_Network_Calculus_LNCS2050.pdf`
- `Stillmaker_Baas_Integration2017_CMOS_Scaling_Equations.pdf`
- `Computer Architecture- A Quantitative Approach.pdf`
- `信号完整性分析_Signal and Power Integrity.pdf`
- `Rabaey-Digital-Integrated-Circuits-A-Design-Perspective.pdf`

### notes/literature/architecture_cases/（11 个，wafer-scale/chiplet 会议论文）
- `Ahn_Choo_Kim_HPCA2012_Network_within_a_network.pdf`
- `Chen_Pal_Kumar_ISCA2024_Waferscale_Network_Switches.pdf`
- `Architectural_Exploration_for_Waferscale_Switching_System.pdf`
- `16-2048-Chiplet-Waferscale-Processor-DAC2021.pdf`
- `15-MLIR-Lowering-Stencils-Wafer-Scale-ASPLOS2026.pdf`
- `14-Ouroboros-Wafer-Scale-SRAM-CIM-ASPLOS2026.pdf`
- `13-Gemini-DNN-Chiplet-Accelerator-HPCA2024.pdf`
- `11-WATOS-LLM-Training-Wafer-Scale-HPCA2026.pdf`
- `09-MoEntwine-Wafer-Scale-Expert-Parallel-HPCA2026.pdf`
- `02-TEMP-Tensor-Partition-Mapping-Wafer-Scale-HPCA2025.pdf`
- `01-FRED-Wafer-scale-Fabric-3D-DNN-Training-ISCA2025.pdf`

### notes/literature/packaging/（3 个，John H. Lau 封装专著）
- `semiconductor-advanced-packaging.pdf`
- `flipchip-hybrid-bonding-fanin-fanout.pdf`
- `chiplet-design-and-heterogeneous-integration-packaging.pdf`

### notes/literature/interconnect/（1 个，规范原文）
- `UCIE_SPECIFICATION_2.0.pdf`

---

共 31 个 PDF。其余 `.md` 文件是笔记/卡片/索引，**进入 git**，clone 即可得。
