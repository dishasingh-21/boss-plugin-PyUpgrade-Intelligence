# Data shapes for risk report.

from dataclasses import dataclass, field
from enum import Enum

class Recommendation(str, Enum):
    UPGRADE = "UPGRADE"
    UPGRADE_WITH_CAUTION = "UPGRADE_WITH_CAUTION"
    HOLD = "HOLD"

@dataclass
class FileRisk:
    file: str
    line: int
    symbol_id: str
    change_type: str
    detail: str

@dataclass
class ScoreBreakdownEntry:
    category: str
    severity: float
    count: int
    contributes_to_max: bool = False

@dataclass
class RiskReport:
    framework: str
    version_from: str
    version_to: str
    score: int
    recommendation: Recommendation
    max_severity: float = 0.0
    breadth: float = 0.0
    worst_change_symbol: str | None=None
    score_breakdown: list[ScoreBreakdownEntry] = field(default_factory=list)
    affected_files: list[FileRisk] = field(default_factory=list)
    total_changes_in_diff: int = 0
    relevant_changes_count: int = 0 
