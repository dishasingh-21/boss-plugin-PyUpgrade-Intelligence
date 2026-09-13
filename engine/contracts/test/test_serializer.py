from contracts.graph import Node
from contracts.diff import Change, ChangeType, DiffResult
from contracts.serializer import save_diff_result, load_diff_result
from contracts.usage import Usage, UsageIndex
from contracts.serializer import save_usage_index, load_usage_index

def test_diff_result_roundtrip(tmp_path):
    old_node = Node(id="x.foo", type="Function", name="foo", file="x.py", line=1, signature="foo()")
    new_node = Node(id="x.foo", type="Function", name="foo", file="x.py", line=1, signature="foo(y)")
    change = Change(
        symbol_id="x.foo", change_type=ChangeType.SIGNATURE_CHANGED,
        old=old_node, new=new_node, detail="added y",
    )
    result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=[change])

    path = str(tmp_path / "test_diff.json")
    save_diff_result(result, path)
    reloaded = load_diff_result(path)

    assert reloaded.framework == "test"
    assert reloaded.changes[0].detail == "added y"
    assert reloaded.changes[0].change_type == ChangeType.SIGNATURE_CHANGED
    assert reloaded.changes[0].old.id == "x.foo"
    assert reloaded.changes[0].new.signature == "foo(y)"


def test_diff_result_roundtrip_handles_none_old_or_new(tmp_path):
    new_node = Node(id="x.bar", type="Function", name="bar", file="x.py", line=1, signature="bar()")
    change = Change(symbol_id="x.bar", change_type=ChangeType.ADDED, old=None, new=new_node, detail="new function")
    result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=[change])

    path = str(tmp_path / "test_diff_added.json")
    save_diff_result(result, path)
    reloaded = load_diff_result(path)

    assert reloaded.changes[0].old is None
    assert reloaded.changes[0].new.id == "x.bar"