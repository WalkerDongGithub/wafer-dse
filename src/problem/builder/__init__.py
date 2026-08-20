"""problem.builder —— 编排层: 拓扑 + 参数 + Layout → LP 模型列表.

层级约定：布局是更高层的设计决策（placement 求解器在更高层被调用），
builder 只接收布局结果、组装 LP 模型——不自己决定 die 摆哪。
exp 只做"布局 → 建模 → 跑查询 → 收集结果"的编排.

依赖方向:
  - 上游: physical.layout (Layout, DiePlacement, MfitStackConfig) +
          physical.config (DieBumpBudget) + physical.params (ExpParams)
  - 下游: problem.models (LP 约束模板: BumpModel, SteadyStateModel, ...)

模块组织:
  _scenario.py   build_scenario + die_to_links (场景组装 + 链路派生)
"""

from problem.builder._scenario import (
    build_scenario, build_wiring_fixed, die_to_links,
)

__all__ = [
    "build_scenario",
    "build_wiring_fixed",
    "die_to_links",
]
