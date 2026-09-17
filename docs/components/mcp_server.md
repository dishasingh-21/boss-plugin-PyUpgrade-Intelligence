# MCP server

## What it is
Exposes the engine as a standalone MCP server, usable from any MCP client (Claude Desktop, the MCP Inspector, or BOSS through the Kotlin plugin).

## How it works
Built on the MCP Python SDK, exposing 7 tools, each a thin wrapper around an orchestrator function, matching the CLI's commands one for one. Each tool's description is written to actively guide an AI agent's behavior. For example, `pyupgrade_check`'s own description tells an agent to call `pyupgrade_warm_cache` first on a framework/version pair it hasn't seen yet, so a real check lands on an already-fast path.

`pyupgrade_get_breaking_changes` filters to high-confidence change types by default, only returning the lower-confidence, implementation-only signals if explicitly asked for, the same anti-noise principle the risk scorer uses.

Validated at two levels: the MCP Inspector, confirming the protocol and tool schemas are correct; and a real connected AI assistant (Claude Desktop), confirming an actual agent uses the tools correctly and gets back a sensible result.

Connect it to any MCP client by pointing that client at this script. See [`USER_GUIDE.md`](../USER_GUIDE.md) for exact connection steps, including a real Claude Desktop config example.