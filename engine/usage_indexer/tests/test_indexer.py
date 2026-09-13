from contracts.graph import Graph, Node
from usage_indexer.indexer import build_usage_index


def _framework_graph():
    return Graph(framework="test", version="1.0", nodes={
        "django.db.models.Model": Node(id="django.db.models.Model", type="Class", name="Model", file="x.py", line=1),
        "django.db.models.Model.save": Node(id="django.db.models.Model.save", type="Method", name="save", file="x.py", line=2),
        "django.shortcuts.render": Node(id="django.shortcuts.render", type="Function", name="render", file="y.py", line=1),
    })


def test_detects_usage_via_direct_function_import(tmp_path):
    (tmp_path / "views.py").write_text(
        "from django.shortcuts import render\n\ndef my_view():\n    return render(None, 'x.html')\n"
    )

    index = build_usage_index(str(tmp_path), _framework_graph())

    assert "django.shortcuts.render" in index.usages
    assert index.usages["django.shortcuts.render"][0].line == 4


def test_detects_usage_via_attribute_call(tmp_path):
    (tmp_path / "models.py").write_text(
        "from django.db import models\n\ndef save_it(obj):\n    models.Model.save(obj)\n"
    )

    index = build_usage_index(str(tmp_path), _framework_graph())

    assert "django.db.models.Model.save" in index.usages


def test_detects_usage_via_class_inheritance(tmp_path):
    (tmp_path / "models.py").write_text(
        "from django.db.models import Model\n\nclass MyModel(Model):\n    pass\n"
    )

    index = build_usage_index(str(tmp_path), _framework_graph())

    assert "django.db.models.Model" in index.usages


def test_unrelated_import_produces_no_false_positive(tmp_path):
    (tmp_path / "utils.py").write_text(
        "import os\n\ndef foo():\n    return os.path.join('a', 'b')\n"
    )

    index = build_usage_index(str(tmp_path), _framework_graph())

    assert index.usages == {}

def test_resolves_usage_through_public_reexport_alias(tmp_path):
    from contracts.graph import Edge

    graph = Graph(framework="test", version="1.0", nodes={
        "pkg.base.Model": Node(id="pkg.base.Model", type="Class", name="Model", file="base.py", line=1),
    }, edges=[
        Edge(from_id="pkg.models", to_id="pkg.base.Model", type="imports"),
    ])

    (tmp_path / "app.py").write_text(
        "from pkg import models\n\nclass Foo(models.Model):\n    pass\n"
    )

    index = build_usage_index(str(tmp_path), graph)

    # the usage should be recorded under the resolved id, not the alias
    assert "pkg.base.Model" in index.usages
    assert "pkg.models.Model" not in index.usages

def test_class_instantiation_recorded_as_init_usage():
    graph = Graph(framework="test", version="1.0", nodes={
        "pkg.mod.Paginator": Node(id="pkg.mod.Paginator", type="Class", name="Paginator", file="mod.py", line=1),
        "pkg.mod.Paginator.__init__": Node(id="pkg.mod.Paginator.__init__", type="Method", name="__init__", file="mod.py", line=2),
    })

    def write_source(tmp_path):
        (tmp_path / "app.py").write_text(
            "from pkg.mod import Paginator\n\ndef paginate(items):\n    return Paginator(items, per_page=10)\n"
        )

    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        write_source(tmp_path)
        index = build_usage_index(str(tmp_path), graph)

    assert "pkg.mod.Paginator.__init__" in index.usages
    assert "pkg.mod.Paginator" in index.usages