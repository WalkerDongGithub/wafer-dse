"""用户指令级 DSE 驱动。

输入：用户需求配置，其中包含目标无阻塞带宽、功耗上限、严格程度、封装配置和拓扑候选。
输出：每个 topology 的耦合可行性报告。
目的：把 architecture model 与 packaging model 串起来，判断拓扑是否至少有落地潜力。
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from wafer_dse.architecture_model import ArchitectureModel
from wafer_dse.config import load_config
from wafer_dse.models import FeasibilityReport, Requirement, Strictness, TopologySpec
from wafer_dse.packaging_model.model import PackagingModel
from wafer_dse.reporting.report import write_reports


CERTIFICATE_FAIL = {"not_implemented", "unknown"}


def parse_requirement(cfg: dict) -> Requirement:
    """输入配置 dict，输出标准 Requirement。"""
    # 用户指令只保留当前必要目标：带宽、功耗、严格程度、封装配置。
    r = cfg["requirement"]
    s = r.get("strictness", {})
    return Requirement(
        target_nonblocking_gbps_per_port=float(r["target_nonblocking_gbps_per_port"]),
        max_power_w=float(r["max_power_w"]),
        strictness=Strictness(mode=s.get("mode", "full"), percent=s.get("percent"), benchmark=s.get("benchmark")),
        packaging_config=str(r["packaging_config"]),
        port_count=r.get("port_count"),
        max_die_area_mm2=r.get("max_die_area_mm2"),
    )


def parse_topologies(cfg: dict) -> list[TopologySpec]:
    """输入配置 dict，输出拓扑候选列表。"""
    # 当前只考查拓扑结构；不同 route 作为同一拓扑的体系结构策略变体。
    specs: list[TopologySpec] = []
    topology_cfg = cfg["topologies"]
    items = topology_cfg.values() if isinstance(topology_cfg, dict) else topology_cfg
    for item in items:
        for route in item.get("routes", ["det"]):
            specs.append(TopologySpec(kind=item["kind"], size=item.get("size"), route=route, a=item.get("a"), p=item.get("p"), h=item.get("h")))
    return specs


def couple(req: Requirement, spec: TopologySpec, arch: ArchitectureModel, pack: PackagingModel) -> FeasibilityReport:
    """输入一个拓扑预案，输出网络-封装耦合可行性判断。"""
    # 1) 体系结构级初筛：得到无阻塞潜能和 required speedup。
    network = arch.evaluate(req, spec)

    # 2) 封装级初筛：根据网络需求估算面积、功耗和 IO 预算。
    packaging = pack.estimate(req, network)

    # 3) 耦合判断：端口、内部链路、面积、功耗、证书都必须通过。
    fail: list[str] = []
    port_count = req.port_count or network.terminal_count
    if port_count != network.terminal_count:
        fail.append("terminal_count_mismatch")
    if network.certificate_status in CERTIFICATE_FAIL:
        fail.append("certificate_not_available")
    if not packaging.external_ports_ok:
        fail.append("external_ports")
    if not packaging.internal_links_ok:
        fail.append("internal_links")
    if not packaging.area_ok:
        fail.append("die_area")
    if not packaging.power_ok:
        fail.append("power")

    feasible = not fail
    recommendation = _recommendation(fail)
    return FeasibilityReport(req, spec, network, packaging, feasible, tuple(fail), recommendation)


def _recommendation(fail: list[str]) -> str:
    """根据失败原因给出简短建议。"""
    if not fail:
        return "两关均通过：该拓扑至少具有进入详细实现研究的潜力。"
    if "certificate_not_available" in fail:
        return "先补充对应严格程度的体系结构求解器或 benchmark traffic。"
    if "terminal_count_mismatch" in fail:
        return "调整端口数或拓扑规模，使 terminal 数与需求一致。"
    if "internal_links" in fail:
        return "网络需要的内部 speedup 超过封装 lane 预算；考虑换 topology/routing 或提高 lane rate。"
    if "external_ports" in fail:
        return "外部端口超过 connector/lane 预算；考虑减少端口或更强封装。"
    if "power" in fail:
        return "功耗超过上限；优先降低 SerDes/lane 功耗或减少内部 speedup。"
    if "die_area" in fail:
        return "面积超过上限；优先降低 lane 数、buffer/router 面积或换更大 die/先进工艺。"
    return "存在多个瓶颈，需要同时调整拓扑和封装配置。"


def run(config_path: str | Path):
    """输入用户配置路径，运行 DSE 并写出报告。"""
    cfg_path = Path(config_path)
    cfg = load_config(cfg_path)
    req = parse_requirement(cfg)
    pack_path = (cfg_path.parent / req.packaging_config).resolve() if not Path(req.packaging_config).is_absolute() else Path(req.packaging_config)
    req = Requirement(req.target_nonblocking_gbps_per_port, req.max_power_w, req.strictness, str(pack_path), req.port_count, req.max_die_area_mm2)

    arch = ArchitectureModel()
    pack = PackagingModel(req.packaging_config)
    reports = [couple(req, spec, arch, pack) for spec in parse_topologies(cfg)]

    out_dir = Path(cfg.get("output", {}).get("directory", "outputs"))
    if not out_dir.is_absolute():
        out_dir = cfg_path.parent / out_dir
    write_reports(out_dir, reports)
    return reports


def reports_as_dicts(reports: list[FeasibilityReport]) -> list[dict]:
    """把 dataclass 报告转换成可 JSON 序列化的 dict。"""
    return [asdict(r) for r in reports]
