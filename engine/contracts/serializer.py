# Converts a Graph to/from JSON so we can cache the built graphs on disk instead of rebuilding from source everytime.
import json
from dataclasses import asdict
from contracts.graph import Graph, Node, Param, Edge

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
