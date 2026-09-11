from context_graph_builder.resolver import build_graph, FileInfo


def test_cross_file_call_resolves_through_import():
    models_source = """
class Model:
    def save(self, force_insert=False):
        pass
"""
    views_source = """
from models import Model

def create_user():
    Model.save(None, force_insert=True)
"""

    files = [
        FileInfo(file_path="models.py", module_prefix="models", source=models_source),
        FileInfo(file_path="views.py", module_prefix="views", source=views_source),
    ]

    graph = build_graph(framework="testapp", version="1.0", files=files)

    # nodes from both files should be present
    assert "models.Model" in graph.nodes
    assert "models.Model.save" in graph.nodes
    assert "views.create_user" in graph.nodes

    # the import edge
    import_edges = [e for e in graph.edges if e.type == "imports"]
    assert any(e.from_id == "views" and e.to_id == "models.Model" for e in import_edges)

    # the cross-file call edge — the actual thing we're testing
    call_edges = [e for e in graph.edges if e.type == "calls"]
    assert any(
        e.from_id == "views.create_user" and e.to_id == "models.Model.save"
        for e in call_edges
    )