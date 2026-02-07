"""
Unit Tests for AI Governance Platform Gemini Services
Tests cover: AI Act Chat, Compliance Scanner, Autofill, Function Calling, Streaming
All Gemini API calls are mocked.
"""
import json
import uuid
import time
from unittest.mock import patch, MagicMock, PropertyMock, call
from django.test import SimpleTestCase as TestCase, RequestFactory, override_settings

from django.conf import settings
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper: Build a mock Gemini response object
# ---------------------------------------------------------------------------

def _mock_gemini_response(text="Test response", function_calls=None):
    """
    Create a mock Gemini response object.

    Args:
        text: The text content of the response.
        function_calls: Optional list of dicts with 'name' and 'args' keys
                        to simulate function_call parts.
    Returns:
        A MagicMock that behaves like a Gemini GenerateContentResponse.
    """
    response = MagicMock()
    response.text = text

    if function_calls:
        parts = []
        for fc in function_calls:
            part = MagicMock()
            part.function_call = MagicMock()
            part.function_call.name = fc["name"]
            part.function_call.args = fc.get("args", {})
            parts.append(part)

        candidate = MagicMock()
        candidate.grounding_metadata = None
        candidate.content = MagicMock()
        candidate.content.parts = parts
        response.candidates = [candidate]
    else:
        candidate = MagicMock()
        candidate.grounding_metadata = None
        candidate.content = MagicMock()
        part = MagicMock()
        part.function_call = None
        candidate.content.parts = [part]
        response.candidates = [candidate]

    return response


# ===========================================================================
# 1-5. Function Declarations & _execute_function_call tests
# ===========================================================================

class TestFunctionDeclarations(TestCase):
    """Tests for _build_function_declarations and _execute_function_call."""

    @patch(
        "governance.infrastructure.services.gemini_ai_act_service.types",
        create=True,
    )
    def test_function_declarations(self, mock_types):
        """Verify _build_function_declarations() returns exactly 3 tools."""
        mock_types.Type.OBJECT = "OBJECT"
        mock_types.Type.STRING = "STRING"

        def fake_schema(**kwargs):
            return kwargs

        mock_types.Schema = fake_schema

        def fake_func_decl(**kwargs):
            return kwargs

        mock_types.FunctionDeclaration = fake_func_decl

        from governance.infrastructure.services.gemini_ai_act_service import (
            _build_function_declarations,
        )

        tools = _build_function_declarations()
        self.assertEqual(len(tools), 3)

        names = {t["name"] for t in tools}
        self.assertIn("classify_ai_system_risk", names)
        self.assertIn("get_compliance_skills", names)
        self.assertIn("run_compliance_scan", names)

        classify_tool = [t for t in tools if t["name"] == "classify_ai_system_risk"][0]
        self.assertIn("parameters", classify_tool)

    @patch(
        "governance.infrastructure.services.governance_agent_service.get_governance_agent_service"
    )
    def test_execute_function_call_classify_risk(self, mock_get_agent):
        """Mock governance_agent_service, verify classify_ai_system_risk."""
        mock_agent = MagicMock()
        mock_agent.assess_ai_system.return_value = {
            "risk_classification": {
                "category": "High-Risk",
                "confidence": "high",
                "reasoning": "Facial recognition in public spaces",
            },
            "applicable_regulations": [
                {"name": "EU AI Act", "reason": "Applies to all AI in EU"}
            ],
            "recommended_skills": [
                {"skill": "risk-assessment", "reason": "Core"},
                {"skill": "bias-assessment", "reason": "Biometric"},
            ],
        }
        mock_get_agent.return_value = mock_agent

        from governance.infrastructure.services.gemini_ai_act_service import (
            _execute_function_call,
        )

        result = _execute_function_call(
            "classify_ai_system_risk",
            {"system_description": "facial recognition system"},
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["risk_category"], "High-Risk")
        self.assertEqual(result["confidence"], "high")
        self.assertIn("reasoning", result)
        self.assertIn("applicable_articles", result)
        self.assertIsInstance(result["applicable_articles"], list)
        mock_agent.assess_ai_system.assert_called_once_with("facial recognition system")

    @patch(
        "governance.infrastructure.services.governance_agent_service.get_governance_agent_service"
    )
    def test_execute_function_call_get_skills(self, mock_get_agent):
        """Mock governance_agent_service, verify get_compliance_skills."""
        mock_agent = MagicMock()
        mock_agent.skills = [
            {"id": "risk-assessment", "description": "Risk assessment skill"},
            {"id": "ai-governance", "description": "AI governance"},
        ]
        mock_agent.assess_ai_system.return_value = {
            "recommended_skills": [
                {"skill": "risk-assessment", "reason": "Core"},
            ],
        }
        mock_get_agent.return_value = mock_agent

        from governance.infrastructure.services.gemini_ai_act_service import (
            _execute_function_call,
        )

        result = _execute_function_call(
            "get_compliance_skills",
            {"risk_category": "HIGH-RISK"},
        )

        self.assertIsInstance(result, dict)
        self.assertIn("recommended_skills", result)

    @patch(
        "governance.infrastructure.services.governance_agent_service.get_governance_agent_service"
    )
    def test_execute_function_call_run_scan(self, mock_get_agent):
        """Mock governance_agent_service, verify run_compliance_scan."""
        mock_agent = MagicMock()
        mock_agent.assess_ai_system.return_value = {
            "risk_classification": {
                "category": "High-Risk",
                "confidence": "high",
                "reasoning": "Healthcare system",
            },
            "applicable_regulations": [
                {"name": "EU AI Act", "reason": "Applies"},
                {"name": "HIPAA", "reason": "Healthcare"},
            ],
            "recommended_skills": [
                {"skill": "risk-assessment", "reason": "Core"},
                {"skill": "hipaa-compliance", "reason": "Healthcare data"},
                {"skill": "ai-safety-planning", "reason": "Safety"},
            ],
        }
        mock_get_agent.return_value = mock_agent

        from governance.infrastructure.services.gemini_ai_act_service import (
            _execute_function_call,
        )

        result = _execute_function_call(
            "run_compliance_scan",
            {
                "system_name": "HealthBot",
                "system_description": "AI for healthcare diagnostics",
                "domain": "healthcare",
            },
        )

        self.assertIsInstance(result, dict)
        self.assertIn("risk_level", result)
        self.assertIn("action_items", result)
        self.assertEqual(result["system_name"], "HealthBot")

    def test_execute_function_call_unknown(self):
        """Call with unknown function name, verify error dict."""
        from governance.infrastructure.services.gemini_ai_act_service import (
            _execute_function_call,
        )

        result = _execute_function_call("nonexistent_function", {})
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("Unknown function", result["error"])


# ===========================================================================
# 6. TestGeminiAIActService
# ===========================================================================

class TestGeminiAIActService(TestCase):
    """Tests for the GeminiAIActService class."""

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai", new=MagicMock())
    @patch("governance.infrastructure.services.gemini_ai_act_service.types", new=MagicMock())
    @override_settings(GEMINI_API_KEY="")
    def test_init_missing_api_key(self):
        """Verify ValueError is raised when GEMINI_API_KEY is missing."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
            with self.assertRaises(ValueError) as ctx:
                GeminiAIActService()
            self.assertIn("GEMINI_API_KEY", str(ctx.exception))

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai", new=None)
    @override_settings(GEMINI_API_KEY="test-key")
    def test_init_missing_genai(self):
        """Verify ImportError is raised when google-genai is not installed."""
        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        with self.assertRaises(ImportError) as ctx:
            GeminiAIActService()
        self.assertIn("google-genai", str(ctx.exception))

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types", new=MagicMock())
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=10, AI_ACT_ARTICLES_DIR=Path("/tmp/test_articles"),
    )
    def test_load_full_text(self, mock_genai):
        """Mock file system, verify text loaded."""
        mock_genai.Client.return_value = MagicMock()
        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        svc = GeminiAIActService()
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="Full text of EU AI Act..."):
                result = svc._load_full_text()
        self.assertEqual(result, "Full text of EU AI Act...")

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types", new=MagicMock())
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=10, AI_ACT_ARTICLES_DIR=None,
    )
    def test_load_full_text_missing(self, mock_genai):
        """Verify empty string returned when articles_dir is None."""
        mock_genai.Client.return_value = MagicMock()
        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        svc = GeminiAIActService()
        result = svc._load_full_text()
        self.assertEqual(result, "")

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types")
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_query_new_session(self, mock_types, mock_genai):
        """Mock Gemini client, verify new chat session created."""
        mock_types.Tool = MagicMock
        mock_types.GenerateContentConfig = MagicMock
        mock_types.ThinkingConfig = MagicMock
        mock_types.ThinkingLevel.HIGH = "HIGH"
        mock_types.FunctionDeclaration = MagicMock
        mock_types.Schema = MagicMock
        mock_types.Type.OBJECT = "OBJECT"
        mock_types.Type.STRING = "STRING"
        mock_types.Part.from_function_response = MagicMock()
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_chat = MagicMock()
        mock_response = _mock_gemini_response(text="This is Article 5 answer.")
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat

        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        from governance.domain.services.ai_act_service import AIActQueryRequest
        svc = GeminiAIActService()
        request = AIActQueryRequest(question="What does Article 5 say?")
        result = svc.query(request)
        self.assertEqual(result.message, "This is Article 5 answer.")
        self.assertIsNotNone(result.chat_history_id)
        mock_client.chats.create.assert_called_once()
        mock_chat.send_message.assert_called_once_with("What does Article 5 say?")

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types")
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_query_continue_session(self, mock_types, mock_genai):
        """Verify existing session reused when chat_history_id provided."""
        mock_types.Tool = MagicMock
        mock_types.GenerateContentConfig = MagicMock
        mock_types.ThinkingConfig = MagicMock
        mock_types.ThinkingLevel.HIGH = "HIGH"
        mock_types.FunctionDeclaration = MagicMock
        mock_types.Schema = MagicMock
        mock_types.Type.OBJECT = "OBJECT"
        mock_types.Type.STRING = "STRING"
        mock_types.Part.from_function_response = MagicMock()
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_chat = MagicMock()
        mock_response = _mock_gemini_response(text="Follow-up answer.")
        mock_chat.send_message.return_value = mock_response

        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        from governance.domain.services.ai_act_service import AIActQueryRequest
        svc = GeminiAIActService()
        existing_id = str(uuid.uuid4())
        svc._chat_sessions[existing_id] = mock_chat
        svc._chat_histories[existing_id] = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]
        request = AIActQueryRequest(question="Follow-up question", chat_history_id=existing_id)
        result = svc.query(request)
        mock_client.chats.create.assert_not_called()
        self.assertEqual(result.message, "Follow-up answer.")
        self.assertEqual(result.chat_history_id, existing_id)

    @patch("governance.infrastructure.services.gemini_ai_act_service._execute_function_call")
    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types")
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_query_with_function_calls(self, mock_types, mock_genai, mock_exec_fn):
        """Mock response with function_call parts, verify loop executes."""
        mock_types.Tool = MagicMock
        mock_types.GenerateContentConfig = MagicMock
        mock_types.ThinkingConfig = MagicMock
        mock_types.ThinkingLevel.HIGH = "HIGH"
        mock_types.FunctionDeclaration = MagicMock
        mock_types.Schema = MagicMock
        mock_types.Type.OBJECT = "OBJECT"
        mock_types.Type.STRING = "STRING"
        mock_types.Part.from_function_response = MagicMock(return_value="mock_part")
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        fc_response = _mock_gemini_response(
            text=None,
            function_calls=[{"name": "classify_ai_system_risk", "args": {"system_description": "face recognition"}}],
        )
        fc_response.text = None
        final_response = _mock_gemini_response(text="Based on the classification, this is High-Risk.")
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = [fc_response, final_response]
        mock_client.chats.create.return_value = mock_chat
        mock_exec_fn.return_value = {"risk_category": "High-Risk", "confidence": "high"}

        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        from governance.domain.services.ai_act_service import AIActQueryRequest
        svc = GeminiAIActService()
        request = AIActQueryRequest(question="Classify this facial recognition system")
        result = svc.query(request)
        mock_exec_fn.assert_called_once_with("classify_ai_system_risk", {"system_description": "face recognition"})
        self.assertEqual(mock_chat.send_message.call_count, 2)
        self.assertEqual(result.message, "Based on the classification, this is High-Risk.")

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types", new=MagicMock())
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_extract_function_calls(self, mock_genai):
        """Test _extract_function_calls correctly parses function call parts."""
        mock_genai.Client.return_value = MagicMock()
        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        svc = GeminiAIActService()
        response = _mock_gemini_response(function_calls=[
            {"name": "classify_ai_system_risk", "args": {"system_description": "test"}},
            {"name": "get_compliance_skills", "args": {"risk_category": "HIGH-RISK"}},
        ])
        calls = svc._extract_function_calls(response)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["name"], "classify_ai_system_risk")
        self.assertEqual(calls[1]["name"], "get_compliance_skills")
        plain_response = _mock_gemini_response(text="Plain text")
        calls = svc._extract_function_calls(plain_response)
        self.assertEqual(len(calls), 0)

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types", new=MagicMock())
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_format_response(self, mock_genai):
        """Test _format_response properly builds an AIActQueryResponse."""
        mock_genai.Client.return_value = MagicMock()
        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        svc = GeminiAIActService()
        chat_id = str(uuid.uuid4())
        svc._chat_histories[chat_id] = [
            {"role": "user", "content": "Test question"},
            {"role": "assistant", "content": "Test answer"},
        ]
        mock_response = _mock_gemini_response(text="Formatted answer text")
        result = svc._format_response(mock_response, chat_id, None)
        self.assertEqual(result.message, "Formatted answer text")
        self.assertEqual(result.chat_history_id, chat_id)
        self.assertIsInstance(result.references, list)
        self.assertIsNotNone(result.chat_history)
        self.assertEqual(len(result.chat_history), 2)


# ===========================================================================
# 7. TestQueryStream
# ===========================================================================

class TestQueryStream(TestCase):
    """Tests for the query_stream method (SSE streaming)."""

    def _setup_mock_types(self, mock_types):
        """Configure mock types for all stream tests."""
        mock_types.Tool = MagicMock
        mock_types.GenerateContentConfig = MagicMock
        mock_types.ThinkingConfig = MagicMock
        mock_types.ThinkingLevel.HIGH = "HIGH"
        mock_types.FunctionDeclaration = MagicMock
        mock_types.Schema = MagicMock
        mock_types.Type.OBJECT = "OBJECT"
        mock_types.Type.STRING = "STRING"
        mock_types.Part.from_function_response = MagicMock(return_value="mock_part")

    def _create_service_and_stream(self, mock_genai, mock_types, chat_response, chat_history_id=None):
        self._setup_mock_types(mock_types)
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_chat = MagicMock()
        if isinstance(chat_response, list):
            mock_chat.send_message.side_effect = chat_response
        else:
            mock_chat.send_message.return_value = chat_response
        mock_client.chats.create.return_value = mock_chat
        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        from governance.domain.services.ai_act_service import AIActQueryRequest
        svc = GeminiAIActService()
        request = AIActQueryRequest(question="Stream test question", chat_history_id=chat_history_id)
        return svc, svc.query_stream(request)

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types")
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_stream_yields_sse_format(self, mock_types, mock_genai):
        """Verify each yielded chunk starts with 'data: ' and ends with newlines."""
        response = _mock_gemini_response(text="Hello world")
        _, gen = self._create_service_and_stream(mock_genai, mock_types, response)
        chunks = list(gen)
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertTrue(chunk.startswith("data: "), f"Chunk does not start with 'data: ': {chunk!r}")
            self.assertTrue(chunk.endswith("\n\n"), f"Chunk does not end with double newline: {chunk!r}")

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types")
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_stream_sends_chat_history_id(self, mock_types, mock_genai):
        """Verify the first chunk contains a chat_history_id."""
        response = _mock_gemini_response(text="Response")
        _, gen = self._create_service_and_stream(mock_genai, mock_types, response)
        chunks = list(gen)
        first_data = json.loads(chunks[0].replace("data: ", "").strip())
        self.assertIn("chat_history_id", first_data)
        self.assertTrue(len(first_data["chat_history_id"]) > 0)

    @patch("governance.infrastructure.services.gemini_ai_act_service._execute_function_call")
    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types")
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_stream_tool_use_notification(self, mock_types, mock_genai, mock_exec_fn):
        """Verify tool use events are sent when function calls occur."""
        mock_exec_fn.return_value = {"risk_category": "High-Risk"}
        fc_response = _mock_gemini_response(
            function_calls=[{"name": "classify_ai_system_risk", "args": {"system_description": "test"}}],
        )
        fc_response.text = None
        final_response = _mock_gemini_response(text="Result after tool use")
        _, gen = self._create_service_and_stream(mock_genai, mock_types, [fc_response, final_response])
        chunks = list(gen)
        tool_events = []
        for chunk in chunks:
            data = json.loads(chunk.replace("data: ", "").strip())
            if "tool_use" in data:
                tool_events.append(data)
        self.assertGreater(len(tool_events), 0, "Expected at least one tool_use notification event")
        self.assertIn("classify_ai_system_risk", tool_events[0]["tool_use"])

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types")
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_stream_error_handling(self, mock_types, mock_genai):
        """Verify that when an exception occurs, an error event is yielded."""
        self._setup_mock_types(mock_types)
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = RuntimeError("API timeout")
        mock_client.chats.create.return_value = mock_chat
        from governance.infrastructure.services.gemini_ai_act_service import GeminiAIActService
        from governance.domain.services.ai_act_service import AIActQueryRequest
        svc = GeminiAIActService()
        request = AIActQueryRequest(question="Failing question")
        chunks = list(svc.query_stream(request))
        error_events = []
        for chunk in chunks:
            data = json.loads(chunk.replace("data: ", "").strip())
            if "error" in data:
                error_events.append(data)
        self.assertGreater(len(error_events), 0, "Expected at least one error event in stream")
        self.assertTrue(error_events[-1]["done"])

    @patch("governance.infrastructure.services.gemini_ai_act_service.genai")
    @patch("governance.infrastructure.services.gemini_ai_act_service.types")
    @override_settings(
        GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
        AI_ACT_API_TIMEOUT=30, AI_ACT_ARTICLES_DIR=None,
    )
    def test_stream_done_flag(self, mock_types, mock_genai):
        """Verify the final chunk has done=True."""
        response = _mock_gemini_response(text="Complete response")
        _, gen = self._create_service_and_stream(mock_genai, mock_types, response)
        chunks = list(gen)
        last_data = json.loads(chunks[-1].replace("data: ", "").strip())
        self.assertTrue(last_data.get("done"), "Last streamed chunk should have done=True")


# ===========================================================================
# 8. TestGeminiScannerService
# ===========================================================================

class TestGeminiScannerService(TestCase):
    """Tests for GeminiScannerService."""

    @patch("governance.infrastructure.services.gemini_scanner_service.genai", new=None)
    @override_settings(GEMINI_API_KEY="", AI_ACT_MODEL_NAME="gemini-test",
                       BASE_DIR=Path("/tmp/test_governance"))
    def test_init_no_api(self):
        """Verify initialization when genai is not available."""
        from governance.infrastructure.services.gemini_scanner_service import GeminiScannerService
        svc = GeminiScannerService()
        self.assertIsNone(svc.client)

    @patch("governance.infrastructure.services.gemini_scanner_service.genai")
    @override_settings(GEMINI_API_KEY="test-key", AI_ACT_MODEL_NAME="gemini-test",
                       BASE_DIR=Path("/tmp/test_governance"))
    def test_init_with_api(self, mock_genai):
        """Verify initialization with a valid API key."""
        mock_genai.Client.return_value = MagicMock()
        from governance.infrastructure.services.gemini_scanner_service import GeminiScannerService
        svc = GeminiScannerService()
        self.assertIsNotNone(svc.client)
        mock_genai.Client.assert_called_once_with(api_key="test-key")

    @patch("governance.infrastructure.services.gemini_scanner_service.genai", new=None)
    @override_settings(GEMINI_API_KEY="", AI_ACT_MODEL_NAME="gemini-test",
                       BASE_DIR=Path("/tmp/test_governance"))
    def test_discover_skills_caching(self):
        """Verify _discover_skills uses caching on the second call."""
        from governance.infrastructure.services.gemini_scanner_service import GeminiScannerService
        GeminiScannerService._skills_cache = None
        GeminiScannerService._cache_timestamp = None
        svc = GeminiScannerService()
        svc._discover_skills()
        GeminiScannerService._skills_cache = {"test-skill": "test/SKILL.md"}
        GeminiScannerService._cache_timestamp = time.time()
        result2 = svc._discover_skills()
        self.assertEqual(result2, {"test-skill": "test/SKILL.md"})
        GeminiScannerService._skills_cache = None
        GeminiScannerService._cache_timestamp = None

    @patch("governance.infrastructure.services.gemini_scanner_service.genai", new=None)
    @override_settings(GEMINI_API_KEY="", AI_ACT_MODEL_NAME="gemini-test",
                       BASE_DIR=Path("/tmp/test_governance"))
    def test_run_scan_no_client(self):
        """Verify mock scan returned when no API key."""
        from governance.infrastructure.services.gemini_scanner_service import GeminiScannerService
        svc = GeminiScannerService()
        svc._governance_agent = None
        with patch.object(svc, "_get_governance_agent", return_value=None):
            with patch.object(svc, "_generate_and_save_md_report", return_value={
                "content": "# Mock Report", "file_path": "/scan-reports/mock.md", "filename": "mock.md",
            }):
                result = svc.run_scan(
                    {"name": "TestProject", "description": "Test AI system"}, "risk-assessment",
                )
        self.assertIn("compliance_status", result)
        self.assertIn("score", result)
        self.assertEqual(result["skill_applied"], "risk-assessment")
        self.assertIn("summary", result)


# ===========================================================================
# 9. TestAutofillService
# ===========================================================================

class TestAutofillService(TestCase):
    """Tests for AutofillService."""

    @patch("governance.infrastructure.services.autofill.autofill_service.genai", new=None)
    def test_init_no_client(self):
        """Verify graceful handling when genai is not available."""
        from governance.infrastructure.services.autofill.autofill_service import AutofillService
        svc = AutofillService()
        self.assertIsNone(svc.client)

    @patch("governance.infrastructure.services.autofill.autofill_service.genai")
    @override_settings(GEMINI_API_KEY="test-key")
    def test_init_with_client(self, mock_genai):
        """Verify client is initialized when API key is available."""
        mock_genai.Client.return_value = MagicMock()
        from governance.infrastructure.services.autofill.autofill_service import AutofillService
        svc = AutofillService()
        self.assertIsNotNone(svc.client)

    @patch("governance.infrastructure.services.autofill.autofill_service.genai", new=None)
    def test_run_bulk_autofill_no_client(self):
        """Verify error response when Gemini client is not initialized."""
        from governance.infrastructure.services.autofill.autofill_service import AutofillService
        svc = AutofillService()
        result = svc.run_bulk_autofill(
            file_paths=["/tmp/test.pdf"],
            fields_metadata=[{"name": "entity_name", "type": "text"}],
        )
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("not initialized", result["error"])

    @patch("governance.infrastructure.services.autofill.autofill_service.genai")
    @override_settings(GEMINI_API_KEY="test-key")
    def test_run_bulk_autofill_success(self, mock_genai):
        """Verify successful autofill."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Acme Corporation"
        mock_client.models.generate_content.return_value = mock_response
        from governance.infrastructure.services.autofill.autofill_service import AutofillService
        svc = AutofillService()
        with patch.object(svc, "_extract_text", return_value="Company: Acme Corporation, Registration: 12345"):
            result = svc.run_bulk_autofill(
                file_paths=["/tmp/test.pdf"],
                fields_metadata=[{"name": "entity_name", "type": "text"}],
            )
        self.assertTrue(result["success"])
        self.assertIn("data", result)
        self.assertIn("entity_name", result["data"])


# ===========================================================================
# 10. TestChatView
# ===========================================================================

class TestChatView(TestCase):
    """Tests for the AI Act Chat view endpoints."""

    def test_chat_api_missing_message(self):
        """POST without message should return 400."""
        response = self.client.post(
            "/ai-assistant/chat",
            data=json.dumps({"agent_id": "agent_ai_act"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_chat_api_empty_message(self):
        """POST with empty message string should return 400."""
        response = self.client.post(
            "/ai-assistant/chat",
            data=json.dumps({"message": "", "agent_id": "agent_ai_act"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_chat_api_invalid_json(self):
        """POST with invalid JSON should return 400."""
        response = self.client.post(
            "/ai-assistant/chat",
            data="this is not json{{{",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)
        self.assertIn("Invalid JSON", data["error"])

    def test_stream_api_missing_message(self):
        """POST to streaming endpoint without message should return 400."""
        response = self.client.post(
            "/ai-assistant/chat/stream",
            data=json.dumps({"agent_id": "agent_ai_act"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_stream_api_invalid_json(self):
        """POST to streaming endpoint with invalid JSON should return 400."""
        response = self.client.post(
            "/ai-assistant/chat/stream",
            data="broken json!!!",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_chat_api_get_not_allowed(self):
        """GET request to chat API should return 405."""
        response = self.client.get("/ai-assistant/chat")
        self.assertEqual(response.status_code, 405)

    def test_stream_api_get_not_allowed(self):
        """GET request to stream API should return 405."""
        response = self.client.get("/ai-assistant/chat/stream")
        self.assertEqual(response.status_code, 405)

    @patch("governance.infrastructure.services.gemini_ai_act_service.get_ai_act_service")
    def test_chat_api_service_unavailable(self, mock_get_svc):
        """When AI Act service raises ValueError, view should return 503."""
        mock_get_svc.side_effect = ValueError("GEMINI_API_KEY not configured")
        response = self.client.post(
            "/ai-assistant/chat",
            data=json.dumps({"message": "Test question", "agent_id": "agent_ai_act"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)

    @patch("governance.infrastructure.services.gemini_ai_act_service.get_ai_act_service")
    def test_chat_api_success(self, mock_get_svc):
        """When AI Act service returns valid response, view should return 200."""
        from governance.domain.services.ai_act_service import AIActQueryResponse
        mock_service = MagicMock()
        chat_id = str(uuid.uuid4())
        mock_service.query.return_value = AIActQueryResponse(
            message="Article 5 prohibits...",
            references=[{"title": "Article 5"}],
            sources=[],
            chat_history_id=chat_id,
            chat_history=[
                {"role": "user", "content": "What does Article 5 say?"},
                {"role": "assistant", "content": "Article 5 prohibits..."},
            ],
        )
        mock_get_svc.return_value = mock_service
        response = self.client.post(
            "/ai-assistant/chat",
            data=json.dumps({"message": "What does Article 5 say?", "agent_id": "agent_ai_act"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("id", data)
        self.assertIn("data", data)
        self.assertEqual(data["data"]["message"], "Article 5 prohibits...")

    @patch("governance.infrastructure.services.gemini_ai_act_service.get_ai_act_service")
    def test_stream_api_success(self, mock_get_svc):
        """Streaming endpoint should return StreamingHttpResponse."""
        mock_service = MagicMock()
        chat_id = str(uuid.uuid4())

        def fake_stream(request):
            yield f'data: {json.dumps({"chat_history_id": chat_id, "chunk": "", "done": False})}\n\n'
            yield f'data: {json.dumps({"chunk": "Hello", "done": False})}\n\n'
            yield f'data: {json.dumps({"chunk": "", "done": True, "chat_history_id": chat_id})}\n\n'

        mock_service.query_stream = fake_stream
        mock_get_svc.return_value = mock_service
        response = self.client.post(
            "/ai-assistant/chat/stream",
            data=json.dumps({"message": "Hello AI Act", "agent_id": "agent_ai_act"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        content = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("chat_history_id", content)


# ===========================================================================
# 11. TestGovernanceAgentService
# ===========================================================================

class TestGovernanceAgentService(TestCase):
    """Tests for GovernanceAgentService helper logic."""

    def test_classify_risk_high(self):
        """Verify high-risk classification for healthcare description."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        result = agent._classify_risk("A healthcare diagnostic AI system")
        self.assertEqual(result["category"], "High-Risk")
        self.assertEqual(result["confidence"], "high")

    def test_classify_risk_limited(self):
        """Verify limited-risk classification for chatbot description."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        result = agent._classify_risk("A chatbot for customer service")
        self.assertEqual(result["category"], "Limited Risk")

    def test_classify_risk_minimal(self):
        """Verify minimal-risk classification for generic description."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        result = agent._classify_risk("A weather forecasting tool")
        self.assertEqual(result["category"], "Minimal Risk")

    def test_identify_regulations_eu_ai_act_always(self):
        """EU AI Act should always be in identified regulations."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        regs = agent._identify_regulations("simple analytics tool")
        reg_names = [r["name"] for r in regs]
        self.assertIn("EU AI Act", reg_names)

    def test_identify_regulations_gdpr(self):
        """GDPR should be identified when personal data is mentioned."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        regs = agent._identify_regulations("System processing personal data of EU citizens")
        reg_names = [r["name"] for r in regs]
        self.assertIn("GDPR", reg_names)

    def test_assess_ai_system_structure(self):
        """Verify assess_ai_system returns the expected dict structure."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        result = agent.assess_ai_system("A medical imaging AI")
        self.assertIn("system_description", result)
        self.assertIn("risk_classification", result)
        self.assertIn("applicable_regulations", result)
        self.assertIn("recommended_skills", result)
        self.assertIn("initial_assessment", result)

    def test_export_assessment_json(self):
        """Verify export to JSON format."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        data = {"test": "value", "number": 42}
        result = agent.export_assessment(data, fmt="json")
        parsed = json.loads(result)
        self.assertEqual(parsed["test"], "value")

    def test_export_assessment_unsupported_format(self):
        """Verify ValueError for unsupported export format."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        with self.assertRaises(ValueError):
            agent.export_assessment({}, fmt="csv")

    def test_get_compulsory_skills_for_tool(self):
        """Verify compulsory skills are returned for a known tool."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        skills = agent.get_compulsory_skills_for_tool("risk-management")
        self.assertIsInstance(skills, list)
        if skills:
            self.assertIn("risk-management", skills)

    def test_get_article_for_tool(self):
        """Verify correct article returned for a known tool."""
        from governance.infrastructure.services.governance_agent_service import GovernanceAgentService
        with patch.object(GovernanceAgentService, "_discover_skills"):
            agent = GovernanceAgentService()
        article = agent.get_article_for_tool("risk-management")
        self.assertEqual(article, "Art. 9")


# ===========================================================================
# 12. TestFormAnalyzer
# ===========================================================================

class TestFormAnalyzer(TestCase):
    """Tests for FormAnalyzer utility class."""

    def test_detect_field_type_email(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer, FieldType
        result = FormAnalyzer.detect_field_type("contact_email")
        self.assertEqual(result, FieldType.EMAIL)

    def test_detect_field_type_phone(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer, FieldType
        result = FormAnalyzer.detect_field_type("telephone_number")
        self.assertEqual(result, FieldType.PHONE)

    def test_detect_field_type_date(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer, FieldType
        result = FormAnalyzer.detect_field_type("go_live_date")
        self.assertEqual(result, FieldType.DATE)

    def test_detect_field_type_default_text(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer, FieldType
        result = FormAnalyzer.detect_field_type("entity_name")
        self.assertEqual(result, FieldType.TEXT)

    def test_parse_response_text(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer, FieldType
        result = FormAnalyzer.parse_response("  Acme Corp  ", FieldType.TEXT)
        self.assertEqual(result, "Acme Corp")

    def test_parse_response_checkbox_json(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer, FieldType
        result = FormAnalyzer.parse_response('["Option A", "Option B"]', FieldType.CHECKBOX)
        self.assertEqual(result, ["Option A", "Option B"])

    def test_parse_response_not_specified(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer, FieldType
        result = FormAnalyzer.parse_response("Not specified in the documents", FieldType.TEXT)
        self.assertEqual(result, "")

    def test_build_structured_prompt(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer, FormField, FieldType
        field = FormField("entity_name", FieldType.TEXT)
        prompt = FormAnalyzer.build_structured_prompt(field, "Company: Test Corp")
        self.assertIn("entity_name", prompt)
        self.assertIn("Test Corp", prompt)
        self.assertIn("DOCUMENT CONTENT", prompt)

    def test_extract_options_json(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer
        result = FormAnalyzer.extract_options('["A", "B", "C"]')
        self.assertEqual(result, ["A", "B", "C"])

    def test_extract_options_comma_separated(self):
        from governance.infrastructure.services.autofill.form_analyzer import FormAnalyzer
        result = FormAnalyzer.extract_options("Red, Green, Blue")
        self.assertEqual(result, ["Red", "Green", "Blue"])
