# Bundles every component's raw output into a single zip file, mirroring the engine's own folder structure.

import zipfile
import json
from pathlib import Path
from dataclasses import asdict

def bundle_run_outputs(output_dir: str, graph_a=None, graph_b=None, diff_result_raw=None, diff_result_enriched=None, config_diff:dict | None=None, usage_index=None, changelog=None, risk_report=None, zip_path: str = "PyUpgrade_Intelligence_run_outputs.zip") -> str:
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    folders = {
        "context_graph_builder": base / "context_graph_builder",
        "diff_engine": base / "diff_engine",
        "usage_indexer": base / "usage_indexer",
        "changelog_parser": base / "changelog_parser",
        "risk_scorer": base / "risk_scorer",
    }
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    if graph_a is not None:
        _write_json(folders["context_graph_builder"] / "old_graph.json", asdict(graph_a))
    if graph_b is not None:
        _write_json(folders["context_graph_builder"] / "new_graph.json", asdict(graph_b))
    if diff_result_raw is not None:
        _write_json(folders["diff_engine"] / "diff_result_raw.json", asdict(diff_result_raw))
    if diff_result_enriched is not None:
        _write_json(folders["diff_engine"] / "diff_result_enriched.json", asdict(diff_result_enriched))
    if config_diff is not None:
        _write_json(folders["diff_engine"] / "config_diff.json", config_diff)
    if usage_index is not None:
        _write_json(folders["usage_indexer"] / "usage_index.json", asdict(usage_index))
    if changelog is not None:
        _write_json(folders["changelog_parser"] / "changelog.json", changelog)
    if risk_report is not None:
        _write_json(folders["risk_scorer"] / "risk_scorer.json", risk_report)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in base.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, arcname=file_path.relative_to(base))
    return zip_path

def _write_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

