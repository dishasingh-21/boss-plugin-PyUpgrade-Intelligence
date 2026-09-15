import os
from context_graph_builder.file_loader import build_graph_from_directory
from contracts.serializer import save_graph, load_graph


def test_builds_graph_from_real_directory(tmp_path):
    # tmp_path is a pytest built-in fixture: a temporary folder,
    # auto-created and auto-cleaned-up for each test run.
    (tmp_path / "models.py").write_text(
        "class Model:\n    def save(self, force_insert=False):\n        pass\n"
    )
    (tmp_path / "views.py").write_text(
        "from models import Model\n\ndef create_user():\n    Model.save(None, force_insert=True)\n"
    )

    graph = build_graph_from_directory("testapp", "1.0", str(tmp_path))

    root_name = tmp_path.name
    assert f"{root_name}.models.Model.save" in graph.nodes
    assert f"{root_name}.views.create_user" in graph.nodes
    assert any(e.type == "calls" and e.to_id == f"{root_name}.models.Model.save" for e in graph.edges)

def test_inheritance_edge_detected(tmp_path):
    (tmp_path / "base.py").write_text("class Base:\n    pass\n")
    (tmp_path / "child.py").write_text("from base import Base\n\nclass Child(Base):\n    pass\n")

    graph = build_graph_from_directory("testapp", "1.0", str(tmp_path))

    root_name = tmp_path.name
    assert any(e.type == "inherits" and e.to_id == f"{root_name}.base.Base" for e in graph.edges)


def test_save_and_load_graph_roundtrip(tmp_path):
    (tmp_path / "models.py").write_text("class Model:\n    def save(self):\n        pass\n")
    graph = build_graph_from_directory("testapp", "1.0", str(tmp_path))

    json_path = str(tmp_path / "graph.json")
    save_graph(graph, json_path)
    reloaded = load_graph(json_path)

    assert reloaded.nodes.keys() == graph.nodes.keys()
    assert reloaded.framework == graph.framework

def test_files_in_excluded_directories_are_skipped(tmp_path):
    (tmp_path / "models.py").write_text("class Model:\n    pass\n")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_models.py").write_text("def test_something():\n    pass\n")

    graph = build_graph_from_directory("testapp", "1.0", str(tmp_path))

    assert any("models.Model" in node_id for node_id in graph.nodes)
    assert not any("test_something" in node_id for node_id in graph.nodes)