"""
Mock Model Repository Implementation
"""
from typing import List, Optional
from pathlib import Path
import json

from ...domain.entities.model import Model
from ...domain.repositories.model_repository import IModelRepository


class MockModelRepository(IModelRepository):
    """Mock implementation of model repository"""
    
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache = None
    
    def _load_data(self) -> List[dict]:
        """Load models from JSON file"""
        if self._cache is None:
            filepath = self._data_dir / 'models.json'
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = []
        return self._cache
    
    def _dict_to_entity(self, data: dict) -> Model:
        """Convert dict to Model entity"""
        return Model(
            id=data.get('id'),
            name=data.get('name', ''),
            vendor=data.get('vendor'),
            description=data.get('description'),
        )
    
    def get_by_id(self, model_id: int) -> Optional[Model]:
        """Get model by ID"""
        data = self._load_data()
        model_data = next((m for m in data if m.get('id') == model_id), None)
        if model_data:
            return self._dict_to_entity(model_data)
        return None
    
    def get_all(self) -> List[Model]:
        """Get all models"""
        data = self._load_data()
        return [self._dict_to_entity(model_data) for model_data in data]
    
    def get_by_ids(self, model_ids: List[int]) -> List[Model]:
        """Get models by IDs"""
        data = self._load_data()
        filtered = [
            model_data for model_data in data
            if model_data.get('id') in model_ids
        ]
        return [self._dict_to_entity(model_data) for model_data in filtered]
    
    def create(self, model: Model) -> Model:
        """Create new model (mock - doesn't persist)"""
        return model
