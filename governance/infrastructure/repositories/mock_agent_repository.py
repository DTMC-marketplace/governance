"""
Mock Agent Repository Implementation
"""
from typing import List, Optional
from pathlib import Path
import json

from ...domain.entities.agent import Agent, ComplianceStatus, AIActRole, RiskClassification
from ...domain.repositories.agent_repository import IAgentRepository
from ...domain.factories.agent_factory import AgentFactory
from ...application.exceptions.domain_exceptions import EntityNotFoundException


class MockAgentRepository(IAgentRepository):
    """Mock implementation of agent repository"""
    
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache = None
    
    def _load_data(self) -> List[dict]:
        """Load agents from JSON file"""
        if self._cache is None:
            filepath = self._data_dir / 'agents.json'
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = []
        return self._cache
    
    def _dict_to_entity(self, data: dict) -> Agent:
        """Convert dict to Agent entity using Factory Pattern"""
        return AgentFactory.create_from_dict(data)
    
    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        data = self._load_data()
        agent_data = next((a for a in data if a.get('id') == agent_id), None)
        if agent_data:
            return self._dict_to_entity(agent_data)
        return None
    
    def get_all(self) -> List[Agent]:
        """Get all agents"""
        data = self._load_data()
        return [self._dict_to_entity(agent_data) for agent_data in data]
    
    def search(self, search_term: str) -> List[Agent]:
        """Search agents by name"""
        if not search_term:
            return self.get_all()
        
        data = self._load_data()
        search_lower = search_term.lower()
        filtered = [
            agent_data for agent_data in data
            if search_lower in agent_data.get('name', '').lower()
        ]
        return [self._dict_to_entity(agent_data) for agent_data in filtered]
    
    def create(self, agent: Agent) -> Agent:
        """Create new agent (mock - doesn't persist)"""
        # In a real implementation, this would save to database
        return agent
