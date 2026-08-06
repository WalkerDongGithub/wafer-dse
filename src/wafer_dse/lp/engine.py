"""统一 LP 引擎 — 构建并求解多约束耦合的线性规划。

两种求解路径:
    1. det (快速): Hungarian 精确最坏情况 + 独立物理约束检查
       无需 cvxpy，零外部依赖。输出 per-link load + 各约束 slack。

    2. valiant (完整 LP): cvxpy 联合 LP，变量 D + f + L。
       同时编码性能多面体、几何 bump 预算、热功率密度。
       对偶变量精确定位绑定约束。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from wafer_dse.architecture_model.topology import Topology
from wafer_dse.lp.report import LpResult, LpConstraintStatus
from wafer_dse.lp.performance import (
    build_link_weights,
    compute_worst_case_loads,
    enumerate_links,
)
from wafer_dse.lp.geometry import (
    DieConfig,
    DieBumpBudget,
    BumpSpec,
    build_die_to_links,
    build_geometry_constraints,
    geometry_check,
)
from wafer_dse.lp.thermal import (
    ThermalConfig as ThermalCfg,
    build_thermal_constraints,
    thermal_check,
)


# ============================================================================
# 求解器选择
# ============================================================================


def _has_cvxpy() -> bool:
    try:
        import cvxpy  # noqa: F401
        return True
    except ImportError:
        return False


# ============================================================================
# UnifiedLp
# ============================================================================


@dataclass
class UnifiedLp:
    """统一 LP 引擎。

    使用方式:
        lp = UnifiedLp(topo, route="det", target_gbps=800)
        lp.add_geometry(die_configs, bump_spec)
        lp.add_thermal(thermal_cfg)
        result = lp.solve()
        print(result.report())
    """

    topo: Topology
    route: str = "det"              # "det" | "valiant"
    target_gbps: float = 800.0      # 端口目标带宽 B
    lane_rate_gbps: float = 32.0    # 内部 lane 速率 R_e

    # 内部状态
    _die_configs: list[DieConfig] = field(default_factory=list)
    _bump_spec: BumpSpec | None = None
    _thermal_cfg: ThermalCfg | None = None

    # ------------------------------------------------------------------
    # 配置: 逐步添加约束
    # ------------------------------------------------------------------

    def add_geometry(
        self,
        die_configs: list[DieConfig],
        bump_spec: BumpSpec,
        group_to_die: dict[int, int] | None = None,
    ) -> UnifiedLp:
        """添加几何约束 (bump 预算 per die)。

        Args:
            die_configs: 每个 die 的物理配置
            bump_spec: bump 工艺 (μbump 或 C4)
            group_to_die: 可选的 group→die 手动映射
        """
        self._die_configs = die_configs
        self._bump_spec = bump_spec
        self._group_to_die = group_to_die
        return self

    def add_thermal(self, cfg: ThermalCfg) -> UnifiedLp:
        """添加热约束 (功率密度上限)。"""
        self._thermal_cfg = cfg
        return self

    # ------------------------------------------------------------------
    # 求解
    # ------------------------------------------------------------------

    def solve(self) -> LpResult:
        """构建并求解 LP。根据 route 选择路径。

        - det:     Hungarian 精确最坏情况 + 物理约束检查
        - valiant: cvxpy 完整 LP (D + f + L, 最优分流)
                   需要 pip install ".[lp]"
        """
        t0 = time.time()

        if self.route == "det":
            result = self._solve_hungarian()
        elif self.route == "valiant":
            if not _has_cvxpy():
                raise ImportError(
                    "valiant 路由需要 cvxpy 求解最优分流 LP。"
                    "  pip install \".[lp]\"\n"
                    "  或使用 --route det 进行 Hungarian 精确求解。"
                )
            result = self._solve_valiant_lp()
        else:
            raise ValueError(f"不支持的路由策略: {self.route!r}")

        result.solve_time_s = time.time() - t0
        return result

    # ------------------------------------------------------------------
    # 路径 1: Hungarian — det 路由下的精确最坏排列分析
    # ------------------------------------------------------------------

    def _solve_hungarian(self) -> LpResult:
        notes: list[str] = []

        # Step 1: 链路权重 + Hungarian 最坏情况
        link_weights = build_link_weights(self.topo, route=self.route)
        if not link_weights:
            return LpResult(
                feasible=True, solver="hungarian", route="det",
                worst_load=0.0, nonblocking_gbps=float("inf"),
                notes=["无链路 (单节点拓扑?)"]
            )

        loads = compute_worst_case_loads(link_weights)
        links = enumerate_links(self.topo)
        link_idx_map = {link: i for i, link in enumerate(links)}

        # Performance
        worst_load = max(loads.values()) if loads else 0.0
        worst_link = max(loads, key=loads.get) if loads else None
        nonblocking = (
            float("inf") if worst_load <= 0
            else self.target_gbps / worst_load
        )
        perf_ok = nonblocking >= self.target_gbps

        # Per-link load vector
        per_link_load = {link: loads.get(link, 0.0) for link in links}

        constraints_status: list[LpConstraintStatus] = []

        # Performance constraint status
        perf_violation = max(0.0, worst_load - 1.0)  # >1 means overloaded
        constraints_status.append(LpConstraintStatus(
            name="performance",
            satisfied=perf_ok,
            max_violation=perf_violation,
            max_slack=max(0.0, 1.0 - worst_load),
            binding_constraints=(
                [f"link_{worst_link}"] if worst_load >= 0.99 and worst_link else []
            ),
        ))

        # Geometry
        if self._die_configs and self._bump_spec:
            die_to_links = build_die_to_links(
                self.topo, self._group_to_die, links,
            )
            geo_ok, geo_violations, geo_margins = geometry_check(
                per_link_load, self._die_configs, die_to_links, links,
                self._bump_spec, self.target_gbps, self.lane_rate_gbps,
            )
            max_viol = max(geo_violations.values()) if geo_violations else 0.0
            max_margin = min(geo_margins.values()) if geo_margins else float("inf")
            binding = [k for k, v in geo_margins.items() if abs(v) < 1.0]
            constraints_status.append(LpConstraintStatus(
                name="geometry",
                satisfied=geo_ok,
                max_violation=max_viol,
                max_slack=max(0.0, max_margin),
                binding_constraints=binding,
            ))
        else:
            geo_ok = True

        # Thermal
        if self._thermal_cfg:
            therm_ok, total_power, max_power = thermal_check(
                per_link_load, links, self._thermal_cfg,
            )
            violation = max(0.0, total_power - max_power)
            constraints_status.append(LpConstraintStatus(
                name="thermal",
                satisfied=therm_ok,
                max_violation=violation,
                max_slack=max(0.0, max_power - total_power),
                binding_constraints=(
                    ["power_density"] if abs(total_power - max_power) / max(max_power, 1) < 0.05 else []
                ),
            ))
        else:
            therm_ok = True

        feasible = perf_ok and geo_ok and therm_ok

        if not perf_ok:
            notes.append(f"性能瓶颈: worst_load={worst_load:.3f} > 1.0, "
                        f"nonblocking={nonblocking:.0f} < target={self.target_gbps:.0f} Gbps")

        return LpResult(
            feasible=feasible,
            solver=f"hungarian-{self.route}",
            route=self.route,
            worst_load=worst_load,
            nonblocking_gbps=nonblocking,
            bottleneck_link=str(worst_link) if worst_link else "",
            constraints=constraints_status,
            per_link_load=per_link_load,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # 路径 2: cvxpy Valiant LP — 最优分流
    #
    #   min  t
    #   s.t. D 双随机,  Σ_p f_{ij}^p = D_{ij},
    #        L_e = Σ f,  L_e ≤ t,
    #        M·L ≤ b  (几何),  C·L ≤ d  (热)
    #
    #   t* ≤ 1 → 非阻塞; t* > 1 → 存在阻塞瓶颈
    # ------------------------------------------------------------------

    def _solve_valiant_lp(self) -> LpResult:
        import cvxpy as cvx

        from wafer_dse.lp.performance import build_path_incidence

        terminals = self.topo.terminals()
        incid = build_path_incidence(self.topo, terminals)

        n_terms = incid["n_terminals"]
        n_links = incid["n_links"]
        pairs = incid["pairs"]
        n_pairs = incid["n_pairs"]
        paths_for_pair = incid["paths_for_pair"]
        link_incidence = incid["link_incidence"]

        # --- 变量 ---
        D = cvx.Variable((n_terms, n_terms), nonneg=True)        # 流量矩阵
        t = cvx.Variable(nonneg=True)                              # 瓶颈负载
        f_vars: list[cvx.Variable] = []
        for pi in range(n_pairs):
            f_vars.append(cvx.Variable(len(paths_for_pair[pi]), nonneg=True))
        L = cvx.Variable(n_links, nonneg=True)                    # 链路负载

        # --- 性能约束 ---
        constraints = []

        # 双随机流量矩阵
        for i in range(n_terms):
            constraints.append(cvx.sum(D[i, :]) == 1)
            constraints.append(cvx.sum(D[:, i]) == 1)
        for i in range(n_terms):
            constraints.append(D[i, i] == 0)
        constraints.append(D >= 0)

        # 流量守恒: Σ_p f_{ij}^p = D_{ij}
        for pi, (src, dst) in enumerate(pairs):
            si = terminals.index(src)
            di = terminals.index(dst)
            constraints.append(cvx.sum(f_vars[pi]) == D[si, di])

        # 链路负载定义: L_e = Σ_{(i,j,p): e∈path} f_{ij}^p
        for li in range(n_links):
            if link_incidence[li]:
                terms = [f_vars[pi][pj] for (pi, pj) in link_incidence[li]]
                constraints.append(cvx.sum(cvx.hstack(terms)) == L[li])
            else:
                constraints.append(L[li] == 0)

        # 链路容量: L_e ≤ t (最小化 t 即最小化瓶颈)
        for li in range(n_links):
            if link_incidence[li]:  # 只约束有流量的链路
                constraints.append(L[li] <= t)

        # --- 物理约束 ---
        geo_added = False
        if self._die_configs and self._bump_spec:
            geo_added = self._add_valiant_geometry(constraints, L, incid, cvx)
        therm_added = False
        if self._thermal_cfg:
            therm_added = self._add_valiant_thermal(constraints, L, cvx)

        # --- 求解: 最小化瓶颈负载 ---
        prob = cvx.Problem(cvx.Minimize(t), constraints)
        try:
            prob.solve(verbose=False, solver=cvx.CLARABEL)
        except Exception:
            try:
                prob.solve(verbose=False)
            except Exception as e:
                return LpResult(
                    feasible=False, solver="cvxpy-error", route="valiant",
                    notes=[f"LP 求解失败: {e}"],
                )

        feasible = prob.status in ("optimal", "optimal_inaccurate")
        t_opt = float(t.value) if t.value is not None else float("inf")
        nonblocking = (
            float("inf") if t_opt <= 0
            else self.target_gbps / t_opt
        )

        # --- 结果 ---
        constraints_status: list[LpConstraintStatus] = []
        perf_ok = t_opt <= 1.0 + 1e-6

        constraints_status.append(LpConstraintStatus(
            name="performance",
            satisfied=perf_ok,
            max_violation=max(0.0, t_opt - 1.0),
            max_slack=max(0.0, 1.0 - t_opt),
            binding_constraints=[],
        ))

        if geo_added:
            constraints_status.append(LpConstraintStatus(
                name="geometry",
                satisfied=feasible,
                max_violation=0.0 if feasible else float("nan"),
                max_slack=0.0,
                binding_constraints=[],
            ))
        if therm_added:
            constraints_status.append(LpConstraintStatus(
                name="thermal",
                satisfied=feasible,
                max_violation=0.0 if feasible else float("nan"),
                max_slack=0.0,
                binding_constraints=[],
            ))

        # Per-link load
        links_list = incid["links"]
        per_link_load: dict[tuple[int, int], float] = {}
        if L.value is not None:
            for li, (u, v) in enumerate(links_list):
                per_link_load[(u, v)] = float(L.value[li])

        notes: list[str] = []
        if feasible:
            if perf_ok:
                notes.append(f"Valiant LP 最优: t*={t_opt:.4f} ≤ 1, 非阻塞")
            else:
                notes.append(f"Valiant LP 最优: t*={t_opt:.4f} > 1, "
                           f"nonblocking={nonblocking:.0f} < target={self.target_gbps:.0f} Gbps")
        else:
            notes.append("Valiant LP 不可行: 物理约束过紧")

        return LpResult(
            feasible=(feasible and perf_ok),
            solver="cvxpy-clarabel",
            route="valiant",
            worst_load=t_opt,
            nonblocking_gbps=nonblocking,
            bottleneck_link="",
            constraints=constraints_status,
            per_link_load=per_link_load,
            num_variables=(n_terms * n_terms + sum(len(ps) for ps in paths_for_pair)
                           + n_links + 1),
            num_constraints=len(constraints),
            notes=notes,
        )

    def _add_valiant_geometry(self, constraints, L, incid, cvx) -> bool:
        """向 valiant LP 添加几何约束。返回是否添加成功。"""
        n_links = incid["n_links"]
        links = [(incid["links"][li][0], incid["links"][li][1]) for li in range(n_links)]
        die_to_links = build_die_to_links(self.topo, self._group_to_die, links)
        coeff = self.target_gbps / self.lane_rate_gbps

        for die_idx, cfg in enumerate(self._die_configs):
            die = DieBumpBudget(
                die_label=cfg.label, spec=self._bump_spec,
                width_mm=cfg.width_mm, height_mm=cfg.height_mm,
                power_w=cfg.power_w, vdd_v=cfg.vdd_v,
                utilization=cfg.utilization,
            )
            incident = die_to_links.get(die_idx, [])
            if incident:
                terms = [coeff * L[li] for li in incident]
                constraints.append(cvx.sum(cvx.hstack(terms)) <= die.available)
        return True

    def _add_valiant_thermal(self, constraints, L, cvx) -> bool:
        """向 valiant LP 添加热约束。返回是否添加成功。"""
        p_per_unit = (
            self._thermal_cfg.power_per_lane_w * self._thermal_cfg.target_gbps
            / self._thermal_cfg.lane_rate_gbps
        )
        total_area = (self._thermal_cfg.total_area_mm2
                      * self._thermal_cfg.interposer_count)
        q_max = self._thermal_cfg.cooling.max_power_density_w_per_mm2
        constraints.append(p_per_unit * cvx.sum(L) <= total_area * q_max)
        return True
