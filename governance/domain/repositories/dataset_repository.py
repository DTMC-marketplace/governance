"""
Dataset Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.dataset import Dataset


class IDatasetRepository(ABC):
    """Interface for Dataset repository"""
    
    @abstractmethod
    def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        """Get dataset by ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Dataset]:
        """Get all datasets"""
        pass
    
    @abstractmethod
    def get_by_ids(self, dataset_ids: List[int]) -> List[Dataset]:
        """Get datasets by IDs"""
        pass
    
    @abstractmethod
    def create(self, dataset: Dataset) -> Dataset:
        """Create new dataset"""
        pass
