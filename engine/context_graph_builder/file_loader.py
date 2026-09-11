from pathlib import Path
from context_graph_builder.resolver import build_graph, FileInfo
from contracts.graph import Graph

def _module_prefix_from_path(file_path: Path, root: Path) -> str:
    rel = file_path.relative_to(root)
    parts = list(rel.parts)

    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]

    return ".".join(parts)

def build_graph_from_directory(framework: str, version: str, root_dir: str) -> Graph:
    root = Path(root_dir)
    files: list[FileInfo] = []
    for pyfile in root.rglob("*.py"):
        try:
            source = pyfile.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            print(f"Skipping {pyfile}: Could not read ({e})")

        module_prefix = _module_prefix_from_path(pyfile, root)
        files.append(FileInfo(file_path=str(pyfile), module_prefix=module_prefix, source=source))

    return build_graph(framework, version, files)
