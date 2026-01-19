"""
Presentation View for AI Act Chat API
Handles HTTP requests for AI Act chat functionality
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from ...application.use_cases.ai_act_chat_use_case import AIActChatUseCase
from ...domain.services.ai_act_service import AIActService


@csrf_exempt  # TODO: Add proper CSRF protection in production
@require_http_methods(["POST"])
def ai_act_chat_api(request):
    """
    API endpoint for AI Act chat queries.
    
    Expected JSON payload:
    {
        "message": "What are prohibited AI practices?",
        "agent_id": "agent_ai_act",
        "chat_type": "Company"
    }
    
    Returns:
        JSON response with:
        {
            "id": <chat_history_id>,
            "data": {
                "message": "<AI response>",
                "references": [...],
                "sources": [...]
            }
        }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Parse request body
        body = json.loads(request.body)
        message = body.get('message', '').strip()
        agent_id = body.get('agent_id')
        chat_type = body.get('chat_type', 'Company')
        chat_history_id = body.get('chat_history_id')  # Optional: to continue existing conversation
        
        logger.info(f"Received chat request: message='{message[:50]}...', agent_id={agent_id}, chat_type={chat_type}, chat_history_id={chat_history_id}")
        
        if not message:
            return JsonResponse({
                'error': 'Message is required'
            }, status=400)
        
        # Get AI Act service from dependency injection
        # Use singleton pattern to avoid recreating service on each request
        from ...infrastructure.services.gemini_ai_act_service import (
            GeminiAIActService,
            get_ai_act_service
        )
        
        logger.info("Getting AI Act service instance...")
        try:
            ai_act_service: AIActService = get_ai_act_service()
            logger.info(f"AI Act service ready with model: {ai_act_service.model_name}")
        except ValueError as e:
            logger.error(f"AI Act service configuration error: {str(e)}")
            return JsonResponse({
                'error': f'AI Act service not configured: {str(e)}'
            }, status=503)
        except ImportError as e:
            logger.error(f"AI Act service import error: {str(e)}")
            return JsonResponse({
                'error': f'AI Act service dependencies not installed: {str(e)}'
            }, status=503)
        
        # Create use case
        logger.info("Creating use case and executing query...")
        use_case = AIActChatUseCase(ai_act_service)
        
        # Execute use case
        result = use_case.execute(message, agent_id, chat_type, chat_history_id)
        
        logger.info(f"Query completed successfully. Response length: {len(result.get('data', {}).get('message', ''))}")
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except ValueError as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)
    except Exception as e:
        # Log error in production
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in AI Act chat API: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'error': 'An error occurred processing your request'
        }, status=500)
