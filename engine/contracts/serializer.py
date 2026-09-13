# Converts a Graph to/from JSON so we can cache the built graphs on disk instead of rebuilding from source everytime.
import json
from dataclasses import asdict
from contracts.graph import Graph, Node, Param, Edge
from contracts.diff import DiffResult, Change, ChangeType
from contracts.usage import Usage, UsageIndex
from contracts.risk import RiskReport, FileRisk, ScoreBreakdownEntry, Recommendation

def save_graph(graph: Graph, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(graph), f, indent=2)

def load_graph(path: str) -> Graph:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    nodes: dict[str, Node] = {}
    for node_id, node_data in data["nodes"].items():
        params = [Param(**p) for p in node_data["params"]]
        nodes[node_id] = Node(**{**node_data, "params": params})
    edges = [Edge(**e) for e in data["edges"]]
    return Graph(framework=data["framework"], version=data["version"], nodes=nodes, edges=edges)

def save_diff_result(result: DiffResult, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2)

def load_diff_result(path: str) -> DiffResult:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    changes = []
    for c in data["changes"]:
        old_node = Node(**{**c["old"], "params": [Param(**p) for p in c["old"]["params"]]}) if c["old"] else None
        new_node = Node(**{**c["new"], "params": [Param(**p) for p in c["new"]["params"]]}) if c["new"] else None
        changes.append(Change(
            symbol_id=c["symbol_id"],
            change_type=ChangeType(c["change_type"]),
            old=old_node,
            new=new_node,
            detail=c["detail"],
            body_diff_text=c.get("body_diff_text", "")
        ))
    return DiffResult(
        framework=data["framework"],
        version_from=data["version_from"],
        version_to=data["version_to"],
        changes=changes
    )

def save_usage_index(index: UsageIndex, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(index), f, indent=2)

def load_usage_index(path: str) -> UsageIndex:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    usages = {
        symbol_id: [Usage(**u) for u in usage_list]
        for symbol_id, usage_list in data["usages"].items()
    }
    return UsageIndex(repo_path=data["repo_path"], usages=usages)

def save_risk_report(report: RiskReport, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2)

def load_risk_report(path: str) -> RiskReport:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return RiskReport(
        framework = data["framework"],
        version_from = data["version_from"],
        version_to = data["version_to"],
        score = data["score"],
        recommendation = Recommendation(data["recommendation"]),
        max_severity = data["max_severity"],
        breadth = data["breadth"],
        worst_change_symbol = data.get("worst_change_symbol"),
        score_breakdown = [ScoreBreakdownEntry(**b) for b in data["score_breakdown"]],
        affected_files = [FileRisk(**f) for f in data["affected_files"]],
        total_changes_in_diff = data["total_changes_in_diff"],
        relevant_changes_count = data["relevant_changes_count"],
    )

