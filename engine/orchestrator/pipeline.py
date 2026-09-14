# Wires every engine component into clean, single-purpose functions. This is what every CLI command and MCP tool calls directly.

import copy
from dataclasses import dataclass
from pathlib import Path
from contracts.graph import Graph
from contracts.diff import DiffResult
from contracts.usage import UsageIndex
from contracts.risk import RiskReport, FileRisk
from context_graph_builder.graph_cache import get_or_build_graph
from context_graph_builder.tarball_ingestion import fetch_source
from diff_engine.differ import diff
from diff_engine.enricher import enrich_body_diffs
from diff_engine.config_differ import diff_config_files
from usage_indexer.indexer import build_usage_index
from risk_scorer.scorer import score_risk
from risk_scorer.enricher import enrich_affected_files

def upgrade_check(framework: str, version_from: str, version_to: str, repo_path: str) -> RiskReport:
    # To get risk report and upgrade recommendation.
    graph_a = get_or_build_graph(framework, version_from)
    graph_b = get_or_build_graph(framework, version_to)
    diff_result = diff(graph_a, graph_b)
    usage_index = build_usage_index(repo_path, graph_a)
    return score_risk(diff_result, usage_index)

def get_breaking_changes(framework: str, version_from: str, version_to: str) -> DiffResult:
    # Breaking changes that will surface up when you upgrade to the framework's target version.
    graph_a = get_or_build_graph(framework, version_from)
    graph_b = get_or_build_graph(framework, version_to)
    return diff(graph_a, graph_b)

def get_usage_in_code(framework: str, version: str, repo_path: str) -> UsageIndex:
    # Raw usage — every framework symbol the user's repo code matches against, regardless of whether any of them changed.
    graph = get_or_build_graph(framework, version)
    return build_usage_index(repo_path, graph)

def get_affected_files_raw(framework: str, version_from: str, version_to: str, repo_path: str) -> list[FileRisk]:
    # Fast path: file/line/symbol/change-type/detail only
    report = upgrade_check(framework, version_from, version_to, repo_path)
    return report.affected_files

def get_affected_files_enriched(framework: str, version_from: str, version_to: str, repo_path: str) -> list[FileRisk]:
    # Slower, richer path: real body diff text for BODY_CHANGED symbols, plus the actual line of the user's own code that triggered each match.
    graph_a = get_or_build_graph(framework, version_from)
    graph_b = get_or_build_graph(framework, version_to)
    diff_result_raw = diff(graph_a, graph_b)
    diff_result_for_enriched = copy.deepcopy(diff_result_raw)
    source_root_a = fetch_source(framework, version_from)
    source_root_b = fetch_source(framework, version_to)
    old_source = _read_source_by_file(source_root_a)
    new_source = _read_source_by_file(source_root_b)
    diff_result_enriched = enrich_body_diffs(diff_result_for_enriched, old_source, new_source)
    usage_index = build_usage_index(repo_path, graph_a)
    risk_report = score_risk(diff_result_raw, usage_index)
    repo_source = _read_source_by_file(repo_path)
    return enrich_affected_files(risk_report.affected_files, diff_result_enriched, repo_source)

@dataclass
class FullPipelineResult:
    graph_a: Graph
    graph_b: Graph
    diff_result_raw: DiffResult
    diff_result_enriched: DiffResult
    config_diff: dict
    usage_index: UsageIndex
    risk_report: RiskReport

def run_full_pipeline(framework: str, version_from: str, version_to: str, repo_path: str) -> FullPipelineResult:
    # Run the whole pipeline, get a debug bundle (zip file containing raw outputs of each component.
    graph_a = get_or_build_graph(framework, version_from)
    graph_b = get_or_build_graph(framework, version_to)
    diff_result_raw = diff(graph_a, graph_b)
    diff_result_for_enriched = copy.deepcopy(diff_result_raw)
    source_root_a = fetch_source(framework, version_from)
    source_root_b = fetch_source(framework, version_to)
    old_source = _read_source_by_file(source_root_a)
    new_source = _read_source_by_file(source_root_b)
    diff_result_enriched = enrich_body_diffs(diff_result_for_enriched, old_source, new_source)
    config_diff = diff_config_files(str(source_root_a.parent), str(source_root_b.parent))
    usage_index = build_usage_index(repo_path, graph_a)
    risk_report = score_risk(diff_result_raw, usage_index)

    return FullPipelineResult(
        graph_a=graph_a,
        graph_b=graph_b,
        diff_result_raw=diff_result_raw,
        diff_result_enriched=diff_result_enriched,
        config_diff=config_diff,
        usage_index=usage_index,
        risk_report=risk_report
    )

def _read_source_by_file(root_dir) -> dict[str,str]:
    root = Path(root_dir)
    sources = {}
    for py_file in root.rglob("*.py"):
        try:
            sources[str(py_file)] = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
    return sources