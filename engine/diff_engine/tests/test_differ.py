from contracts.graph import Graph, Node, Param
from contracts.diff import ChangeType
from diff_engine.differ import diff


def _node(id_, type_="Function", name=None, params=None, signature="", body_hash="abc", is_async=False, is_property=False):
    return Node(
        id=id_, type=type_, name=name or id_.split(".")[-1],
        file="x.py", line=1, params=params or [], signature=signature,
        body_hash=body_hash, is_async=is_async, is_property=is_property,
    )


def test_removed_symbol_detected():
    graph_a = Graph(framework="test", version="1.0", nodes={"x.old_func": _node("x.old_func", signature="old_func()")})
    graph_b = Graph(framework="test", version="2.0", nodes={})
    result = diff(graph_a, graph_b)
    assert len(result.changes) == 1
    assert result.changes[0].change_type == ChangeType.REMOVED


def test_added_symbol_detected():
    graph_a = Graph(framework="test", version="1.0", nodes={})
    graph_b = Graph(framework="test", version="2.0", nodes={"x.new_func": _node("x.new_func", signature="new_func()")})
    result = diff(graph_a, graph_b)
    assert len(result.changes) == 1
    assert result.changes[0].change_type == ChangeType.ADDED


def test_signature_changed_detected():
    old_node = _node("x.save", params=[Param(name="force_insert", default="False", position=0)], signature="save(force_insert=False)")
    new_node = _node("x.save", params=[
        Param(name="force_insert", default="False", position=0),
        Param(name="using", default="None", position=1),
    ], signature="save(force_insert=False, using=None)")
    graph_a = Graph(framework="test", version="1.0", nodes={"x.save": old_node})
    graph_b = Graph(framework="test", version="2.0", nodes={"x.save": new_node})
    result = diff(graph_a, graph_b)
    assert result.changes[0].change_type == ChangeType.SIGNATURE_CHANGED
    assert "using" in result.changes[0].detail


def test_unchanged_symbol_produces_no_change():
    node = _node("x.stable", signature="stable()")
    graph_a = Graph(framework="test", version="1.0", nodes={"x.stable": node})
    graph_b = Graph(framework="test", version="2.0", nodes={"x.stable": node})
    result = diff(graph_a, graph_b)
    assert len(result.changes) == 0


def test_body_changed_detected_when_signature_identical():
    old_node = _node("x.save", signature="save()", body_hash="hash_v1")
    new_node = _node("x.save", signature="save()", body_hash="hash_v2")
    graph_a = Graph(framework="test", version="1.0", nodes={"x.save": old_node})
    graph_b = Graph(framework="test", version="2.0", nodes={"x.save": new_node})
    result = diff(graph_a, graph_b)
    assert result.changes[0].change_type == ChangeType.BODY_CHANGED


def test_async_change_detected_as_signature_changed():
    old_node = _node("x.fetch", signature="fetch()", is_async=False)
    new_node = _node("x.fetch", signature="fetch()", is_async=True)
    graph_a = Graph(framework="test", version="1.0", nodes={"x.fetch": old_node})
    graph_b = Graph(framework="test", version="2.0", nodes={"x.fetch": new_node})
    result = diff(graph_a, graph_b)
    assert result.changes[0].change_type == ChangeType.SIGNATURE_CHANGED
    assert "async" in result.changes[0].detail


def test_property_change_detected_as_signature_changed():
    old_node = _node("x.Foo.bar", type_="Method", signature="bar()", is_property=False)
    new_node = _node("x.Foo.bar", type_="Method", signature="bar()", is_property=True)
    graph_a = Graph(framework="test", version="1.0", nodes={"x.Foo.bar": old_node})
    graph_b = Graph(framework="test", version="2.0", nodes={"x.Foo.bar": new_node})
    result = diff(graph_a, graph_b)
    assert result.changes[0].change_type == ChangeType.SIGNATURE_CHANGED
    assert "@property" in result.changes[0].detail


def test_moved_symbol_with_also_changed_signature():
    old_node = _node("x.old_loc.save", name="save", signature="save(x)")
    new_node = _node("y.new_loc.save", name="save", signature="save(x, y)")
    graph_a = Graph(framework="test", version="1.0", nodes={"x.old_loc.save": old_node})
    graph_b = Graph(framework="test", version="2.0", nodes={"y.new_loc.save": new_node})
    result = diff(graph_a, graph_b)
    assert result.changes[0].change_type == ChangeType.MOVED_ALSO_CHANGED


def test_moved_symbol_without_other_changes():
    old_node = _node("x.old_loc.save", name="save", signature="save(x)")
    new_node = _node("y.new_loc.save", name="save", signature="save(x)")
    graph_a = Graph(framework="test", version="1.0", nodes={"x.old_loc.save": old_node})
    graph_b = Graph(framework="test", version="2.0", nodes={"y.new_loc.save": new_node})
    result = diff(graph_a, graph_b)
    assert result.changes[0].change_type == ChangeType.MOVED_UNCHANGED

def test_class_base_change_produces_meaningful_detail():
    old_node = _node("x.BoundField", type_="Class", signature="class BoundField(object)")
    new_node = _node("x.BoundField", type_="Class", signature="class BoundField(RenderableFieldMixin)")
    graph_a = Graph(framework="test", version="1.0", nodes={"x.BoundField": old_node})
    graph_b = Graph(framework="test", version="2.0", nodes={"x.BoundField": new_node})
    result = diff(graph_a, graph_b)
    assert result.changes[0].change_type == ChangeType.SIGNATURE_CHANGED
    assert "base classes changed" in result.changes[0].detail
    assert "RenderableFieldMixin" in result.changes[0].detail