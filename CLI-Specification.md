# CLI Specification — `cli.py`

## Purpose
A command-line interface exposing the engine directly. The CLI and the MCP server (`mcp_server.py`) call the exact same underlying functions, so the two delivery surfaces can never drift out of sync with each other.

**Invocation:** run as a script from inside `engine/`, or `python engine/cli.py <command> ...` from the repo root (the script sets its own working directory internally, so either location works).

---
## Commands
 
### `check`
 
Runs the full pipeline and prints a compact risk report: score, recommendation, breakdown, affected files.
```bash
python cli.py check <framework> <old_version> <new_version> --repo <path_to_your_repo> [--package <import_name>]
```

example commands:
```bash
python cli.py check django 4.2 5.0 --repo path/to/your/repo
python cli.py check livekit-agents 1.5.1 1.8.1 --repo path/to/your/repo --package livekit
```

`--package` is optional, only needed when a framework's import name differs from its PyPI name and the automatic detection can't resolve it (see `PyUpgrade-Intelligence-Design.md` for how that detection works).

### `changes`
 
Lists the structural diff between two versions, without cross-referencing any specific codebase.
 
```bash
python cli.py changes <framework> <old_version> <new_version> [--type <types>]
```

example commands:
```bash
python cli.py changes django 4.2 5.0
python cli.py changes django 4.2 5.0 --type BODY_CHANGED,ADDED
```

**All possible change types** (`--type` accepts any comma-separated subset of these):

| Type | Meaning | In default set?                                  |
|---|---|--------------------------------------------------|
| `REMOVED` | Symbol no longer exists | Yes                                              |
| `SIGNATURE_CHANGED` | Parameters, defaults, async/property status changed | Yes                                              |
| `MOVED_ALSO_SIGNATURE_CHANGED` | Moved to a new location AND its signature changed | Yes                                              |
| `MOVED_UNCHANGED` | Moved to a new location, nothing else about it changed | Yes                                              |
| `ADDED` | New symbol in the newer version | No                                               |
| `MOVED_ALSO_BODY_CHANGED` | Moved, and only its implementation changed (signature identical) | No: lower confidence, may be a harmless refactor |
| `BODY_CHANGED` | Implementation changed, signature identical | No: lower confidence, may be a harmless refactor |

Without `--type`, only the four "Yes" rows are shown, every case that represents a certain, structural break. Pass `--type` explicitly to widen the results, e.g. `--type BODY_CHANGED,MOVED_ALSO_BODY_CHANGED` to also see the lower-confidence, implementation-only signals.

### `usage`
 
Lists every framework symbol a codebase uses, independent of any version comparison.
 
```bash
python cli.py usage <framework> <version> --repo <path> [--enriched]
```

example command:
```bash
python cli.py usage django 4.2 --repo ./my-django-project
python cli.py usage django 4.2 --repo ./my-django-project --enriched
```
 
`--enriched` adds the actual source code line for each usage, at the cost of extra file reads.

### `affected`
 
Just the specific files and lines affected by changes between two versions, faster than `check` when only the locations matter, not a full score.
 
```bash
python cli.py affected <framework> <old_version> <new_version> --repo <path> [--enriched]
```

example command:
```bash
python cli.py affected django 4.2 5.0 --repo ./my-django-project
python cli.py affected django 4.2 5.0 --repo ./my-django-project --enriched
```
 
`--enriched` adds real source snippets, before/after signatures (for signature changes), and real body diff text (for implementation changes).
 
### `config-diff`
 
Plain-text diff of config/dependency files (`pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`) between two versions. No repo needed, this compares the framework's own files across versions.
 
```bash
python cli.py config-diff <framework> <old_version> <new_version>
```

example command:
```bash
python cli.py config-diff django 4.2 5.0
```

### `export`
 
Exports the full raw output of the pipeline as a zip file, for debugging or manual inspection - each part as a separate JSON file, mirroring the engine's own folder structure. Never runs automatically as part of any other command.
 
```bash
python cli.py export <framework> <old_version> <new_version> --repo <path> [--include <parts>] [--out <file.zip>]
```

example command:
```bash
python cli.py export django 4.2 5.0 --repo ./my-project --out debug.zip
python cli.py export django 4.2 5.0 --repo ./my-project --include graph,diff-raw --out partial.zip
```
 
**All possible `--include` values** (comma-separated, or `all`):
 
| Value | What it includes |
|---|---|
| `graph` | Both framework versions' full semantic graphs |
| `diff-raw` | The structural diff, before source-text enrichment |
| `diff-enriched` | The same diff, with real body-diff text and before/after signatures added |
| `config-diff` | The config/dependency file diff |
| `usage` | The full usage index for the given repo |
| `risk` | The final risk report |
| `all` | Everything above (the default if `--include` is omitted) |

### `warm`
 
Pre-builds and caches a single version's graph, without running a diff or score. Useful to run ahead of a real check, especially for a framework/version pair not yet used this session.
 
```bash
python cli.py warm <framework> <version> [--package <import_name>]
```

example command:
```bash
python cli.py warm django 5.0
python cli.py warm livekit-agents 1.8.1 --package livekit
```

### `cache list` / `cache clear`
 
Manages the cached graph files on disk, so a version pair is never rebuilt from source unless explicitly asked to be.
 
```bash
python cli.py cache list
python cli.py cache clear [<framework>]
```

example command:
```bash
python cli.py cache list
python cli.py cache clear
python cli.py cache clear django
```

---
## Design notes
- **Every command is a thin wrapper around an orchestrator function** - the CLI, the MCP server, and the BOSS plugin all call the same handful of functions in `orchestrator/pipeline.py`. Nothing about how a check is performed differs between delivery surfaces.
- **`check` is the only command that touches a user's own repository by default**, every other command either operates purely on public framework data, or requires `--repo` explicitly. Nothing about a user's code is read unless they specifically point the tool at it.
- **Not yet built:** an interactive graph visualization command was designed but deliberately deferred, see `PyUpgrade-Intelligence-Design.md` for the reasoning and the intended design if picked up later. A changelog-fetching command was designed, then dropped from scope entirely (also documented there, with the reasoning for why it turned out not to be necessary).