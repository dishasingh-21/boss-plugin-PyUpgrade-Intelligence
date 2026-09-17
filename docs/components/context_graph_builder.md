# context_graph_builder
 
## What it is
Builds a semantic graph of one version of a framework's source code, every function, class, and method it contains, with real signatures and how they relate to each other. This is the foundation everything else is built on.
 
## How it works
1. **Downloads the source** for the requested version from PyPI, caching it so it's never downloaded twice.
2. **Finds the real package folder** inside the downloaded files: not always obvious, since a package's install name and its actual code folder can differ (see [`PyUpgrade-Intelligence-Design.md`](../../PyUpgrade-Intelligence-Design.md) for how this works).
3. **Parses every `.py` file** using Python's own `ast` module, the same way Python itself reads code, just stopping short of running it.
4. **Extracts every function, method, and class**, capturing its name, parameters, whether it's `async`, whether it's a `@property`, and a fingerprint of its actual implementation (not just its signature).
5. **Resolves relationships across files**: which functions call which, which classes inherit from which, which imports point where including resolving a framework's own internal re-exports.
6. **Skips non-source folders** (tests, docs, examples) inside the package using a fixed list of common names.
7. **Saves the result to disk as JSON**, so the same version is never rebuilt from scratch twice.

