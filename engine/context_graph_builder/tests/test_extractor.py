from context_graph_builder.extractor import extract_from_source


def test_extracts_standalone_function():
    source = "def greet(name, greeting='hello'):\n    pass"
    nodes = extract_from_source(source, file_path="x.py", module_prefix="x")

    assert "x.greet" in nodes
    node = nodes["x.greet"]
    assert node.type == "Function"
    assert node.name == "greet"
    assert node.signature == "greet(name, greeting='hello')"


def test_extracts_method_inside_class():
    source = "class Foo:\n    def bar(self):\n        pass"
    nodes = extract_from_source(source, file_path="x.py", module_prefix="x")

    assert "x.Foo.bar" in nodes
    assert nodes["x.Foo.bar"].type == "Method"


def test_private_function_marked_not_public():
    source = "def _hidden():\n    pass"
    nodes = extract_from_source(source, file_path="x.py", module_prefix="x")

    assert nodes["x._hidden"].is_public is False