# Derives a mapping from a framework's "public" import paths to their "real" definition ids, using the framework's own internal "imports" edges (already captured by the resolver during graph building).

from contracts.graph import Graph

def build_public_alias_map(graph: Graph) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for edge in graph.edges:
        if edge.type != "imports":
            continue
        if edge.to_id not in graph.nodes:
            continue

        last_segment = edge.to_id.split(".")[-1]
        alias_id = f"{edge.from_id}.{last_segment}"
        if alias_id == edge.to_id:
            continue

        alias_map[alias_id] = edge.to_id

    return alias_map
