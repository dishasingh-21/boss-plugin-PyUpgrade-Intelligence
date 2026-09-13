import difflib
from contracts.diff import DiffResult, ChangeType

_BODY_TEXT_TYPES = (ChangeType.BODY_CHANGED, ChangeType.MOVED_ALSO_BODY_CHANGED)
def enrich_body_diffs(result: DiffResult, old_source_by_file: dict[str, str], new_source_by_file: dict[str,str]) -> DiffResult:
    for change in result.changes:
        if change.change_type not in _BODY_TEXT_TYPES:
            continue
        old_node, new_node = change.old, change.new
        old_text = old_source_by_file.get(old_node.file)
        new_text = new_source_by_file.get(new_node.file)
        if old_text is None or new_text is None:
            continue
        old_lines = old_text.splitlines(keepends=True)[old_node.line - 1:old_node.line_end]
        new_lines = new_text.splitlines(keepends=True)[new_node.line - 1:new_node.line_end]
        diff_lines = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"old/{old_node.file}",
            tofile=f"new/{new_node.file}",
            lineterm="",
        )
        change.body_diff_text="\n".join(diff_lines)
    return result