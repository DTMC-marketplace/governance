"""
Mock Dataset Repository Implementation
"""
from typing import List, Optional
from pathlib import Path
import json

from ...domain.entities.dataset import Dataset
from ...domain.repositories.dataset_repository import IDatasetRepository


class MockDatasetRepository(IDatasetRepository):
    """Mock implementation of dataset repository"""
    
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache = None
    
    def _load_data(self) -> List[dict]:
        """Load datasets from JSON file"""
        if self._cache is None:
            filepath = self._data_dir / 'datasets.json'
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = []
        return self._cache
    
    def _dict_to_entity(self, data: dict) -> Dataset:
        """Convert dict to Dataset entity"""
        return Dataset(
            id=data.get('id'),
            name=data.get('name', ''),
            source=data.get('source'),
            description=data.get('description'),
        )
    
    def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        """Get dataset by ID"""
        data = self._load_data()
        dataset_data = next((d for d in data if d.get('id') == dataset_id), None)
        if dataset_data:
            return self._dict_to_entity(dataset_data)
        return None
    
    def get_all(self) -> List[Dataset]:
        """Get all datasets"""
        data = self._load_data()
        return [self._dict_to_entity(dataset_data) for dataset_data in data]
    
    def get_by_ids(self, dataset_ids: List[int]) -> List[Dataset]:
        """Get datasets by IDs"""
        data = self._load_data()
        filtered = [
            dataset_data for dataset_data in data
            if dataset_data.get('id') in dataset_ids
        ]
        return [self._dict_to_entity(dataset_data) for dataset_data in filtered]
    
    def create(self, dataset: Dataset) -> Dataset:
        """Create new dataset (mock - doesn't persist)"""
        return dataset
