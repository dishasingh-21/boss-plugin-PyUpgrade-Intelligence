from contracts.graph import Node, Param
from contracts.diff import Change, ChangeType, DiffResult
from contracts.usage import Usage, UsageIndex
from contracts.risk import Recommendation
from risk_scorer.scorer import score_risk


def _node(id_, params=None, is_async=False, is_property=False):
    return Node(id=id_, type="Function", name=id_.split(".")[-1], file="x.py", line=1, params=params or [], is_async=is_async, is_property=is_property)


def _usage_index(changed_symbol_ids, extra_unaffected_count=0):
    usages = {sid: [Usage(file="app.py", line=1)] for sid in changed_symbol_ids}
    for i in range(extra_unaffected_count):
        usages[f"unaffected.symbol{i}"] = [Usage(file="app.py", line=1)]
    return UsageIndex(repo_path="test", usages=usages)


def test_removed_symbol_forces_hold_regardless_of_noise():
    """Theorem 3: a single REMOVED symbol guarantees score >= 80, regardless of breadth."""
    changes = [Change(symbol_id="x.gone", change_type=ChangeType.REMOVED, old=_node("x.gone"), new=None, detail="removed")]
    for i in range(20):
        changes.append(Change(symbol_id=f"x.body{i}", change_type=ChangeType.BODY_CHANGED, old=_node(f"x.body{i}"), new=_node(f"x.body{i}"), detail="body changed"))

    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = _usage_index([c.symbol_id for c in changes], extra_unaffected_count=100)

    report = score_risk(diff_result, usage_index)

    assert report.score >= 80
    assert report.recommendation == Recommendation.HOLD
    assert report.worst_change_symbol == "x.gone"


def test_body_changed_only_never_reaches_hold():
    """Theorem 4: BODY_CHANGED-only scenario is capped at 28, even at maximum breadth (B=1)."""
    changes = [
        Change(symbol_id=f"x.body{i}", change_type=ChangeType.BODY_CHANGED, old=_node(f"x.body{i}"), new=_node(f"x.body{i}"), detail="body changed")
        for i in range(30)
    ]
    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = _usage_index([c.symbol_id for c in changes])

    report = score_risk(diff_result, usage_index)

    assert report.score <= 28
    assert report.recommendation != Recommendation.HOLD


def test_moved_unchanged_only_never_reaches_hold():
    """Theorem 5: MOVED_UNCHANGED-only (no accompanying breaking change) is capped at 48, even at B=1."""
    changes = [
        Change(symbol_id=f"x.moved{i}", change_type=ChangeType.MOVED_UNCHANGED, old=_node(f"x.moved{i}"), new=_node(f"y.moved{i}"), detail=f"Moved from x.moved{i} to y.moved{i}")
        for i in range(25)
    ]
    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = _usage_index([c.symbol_id for c in changes])

    report = score_risk(diff_result, usage_index)

    assert report.score <= 48


def test_moved_also_signature_changed_scores_same_as_breaking_signature():
    changes = [
        Change(symbol_id=f"x.moved{i}", change_type=ChangeType.MOVED_ALSO_SIGNATURE_CHANGED, old=_node(f"x.moved{i}"), new=_node(f"y.moved{i}"), detail="moved and changed")
        for i in range(3)
    ]
    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = _usage_index([c.symbol_id for c in changes], extra_unaffected_count=17)

    report = score_risk(diff_result, usage_index)

    assert report.max_severity == 0.85


def test_moved_also_body_changed_scores_between_moved_and_breaking():
    changes = [
        Change(symbol_id="x.moved0", change_type=ChangeType.MOVED_ALSO_BODY_CHANGED, old=_node("x.moved0"), new=_node("y.moved0"), detail="moved, body changed")
    ]
    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = _usage_index(["x.moved0"], extra_unaffected_count=19)

    report = score_risk(diff_result, usage_index)

    assert report.max_severity == 0.40


def test_irrelevant_changes_excluded_from_scoring():
    changes = [Change(symbol_id="x.unused", change_type=ChangeType.REMOVED, old=_node("x.unused"), new=None, detail="removed")]
    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = UsageIndex(repo_path="test", usages={})

    report = score_risk(diff_result, usage_index)

    assert report.score == 0
    assert report.relevant_changes_count == 0
    assert report.total_changes_in_diff == 1


def test_additive_signature_change_is_low_severity():
    old_node = _node("x.save", params=[Param(name="a", position=0)])
    new_node = _node("x.save", params=[Param(name="a", position=0), Param(name="b", default="None", position=1)])
    changes = [Change(symbol_id="x.save", change_type=ChangeType.SIGNATURE_CHANGED, old=old_node, new=new_node, detail="parameters changed")]

    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = _usage_index(["x.save"], extra_unaffected_count=19)

    report = score_risk(diff_result, usage_index)

    assert report.max_severity == 0.15
    assert report.recommendation == Recommendation.UPGRADE


def test_reordered_params_detected_as_breaking():
    old_node = _node("x.save", params=[Param(name="a", position=0), Param(name="b", position=1)])
    new_node = _node("x.save", params=[Param(name="b", position=0), Param(name="a", position=1)])
    changes = [Change(symbol_id="x.save", change_type=ChangeType.SIGNATURE_CHANGED, old=old_node, new=new_node, detail="reordered")]

    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = _usage_index(["x.save"], extra_unaffected_count=19)

    report = score_risk(diff_result, usage_index)

    assert report.max_severity == 0.85


def test_worked_example_from_spec_doc():
    """
    Reproduces the worked example in Risk-Scoring-Mathematical-Model.md:
    a project using 20 distinct framework symbols in total, 11 of which
    are relevant changes. Expects score 91, HOLD.
    """
    changes = []
    changes.append(Change(symbol_id="x.removed", change_type=ChangeType.REMOVED, old=_node("x.removed"), new=None, detail="removed"))
    for i in range(2):
        old_n = _node(f"x.sig{i}", params=[Param(name="a", position=0)])
        new_n = _node(f"x.sig{i}", params=[])
        changes.append(Change(symbol_id=f"x.sig{i}", change_type=ChangeType.SIGNATURE_CHANGED, old=old_n, new=new_n, detail="param removed"))
    for i in range(3):
        changes.append(Change(symbol_id=f"x.moved{i}", change_type=ChangeType.MOVED_UNCHANGED, old=_node(f"x.moved{i}"), new=_node(f"y.moved{i}"), detail=f"Moved from x.moved{i} to y.moved{i}"))
    for i in range(5):
        changes.append(Change(symbol_id=f"x.body{i}", change_type=ChangeType.BODY_CHANGED, old=_node(f"x.body{i}"), new=_node(f"x.body{i}"), detail="body changed"))

    diff_result = DiffResult(framework="test", version_from="1.0", version_to="2.0", changes=changes)
    usage_index = _usage_index([c.symbol_id for c in changes], extra_unaffected_count=9)

    report = score_risk(diff_result, usage_index)

    assert report.relevant_changes_count == 11
    assert report.breadth == 0.55
    assert report.score == 91
    assert report.recommendation == Recommendation.HOLD