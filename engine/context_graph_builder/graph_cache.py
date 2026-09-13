# Gets a framework's semantic Graph for a given version, transparently using a cached JSON graph if one exists, or building (and caching) a fresh one from source if not.

from pathlib import Path
from contracts.graph import Graph
from contracts.serializer import save_graph, load_graph
from context_graph_builder.tarball_ingestion import fetch_source
from context_graph_builder.file_loader import build_graph_from_directory

def get_or_build_graph(framework: str, version: str, cache_dir: str = "./graph_cache") -> Graph:
    cache_path = Path(cache_dir) / f"{framework}_{version}_graph.json"
    if cache_path.exists():
        return load_graph(str(cache_path))
    source_root = fetch_source(framework, version)
    graph = build_graph_from_directory(framework, version, str(source_root))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    save_graph(graph, str(cache_path))
    return graph