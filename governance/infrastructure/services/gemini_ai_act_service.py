"""
Infrastructure Service for Gemini AI Act Integration
Handles actual API calls to Gemini for AI Act queries using Long Context approach.

Strategy: Injects the full EU AI Act text into Gemini's system instruction,
leveraging the 1M token context window for native reasoning over the entire regulation.

Features:
- Long Context (1M tokens): Full EU AI Act injected into system instruction
- Gemini 3 Thinking: Deep reasoning with ThinkingLevel.HIGH for legal analysis
- Function Calling: Tool use for risk classification, article lookup, skill recommendation
- Streaming: Server-Sent Events for real-time chat responses
"""
import os
import json
import uuid
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Generator, Tuple

try:
    from google import genai
    from google.genai import types, errors
except ImportError:
    genai = None
    types = None
    errors = None

from django.conf import settings
from ...domain.services.ai_act_service import (
    AIActService,
    AIActQueryRequest,
    AIActQueryResponse
)

logger = logging.getLogger(__name__)


# ============================================================================
# Function Calling: Tool Declarations for Gemini 3
# These tools enable the AI to perform real governance operations during chat
# ============================================================================

def _build_function_declarations():
    """Build function declarations for Gemini 3 function calling.

    Returns:
        list: A list of FunctionDeclaration objects for risk classification,
              compliance skills lookup, and compliance scanning tools.
              Returns an empty list if the google-genai types module is unavailable.
    """
    if types is None:
        return []

    return [
        types.FunctionDeclaration(
            name="classify_ai_system_risk",
            description=(
                "Classify an AI system into EU AI Act risk tiers "
                "(Unacceptable, High-Risk, Limited Risk, Minimal Risk). "
                "Use this tool when the user describes an AI system and wants to know its risk level."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "system_description": types.Schema(
                        type=types.Type.STRING,
                        description="Description of the AI system to classify"
                    ),
                },
                required=["system_description"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_compliance_skills",
            description=(
                "Get recommended compliance skills/tools for a specific EU AI Act risk category. "
                "Returns a list of governance skills with descriptions. "
                "Use this when the user asks what they need to do for compliance."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "risk_category": types.Schema(
                        type=types.Type.STRING,
                        description="Risk category: 'HIGH-RISK', 'LIMITED-RISK', 'MINIMAL-RISK', or 'UNACCEPTABLE'",
                        enum=["HIGH-RISK", "LIMITED-RISK", "MINIMAL-RISK", "UNACCEPTABLE"],
                    ),
                    "system_description": types.Schema(
                        type=types.Type.STRING,
                        description="Optional: description of the AI system for more targeted recommendations"
                    ),
                },
                required=["risk_category"],
            ),
        ),
        types.FunctionDeclaration(
            name="run_compliance_scan",
            description=(
                "Run a quick compliance scan on an AI system description. "
                "Returns compliance score, identified risks, and action items. "
                "Use this when the user wants a compliance assessment."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "system_name": types.Schema(
                        type=types.Type.STRING,
                        description="Name of the AI system"
                    ),
                    "system_description": types.Schema(
                        type=types.Type.STRING,
                        description="Detailed description of the AI system"
                    ),
                    "domain": types.Schema(
                        type=types.Type.STRING,
                        description="Domain/industry of the AI system (e.g., healthcare, finance, education)"
                    ),
                },
                required=["system_name", "system_description"],
            ),
        ),
    ]


def _execute_function_call(function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a function call from Gemini and return results.

    Args:
        function_name: Name of the function to execute.
        function_args: Dictionary of arguments to pass to the function.

    Returns:
        Dictionary containing the function execution results, or an error dict
        if the function is unknown or execution fails.
    """
    logger.info(f"Executing function call: {function_name} with args: {list(function_args.keys())}")

    if function_name == "classify_ai_system_risk":
        return _tool_classify_risk(function_args.get("system_description", ""))

    elif function_name == "get_compliance_skills":
        return _tool_get_skills(
            function_args.get("risk_category", "HIGH-RISK"),
            function_args.get("system_description", "")
        )

    elif function_name == "run_compliance_scan":
        return _tool_run_scan(
            function_args.get("system_name", "AI System"),
            function_args.get("system_description", ""),
            function_args.get("domain", "general")
        )

    return {"error": f"Unknown function: {function_name}"}


def _tool_classify_risk(system_description: str) -> Dict[str, Any]:
    """Tool: Classify AI system risk using GovernanceAgentService."""
    try:
        from .governance_agent_service import get_governance_agent_service
        agent = get_governance_agent_service()
        assessment = agent.assess_ai_system(system_description)
        risk = assessment.get("risk_classification", {})
        return {
            "risk_category": risk.get("category", "Unknown"),
            "confidence": risk.get("confidence", "N/A"),
            "reasoning": risk.get("reasoning", ""),
            "applicable_articles": [
                r.get("name", "") for r in assessment.get("applicable_regulations", [])
            ],
            "total_recommended_skills": len(assessment.get("recommended_skills", [])),
        }
    except Exception as e:
        logger.error(f"Risk classification tool error: {e}")
        return {"error": str(e), "risk_category": "Unable to classify"}


def _tool_get_skills(risk_category: str, system_description: str = "") -> Dict[str, Any]:
    """Tool: Get compliance skills from GovernanceAgentService."""
    try:
        from .governance_agent_service import get_governance_agent_service
        agent = get_governance_agent_service()

        if system_description:
            assessment = agent.assess_ai_system(system_description)
            skills = assessment.get("recommended_skills", [])
        else:
            # Get all skills for the risk category
            # agent.skills is a Dict[str, SkillMetadata], so we need to get values() and convert to list for slicing
            all_skills = list(agent.skills.values())
            skills = [
                {"skill": s.name, "reason": s.description}
                for s in all_skills[:20]
            ]

        return {
            "risk_category": risk_category,
            "total_skills_available": len(agent.skills),
            "recommended_skills": skills[:15],
        }
    except Exception as e:
        logger.error(f"Get skills tool error: {e}")
        return {"error": str(e), "recommended_skills": []}


def _tool_run_scan(name: str, description: str, domain: str = "general") -> Dict[str, Any]:
    """Tool: Run quick compliance scan using GovernanceAgentService."""
    try:
        from .governance_agent_service import get_governance_agent_service
        agent = get_governance_agent_service()
        assessment = agent.assess_ai_system(description)
        risk = assessment.get("risk_classification", {})
        regulations = assessment.get("applicable_regulations", [])
        skills = assessment.get("recommended_skills", [])

        return {
            "system_name": name,
            "risk_level": risk.get("category", "Unknown"),
            "confidence": risk.get("confidence", "N/A"),
            "applicable_regulations": [r.get("name", "") for r in regulations],
            "recommended_skills_count": len(skills),
            "top_skills": [s.get("skill", "") for s in skills[:5]],
            "action_items": [
                f"Implement {s.get('skill', 'Unknown')}: {s.get('reason', '')}"
                for s in skills[:3]
            ],
        }
    except Exception as e:
        logger.error(f"Compliance scan tool error: {e}")
        return {"error": str(e)}

# Singleton instance for service (to avoid recreating on each request)
_service_instance: Optional['GeminiAIActService'] = None


def get_ai_act_service() -> 'GeminiAIActService':
    """Get or create singleton instance of GeminiAIActService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = GeminiAIActService()
    return _service_instance


class GeminiAIActService(AIActService):
    """
    Infrastructure implementation of AIActService using Gemini API.

    Uses Long Context approach: injects the full EU AI Act regulation text
    into the system instruction, leveraging Gemini's 1M token context window
    for native reasoning over the entire document set.
    """

    def __init__(self):
        """Initialize the Gemini AI Act service.

        Raises:
            ValueError: If GEMINI_API_KEY is not configured.
            ImportError: If google-genai package is not installed.
        """
        # Try settings first, then fallback to environment variable (like setup script)
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured in settings or environment variables")

        if genai is None:
            raise ImportError("google-genai package not installed. Run: pip install google-genai")

        # Initialize client (timeout is not supported in Client constructor)
        self.client = genai.Client(api_key=self.api_key)
        # Default to gemini-3-pro-preview (aligned with ai_act_cli.py for best accuracy)
        # Alternative options: gemini-2.5-flash (faster/cheaper), gemini-3-flash-preview
        self.model_name = getattr(settings, 'AI_ACT_MODEL_NAME', 'gemini-3-pro-preview')
        self.api_timeout = getattr(settings, 'AI_ACT_API_TIMEOUT', 30)
        self.articles_dir = getattr(settings, 'AI_ACT_ARTICLES_DIR', None)

        # Full text content for long context injection
        self._full_text = None

        # Function calling: build tool declarations
        self._function_tools = _build_function_declarations()

        # Chat session storage: {chat_history_id: chat_session}
        # Using in-memory storage for now (could be moved to database/cache later)
        self._chat_sessions: Dict[str, Any] = {}
        # Chat history storage: {chat_history_id: [messages]}
        # Track conversation history manually
        self._chat_histories: Dict[str, List[Dict[str, Any]]] = {}

    def _load_full_text(self) -> str:
        """Load the complete EU AI Act full text for long context injection.

        Returns:
            The full regulation text as a string, or an empty string if the
            file is not configured or cannot be read.
        """
        if self._full_text is not None:
            return self._full_text

        if not self.articles_dir:
            self._full_text = ""
            return ""

        full_text_path = self.articles_dir / "EU_AI_Act_Full_Text.txt"
        if not full_text_path.exists():
            self._full_text = ""
            return ""

        try:
            self._full_text = full_text_path.read_text(encoding='utf-8')
            return self._full_text
        except Exception:
            self._full_text = ""
            return ""

    # ========================================================================
    # Private helpers: extracted to eliminate duplication between query()
    # and query_stream()
    # ========================================================================

    def _build_system_instruction(self, full_text: str) -> str:
        """Build the system instruction for the Gemini chat session.

        Constructs the system prompt that configures Gemini as an EU AI Act
        legal assistant. When the full regulation text is available it is
        injected as context (Long Context approach); otherwise a fallback
        prompt using the model's built-in knowledge is returned.

        Args:
            full_text: The full EU AI Act regulation text. Pass an empty
                       string to use the fallback prompt.

        Returns:
            The complete system instruction string.
        """
        common_header = (
            "You are an expert legal assistant on the EU AI Act (Regulation 2024/1689) and GDPR.\n\n"
            "IMPORTANT - EU AI Act Article 50 Compliance:\n"
            "You are an AI assistant. Users have been informed they are interacting with an AI system.\n"
            "Your responses must be helpful but include appropriate disclaimers about verification and legal counsel.\n\n"
        )

        if full_text:
            context_block = (
                "CONTEXT DOCUMENT (Full Text of the Regulation):\n"
                "================================================================================\n"
                f"{full_text}\n"
                "================================================================================\n\n"
                "Your goal is to provide accurate, comprehensive answers based ONLY on the provided context document above.\n\n"
            )
            guidelines = (
                "Guidelines:\n"
                "1. ALWAYS cite specific Articles and paragraphs (e.g., \"Article 5(1)\").\n"
                "2. If the answer is not in the document, state that clearly.\n"
                "3. Be precise with legal definitions.\n"
                "4. Use structured formatting (bullet points, bold text).\n"
                "5. Remind users when appropriate that AI-generated responses should be verified with legal counsel.\n"
                "6. For compliance-critical questions, emphasize the importance of professional legal advice."
            )
            return common_header + context_block + guidelines
        else:
            fallback_block = (
                "Your goal is to provide accurate, comprehensive answers about the EU AI Act and GDPR.\n\n"
                "Note: The full regulation text is not currently loaded. Answers are based on your training knowledge.\n"
                "Please advise users to verify critical information against the official regulation text.\n\n"
            )
            guidelines = (
                "Guidelines:\n"
                "1. ALWAYS cite specific Articles and paragraphs (e.g., \"Article 5(1)\").\n"
                "2. If you are unsure about specific details, state that clearly.\n"
                "3. Be precise with legal definitions.\n"
                "4. Use structured formatting (bullet points, bold text).\n"
                "5. Remind users when appropriate that AI-generated responses should be verified with legal counsel.\n"
                "6. For compliance-critical questions, emphasize the importance of professional legal advice."
            )
            return common_header + fallback_block + guidelines

    def _create_chat_session(self, chat_history_id: str) -> Tuple[str, Any]:
        """Create a new Gemini chat session with full configuration.

        Handles the complete session bootstrap: loads the regulation text,
        builds the system instruction via ``_build_system_instruction``,
        configures ThinkingLevel.HIGH, tools and temperature, and creates
        the chat via the Gemini client.

        If the provided ``chat_history_id`` already maps to a live session it
        is returned directly. Otherwise a new session is created (and a fresh
        UUID is generated when the supplied id is ``None`` or not found).

        Args:
            chat_history_id: An existing chat history identifier, or ``None``
                             to create a brand-new session.

        Returns:
            A tuple of ``(chat_history_id, chat_session)`` where
            ``chat_history_id`` is guaranteed to be non-empty.

        Raises:
            Exception: Propagated from the Gemini client if session creation fails.
        """
        # Return existing session when available
        if chat_history_id and chat_history_id in self._chat_sessions:
            logger.info(f"Continuing existing chat session: {chat_history_id}")
            return chat_history_id, self._chat_sessions[chat_history_id]

        # Create a new session
        if chat_history_id:
            logger.warning(f"Chat history ID {chat_history_id} not found, creating new session")
        chat_history_id = str(uuid.uuid4())
        logger.info(f"Creating new chat session: {chat_history_id}")

        # Long Context approach: inject full regulation text into system instruction
        full_text = self._load_full_text()
        if full_text:
            logger.info(f"Using Long Context injection ({len(full_text)} characters)...")
        else:
            logger.warning("Full text not available, using model's built-in knowledge...")

        system_instruction = self._build_system_instruction(full_text)

        # Build tools config for function calling
        tools_config = []
        if self._function_tools:
            tools_config = [types.Tool(function_declarations=self._function_tools)]

        # GenerateContentConfig with:
        # - temperature=0.3 (aligned with CLI for precise legal reasoning)
        # - Gemini 3 Thinking: Deep reasoning with ThinkingLevel.HIGH
        # - Function Calling: Tools for risk classification, skill lookup, compliance scan
        generate_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.HIGH
            ),
            tools=tools_config if tools_config else None,
        )

        chat_session = self.client.chats.create(
            model=self.model_name,
            config=generate_config,
            history=[]
        )
        self._chat_sessions[chat_history_id] = chat_session
        logger.info(f"Chat session created with tools: {[t.name for t in self._function_tools]}")

        return chat_history_id, chat_session

    def _handle_function_calling_loop(
        self,
        chat_session: Any,
        response: Any,
        max_rounds: int = 5
    ) -> Tuple[Any, int]:
        """Handle the Gemini function calling loop until a final text response.

        Iteratively extracts function calls from the model response, executes
        them via ``_execute_function_call``, feeds the results back into the
        chat session, and repeats until the model returns a text-only response
        or ``max_rounds`` is reached.

        Args:
            chat_session: The active Gemini chat session.
            response: The initial model response (which may contain function
                      call requests).
            max_rounds: Maximum number of tool-call round-trips to prevent
                        infinite loops. Defaults to 5.

        Returns:
            A tuple of ``(final_response, tool_rounds)`` where
            ``final_response`` is the Gemini response object containing the
            final text answer and ``tool_rounds`` is the number of
            function-calling iterations that were executed.
        """
        tool_round = 0
        while tool_round < max_rounds:
            function_calls = self._extract_function_calls(response)
            if not function_calls:
                break  # No function calls, we have the final response

            tool_round += 1
            logger.info(f"Function call round {tool_round}: {[fc['name'] for fc in function_calls]}")

            # Execute each function call and collect results
            function_responses = []
            for fc in function_calls:
                result = _execute_function_call(fc['name'], fc['args'])
                function_responses.append(
                    types.Part.from_function_response(
                        name=fc['name'],
                        response=result
                    )
                )
                logger.info(f"Tool '{fc['name']}' executed successfully")

            # Send function results back to Gemini for the next round
            response = chat_session.send_message(function_responses)

        if tool_round > 0:
            logger.info(f"Completed {tool_round} function call round(s)")

        return response, tool_round

    def _cleanup_session(self, chat_history_id: str) -> None:
        """Remove a chat session and its history from in-memory storage.

        Args:
            chat_history_id: The session identifier to clean up.
        """
        if chat_history_id in self._chat_sessions:
            del self._chat_sessions[chat_history_id]
        if chat_history_id in self._chat_histories:
            del self._chat_histories[chat_history_id]

    def _track_message(self, chat_history_id: str, role: str, content: str) -> None:
        """Append a message to the tracked conversation history.

        Args:
            chat_history_id: The session identifier.
            role: Message role, typically ``'user'`` or ``'assistant'``.
            content: The message text.
        """
        if chat_history_id not in self._chat_histories:
            self._chat_histories[chat_history_id] = []
        self._chat_histories[chat_history_id].append({
            'role': role,
            'content': content
        })

    # ========================================================================
    # Public API
    # ========================================================================

    def query(self, request: AIActQueryRequest) -> AIActQueryResponse:
        """Query the AI Act using Gemini Chat API with Long Context approach.

        Injects the full EU AI Act text into the system instruction to leverage
        Gemini's 1M token context window for native reasoning.

        Args:
            request: The query request (may include chat_history_id to continue
                     a conversation).

        Returns:
            AIActQueryResponse with answer, references, and chat_history_id.

        Raises:
            ValueError: If the request question is empty or blank.
        """
        # Validate input
        if not request.question or not request.question.strip():
            raise ValueError("Question must not be empty")

        logger.info(f"Starting query with model: {self.model_name}")
        logger.info(f"Question: {request.question[:100]}...")
        logger.info(f"Chat history ID: {request.chat_history_id}")

        # Get or create chat session
        try:
            chat_history_id, chat_session = self._create_chat_session(
                request.chat_history_id
            )
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            raise

        # Send message to chat session (with function calling loop)
        try:
            logger.info(f"Sending message to chat session: {chat_history_id}")

            # Track user message in chat history
            self._track_message(chat_history_id, 'user', request.question)

            response = chat_session.send_message(request.question)
            logger.info("Message sent successfully")

            # Function Calling Loop: handle tool calls from Gemini
            response, tool_round = self._handle_function_calling_loop(
                chat_session, response
            )

            # Track assistant response in chat history
            assistant_message = response.text if response.text else "No response generated."
            self._track_message(chat_history_id, 'assistant', assistant_message)

            return self._format_response(response, chat_history_id, chat_session)

        except Exception as e:
            logger.error(f"Error sending message to chat session: {e}")
            self._cleanup_session(chat_history_id)
            raise

    def _extract_function_calls(self, response) -> List[Dict[str, Any]]:
        """Extract function calls from a Gemini response.

        Args:
            response: A Gemini API response object.

        Returns:
            A list of dicts, each with ``'name'`` (str) and ``'args'`` (dict)
            keys. Returns an empty list if no function calls are present.
        """
        function_calls = []
        try:
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                fc = part.function_call
                                function_calls.append({
                                    'name': fc.name,
                                    'args': dict(fc.args) if fc.args else {}
                                })
        except Exception as e:
            logger.warning(f"Error extracting function calls: {e}")
        return function_calls

    def query_stream(self, request: AIActQueryRequest) -> Generator[str, None, None]:
        """Stream a query response using Server-Sent Events format.

        Yields chunks of text as they arrive from Gemini's streaming API.
        Handles function calls inline (executes tools, then streams the final
        response).

        Args:
            request: The query request.

        Yields:
            SSE-formatted strings: ``'data: {"chunk": "...", "done": false}\\n\\n'``

        Raises:
            ValueError: If the request question is empty or blank (yielded as
                        an SSE error event rather than raised).
        """
        # Validate input
        if not request.question or not request.question.strip():
            yield f'data: {json.dumps({"error": "Question must not be empty", "done": True})}\n\n'
            return

        # Get or create chat session
        try:
            chat_history_id, chat_session = self._create_chat_session(
                request.chat_history_id
            )
        except Exception as e:
            yield f'data: {json.dumps({"error": str(e), "done": True})}\n\n'
            return

        # Track user message
        self._track_message(chat_history_id, 'user', request.question)

        # Send initial chat_history_id
        yield f'data: {json.dumps({"chat_history_id": chat_history_id, "chunk": "", "done": False})}\n\n'

        try:
            # First, handle any function calls (non-streaming)
            response = chat_session.send_message(request.question)

            max_tool_rounds = 5
            tool_round = 0
            while tool_round < max_tool_rounds:
                function_calls = self._extract_function_calls(response)
                if not function_calls:
                    break
                tool_round += 1
                # Notify client that tools are being used
                tool_names = [fc['name'] for fc in function_calls]
                yield f'data: {json.dumps({"chunk": "", "tool_use": tool_names, "done": False})}\n\n'

                function_responses = []
                for fc in function_calls:
                    result = _execute_function_call(fc['name'], fc['args'])
                    function_responses.append(
                        types.Part.from_function_response(
                            name=fc['name'],
                            response=result
                        )
                    )
                response = chat_session.send_message(function_responses)

            # Now stream the final text response
            # Since we already have the response from the function calling loop,
            # stream it chunk by chunk
            full_text_response = response.text if response.text else "No response generated."

            # Stream in chunks for smooth UI rendering
            chunk_size = 50  # characters per chunk
            for i in range(0, len(full_text_response), chunk_size):
                chunk = full_text_response[i:i + chunk_size]
                yield f'data: {json.dumps({"chunk": chunk, "done": False})}\n\n'

            # Track in history
            self._track_message(chat_history_id, 'assistant', full_text_response)

            # Final message with done flag
            yield f'data: {json.dumps({"chunk": "", "done": True, "chat_history_id": chat_history_id})}\n\n'

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f'data: {json.dumps({"error": str(e), "done": True})}\n\n'
            self._cleanup_session(chat_history_id)

    def _format_response(self, response,
                        chat_history_id: Optional[str] = None,
                        chat_session: Optional[Any] = None) -> AIActQueryResponse:
        """Format the Gemini response into an AIActQueryResponse.

        Extracts the text answer and any grounding metadata (citations) from
        the raw Gemini response and builds the domain response object.

        Args:
            response: The raw Gemini API response object.
            chat_history_id: Optional session identifier to include in the
                             response.
            chat_session: Optional chat session reference (unused but kept
                          for potential future use).

        Returns:
            An AIActQueryResponse populated with the answer text, references,
            sources, and conversation metadata.
        """
        message = response.text if response.text else "No response generated."

        references: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = []

        # Extract citations from grounding metadata (if available)
        if response.candidates and response.candidates[0].grounding_metadata:
            grounding = response.candidates[0].grounding_metadata
            if grounding.grounding_chunks:
                for chunk in grounding.grounding_chunks[:5]:
                    if hasattr(chunk, 'retrieved_context'):
                        ctx = chunk.retrieved_context
                        source = {
                            'title': getattr(ctx, 'title', 'Document'),
                            'text': getattr(ctx, 'text', '')[:200] + "..." if len(getattr(ctx, 'text', '')) > 200 else getattr(ctx, 'text', '')
                        }
                        sources.append(source)
                        references.append(source)

        # Get chat history from tracked history
        chat_history: Optional[List[Dict[str, Any]]] = None
        if chat_history_id and chat_history_id in self._chat_histories:
            chat_history = self._chat_histories[chat_history_id]

        return AIActQueryResponse(
            message=message,
            references=references,
            sources=sources,
            chat_history_id=chat_history_id,
            chat_history=chat_history if chat_history else None
        )
