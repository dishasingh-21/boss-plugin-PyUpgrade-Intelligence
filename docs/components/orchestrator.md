# orchestrator

## What it is
The glue layer. Wires every other component into a small number of clean functions, this is the only place in the whole engine allowed to know about every component at once.

## How it works
Every function here is a thin wrapper, calling already-built pieces in the right order. It contains no real logic of its own, the actual work happens inside the components it calls.

| Function | What it does                                                                     |
|---|----------------------------------------------------------------------------------|
| `upgrade_check` | The full pipeline - graph_builder, diff, usage, score                            |
| `warm_cache` | Just builds and caches one version's graph                                       |
| `get_breaking_changes` | Structural diff only, no repo needed                                             |
| `get_usage_in_code` | Raw usage, no diff involved                                                      |
| `get_affected_files_raw` / `get_affected_files_enriched` | Just the flagged hits, fast or detailed                                          |
| `run_full_pipeline` | Everything, including config diff and full enrichment, used for the debug bundle |

Every function accepts an optional progress callback, so a caller (the CLI, or eventually an agent) can report what's happening during a slower first-time run.

**Both the CLI and the MCP server call these exact same functions.** Nothing about how a check runs differs between delivery surfaces.