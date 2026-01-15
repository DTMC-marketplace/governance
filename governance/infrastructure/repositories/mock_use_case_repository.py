"""
Mock Use Case Repository Implementation
"""
from typing import List, Optional
from pathlib import Path
import json

from ...domain.entities.use_case import UseCase, ReviewStatus
from ...domain.repositories.use_case_repository import IUseCaseRepository
from ...domain.factories.use_case_factory import UseCaseFactory


class MockUseCaseRepository(IUseCaseRepository):
    """Mock implementation of use case repository"""
    
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache = None
    
    def _load_data(self) -> List[dict]:
        """Load use cases from JSON file"""
        if self._cache is None:
            filepath = self._data_dir / 'use_cases.json'
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = []
        return self._cache
    
    def _dict_to_entity(self, data: dict) -> UseCase:
        """Convert dict to UseCase entity using Factory Pattern"""
        return UseCaseFactory.create_from_dict(data)
    
    def get_by_id(self, use_case_id: int) -> Optional[UseCase]:
        """Get use case by ID"""
        data = self._load_data()
        uc_data = next((uc for uc in data if uc.get('id') == use_case_id), None)
        if uc_data:
            return self._dict_to_entity(uc_data)
        return None
    
    def get_all(self) -> List[UseCase]:
        """Get all use cases"""
        data = self._load_data()
        return [self._dict_to_entity(uc_data) for uc_data in data]
    
    def get_by_agent_id(self, agent_id: int) -> List[UseCase]:
        """Get use cases by agent ID"""
        data = self._load_data()
        filtered = [
            uc_data for uc_data in data
            if uc_data.get('agent_id') == agent_id
        ]
        return [self._dict_to_entity(uc_data) for uc_data in filtered]
    
    def search(self, search_term: str) -> List[UseCase]:
        """Search use cases by name"""
        if not search_term:
            return self.get_all()
        
        data = self._load_data()
        search_lower = search_term.lower()
        filtered = [
            uc_data for uc_data in data
            if search_lower in uc_data.get('name', '').lower()
        ]
        return [self._dict_to_entity(uc_data) for uc_data in filtered]
    
    def create(self, use_case: UseCase) -> UseCase:
        """Create new use case (mock - doesn't persist)"""
        return use_case
