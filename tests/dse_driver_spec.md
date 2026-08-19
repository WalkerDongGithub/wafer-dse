# 大规模 DSE 实验驱动 —— 测试规格

## 1. 功能规格

### 1.1 实验矩阵生成
- **输入**: 拓扑列表 × 参数列表 × 场景列表
- **输出**: ProblemSpec 列表，每个组合一个
- **约束**: 
  - 拓扑参数必须是合法的构造参数
  - 参数 YAML 必须能正确加载
  - 场景必须是 perf / perf+bump / perf+bump+therm 之一

### 1.2 批量求解
- 对每个 ProblemSpec 执行:
  1. 创建拓扑实例
  2. 布局 (place)
  3. 场景建模 (build_scenario)
  4. Runner + CvxSolver + ResultStore 求解
  5. BmaxQuery 二分搜索
  6. 返回结构化结果

### 1.3 缓存管理
- L1 缓存: 内存中，key = (query_id, B, model_keys...)
- L2 缓存: 磁盘持久化，路径 `exp/output/.cache`
- 缓存命中统计
- 缓存完整性校验（sha256 + size）

### 1.4 结果收集
- 每条记录: topo, params, scenario, B_star, iterations, n_terminals, n_links, n_dies, ledger
- 汇总 CSV 输出
- 汇总 JSON 输出

## 2. 测试用例

### T1: 基础拓扑构造
- 输入: MeshTopology(2), TorusTopology(3), FullMeshTopology(2,1), DragonflyTopology(2,1,1)
- 期望: 所有拓扑正确构造，n_terminals, n_links 合理

### T2: 参数加载
- 输入: config/params/ucie-12g.yaml
- 期望: ExpParams 正确加载，所有字段非零

### T3: 单组合求解
- 输入: MeshTopology(2) + ucie-12g + perf
- 期望: BmaxQuery 返回 B_star > 0，iterations > 0

### T4: 缓存生效
- 执行 T3 两次
- 期望: 第二次运行 L2 缓存命中，无需重新求解 LP

### T5: 全场景覆盖
- 对同一 (topo, params) 组合执行 perf, perf+bump, perf+bump+therm 三个场景
- 期望: 三个场景均能正确求解

### T6: 大规模矩阵
- 至少 20 个不同组合
- 期望: 所有组合都能完成求解，无崩溃

### T7: 结果格式
- CSV 包含所有预期列
- JSON 包含完整 B_star, ledger 信息

### T8: 缓存持久化
- 运行结束后缓存目录存在
- 重启 Python 后缓存仍可命中

## 3. 边界条件

- 不可行: B_star = 0 表示 lo 不可行
- 异常捕获: 单个组合失败不影响其他组合
- 超时: 单次 BmaxQuery > 300 秒超时跳过
