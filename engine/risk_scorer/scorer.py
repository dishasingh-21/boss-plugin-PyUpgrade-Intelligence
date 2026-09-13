# Joins the result of diff engine with that of Usage Indexer to produce the Risk Report.

from contracts.diff import DiffResult, ChangeType
from contracts.usage import UsageIndex
from contracts.risk import RiskReport, FileRisk, ScoreBreakdownEntry, Recommendation

SEVERITY = {
    "REMOVED": 1.00,
    "SIGNATURE_CHANGED_BREAKING": 0.85,
    "MOVED_ALSO_SIGNATURE_CHANGED": 0.85,
    "MOVED_ALSO_BODY_CHANGED": 0.40,
    "MOVED_UNCHANGED": 0.35,
    "SIGNATURE_CHANGED_ADDITIVE": 0.15,
    "BODY_CHANGED": 0.10
}
ALPHA = 0.8         # Weight of worst-case severity
BETA = 0.2          # Weight of breadth

def score_risk(diff_result: DiffResult, usage_index: UsageIndex) -> RiskReport:
    relevant = [c for c in diff_result.changes if c.symbol_id in usage_index.usages]
    category_counts: dict[str, int] = {}
    affected_files: list[FileRisk] = []
    worst_symbol = None
    worst_severity = -1.0

    for change in relevant:
        category = _classify(change)
        category_counts[category] = category_counts.get(category, 0) + 1
        severity = SEVERITY[category]
        if severity > worst_severity:
            worst_severity = severity
            worst_symbol = change.symbol_id
        for usage in usage_index.usages[change.symbol_id]:
            affected_files.append(FileRisk(
                file = usage.file,
                line = usage.line,
                symbol_id = change.symbol_id,
                change_type = change.change_type.value,
                detail = change.detail,
            ))

    n = len(relevant)
    total_used = len(usage_index.usages)
    M = worst_severity if n>0 else 0.0
    B = (n/total_used) if total_used>0 else 0.0
    score = round(100*(ALPHA*M + BETA*B))
    recommendation = _recommend(score)
    breakdown = [
        ScoreBreakdownEntry(
            category = cat,
            severity = SEVERITY[cat],
            count = count,
            contributes_to_max= (SEVERITY[cat] == M)
        ) for cat,count in category_counts.items()
    ]

    return RiskReport(
        framework = diff_result.framework,
        version_from = diff_result.version_from,
        version_to = diff_result.version_to,
        score = score,
        recommendation = recommendation,
        max_severity = M,
        breadth = round(B,3),
        worst_change_symbol = worst_symbol,
        score_breakdown = breakdown,
        affected_files = affected_files,
        total_changes_in_diff = len(diff_result.changes),
        relevant_changes_count = n
    )

def _classify(change) -> str:
    if change.change_type == ChangeType.REMOVED:
        return "REMOVED"
    if change.change_type in (ChangeType.MOVED_ALSO_SIGNATURE_CHANGED, ChangeType.MOVED_ALSO_BODY_CHANGED, ChangeType.MOVED_UNCHANGED):
        return change.change_type
    if change.change_type == ChangeType.SIGNATURE_CHANGED:
        if _is_breaking_signature_change(change):
            return "SIGNATURE_CHANGED_BREAKING"
        return "SIGNATURE_CHANGED_ADDITIVE"
    return "BODY_CHANGED"

def _is_breaking_signature_change(change) -> bool:
    old_node, new_node = change.old, change.new
    if old_node is None or new_node is None:
        return True
    if old_node.is_async != new_node.is_async:
        return True
    if old_node.is_property != new_node.is_property:
        return True

    old_names = [p.name for p in old_node.params]
    new_names = [p.name for p in new_node.params]
    if not all(name in new_names for name in old_names):
        return True
    if old_names != [n for n in new_names if n in old_names]:
        return True

    return False

def _recommend(score: int) -> Recommendation:
    if score<20:
        return Recommendation.UPGRADE
    if score<60:
        return Recommendation.UPGRADE_WITH_CAUTION
    return Recommendation.HOLD

