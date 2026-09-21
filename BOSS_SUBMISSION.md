# Submission - BOSS Contributor Hackathon

---
## 1. User and problem
USER: Developers and teams maintaining Python projects on frameworks, who need to decide whether it's safe to upgrade a dependency.

Today, answering a question like "is it safe to upgrade Django from 4.2 to 5.0?" means manually reading changelogs and guessing which changes actually touch your codebase. Majority tools in this space work by reading what maintainers *wrote* about a release, and none target Python. This tool builds a semantic graphs of both framework versions, structurally diffs them, cross-references the diff against your own codebase's actual usage, and returns a deterministic, auditable risk score with the exact files and lines affected.

---
## 2. Source

- **Repository:** https://github.com/dishasingh-21/boss-plugin-PyUpgrade-Intelligence
- **Implementation:** https://github.com/dishasingh-21/boss-plugin-PyUpgrade-Intelligence/commit/5d4bd51a117bd2eb963873d5cce14c37adc40913

---
## 3. Demo
**MCP Client demo, Claude Code, attached as the agent inside BOSS**: https://drive.google.com/drive/u/0/folders/1P5XlD8omfoCXIJFq-tUNC7Isv-qCTxGl

**CLI demo, run directly in BOSS's terminal panel**: https://drive.google.com/drive/u/0/folders/1OH834OVjMg9iMgg3wiT04bdMT-Sjkfc4

---
## 4. Reproduction 
### Set up the Python engine
```bash
git clone https://github.com/dishasingh-21/boss-plugin-PyUpgrade-Intelligence.git
cd boss-plugin-PyUpgrade-Intelligence/engine
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run the automated test suite
```bash
cd engine
python -m pytest
```

Expected: `61 passed` (no failures, no skips). Requires the Python engine setup from the steps above (venv activated, dependencies installed)

### Build the plugin
```bash
cd ..\..
git clone https://github.com/risa-labs-inc/boss-plugin-api.git
cd boss-plugin-api
.\gradlew.bat buildPluginJar
 
cd ..\boss-plugin-PyUpgrade-Intelligence
.\gradlew.bat buildPluginJar
```

`boss-plugin-api` and `boss-plugin-PyUpgrade-Intelligence` must to be sibling directories.

### Configure
Set one environment variable, pointing at `boss-plugin-PyUpgrade-Intelligence` repo's `engine` folder:
```
PYUPGRADE_ENGINE_PATH=<absolute path to engine>
```

### Install into BOSS
If BOSS isn't already installed, get it from the official release page ([`risa-labs-inc/BossConsole` → Releases](https://github.com/risa-labs-inc/BossConsole/releases)). Then:
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.boss\plugins"
Copy-Item "build\libs\boss-plugin-pyupgrade-intelligence-0.1.0.jar" "$env:USERPROFILE\.boss\plugins\"
```

Write the exact name of the JAR file, so produced, after the step where you built the plugin.

Launch BOSS, open **Toolbox**, confirm the plugin is enabled, then check **Toolbox → MCP** for its 7 tools.

### Minimal example task
Attach an AI CLI (Claude Code, Codex, Gemini, or OpenCode) via **Toolbox → MCP → Attach CLI**. Open a terminal tab inside BOSS, start it (e.g. if you've attached Claude, start by activating it for this type - `claude`), and ask:

> "Is it safe to upgrade Django from 4.2 to 5.0 for the project at `../test_django_project`?"

Expected result: It should produce a response including a numeric score, a recommendation (`UPGRADE`/`UPGRADE_WITH_CAUTION`/`HOLD`), and specific affected files with line numbers - e.g., for `test_django_project`: score 89/100, `HOLD`, driven by a removed symbol (`LocaleMiddleware.get_fallback_language`).

I would also suggest try running commands mentioned in [CLI-Specification.md](CLI-Specification.md) in the terminal.

### Note on infrastructure, separate from any test failure
Building BOSS from source in dev mode requires local Supabase credentials not available to external contributors, which blocked that specific path and is not a defect in this plugin. Testing instead used the official released BOSS build.

---
## 5. Compatibility

- **BOSS:** tested against the latest official Windows release (v9.5.18 at time of testing), installed via the official `.msi` installer
- **Declared `apiVersion`:** `1.0.51` (the lowest version with `McpToolProvider` support, for the widest host compatibility)
- **Compiled against:** `boss-plugin-api` 1.0.93
- **Operating system tested:** Windows 11
- **Python:** 3.12.8 (3.11+ required)
- **JDK:** 17 (tested on Temurin 17.0.20.1)
- **Attached agent tested:** Claude Code
- **Key dependencies:** MCP Python SDK 2.2.0, full list in [`engine/requirements.txt`](engine/requirements.txt). `kotlinx-coroutines-core` only on the Kotlin side - no UI dependencies, since this is a `service`-type, MCP-only plugin.

---
## 6. Access and data
- **Required permissions:** filesystem read/write only within paths the user explicitly provides (framework source cache, graph cache, the codebase path pointed at)
- **External services contacted:** `pypi.org` only, to fetch public framework source and metadata.
- **Data sent outside BOSS:** none of the user's own source code is ever sent anywhere. Usage analysis runs entirely locally, in the same process BOSS itself runs in.

---
## 7. Verification
**Automated tests:** 61 tests across the Python engine: extraction, cross-file resolution, diffing, usage detection, and scoring.

**Also tested in following modes:** 

| Level | What was tested                                                                                   | Result                                                                                                                                                                                                             |
|---|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Via CLI | Django 4.2 to 5.0, Flask, LiveKit Agents 1.5.1 to 1.8.1                                           | Django: 804 real changes found; a real risk score was hand-recalculated from the formula and matched exactly (89/100, `HOLD`). LiveKit Agents (a structurally different codebase) confirmed the design generalizes. |
| MCP protocol | MCP Inspector                                                                                     | Tool schemas and protocol correctness confirmed                                                                                                                                                                    |
| AI MCP client, standalone | Claude Desktop                                                                                    | Real tool calls, correct results, independent of BOSS                                                                                                                                                              |
| Full BOSS integration | Official BOSS release (not a dev build), installed via Toolbox, Claude Code attached as the agent | Plugin loaded correctly, all 7 MCP tools appeared correctly, and a plain-language question about a real Django upgrade was correctly answered end to end                                                           |

**Known limitations:** Documented in [`PyUpgrade-Intelligence-Design.md`](PyUpgrade-Intelligence-Design.md).

**Testing not done on:** macOS, Linux

---
## 8. Ownership
- **Author:** Disha Singh ([@dishasingh-21](https://github.com/dishasingh-21))
- **License:** MIT (see [`LICENSE`](LICENSE))
- **Attribution:** built for the BOSS Contributor Hackathon. The Kotlin plugin structure follows the patterns in [`boss-plugins/PLUGIN_DEVELOPMENT.md`](https://github.com/risa-labs-inc/boss-plugins/blob/main/PLUGIN_DEVELOPMENT.md); no code was copied from other plugins.

---
## 9. Request
- Feedback on the plugin's design and MCP tool set.

---
## Further documentation
- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md): setup, CLI, standalone MCP server, BOSS usage
- [`docs/components`](docs/components/): one doc per component - what it is, how it works, how to use it directly
- [`PyUpgrade-Intelligence-Design.md`](PyUpgrade-Intelligence-Design.md): every design decision, deferred feature, and known limitation with reasoning
- [`CLI-Specification.md`](CLI-Specification.md): exact command reference
- [`Risk-Scoring-Mathematical-Model.md`](Risk-Scoring-Mathematical-Model.md): Risk Scoring model
