# PyUpgrade Intelligence design notes
What the tool can't do yet, what I chose not to build yet, some key approaches, and what all the engine is tested on.

---
## Known limitations
**It only catches direct usage.** If your code imports something and calls it right there, the tool sees it. If the usage is indirect, it might miss it:

- **Variables and return values aren't tracked.** `x = get_thing(); x.save()`, the tool can't tell what type `x` is, so it won't catch this call.
- **Subclasses aren't linked to their parent's constructor.** If you write `class Article(Model)` and then call `Article(...)`, the tool sees the inheritance but doesn't connect the call back to `Model.__init__`.
- **Fully dynamic calls can't be solved at all**, `getattr(obj, some_string)()` needs the code to actually run to know what it calls.

**A moved symbol can rarely be matched wrong.** If a symbol disappears from its old location, the tool looks for a same-name, same-type symbol elsewhere and calls it "moved." In a codebase with many methods sharing the same name across different classes, this can occasionally match the wrong one.

**After package detection has already found the correct package folder, non-source subfolders inside it are skipped using a fixed list of common names** (`tests`, `docs`, `examples`, and similar) and not by reading the project's own build configuration. It works by matching known names rather than understanding what a folder actually contains, so a project using an unusual name for a non-source folder would have those files mistakenly treated as real framework code.

None of these cause false alarms. The tool stays quiet when unsure. It can miss something real, but it won't invent a problem that isn't there.

---
## Deferred features (designed but not built)
- **Daily-use features on top of the same engine**: inline warnings while typing, diagnosing a break after an upgrade, a weekly dependency health summary, a check that runs on every pull request. All reuse the core engine, none are built yet.
- **Auto-generating the actual fix code**
- **A visual explorer for the semantic graph**: zoom from a high-level view down to one function's exact relationships. The graph already has everything needed to build this later.
- **Tracing indirect impact through the call graph**: if function A calls function B, and B changed, flag A too, even if your code never touches B directly. Designed the full algorithm (safe against infinite loops) but didn't ship it. The reason: a function's internals can change with zero actual impact on anyone calling it, and flagging every one of those as "possibly affected" would make the tool noisy and untrustworthy.
- **A changelog reader**: I originally wanted to add it to boost confidence in uncertain signals and explain *why* something changed. Turned out neither needed it: uncertain signals are just scored low by default, and the diff itself already gives enough detail to explain a change. If this gets built later, will keep it as two separate pieces: one part per framework that knows *where* to find the text, one shared part that knows how to *read* it.

---
## Data Privacy
A user's code never leaves their machine. The tool only ever downloads public framework source code from PyPI. It never sends anything about the user's project, its files, or source code anywhere. All analysis of the codebase happens locally, in the same process the tool runs in.

---
## How package detection works
Not every framework's installed name matches its actual code folder. For e.g., `pillow` installs under that name but you `import PIL`. `scikit-learn` installs under that name but you `import sklearn`. `livekit-agents` installs under that name but the real code lives in a folder called `livekit`, showing no resemblance at all.

PyUpgrade Intelligence handles this in two steps:

1. **Try a smart name match first.** Look for a folder whose name matches the framework, allowing for common variations like hyphens versus underscores.
2. **If nothing matches, check what's actually there.** If there's exactly one real code folder sitting in the downloaded source, that's almost certainly the right one, and the tool uses it directly.

The code also handles a third case: if neither step gives a confident answer (nothing matches by name, and more than one real folder is present), it stops and reports a clear error listing what it found, rather than guessing. If this is the case, simple add `--package <correct-package-name>` (if using CLI) or mention the correct package name in the MCP Client you're using.

---
## Speeding up repeated checks
Building a full picture of a framework - downloading its source and reading through every file - takes a little time the first time it's done for a given version. After that, it's saved and reused instantly.
 
To make sure a real check always feels fast, I added a separate step that builds this picture ahead of time, on its own, before you actually need it. Do this once per framework version, and every check against it afterward is quick.

---
## Testing
 
The tool was tested against the following frameworks:

- **Django**, versions 4.2 and 5.0
- **Flask**
- **LiveKit Agents**, versions 1.5.1 and 1.8.1

**61 automated tests** cover every component - extraction, cross-file resolution, diffing, usage detection, and scoring.

**The MCP layer was tested at two levels.** First, with the MCP Inspector (a tool made for checking an MCP server speaks the protocol correctly, confirming the tool list and their schemas are correct). Second, with a real AI assistant (Claude Desktop) actually connected and making real tool calls, confirming the whole thing works the way a user's AI agent would use it.

A test project folder is also added in this tool's repo (check `test_django_project\`) against which the testing was done for django framework, versions 4.2 and 5.0.
