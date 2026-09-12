from contracts.graph import Node
from contracts.diff import Change, ChangeType, DiffResult
from diff_engine.enricher import enrich_body_diffs


def test_body_diff_produces_real_unified_diff():
    old_node = Node(id="x.foo", type="Function", name="foo", file="x.py", line=1, line_end=2)
    new_node = Node(id="x.foo", type="Function", name="foo", file="x.py", line=1, line_end=2)
    change = Change(symbol_id="x.foo", change_type=ChangeType.BODY_CHANGED, old=old_node, new=new_node)
    result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=[change])

    old_source = {"x.py": "def foo():\n    return 1\n"}
    new_source = {"x.py": "def foo():\n    return 2\n"}

    enriched = enrich_body_diffs(result, old_source, new_source)
    assert "return 1" in enriched.changes[0].body_diff_text
    assert "return 2" in enriched.changes[0].body_diff_text