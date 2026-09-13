# Data shapes for tracking where a developer's own code uses symbols from a framework's semantic graph.

from dataclasses import dataclass, field

@dataclass
class Usage:
    file: str
    line: int
    snippet: str = ""

@dataclass
class UsageIndex:
    repo_path: str
    usages: dict[str, list[Usage]] = field(default_factory=dict)

