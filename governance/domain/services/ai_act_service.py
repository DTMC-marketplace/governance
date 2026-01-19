"""
Domain Service for AI Act Query
Provides business logic for querying EU AI Act and GDPR regulations
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class AIActQueryRequest:
    """Request for AI Act query"""
    question: str
    agent_id: Optional[str] = None
    chat_type: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    chat_history_id: Optional[str] = None  # ID to continue existing conversation


@dataclass
class AIActQueryResponse:
    """Response from AI Act query"""
    message: str
    references: List[Dict[str, Any]]
    chat_history_id: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    chat_history: Optional[List[Dict[str, Any]]] = None  # Chat history with messages


class AIActService:
    """
    Domain service for AI Act queries.
    This service defines the business logic interface without implementation details.
    """
    
    def query(self, request: AIActQueryRequest) -> AIActQueryResponse:
        """
        Query the AI Act and GDPR knowledge base.
        
        Args:
            request: The query request containing question and context
            
        Returns:
            AIActQueryResponse with answer, references, and sources
            
        Raises:
            ValueError: If the request is invalid
        """
        raise NotImplementedError("Subclasses must implement query method")
    
    def get_store_name(self) -> Optional[str]:
        """
        Get the name of the AI Act knowledge base store.
        
        Returns:
            Store name if available, None otherwise
        """
        raise NotImplementedError("Subclasses must implement get_store_name method")
