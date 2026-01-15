"""
Agent Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.agent import Agent


class IAgentRepository(ABC):
    """Interface for Agent repository"""
    
    @abstractmethod
    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Agent]:
        """Get all agents"""
        pass
    
    @abstractmethod
    def search(self, search_term: str) -> List[Agent]:
        """Search agents by name"""
        pass
    
    @abstractmethod
    def create(self, agent: Agent) -> Agent:
        """Create new agent"""
        pass
