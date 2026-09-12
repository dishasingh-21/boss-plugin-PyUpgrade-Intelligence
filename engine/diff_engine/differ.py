# Compares two Graph objects and produces a DiffResult classifying every change between them.
from contracts.graph import Graph, Node
from contracts.diff import Change, ChangeType, DiffResult

def diff(graph_a: Graph, graph_b: Graph) -> DiffResult:
    changes: list[Change] = []
    for node_id, node_a in graph_a.nodes.items():
        if node_id not in graph_b.nodes:
            moved_to = _find_moved(node_a, graph_b)
            if moved_to:
                detail = f"Moved from {node_a.id} to {moved_to.id}"
                sig_change = _diff_signature(node_a, moved_to)
                if sig_change:
                    detail += f". Also changed: {sig_change.detail}"
                changes.append(Change(
                    symbol_id=node_id,
                    change_type=ChangeType.MOVED,
                    old=node_a,
                    new=moved_to,
                    detail=detail,
                ))
            else:
                changes.append(Change(
                    symbol_id=node_id,
                    change_type=ChangeType.REMOVED,
                    old=node_a,
                    new=None,
                    detail=f"{node_a.type} '{node_a.name}' no longer exists."
                ))
        else:
            node_b = graph_b.nodes[node_id]
            sig_change = _diff_signature(node_a, node_b)
            if sig_change:
                changes.append(sig_change)

    for node_id, node_b in graph_b.nodes.items():
        if node_id not in graph_a.nodes:
            changes.append(Change(
                symbol_id=node_id,
                change_type=ChangeType.ADDED,
                old=None,
                new=node_b,
                detail=f"New {node_b.type.lower()} '{node_b.name}'",
            ))

    return DiffResult(framework=graph_a.framework, version_from=graph_a.version, version_to= graph_b.version, changes=changes)

def _diff_signature(node_a: Node, node_b: Node) -> Change | None:
    sig_differs = node_a.signature != node_b.signature
    async_differs = node_a.is_async != node_b.is_async
    property_differs = node_a.is_property != node_b.is_property
    body_differs = node_a.body_hash != node_b.body_hash

    if not sig_differs and not async_differs and not property_differs and not body_differs:
        return None
    if sig_differs or async_differs or property_differs:
        old_names = [p.name for p in node_a.params]
        new_names = [p.name for p in node_b.params]
        detail_parts = []
        if property_differs:
            direction = "a regular method to a @property" if node_b.is_property else "a @property to a regular method"
            detail_parts.append(f"Changed from {direction}. Callers must update obj.{node_b.name}() vs. obj.{node_b.name}")
        if async_differs:
            direction = "sync to async" if node_b.is_async else "async to sync"
            detail_parts.append(f"Changed from {direction}. Callers must update await usage")
        if old_names != new_names:
            detail_parts.append(f"parameters changes from ({', '.join(old_names)}) to ({', '.join(new_names)})")
        elif node_a.type == "Class" and sig_differs:
            detail_parts.append(f"base classes changed: {node_a.signature} -> {node_b.signature}")
        elif sig_differs:
            for pa, pb in zip(node_a.params, node_b.params):
                if pa.default != pb.default:
                    detail_parts.append(f"'{pa.name}' default changed from {pa.default} to {pb.default}")

        return Change(
            symbol_id=node_a.id,
            change_type=ChangeType.SIGNATURE_CHANGED,
            old=node_a,
            new=node_b,
            detail="; ".join(detail_parts) if detail_parts else "signature changed",
        )
    return Change(
        symbol_id=node_a.id,
        change_type=ChangeType.BODY_CHANGED,
        old=node_a,
        new=node_b,
        detail="Implementation changed; signature unchanged. May be a behavior change or a harmless refactor, check changelog context before treating as high risk."
    )

def _find_moved(missing_node: Node, graph_b: Graph) -> Node | None:
    for node_b in graph_b.nodes.values():
        if node_b.name == missing_node.name and node_b.type == missing_node.type:
            return node_b
    return None

"""
KNOWN LIMITATION: _find_moved matches on (name, type) only. If two
different classes both define a same-named method, a removed method
could be incorrectly matched elsewhere rather than reported as
REMOVED. A more precise version would use parameter-list similarity
as a tiebreaker; not implemented as of now in this MVP.
"""
