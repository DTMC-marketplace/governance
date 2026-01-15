"""
AI Model Domain Entity
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Model:
    """AI Model domain entity"""
    id: int
    name: str
    vendor: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if not self.name:
            raise ValueError("Model name is required")
        if self.id <= 0:
            raise ValueError("Model ID must be positive")
