"""
Presentation View for AI Act Chat API
Handles HTTP requests for AI Act chat functionality.

Supports both standard JSON responses and Server-Sent Events (SSE) streaming.
"""
import json
import logging
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from ...application.use_cases.ai_act_chat_use_case import AIActChatUseCase
from ...domain.services.ai_act_service import AIActService, AIActQueryRequest

logger = logging.getLogger(__name__)


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
        logger.error(f"Error in AI Act chat API: {str(e)}", exc_info=True)

        return JsonResponse({
            'error': 'An error occurred processing your request'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ai_act_chat_stream_api(request):
    """
    Streaming API endpoint for AI Act chat using Server-Sent Events (SSE).

    Streams response chunks as they arrive from Gemini 3.
    Supports function calling (tool use notifications sent inline).

    Expected JSON payload (same as ai_act_chat_api):
    {
        "message": "What are prohibited AI practices?",
        "agent_id": "agent_ai_act",
        "chat_type": "Company",
        "chat_history_id": "optional-uuid"
    }

    Returns:
        StreamingHttpResponse with SSE events:
        data: {"chat_history_id": "uuid", "chunk": "", "done": false}
        data: {"chunk": "Some text...", "done": false}
        data: {"chunk": "", "tool_use": ["classify_ai_system_risk"], "done": false}
        data: {"chunk": "", "done": true, "chat_history_id": "uuid"}
    """
    try:
        body = json.loads(request.body)
        message = body.get('message', '').strip()
        agent_id = body.get('agent_id')
        chat_type = body.get('chat_type', 'Company')
        chat_history_id = body.get('chat_history_id')

        logger.info(f"Streaming chat request: message='{message[:50]}...', agent_id={agent_id}")

        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        from ...infrastructure.services.gemini_ai_act_service import get_ai_act_service

        try:
            ai_act_service = get_ai_act_service()
        except (ValueError, ImportError) as e:
            logger.error(f"AI Act service error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=503)

        # Build request
        query_request = AIActQueryRequest(
            question=message,
            agent_id=agent_id,
            chat_type=chat_type,
            chat_history_id=chat_history_id
        )

        # Return SSE streaming response
        def event_stream():
            try:
                for chunk in ai_act_service.query_stream(query_request):
                    yield chunk
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f'data: {json.dumps({"error": str(e), "done": True})}\n\n'

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
        return response

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        logger.error(f"Error in streaming chat API: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'An error occurred'}, status=500)
