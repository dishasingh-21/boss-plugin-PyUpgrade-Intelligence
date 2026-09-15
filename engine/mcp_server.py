# MCP Server exposing the engine's orchestrator functions as tools an AI agent can call.

import os
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
from dataclasses import asdict
from mcp.server import MCPServer
from orchestrator.pipeline import(upgrade_check as _upgrade_check, get_breaking_changes as _get_breaking_changes, get_usage_in_code as _get_usage_in_code, get_affected_files_raw as _get_affected_files_raw, get_affected_files_enriched as _get_affected_files_enriched, run_full_pipeline as _run_full_pipeline, warm_cache as _warm_cache)
from diff_engine.config_differ import diff_config_files
from context_graph_builder.tarball_ingestion import fetch_source
from context_graph_builder.graph_cache import list_cached_graphs
from all_outputs_bundler import bundle_run_outputs
from contracts.diff import ChangeType

mcp = MCPServer("pyupgrade-intelligence")
_HIGH_CONFIDENCE_TYPES = {ChangeType.REMOVED, ChangeType.SIGNATURE_CHANGED, ChangeType.MOVED_ALSO_SIGNATURE_CHANGED, ChangeType.MOVED_UNCHANGED}

@mcp.tool()
def upgrade_check(framework: str, version_from: str, version_to: str, repo_path: str) -> dict:
    """
    Check risk of upgrading a Python framework from one version to another, for a specific codebase.
    Returns a compact, auditable risk score (0-100), a recommendation (UPGRADE/UPGRADE_WITH_CAUTION/HOLD), the specific symbol driving the score, and a short list of affected files with exact lines.
    Use this as the default first call or any upgrade question.
    If this is the first time checking this framework/version pair in this session, call warm_graph_cache for both versions first to avoid a slow first-time build inside this call.
    """
    report = _upgrade_check(framework, version_from, version_to, repo_path)
    return asdict(report)

@mcp.tool()
def get_breaking_changes(framework: str, version_from: str, version_to: str, include_low_confidence: bool = False) -> dict:
    """
    Get the structural diff between two framework versions, without cross-referencing any specific codebase -- useful for exploring what changed in general.
    By default only returns high-confidence changes (removed symbols, signature changes, moves).
    Set include_low_confidence=True to also include other types of entries.
    """
    result = _get_breaking_changes(framework, version_from, version_to)
    changes = result.changes if include_low_confidence else [c for c in result.changes if c.change_type in _HIGH_CONFIDENCE_TYPES]
    return {
        "framework": result.framework,
        "version_from": result.version_from,
        "version_to": result.version_to,
        "total_changes": len(result.changes),
        "shown_changes": len(changes),
        "changes": [asdict(c) for c in changes]
    }

@mcp.tool()
def get_usage_in_code(framework: str, version_from: str, repo_path: str, enriched: bool = False) -> dict:
    """
    List every framework symbol a codebase actually uses, with file and
    line for each usage, independent of any version comparison. Useful
    for understanding a codebase's footprint on a framework, e.g. before
    planning a refactor, not just before an upgrade.
    """
    usage_index = _get_usage_in_code(framework, version_from, repo_path, enriched=enriched)
    total_usages = sum(len(v) for v in usage_index.usages.values())
    return {
        "repo_path": usage_index.repo_path,
        "distinct_symbols_used": len(usage_index.usages),
        "total_usage_sites": total_usages,
        "usages": {sid: [asdict(u) for u in ul] for sid, ul in usage_index.usages.items()}
    }

@mcp.tool()
def get_affected_files(framework: str, version_from: str, version_to: str, repo_path: str, enriched: bool = False) -> dict:
    """
     Get just the specific files and lines in a codebase affected by changes between two framework versions, narrower and faster than upgrade_check when only the locations are needed, not a full score.
     By default returns just file/line/symbol/detail (fast). Set enriched=True to also get the actual source line from the codebase, before/after signatures for signature changes, and real body diff text for implementation changes, more useful or explaining a change.
    """
    if enriched:
        files = _get_affected_files_enriched(framework, version_from, version_to, repo_path)
    else:
        files = _get_affected_files_raw(framework, version_from, version_to, repo_path)
    return {"affected_files": [asdict(f) for f in files]}

@mcp.tool()
def get_config_diff(framework: str, version_from: str, version_to: str) -> dict:
    """
    Get the plain text diff of config/dependency files (pyproject.toml, setup.py, setup.cfg, requirements.txt) between two framework versions.
    Dependency and configuration changes like a bumped minimum Python version or a changed pinned dependency can be as breaking as a code change.
    """
    root_a = fetch_source(framework, version_from)
    root_b = fetch_source(framework, version_to)
    result = diff_config_files(str(root_a.parent), str(root_b.parent))
    return {"changed_files": result}

@mcp.tool()
def list_cached_semantic_graphs() -> dict:
    """
    List every framework version whose semantic graph is already built and cached locally, avoiding a redundant re-download/re-parse.
    """
    return {"cached": list_cached_graphs()}

@mcp.tool()
def warm_graph_cache(framework: str, version: str, package_name: str = None) -> dict:
    """
        Pre-builds and caches a framework version's semantic graph without
        running a full check. Call this FIRST, once per version, before
        upgrade_check or get_breaking_changes on a framework/version pair
        you haven't checked before in this session -- the first-time
        build can be slow (downloading and parsing the framework's full
        source), and calling this ahead of time avoids that cost landing
        inside a time-limited check call. If the framework's import name
        differs from its PyPI name (e.g. 'livekit-agents' installs as
        'livekit'), pass package_name explicitly.
    """
    return _warm_cache(framework, version, package_name=package_name)

@mcp.tool()
def export_debug_bundle(framework: str, version_from: str, version_to: str, repo_path: str, out_path: str = "pyupgrade_debug_bundle.zip", include: str = "all") -> dict:
    """
    Export the FULL raw output of every pipeline stage (semantic graphs, raw and enriched diffs, config diff, usage index, risk report) as a zip file, for deep debugging or manual inspection.
    This is a heavy operation, only call this when explicitly asked for raw/debug data, never as part of a normal upgrade check.
    """
    all_parts = {"graph", "diff-raw", "diff-enriched", "config-diff", "usage", "risk"}
    parts = all_parts if include == "all" else set(include.split(","))
    result = _run_full_pipeline(framework, version_from, version_to, repo_path)
    zip_path = bundle_run_outputs(
        output_dir="mcp_export_temp",
        graph_a=result.graph_a if "graph" in parts else None,
        graph_b=result.graph_b if "graph" in parts else None,
        diff_result_raw=result.diff_result_raw if "diff-raw" in parts else None,
        diff_result_enriched=result.diff_result_enriched if "diff-enriched" in parts else None,
        config_diff=result.config_diff if "config-diff" in parts else None,
        usage_index=result.usage_index if "usage" in parts else None,
        risk_report=result.risk_report if "risk" in parts else None,
        zip_path=out_path
    )
    return {"zip_path": zip_path}

if __name__ == "__main__":
    mcp.run()
