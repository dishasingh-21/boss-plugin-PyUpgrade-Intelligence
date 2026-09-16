# diff_engine

## What it is
Compares two versions' semantic graphs and produces a list of every real change between them - additions, removals, signature changes, moves, and implementation-only changes.

## How it works
Matches symbols between the two graphs by their full name, then checks each matched pair for differences. Every change falls into one of these categories:

| Category | Meaning |
|---|---|
| `REMOVED` | No longer exists |
| `ADDED` | New in the newer version |
| `SIGNATURE_CHANGED` | Parameters, defaults, async, or property status changed |
| `MOVED_ALSO_SIGNATURE_CHANGED` | Moved to a new location, and its signature also changed |
| `MOVED_ALSO_BODY_CHANGED` | Moved, and only its implementation changed |
| `MOVED_UNCHANGED` | Moved, nothing else about it changed |
| `BODY_CHANGED` | Implementation changed, signature identical |

`BODY_CHANGED` is the one category no changelog-reading tool can catch, it means the code inside a function changed while its interface stayed exactly the same, detected purely by comparing a structural fingerprint of each version's implementation.

A separate, optional pass (`enricher.py`) fills in real before/after source text for anyone who wants to see exactly what changed, not just that something did — kept separate so a routine comparison stays fast.

Config and dependency files (`pyproject.toml`, `requirements.txt`, and similar) are compared by a fully separate, simpler piece (`config_differ.py`), plain text diffing, no code parsing involved.
