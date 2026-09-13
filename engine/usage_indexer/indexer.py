# Scans a developer's own repository and finds every place their code references a symbol from the given framework's semantic graph.

import ast
from pathlib import Path
from collections import defaultdict
from contracts.graph import Graph
from contracts.usage import Usage, UsageIndex

def build_usage_index(repo_path: str, framework_graph: Graph) -> UsageIndex:
    framework_ids = set(framework_graph.nodes.keys())
    combined: dict[str, list[Usage]] = defaultdict(list)
    root = Path(repo_path)
    for py_file in root.rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (UnicodeDecodeError, OSError, SyntaxError) as e:
            print(f"Skipping {py_file}: {e}")
            continue

        visitor = _UsageVisitor(file_path=str(py_file), framework_ids=framework_ids)
        visitor.visit(tree)
        for symbol_id, usages in visitor.usages.items():
            combined[symbol_id].extend(usages)
    return UsageIndex(repo_path=repo_path, usages=dict(combined))

class _UsageVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, framework_ids: set[str]):
        self.file_path = file_path
        self.framework_ids = framework_ids
        self.local_aliases: dict[str,str] = {}
        self.usages: dict[str, list[Usage]] =defaultdict(list)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            local_name = alias.asname or alias.name
            self.local_aliases[local_name] = f"{module}.{alias.name}"
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.asname:
                local_name, qualified = alias.asname, alias.name
            else:
                local_name, qualified = alias.name.split(".")[0], alias.name
            self.local_aliases[local_name] = qualified
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        for base in node.bases:
            self._record_if_match(base, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        self._record_if_match(node.func, node.lineno)
        self.generic_visit(node)

    def _record_if_match(self, expr: ast.expr, lineno: int):
        parts = _dotted_chain(expr)
        if not parts:
            return
        candidate = _resolve_candidate_id(parts, self.local_aliases)
        if candidate and candidate in self.framework_ids:
            self.usages[candidate].append(Usage(file=self.file_path, line=lineno))

def _dotted_chain(node: ast.expr) -> list[str] | None:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        parts.reverse()
        return parts
    return None

def _resolve_candidate_id(parts: list[str], local_aliases: dict[str, str]) -> str | None:
    if not parts or parts[0] not in local_aliases:
        return None
    resolved_base = local_aliases[parts[0]]
    remainder = parts[1:]
    return ".".join([resolved_base]+remainder) if remainder else resolved_base

"""LIMITATION: It can only catch a symbol when you use it right where you imported it. If it passes through a variable or another function first, the usage gets missed."""