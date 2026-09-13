from contracts.graph import Graph, Node
from contracts.serializer import save_graph
from context_graph_builder.graph_cache import get_or_build_graph


def test_returns_cached_graph_without_fetching(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    graph = Graph(framework="test", version="1.0", nodes={
        "test.foo": Node(id="test.foo", type="Function", name="foo", file="x.py", line=1),
    })
    save_graph(graph, str(cache_dir / "test_1.0_graph.json"))

    def fail_if_called(*args, **kwargs):
        raise AssertionError("fetch_source should not be called when a cached graph exists")

    monkeypatch.setattr("context_graph_builder.graph_cache.fetch_source", fail_if_called)

    result = get_or_build_graph("test", "1.0", cache_dir=str(cache_dir))

    assert "test.foo" in result.nodes