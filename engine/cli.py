# Command-line interface for PyUpgrade Intelligence. Every command is a thin wrapper around an orchestrator function.
# NOTE: The 'graph' visualization command from the spec is not yet implemented.

import argparse
from orchestrator.pipeline import (upgrade_check, get_breaking_changes, get_affected_files_raw, get_affected_files_enriched, get_usage_in_code, run_full_pipeline)
from diff_engine.config_differ import diff_config_files
from context_graph_builder.tarball_ingestion import fetch_source
from context_graph_builder.graph_cache import list_cached_graphs, clear_cache
from all_outputs_bundler import bundle_run_outputs

def _progress(message: str) -> None:
    print(f"  ... {message}")

def cmd_check(args):
    report = upgrade_check(args.framework, args.from_version, args.to_version, args.repo, on_progress=_progress)
    print(f"Risk score: {report.score}/100 - {report.recommendation.value}")
    print(f"Relevant changes: {report.relevant_changes_count} / {report.total_changes_in_diff}")
    print(f"Worst Symbol: {report.worst_change_symbol}")
    print("\nBreakdown:")
    for entry in report.score_breakdown:
        print(f"    {entry.category}: {entry.count} x {entry.severity} = {entry.severity * entry.count:.2f}")
    print("\nAffected files:")
    for fr in report.affected_files:
        print(f"    {fr.file}:{fr.line} -> {fr.symbol_id} ({fr.change_type})")

def cmd_changes(args):
    result = get_breaking_changes(args.framework, args.from_version, args.to_version, on_progress=_progress)
    default_types = {"SIGNATURE_CHANGED", "REMOVED", "MOVED_ALSO_SIGNATURE_CHANGED", "MOVED_UNCHANGED"}
    types_filter = set(args.type.split(",")) if args.type else default_types
    shown = [c for c in result.changes if c.change_type.value in types_filter]
    print(f"{len(shown)} shown (of {len(result.changes)} total; use --type to widen, e.g. --type BODY_CHANGED)")
    for c in shown:
        print(f"    [{c.change_type.value}] {c.symbol_id} --> {c.detail}")

def cmd_usage(args):
    usage_index = get_usage_in_code(args.framework, args.version, args.repo, on_progress=_progress)
    total_usages = sum(len(usages) for usages in usage_index.usages.values())
    print(f"{len(usage_index.usages)} distinct symbols used, {total_usages} total usage sites.\n")
    for symbol_id, usages in usage_index.usages.items():
        print(f"{symbol_id}    ({len(usages)} usage{'s' if len(usages)>1 else ''})")
        for u in usages:
            print(f"   {u.file}:{u.line}")

def cmd_affected(args):
    if args.enriched:
        files = get_affected_files_enriched(args.framework, args.from_version, args.to_version, args.repo, on_progress=_progress)
    else:
        files = get_affected_files_raw(args.framework, args.from_version, args.to_version, args.repo, on_progress=_progress)
    for fr in files:
        print(f"{fr.file}:{fr.line} -> {fr.symbol_id} ({fr.change_type})")
        if args.enriched and fr.code_snippet:
            print(f"CODE SNIPPET    | {fr.code_snippet}")
        if args.enriched and fr.old_signature:
            print(f"SIGNATURE CHANGE    | {fr.old_signature} -> {fr.new_signature}\n")
        if args.enriched and fr.body_diff_text:
            print("BODY CHANGE    | ", fr.body_diff_text, "\n")

def cmd_config_diff(args):
    print("  ... Fetching source for both versions...")
    root_a = fetch_source(args.framework, args.from_version)
    root_b = fetch_source(args.framework, args.to_version)
    result = diff_config_files(str(root_a.parent), str(root_b.parent))
    print()
    if not result:
        print("No config/dependency file changes detected.")
    for filename, text in result.items():
        print(f"<--- {filename} --->")
        print(text)

def cmd_export(args):
    all_parts = {"graph", "diff-raw", "diff-enriched", "config-diff", "usage", "risk"}
    parts = all_parts if args.include == "all" else set(args.include.split(","))
    result = run_full_pipeline(args.framework, args.from_version, args.to_version, args.repo, on_progress=_progress)
    print("Writing bundle...")
    zip_path = bundle_run_outputs(
        output_dir="cli_export_temp",
        graph_a=result.graph_a if "graph" in parts else None,
        graph_b=result.graph_b if "graph" in parts else None,
        diff_result_raw=result.diff_result_raw if "diff-raw" in parts else None,
        diff_result_enriched=result.diff_result_enriched if "diff-enriched" in parts else None,
        config_diff=result.config_diff if "config-diff" in parts else None,
        usage_index=result.usage_index if "usage" in parts else None,
        risk_report=result.risk_report if "risk" in parts else None,
        zip_path=args.out,
    )
    print(f"Exported to {zip_path}")

def cmd_cache_list(args):
    entries = list_cached_graphs()
    if not entries:
        print("No cached graphs found.")
        return
    for e in entries:
        print(f"{e['framework']} {e['version']} - {e['size_kb']} KB - {e['path']}")

def cmd_cache_clear(args):
    removed = clear_cache(framework=args.framework)
    print(f"Removed {removed} cached graph(s).")

def build_parser():
    parser = argparse.ArgumentParser(prog="pyupgrade")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check")
    p.add_argument("framework")
    p.add_argument("from_version")
    p.add_argument("to_version")
    p.add_argument("--repo", required=True)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("changes")
    p.add_argument("framework")
    p.add_argument("from_version")
    p.add_argument("to_version")
    p.add_argument("--type")
    p.set_defaults(func=cmd_changes)

    p = sub.add_parser("usage")
    p.add_argument("framework")
    p.add_argument("version")
    p.add_argument("--repo", required=True)
    p.set_defaults(func=cmd_usage)

    p = sub.add_parser("affected")
    p.add_argument("framework")
    p.add_argument("from_version")
    p.add_argument("to_version")
    p.add_argument("--repo", required=True)
    p.add_argument("--enriched", action="store_true")
    p.set_defaults(func=cmd_affected)

    p = sub.add_parser("config-diff")
    p.add_argument("framework")
    p.add_argument("from_version")
    p.add_argument("to_version")
    p.set_defaults(func=cmd_config_diff)

    p = sub.add_parser("export")
    p.add_argument("framework")
    p.add_argument("from_version")
    p.add_argument("to_version")
    p.add_argument("--repo", required=True)
    p.add_argument("--include", default="all")
    p.add_argument("--out", default="pyupgrade_export.zip")
    p.set_defaults(func=cmd_export)

    cache_parser = sub.add_parser("cache")
    cache_sub = cache_parser.add_subparsers(dest="cache_command", required=True)
    p = cache_sub.add_parser("list")
    p.set_defaults(func=cmd_cache_list)
    p = cache_sub.add_parser("clear")
    p.add_argument("framework", nargs="?", default=None)
    p.set_defaults(func=cmd_cache_clear)

    return parser

def main():
    args = build_parser().parse_args()
    args.func(args)

if __name__ == "__main__":
    main()