from contracts.graph import Graph, Node, Edge
from context_graph_builder.alias_resolver import build_public_alias_map


def test_alias_map_derived_from_reexport_import():
    graph = Graph(framework="test", version="1.0", nodes={
        "pkg.base.Model": Node(id="pkg.base.Model", type="Class", name="Model", file="base.py", line=1),
    }, edges=[
        Edge(from_id="pkg.models", to_id="pkg.base.Model", type="imports"),
    ])

    alias_map = build_public_alias_map(graph)

    assert alias_map["pkg.models.Model"] == "pkg.base.Model"


def test_no_alias_for_non_import_edges():
    graph = Graph(framework="test", version="1.0", nodes={
        "pkg.base.Model": Node(id="pkg.base.Model", type="Class", name="Model", file="base.py", line=1),
    }, edges=[
        Edge(from_id="pkg.views.foo", to_id="pkg.base.Model", type="calls"),
    ])

    alias_map = build_public_alias_map(graph)

    assert alias_map == {}