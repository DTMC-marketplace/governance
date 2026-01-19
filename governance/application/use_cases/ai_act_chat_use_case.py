"""
Application Use Case for AI Act Chat
Handles the business logic for AI Act chat interactions
"""
from typing import Dict, Any, Optional
from ...domain.services.ai_act_service import (
    AIActService,
    AIActQueryRequest,
    AIActQueryResponse
)


class AIActChatUseCase:
    """
    Use case for handling AI Act chat queries.
    Coordinates between domain services and returns application-level DTOs.
    """
    
    def __init__(self, ai_act_service: AIActService):
        """
        Initialize the use case with required services.
        
        Args:
            ai_act_service: The AI Act service for querying regulations
        """
        self.ai_act_service = ai_act_service
    
    def execute(self, message: str, agent_id: Optional[str] = None, 
                chat_type: Optional[str] = None, chat_history_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an AI Act chat query.
        
        Args:
            message: The user's question
            agent_id: Optional agent identifier
            chat_type: Optional chat type (e.g., 'Company', 'Personal')
            chat_history_id: Optional chat history ID to continue existing conversation
            
        Returns:
            Dictionary containing:
            - message: The AI response
            - references: List of reference sources
            - id: Chat history ID for this conversation
            - data: Full response data
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        # Create query request
        request = AIActQueryRequest(
            question=message.strip(),
            agent_id=agent_id,
            chat_type=chat_type,
            chat_history_id=chat_history_id
        )
        
        # Execute query
        response = self.ai_act_service.query(request)
        
        # Format response for presentation layer
        return {
            'id': response.chat_history_id,  # Chat history ID for continuing conversation
            'data': {
                'message': response.message,
                'references': response.references or [],
                'sources': response.sources or [],
                'chat_history': response.chat_history or []  # Include chat history
            }
        }
