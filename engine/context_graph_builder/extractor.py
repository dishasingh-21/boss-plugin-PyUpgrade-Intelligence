import ast
from contracts.graph import Node, Param

class NodeExtractor(ast.NodeVisitor):
    def __init__(self, file_path: str, module_prefix: str):
        self.file_path=file_path
        self.module_prefix=module_prefix
        self.nodes: dict[str, Node]={}
        self._class_stack: list[str]=[]

    def visit_FunctionDef(self, node:ast.FunctionDef):
        self._extract_function(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node:ast.ClassDef):
        qualified_name = self._build_id(node.name)
        bases = [self._name_of(base) for base in node.bases]
        self.nodes[qualified_name] = Node(
            id=qualified_name,
            type="Class",
            name=node.name,
            file=self.file_path,
            line=node.lineno,
            signature=f"class {node.name}({', '.join(bases)})",
            is_public=not node.name.startswith("_"),
        )
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def _extract_function(self, node: ast.FunctionDef):
        qualified_name = self._build_id(node.name)
        node_type = "Method" if self._class_stack else "Function"
        params = self._extract_params(node.args)
        signature = self._build_signature(node.name, params)
        self.nodes[qualified_name] = Node(
            id=qualified_name,
            type=node_type,
            name=node.name,
            file=self.file_path,
            line=node.lineno,
            signature=signature,
            params=params,
            is_public=not node.name.startswith("_"),
        )

    def _extract_params(self, args: ast.arguments) -> list[Param]:
        all_args=args.args
        defaults=args.defaults
        padding = [None]*(len(all_args)-len(defaults))
        aligned_defaults = padding + list(defaults)
        params=[]
        for i, (arg, default) in enumerate(zip(all_args, aligned_defaults)):
            default_str = None
            if default is not None:
                default_str = self._const_to_str(default)
            params.append(Param(name=arg.arg, default=default_str, position=i))
        return params

    def _const_to_str(self, node:ast.expr) -> str:
        if isinstance(node, ast.Constant):
            return repr(node.value)
        return ast.unparse(node)

    def _build_signature(self, name: str, params: list[Param]) -> str:
        parts = []
        for p in params:
            if p.default is not None:
                parts.append(f"{p.name}={p.default}")
            else:
                parts.append(p.name)
        return f"{name}({', '.join(parts)})"

    def _build_id(self, name: str) -> str:
        prefix = ".".join([self.module_prefix] + self._class_stack)
        return f"{prefix}.{name}"

    def _name_of(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ast.unparse(node)

def extract_from_source(source: str, file_path: str, module_prefix: str) -> dict[str, Node]:
    """Entry point: parse source text and return extracted Nodes."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise SyntaxError(f"{file_path}: {e.msg} (line {e.lineno})") from e
    extractor = NodeExtractor(file_path, module_prefix)
    extractor.visit(tree)
    return extractor.nodes