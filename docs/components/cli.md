# CLI

## What it is
A command-line interface to the full engine, usable without BOSS environment or any AI agent at all.

## How it works
Every command is a thin wrapper around one orchestrator function, argument parsing and output formatting only, no real logic lives here. This keeps the CLI and the MCP server permanently in sync, since they call the exact same underlying code.

Nine commands total: `check`, `changes`, `usage`, `affected`, `config-diff`, `export`, `warm`, `cache list`, `cache clear`.

Full command reference: [`CLI-Specification.md`](../../CLI-Specification.md)