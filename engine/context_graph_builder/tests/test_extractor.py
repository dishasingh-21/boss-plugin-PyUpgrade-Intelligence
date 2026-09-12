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

def test_body_hash_differs_for_different_implementations():
    nodes_a = extract_from_source("def foo():\n    return 1", "x.py", "x")
    nodes_b = extract_from_source("def foo():\n    return 2", "x.py", "x")
    assert nodes_a["x.foo"].body_hash != nodes_b["x.foo"].body_hash


def test_body_hash_same_for_identical_implementations():
    source = "def foo():\n    return 1"
    nodes_a = extract_from_source(source, "x.py", "x")
    nodes_b = extract_from_source(source, "x.py", "x")
    assert nodes_a["x.foo"].body_hash == nodes_b["x.foo"].body_hash


def test_property_decorator_detected():
    source = "class Foo:\n    @property\n    def bar(self):\n        return 1"
    nodes = extract_from_source(source, "x.py", "x")
    assert nodes["x.Foo.bar"].is_property is True


def test_regular_method_not_marked_as_property():
    source = "class Foo:\n    def bar(self):\n        return 1"
    nodes = extract_from_source(source, "x.py", "x")
    assert nodes["x.Foo.bar"].is_property is False


def test_async_function_detected():
    source = "async def fetch():\n    pass"
    nodes = extract_from_source(source, "x.py", "x")
    assert nodes["x.fetch"].is_async is True