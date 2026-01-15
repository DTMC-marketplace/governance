"""
Dashboard DTOs
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DataCollectionProgressDTO:
    """Data collection progress DTO"""
    completed: int
    in_progress: int
    not_started: int
    completed_pct: int
    in_progress_pct: int
    not_started_pct: int


@dataclass
class RiskScoringDTO:
    """Risk scoring DTO"""
    ai_risk: float
    data_risk: float
    cyber_risk: float


@dataclass
class ReportingProgressDTO:
    """Reporting progress DTO"""
    completed: int
    in_progress: int
    not_started: int
    deprioritized: int
    completed_pct: int
    in_progress_pct: int
    not_started_pct: int
    deprioritized_pct: int


@dataclass
class FrameworkProgressDTO:
    """Framework progress DTO"""
    completed: int
    in_progress: int
    not_started: int
    deprioritized: int


@dataclass
class DashboardDTO:
    """Dashboard data DTO"""
    total_use_cases: int
    assessed_use_cases: int
    under_reviewed: int
    data_collection_completed: int
    data_collection_progress: DataCollectionProgressDTO
    risk_scoring: RiskScoringDTO
    reporting_progress: ReportingProgressDTO
    frameworks_data: Dict[str, FrameworkProgressDTO]
