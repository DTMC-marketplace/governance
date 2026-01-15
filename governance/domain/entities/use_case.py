"""
Use Case Domain Entity
"""
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class ReviewStatus(Enum):
    """Review status"""
    MISSING = "missing"
    PARTIAL = "partial"
    COMPLETE = "complete"


@dataclass
class UseCase:
    """Use Case domain entity"""
    id: int
    name: str
    display_name: Optional[str] = None
    overview: Optional[str] = None
    risk_type: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.MISSING
    compliance_assessed: bool = False
    agent_id: Optional[int] = None
    models: List[int] = None
    datasets: List[int] = None
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if not self.name:
            raise ValueError("Use case name is required")
        if self.id <= 0:
            raise ValueError("Use case ID must be positive")
        if self.models is None:
            self.models = []
        if self.datasets is None:
            self.datasets = []
    
    @property
    def has_models(self) -> bool:
        """Check if use case has models"""
        return len(self.models) > 0
    
    @property
    def has_datasets(self) -> bool:
        """Check if use case has datasets"""
        return len(self.datasets) > 0
