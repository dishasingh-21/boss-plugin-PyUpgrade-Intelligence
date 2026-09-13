# Fills in the actual source code text for each Usage.

from contracts.usage import UsageIndex

def enrich_usage_snippets(usage_index: UsageIndex, source_by_file: dict[str, str]) -> UsageIndex:
    for usages in usage_index.usages.values():
        for usage in usages:
            text = source_by_file.get(usage.file)
            if text is None:
                continue
            lines = text.splitlines()
            if 0<usage.line<=len(lines):
                usage.snippet = lines[usage.line-1].strip()
    return usage_index

