# Enrichment pass for user's affected file entries. Adds real body diff text (for BODY_CHANGEs, SIGNATURE_CHANGEs, MOVED_ALSO_SIGNATURE_CHANGED, MOVED_ALSO_BODY_CHANGED)

from contracts.risk import FileRisk
from contracts.diff import DiffResult, ChangeType

_SIGNATURE_TEXT_TYPES = (ChangeType.SIGNATURE_CHANGED, ChangeType.MOVED_ALSO_SIGNATURE_CHANGED)
def enrich_affected_files(affected_files: list[FileRisk], diff_result_enriched: DiffResult, repo_source_by_file: dict[str,str]) -> list[FileRisk]:
    body_diff_by_symbol = { c.symbol_id: c.body_diff_text for c in diff_result_enriched.changes if c.body_diff_text }
    signature_by_symbol = { c.symbol_id: (c.old.signature if c.old else "", c.new.signature if c.new else "") for c in diff_result_enriched.changes if c.change_type in _SIGNATURE_TEXT_TYPES}
    for fr in affected_files:
        if fr.symbol_id in body_diff_by_symbol:
            fr.body_diff_text = body_diff_by_symbol[fr.symbol_id]
        if fr.symbol_id in signature_by_symbol:
            fr.old_signature, fr.new_signature = signature_by_symbol[fr.symbol_id]
        repo_text = repo_source_by_file.get(fr.file)
        if repo_text:
            lines = repo_text.splitlines()
            if 0<fr.line<=len(lines):
                fr.code_snippet = lines[fr.line-1].strip()
    return affected_files


