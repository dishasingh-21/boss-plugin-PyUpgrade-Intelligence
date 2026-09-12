import zipfile
from contracts.graph import Graph, Node
from contracts.diff import Change, ChangeType, DiffResult
from all_outputs_bundler import bundle_run_outputs


def test_bundle_creates_correct_folder_structure(tmp_path):
    graph_a = Graph(framework="test", version="1.0", nodes={
        "x.foo": Node(id="x.foo", type="Function", name="foo", file="x.py", line=1, signature="foo()"),
    })
    graph_b = Graph(framework="test", version="2.0", nodes={
        "x.foo": Node(id="x.foo", type="Function", name="foo", file="x.py", line=1, signature="foo(y)"),
    })
    change = Change(symbol_id="x.foo", change_type=ChangeType.SIGNATURE_CHANGED, old=graph_a.nodes["x.foo"], new=graph_b.nodes["x.foo"], detail="added y")
    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=[change])

    output_dir = str(tmp_path / "run_output")
    zip_path = str(tmp_path / "bundle.zip")

    result_path = bundle_run_outputs(
        output_dir=output_dir,
        graph_a=graph_a, graph_b=graph_b, diff_result_raw=diff_result,
        config_diff={"pyproject.toml": "some diff text"},
        zip_path=zip_path,
    )

    assert result_path == zip_path

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()

    assert any("context_graph_builder" in n and "old_graph.json" in n for n in names)
    assert any("context_graph_builder" in n and "new_graph.json" in n for n in names)
    assert any("diff_engine" in n and "diff_result_raw.json" in n for n in names)
    assert any("diff_engine" in n and "config_diff.json" in n for n in names)


def test_bundle_works_with_only_partial_outputs(tmp_path):
    """
    Confirms the bundler works today, before usage_indexer/changelog_parser/
    risk_scorer exist -- only graph + diff outputs should be present, no errors.
    """
    graph_a = Graph(framework="test", version="1.0")
    output_dir = str(tmp_path / "run_output_partial")
    zip_path = str(tmp_path / "partial_bundle.zip")

    bundle_run_outputs(output_dir=output_dir, graph_a=graph_a, zip_path=zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()

    assert any("old_graph.json" in n for n in names)
    assert not any("usage_index.json" in n for n in names)
    assert not any("risk_report.json" in n for n in names)

def test_bundle_keeps_raw_and_enriched_diff_as_separate_files(tmp_path):
    node = Node(id="x.foo", type="Function", name="foo", file="x.py", line=1, signature="foo()")
    change_raw = Change(symbol_id="x.foo", change_type=ChangeType.BODY_CHANGED, old=node, new=node, detail="body changed")
    diff_raw = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=[change_raw])

    change_enriched = Change(
        symbol_id="x.foo", change_type=ChangeType.BODY_CHANGED, old=node, new=node,
        detail="body changed", body_diff_text="-old line\n+new line",
    )
    diff_enriched = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=[change_enriched])

    output_dir = str(tmp_path / "run_output_both")
    zip_path = str(tmp_path / "both_bundle.zip")

    bundle_run_outputs(
        output_dir=output_dir,
        diff_result_raw=diff_raw,
        diff_result_enriched=diff_enriched,
        zip_path=zip_path,
    )

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        raw_content = zf.read([n for n in names if "diff_result_raw.json" in n][0]).decode()
        enriched_content = zf.read([n for n in names if "diff_result_enriched.json" in n][0]).decode()

    assert "diff_result_raw.json" in "".join(names)
    assert "diff_result_enriched.json" in "".join(names)
    assert "body_diff_text" not in raw_content or '""' in raw_content  # raw has empty body_diff_text
    assert "-old line" in enriched_content  # enriched has real diff text