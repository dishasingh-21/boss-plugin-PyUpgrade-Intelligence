from contracts.usage import Usage, UsageIndex
from usage_indexer.enricher import enrich_usage_snippets


def test_enricher_fills_in_snippet_text():
    usage = Usage(file="views.py", line=2)
    index = UsageIndex(repo_path="test", usages={"django.shortcuts.render": [usage]})

    source = {"views.py": "def my_view():\n    return render(request, 'x.html')\n"}

    enriched = enrich_usage_snippets(index, source)

    assert enriched.usages["django.shortcuts.render"][0].snippet == "return render(request, 'x.html')"


def test_enricher_leaves_snippet_empty_when_file_not_found():
    usage = Usage(file="missing.py", line=1)
    index = UsageIndex(repo_path="test", usages={"x.symbol": [usage]})

    enriched = enrich_usage_snippets(index, source_by_file={})

    assert enriched.usages["x.symbol"][0].snippet == ""