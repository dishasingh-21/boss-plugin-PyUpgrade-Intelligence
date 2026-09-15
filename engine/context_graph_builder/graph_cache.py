# Gets a framework's semantic Graph for a given version, transparently using a cached JSON graph if one exists, or building (and caching) a fresh one from source if not.

from pathlib import Path
from contracts.graph import Graph
from contracts.serializer import save_graph, load_graph
from context_graph_builder.tarball_ingestion import fetch_source
from context_graph_builder.file_loader import build_graph_from_directory

def get_or_build_graph(framework: str, version: str, cache_dir: str = "./graph_cache", package_name: str | None=None) -> Graph:
    cache_path = Path(cache_dir) / f"{framework}_{version}_graph.json"
    if cache_path.exists():
        return load_graph(str(cache_path))
    source_root = fetch_source(framework, version, package_name=package_name)
    graph = build_graph_from_directory(framework, version, str(source_root))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    save_graph(graph, str(cache_path))
    return graph

def list_cached_graphs(cache_dir: str = "./graph_cache") -> list[dict]:
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return []

    results = []
    for f in cache_path.glob("*_graph.json"):
        stem = f.stem
        parts = stem.rsplit("_", 1)
        fv = parts[0] if len(parts)==2 else stem
        fv_parts = fv.rsplit("_", 1)
        framework = fv_parts[0] if len(fv_parts)==2 else fv
        version = fv_parts[1] if len(fv_parts)==2 else ""
        stat = f.stat()
        results.append({"framework": framework, "version": version, "path": str(f), "size_kb": round(stat.st_size/1024, 1)})

    return results

def clear_cache(cache_dir: str = "./graph_cache", framework: str | None=None) -> int:
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return 0
    pattern = f"{framework}_*_graph.json" if framework else "*_graph.json"
    removed = 0
    for f in cache_path.glob(pattern):
        f.unlink()
        removed+=1

    return removed
