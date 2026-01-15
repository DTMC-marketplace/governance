"""
Use Case Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.use_case import UseCase


class IUseCaseRepository(ABC):
    """Interface for Use Case repository"""
    
    @abstractmethod
    def get_by_id(self, use_case_id: int) -> Optional[UseCase]:
        """Get use case by ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[UseCase]:
        """Get all use cases"""
        pass
    
    @abstractmethod
    def get_by_agent_id(self, agent_id: int) -> List[UseCase]:
        """Get use cases by agent ID"""
        pass
    
    @abstractmethod
    def search(self, search_term: str) -> List[UseCase]:
        """Search use cases by name"""
        pass
    
    @abstractmethod
    def create(self, use_case: UseCase) -> UseCase:
        """Create new use case"""
        pass
