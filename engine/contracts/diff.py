from dataclasses import dataclass
from enum import Enum
from contracts.graph import Node

class ChangeType(str, Enum):
    REMOVED = "REMOVED"
    ADDED = "ADDED"
    SIGNATURE_CHANGED = "SIGNATURE_CHANGED"
    MOVED_ALSO_CHANGED = "MOVED_ALSO_CHANGED"
    BODY_CHANGED = "BODY_CHANGED"
    MOVED_UNCHANGED = "MOVED_UNCHANGED"

@dataclass
class Change:
    symbol_id: str
    change_type: ChangeType
    old: Node | None
    new: Node | None
    detail: str = ""
    body_diff_text: str = ""
    moved_also_changed: bool = False

@dataclass
class DiffResult:
    framework: str
    version_from: str
    version_to: str
    changes: list[Change]
