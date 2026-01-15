"""
Model Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.model import Model


class IModelRepository(ABC):
    """Interface for Model repository"""
    
    @abstractmethod
    def get_by_id(self, model_id: int) -> Optional[Model]:
        """Get model by ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Model]:
        """Get all models"""
        pass
    
    @abstractmethod
    def get_by_ids(self, model_ids: List[int]) -> List[Model]:
        """Get models by IDs"""
        pass
    
    @abstractmethod
    def create(self, model: Model) -> Model:
        """Create new model"""
        pass
