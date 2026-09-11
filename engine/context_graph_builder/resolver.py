import ast
from contracts.graph import Graph, Edge
from context_graph_builder.extractor import extract_from_source

class FileInfo:
    def __init__(self, file_path: str, module_prefix: str, source: str):
        self.file_path = file_path
        self.module_prefix = module_prefix
        self.source = source

def build_graph(framework: str, version: str, files: list[FileInfo]) -> Graph:
    graph = Graph(framework=framework, version=version)
    # <-------PASS-1: Extract nodes from every file. ------->
    for f in files:
        try:
            nodes = extract_from_source(f.source, f.file_path, f.module_prefix)
            graph.nodes.update(nodes)
        except SyntaxError as e:
            print(f"Skipping {f.file_path}: Syntax Error ({e})")

    short_name_table: dict[str,str]={}
    for node_id, node in graph.nodes.items():
        short_name_table[node.name] = node_id

    # <-------PASS-2: Resolve imports and calls into edges ------->
    for f in files:
        try:
            tree = ast.parse(f.source)
        except SyntaxError as e:
            print(f"Skipping {f.file_path}: Syntax Error ({e})")
            continue
        resolver = _CallAndImportResolver(
            file_path=f.file_path,
            module_prefix=f.module_prefix,
            short_name_table=short_name_table,
        )
        resolver.visit(tree)
        graph.edges.extend(resolver.edges)

    return graph

class _CallAndImportResolver(ast.NodeVisitor):
    def __init__(self, file_path: str, module_prefix: str, short_name_table: dict[str,str]):
        self.file_path=file_path
        self.module_prefix=module_prefix
        self.short_name_table=short_name_table
        self.edges: list[Edge] = []
        self.local_aliases: dict[str,str]={}       # Maps a name used in this file to its fully qualified id, populated as we encounter import statements.
        self._scope_stack: list[str]=[]            # Tracks which function/method we're currently inside, so a call gets the correct from_id.
        self._class_stack: list[str]=[]

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            imported_name = alias.name
            local_name = alias.asname or imported_name
            qualified_id = f"{module}.{imported_name}"
            self.local_aliases[local_name] = qualified_id
            self.edges.append(Edge(from_id=self.module_prefix, to_id=qualified_id, type="imports"))
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.asname:
                local_name=alias.asname
                qualified_id=alias.name
            else:
                local_name=alias.name.split(".")[0]
                qualified_id=alias.name

            self.local_aliases[local_name]=qualified_id
            self.edges.append(Edge(from_id=self.module_prefix, to_id=qualified_id, type="imports"))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        qualified_id = ".".join([self.module_prefix]+self._class_stack+[node.name])
        for base in node.bases:
            base_id=self._resolve_name_expr(base)
            if base_id:
                self.edges.append(Edge(from_id=qualified_id, to_id=base_id, type="inherits"))
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        qualified_id = ".".join([self.module_prefix]+self._class_stack+[node.name])
        self._scope_stack.append(qualified_id)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_Call(self, node: ast.Call):
        target_id = self._resolve_call_target(node.func)
        if target_id and self._scope_stack:
            self.edges.append(Edge(from_id=self._scope_stack[-1], to_id=target_id, type="calls"))
        self.generic_visit(node)

    def _resolve_name_expr(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            name = node.id
            if name in self.local_aliases:
                return self.local_aliases[name]
            if name in self.short_name_table:
                return self.short_name_table[name]
        return None

    def _resolve_call_target(self, func_node: ast.expr) -> str | None:
        if isinstance(func_node, ast.Name):     # CASE-1: Direct call
            return self._resolve_name_expr(func_node)

        if isinstance(func_node, ast.Attribute):
            method_name = func_node.attr
            base = func_node.value
            if isinstance(base, ast.Name):
                base_name = base.id
                if base_name in self.local_aliases:
                    base_id = self.local_aliases[base_name]
                    return f"{base_id}.{method_name}"
                if method_name in self.short_name_table:
                    return self.short_name_table[method_name]
                return None

        return None

