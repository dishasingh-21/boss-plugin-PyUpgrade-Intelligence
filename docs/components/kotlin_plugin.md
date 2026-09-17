# Kotlin plugin

## What it is
The actual BOSS plugin, the piece that makes every MCP tool reachable from inside BOSS by an attached agent.
 
## How it works
A `service`-type plugin (no panel, no tab - MCP tools only, so no UI dependencies at all). Implements `McpToolProvider`, registering 7 tools, each prefixed `pyupgrade_`, matching the standalone MCP server's tool set exactly.

Each tool's handler shells out to the Python engine as a subprocess, wrapped in a coroutine dispatcher so it doesn't block BOSS's UI thread while running. Deliberately does **not** kill that subprocess if a call runs long, this is what lets a slow first-time build keep working in the background and finish successfully, even if the tool call itself reports back sooner.

Needs one thing set up on the machine it runs on: an environment variable (`PYUPGRADE_ENGINE_PATH`) pointing at the PyUpgrade Intelligence engine's location, since a built plugin JAR has no way to find it on its own once installed.

## How to use it
Build it, then install it into BOSS through Toolbox's "From File" option. Full build and install steps: [`BOSS_SUBMISSION.md`](../../BOSS_SUBMISSION.md).