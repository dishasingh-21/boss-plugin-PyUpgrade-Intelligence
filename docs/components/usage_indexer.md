# usage_indexer

## What it is
Scans a developer's own codebase to find which framework symbols it actually uses, and exactly where. This is what turns "here's everything that changed in the framework" into "here's what actually matters for this specific project."

## How it works
Walks every `.py` file in the given codebase and looks for:
- Direct calls to an imported framework function or method
- A locally-defined class inheriting from a framework class
- Instantiating a framework class directly (treated as a usage of its constructor)
Every match is resolved through the same public re-export logic the context graph builder uses.

**Deliberately conservative.** If it can't confidently resolve a usage, it stays silent rather than guessing, a false alarm here would pollute the final risk report, which is worse than missing an indirect usage. See [`PyUpgrade-Intelligence-Design.md`](../../PyUpgrade-Intelligence-Design.md) for the specific, real cases this misses and why.

Produces a fast result by default (just file and line), with an optional enriched pass adding the actual source line for each usage.