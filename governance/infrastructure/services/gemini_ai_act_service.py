"""
Infrastructure Service for Gemini AI Act Integration
Handles actual API calls to Gemini for AI Act queries
"""
import os
import re
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from heapq import nlargest

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
    Handles File Search Store queries and fallback to manual context.
    """
    
    # Stopwords for manual context matching
    STOPWORDS = {
        "what", "are", "the", "and", "for", "with", "that", "this", "from", "into",
        "your", "about", "which", "shall", "will", "does", "can", "may", "must",
        "should", "would", "could", "their", "there", "here", "have", "been",
        "such", "upon", "per", "other", "than", "while", "within", "who", "whom",
        "whose", "why", "how", "when", "where", "any", "each", "some", "many",
    }
    
    MAX_CONTEXT_ARTICLES = 5
    CONTEXT_SNIPPET_CHARS = 4000
    
    def __init__(self):
        """Initialize the Gemini AI Act service."""
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
        self.use_file_search = getattr(settings, 'AI_ACT_USE_FILE_SEARCH', False)
        self.api_timeout = getattr(settings, 'AI_ACT_API_TIMEOUT', 30)
        self.articles_dir = getattr(settings, 'AI_ACT_ARTICLES_DIR', None)
        self.store_name = getattr(settings, 'AI_ACT_STORE_NAME', None)
        
        # Load full text sections for fallback
        self._full_text_sections = None
        self._full_text = None  # Full text content for long context injection (like CLI)
        self._gdpr_sections = None
        
        # Chat session storage: {chat_history_id: chat_session}
        # Using in-memory storage for now (could be moved to database/cache later)
        self._chat_sessions: Dict[str, Any] = {}
        # Chat history storage: {chat_history_id: [messages]}
        # Track conversation history manually
        self._chat_histories: Dict[str, List[Dict[str, Any]]] = {}
        # Cache for manual context to avoid rebuilding
        self._context_cache: Dict[str, List[Dict[str, str]]] = {}
    
    def get_store_name(self) -> Optional[str]:
        """Get the store name from settings or file."""
        if self.store_name:
            return self.store_name
        
        # Try to load from store_info.txt (new location)
        store_info_path = getattr(settings, 'AI_ACT_STORE_INFO_PATH', None)
        if store_info_path and Path(store_info_path).exists():
            try:
                with open(store_info_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('store_name='):
                            return line.split('=', 1)[1].strip()
            except Exception:
                pass
        
        return None
    
    def _load_full_text_sections(self) -> List[str]:
        """Load full text sections from file."""
        if self._full_text_sections is not None:
            return self._full_text_sections
        
        if not self.articles_dir:
            self._full_text_sections = []
            return []
        
        full_text_path = self.articles_dir / "EU_AI_Act_Full_Text.txt"
        if not full_text_path.exists():
            self._full_text_sections = []
            return []
        
        try:
            raw_text = full_text_path.read_text(encoding='utf-8')
            paragraphs = [segment.strip() for segment in raw_text.split("\n\n") if segment.strip()]
            self._full_text_sections = paragraphs
            return paragraphs
        except Exception:
            self._full_text_sections = []
            return []
    
    def _load_full_text(self) -> str:
        """Load the complete EU AI Act full text for long context injection."""
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

    def _load_gdpr_sections(self) -> List[Dict[str, str]]:
        """Load GDPR article files."""
        if self._gdpr_sections is not None:
            return self._gdpr_sections
        
        if not self.articles_dir:
            self._gdpr_sections = []
            return []
        
        sections: List[Dict[str, str]] = []
        for path in sorted(self.articles_dir.glob("GDPR_Article_*.txt")):
            try:
                text = path.read_text(encoding='utf-8').strip()
                if not text:
                    continue
                first_line = text.splitlines()[0].strip()
                title = first_line if first_line else path.stem.replace('_', ' ')
                sections.append({'title': title, 'text': text})
            except Exception:
                continue
        
        self._gdpr_sections = sections
        return sections
    
    def _build_manual_context(self, question: str) -> List[Dict[str, str]]:
        """Build manual context from local files as fallback."""
        # Check cache first (simple cache based on question hash)
        question_key = question.lower().strip()[:100]  # Use first 100 chars as key
        if question_key in self._context_cache:
            return self._context_cache[question_key]
        
        tokens: List[Tuple[str, int]] = []
        question_lower = question.lower()
        
        for tok in re.findall(r"\w+", question_lower):
            if tok in self.STOPWORDS:
                continue
            if len(tok) <= 2 and tok != "ai":
                continue
            weight = 1
            if tok in {"prohibited", "practices"}:
                weight = 5
            elif tok == "ai":
                weight = 2
            elif tok == "gdpr":
                weight = 4
            tokens.append((tok, weight))
        
        if not tokens:
            return []
        
        scored_sections: List[Tuple[int, Dict[str, str]]] = []
        scored_sections.extend(self._score_ai_act_sections(tokens))
        scored_sections.extend(self._score_gdpr_sections(tokens, question_lower))
        
        if not scored_sections:
            result = []
        else:
            top_matches = nlargest(self.MAX_CONTEXT_ARTICLES, scored_sections, key=lambda item: item[0])
            result = [match[1] for match in top_matches]
        
        # Cache result
        self._context_cache[question_key] = result
        # Limit cache size to prevent memory issues
        if len(self._context_cache) > 100:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self._context_cache))
            del self._context_cache[oldest_key]
        
        return result
    
    def _score_ai_act_sections(self, tokens: List[Tuple[str, int]]) -> List[Tuple[int, Dict[str, str]]]:
        """Score AI Act sections for relevance."""
        full_text_sections = self._load_full_text_sections()
        if not full_text_sections:
            return []
        
        scored: List[Tuple[int, Dict[str, str]]] = []
        seen_indices = set()
        
        for idx, section in enumerate(full_text_sections):
            section_lower = section.lower()
            score = sum(section_lower.count(token) * weight for token, weight in tokens)
            
            if 'prohibited ai practices' in section_lower:
                score += 50
            if 'article 5' in section_lower:
                score += 25
            if score <= 0:
                continue
            
            if 'prohibited ai practices' in section_lower:
                if idx in seen_indices:
                    continue
                end_idx = min(idx + 20, len(full_text_sections))
                combined_sections = "\n".join(full_text_sections[idx:end_idx])
                snippet = combined_sections.strip()
                seen_indices.update(range(idx, end_idx))
                title = "AI Act Article 5"
            else:
                if idx in seen_indices:
                    continue
                snippet = section.strip()
                seen_indices.add(idx)
                title_match = re.search(r"Article\s+\d+[a-zA-Z]*", section)
                title = title_match.group(0) if title_match else "EU AI Act Context"
            
            if len(snippet) > self.CONTEXT_SNIPPET_CHARS:
                snippet = snippet[:self.CONTEXT_SNIPPET_CHARS] + "..."
            scored.append((score, {'title': title, 'text': snippet}))
        
        return scored
    
    def _score_gdpr_sections(self, tokens: List[Tuple[str, int]], question_lower: str) -> List[Tuple[int, Dict[str, str]]]:
        """Score GDPR sections for relevance."""
        gdpr_sections = self._load_gdpr_sections()
        if not gdpr_sections:
            return []
        
        gdpr_focus_terms = ['gdpr', 'general data protection regulation', 'personal data']
        gdpr_focus = any(term in question_lower for term in gdpr_focus_terms)
        scored: List[Tuple[int, Dict[str, str]]] = []
        
        for section in gdpr_sections:
            text_lower = section['text'].lower()
            score = sum(text_lower.count(token) * weight for token, weight in tokens)
            score += text_lower.count('gdpr')
            if gdpr_focus:
                score += 15
            if 'personal data' in question_lower and 'personal data' in text_lower:
                score += 5
            
            if score <= 0:
                continue
            
            snippet = section['text']
            if len(snippet) > self.CONTEXT_SNIPPET_CHARS:
                snippet = snippet[:self.CONTEXT_SNIPPET_CHARS] + "..."
            scored.append((score, {'title': section['title'], 'text': snippet}))
        
        return scored
    
    def query(self, request: AIActQueryRequest) -> AIActQueryResponse:
        """
        Query the AI Act using Gemini Chat API to maintain conversation history.
        
        Args:
            request: The query request (may include chat_history_id to continue conversation)
            
        Returns:
            AIActQueryResponse with answer, references, and chat_history_id
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting query with model: {self.model_name}")
        logger.info(f"Question: {request.question[:100]}...")
        logger.info(f"Chat history ID: {request.chat_history_id}")
        
        # Get or create chat session
        chat_history_id = request.chat_history_id
        chat_session = None
        uses_file_search = False  # Track if session uses File Search
        context_sections = None  # Cache for context sections to avoid rebuilding
        
        if chat_history_id and chat_history_id in self._chat_sessions:
            # Continue existing conversation
            logger.info(f"Continuing existing chat session: {chat_history_id}")
            chat_session = self._chat_sessions[chat_history_id]
            # For existing sessions, we don't know if they use File Search, so assume manual context for references
            uses_file_search = False
        else:
            # Create new chat session
            if chat_history_id:
                logger.warning(f"Chat history ID {chat_history_id} not found, creating new session")
            chat_history_id = str(uuid.uuid4())
            logger.info(f"Creating new chat session: {chat_history_id}")
            
            # Build system prompt (aligned with ai_act_cli.py)
            store_name = self.get_store_name() if self.use_file_search else None

            # Try File Search first if store is available
            tools = None
            system_instruction = None

            if store_name and self.use_file_search:
                try:
                    logger.info("Setting up File Search for chat session...")
                    tools = [
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[store_name]
                            )
                        )
                    ]
                    uses_file_search = True
                    system_instruction = (
                        "You are an expert legal assistant on the EU AI Act (Regulation 2024/1689) and GDPR.\n\n"
                        "IMPORTANT - EU AI Act Article 50 Compliance:\n"
                        "You are an AI assistant. Users have been informed they are interacting with an AI system.\n"
                        "Your responses must be helpful but include appropriate disclaimers about verification and legal counsel.\n\n"
                        "Use the File Search tool to find relevant information from the regulations.\n\n"
                        "Your goal is to provide accurate, comprehensive answers based on the regulations.\n\n"
                        "Guidelines:\n"
                        "1. ALWAYS cite specific Articles and paragraphs (e.g., \"Article 5(1)\").\n"
                        "2. If the answer is not in the document, state that clearly.\n"
                        "3. Be precise with legal definitions.\n"
                        "4. Use structured formatting (bullet points, bold text).\n"
                        "5. Remind users when appropriate that AI-generated responses should be verified with legal counsel.\n"
                        "6. For compliance-critical questions, emphasize the importance of professional legal advice."
                    )
                except Exception as e:
                    logger.warning(f"Failed to setup File Search: {e}, using manual context")
                    tools = None
                    uses_file_search = False

            # If no File Search, use full text injection (Long Context approach like CLI)
            if not tools:
                full_text = self._load_full_text()

                if full_text:
                    # Full text injection - same strategy as ai_act_cli.py
                    logger.info(f"Using full text injection ({len(full_text)} characters)...")
                    system_instruction = (
                        "You are an expert legal assistant on the EU AI Act (Regulation 2024/1689) and GDPR.\n\n"
                        "IMPORTANT - EU AI Act Article 50 Compliance:\n"
                        "You are an AI assistant. Users have been informed they are interacting with an AI system.\n"
                        "Your responses must be helpful but include appropriate disclaimers about verification and legal counsel.\n\n"
                        "CONTEXT DOCUMENT (Full Text of the Regulation):\n"
                        "================================================================================\n"
                        f"{full_text}\n"
                        "================================================================================\n\n"
                        "Your goal is to provide accurate, comprehensive answers based ONLY on the provided context document above.\n\n"
                        "Guidelines:\n"
                        "1. ALWAYS cite specific Articles and paragraphs (e.g., \"Article 5(1)\").\n"
                        "2. If the answer is not in the document, state that clearly.\n"
                        "3. Be precise with legal definitions.\n"
                        "4. Use structured formatting (bullet points, bold text).\n"
                        "5. Remind users when appropriate that AI-generated responses should be verified with legal counsel.\n"
                        "6. For compliance-critical questions, emphasize the importance of professional legal advice."
                    )
                else:
                    # Fallback to manual context snippets if full text not available
                    logger.info("Full text not available, using manual context snippets...")
                    context_sections = self._build_manual_context(request.question)
                    base_system_prompt = (
                        "You are an expert legal assistant on the EU AI Act (Regulation 2024/1689) and GDPR.\n\n"
                        "IMPORTANT - EU AI Act Article 50 Compliance:\n"
                        "You are an AI assistant. Users have been informed they are interacting with an AI system.\n"
                        "Your responses must be helpful but include appropriate disclaimers about verification and legal counsel.\n\n"
                        "Your goal is to provide accurate, comprehensive answers based ONLY on the provided context.\n\n"
                        "Guidelines:\n"
                        "1. ALWAYS cite specific Articles and paragraphs (e.g., \"Article 5(1)\").\n"
                        "2. If the answer is not in the document, state that clearly.\n"
                        "3. Be precise with legal definitions.\n"
                        "4. Use structured formatting (bullet points, bold text).\n"
                        "5. Remind users when appropriate that AI-generated responses should be verified with legal counsel.\n"
                        "6. For compliance-critical questions, emphasize the importance of professional legal advice."
                    )
                    if context_sections:
                        context_block = "\n\n".join(
                            f"### {section['title']}\n{section['text']}" for section in context_sections
                        )
                        system_instruction = (
                            base_system_prompt
                            + "\n\nUse the following excerpts from the EU AI Act and GDPR as context:\n"
                            + context_block
                            + "\n\nIf the answer is not covered, explain that explicitly."
                        )
                    else:
                        system_instruction = base_system_prompt

            # Create chat session with temperature=0.3 (aligned with CLI)
            generate_config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools,
                temperature=0.3,
            )
            
            try:
                chat_session = self.client.chats.create(
                    model=self.model_name,
                    config=generate_config,
                    history=[]
                )
                self._chat_sessions[chat_history_id] = chat_session
                logger.info(f"Chat session created and stored: {chat_history_id}")
            except Exception as e:
                logger.error(f"Failed to create chat session: {e}")
                raise
        
        # Send message to chat session
        try:
            logger.info(f"Sending message to chat session: {chat_history_id}")
            
            # Track user message in chat history
            if chat_history_id not in self._chat_histories:
                self._chat_histories[chat_history_id] = []
            self._chat_histories[chat_history_id].append({
                'role': 'user',
                'content': request.question
            })
            
            response = chat_session.send_message(request.question)
            logger.info("Message sent successfully")
            
            # Track assistant response in chat history
            assistant_message = response.text if response.text else "No response generated."
            self._chat_histories[chat_history_id].append({
                'role': 'assistant',
                'content': assistant_message
            })
            
            # Extract fallback sources if needed (for manual context mode)
            # Reuse context_sections if already built (for new sessions)
            fallback_sources = None
            if not uses_file_search:
                # For new sessions, context_sections was already built above
                # For existing sessions, we need to build it for references
                if context_sections is None:
                    context_sections = self._build_manual_context(request.question)
                if context_sections:
                    fallback_sources = context_sections
            
            return self._format_response(response, fallback_sources, chat_history_id, chat_session)
            
        except Exception as e:
            logger.error(f"Error sending message to chat session: {e}")
            # Clean up invalid session
            if chat_history_id in self._chat_sessions:
                del self._chat_sessions[chat_history_id]
            if chat_history_id in self._chat_histories:
                del self._chat_histories[chat_history_id]
            raise
    
    def _format_response(self, response, fallback_sources: Optional[List[Dict[str, str]]], 
                        chat_history_id: Optional[str] = None, 
                        chat_session: Optional[Any] = None) -> AIActQueryResponse:
        """Format the Gemini response into AIActQueryResponse."""
        message = response.text if response.text else "No response generated."
        
        references: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = []
        
        # Extract citations from grounding metadata
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
        elif fallback_sources:
            for section in fallback_sources:
                source = {
                    'title': section['title'],
                    'text': section['text'][:200] + "..." if len(section['text']) > 200 else section['text']
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
