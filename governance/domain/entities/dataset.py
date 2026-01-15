"""
Dataset Domain Entity
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Dataset:
    """Dataset domain entity"""
    id: int
    name: str
    source: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if not self.name:
            raise ValueError("Dataset name is required")
        if self.id <= 0:
            raise ValueError("Dataset ID must be positive")
