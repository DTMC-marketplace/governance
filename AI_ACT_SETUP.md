# AI Act Chat Integration Setup Guide

## Overview
This guide explains how to set up and configure the AI Act chat functionality in the Governance platform. The implementation follows Clean Architecture principles and integrates with Google's Gemini API for querying EU AI Act and GDPR regulations.

## Architecture

The implementation follows Clean Architecture with the following layers:

1. **Domain Layer** (`governance/domain/services/ai_act_service.py`)
   - Defines the business logic interface (`AIActService`)
   - Contains domain models (`AIActQueryRequest`, `AIActQueryResponse`)

2. **Infrastructure Layer** (`governance/infrastructure/services/gemini_ai_act_service.py`)
   - Implements the domain service using Gemini API
   - Handles File Search Store queries and fallback to manual context

3. **Application Layer** (`governance/application/use_cases/ai_act_chat_use_case.py`)
   - Coordinates between domain services
   - Returns application-level DTOs

4. **Presentation Layer** (`governance/presentation/views/ai_act_chat_view.py`)
   - Handles HTTP requests
   - Exposes REST API endpoint

## Security Configuration

### Environment Variables

**IMPORTANT**: Never commit API keys to the repository. Always use environment variables.

Set the following environment variables:

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
export AI_ACT_STORE_NAME="your-store-name"  # Optional, will be loaded from store_info.txt if not set
export AI_ACT_MODEL_NAME="gemini-1.5-pro"  # Optional, defaults to gemini-1.5-pro
```

### Settings Configuration

The settings are automatically loaded from environment variables in `settings.py`:

```python
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
AI_ACT_STORE_NAME = os.environ.get('AI_ACT_STORE_NAME', '')
AI_ACT_MODEL_NAME = os.environ.get('AI_ACT_MODEL_NAME', 'gemini-1.5-pro')
AI_ACT_ARTICLES_DIR = BASE_DIR / 'ai_act_articles'
AI_ACT_STORE_INFO_PATH = BASE_DIR / 'ai_act_store_info.txt'
```

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `Django>=4.2,<5.0`
- `google-genai>=0.2.0`

### 2. Set Up Gemini File Search Store (Optional but Recommended)

If you want to use Gemini's File Search Store for better semantic search:

```bash
python scripts/setup_ai_act_store.py
```

This will:
- Create a File Search Store in Gemini
- Upload all articles from the `ai_act_articles/` directory
- Save the store name to `ai_act_store_info.txt`

### 3. Configure API Key

Set the `GEMINI_API_KEY` environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or add it to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Verify Configuration

Check that the API key is set:

```bash
python -c "import os; print('API Key set:', bool(os.environ.get('GEMINI_API_KEY')))"
```

## API Endpoint

The AI Act chat API is available at:

```
POST /ai-assistant/chat
```

### Request Format

```json
{
    "message": "What are prohibited AI practices?",
    "agent_id": "agent_ai_act",
    "chat_type": "Company"
}
```

### Response Format

```json
{
    "id": null,
    "data": {
        "message": "According to Article 5 of the EU AI Act...",
        "references": [
            {
                "title": "AI Act Article 5",
                "text": "..."
            }
        ],
        "sources": [...]
    }
}
```

## Usage in Frontend

The frontend template (`templates/governance/pages/ai_assistant_chat.html`) automatically detects when `agent_id === 'agent_ai_act'` and uses the new endpoint:

```javascript
const chatEndpoint = agent_id === 'agent_ai_act' 
    ? '/ai-assistant/chat' 
    : `/${requestPlatform}/dashboard/${companyId}/governance/ai-assistant/chat`;
```

## Fallback Behavior

If Gemini File Search Store is not available or not configured, the service will:

1. Load full text sections from `AI act/articles/EU_AI_Act_Full_Text.txt`
2. Load GDPR articles from `AI act/articles/GDPR_Article_*.txt`
3. Use manual keyword matching to find relevant sections
4. Provide context to Gemini for answering questions

## Troubleshooting

### Error: "GEMINI_API_KEY not configured in settings"

**Solution**: Set the `GEMINI_API_KEY` environment variable.

### Error: "google-genai package not installed"

**Solution**: Run `pip install google-genai`

### Error: "No context available for query"

**Solution**: Ensure that `ai_act_articles/` directory exists and contains article files.

### File Search Store Not Working

If File Search Store is unavailable, the service will automatically fall back to manual context matching. This is slower but still functional.

## Security Best Practices

1. **Never commit API keys**: Always use environment variables
2. **Use secrets management**: In production, use a secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)
3. **Rotate keys regularly**: Change API keys periodically
4. **Monitor usage**: Track API usage to detect anomalies
5. **Rate limiting**: Implement rate limiting in production to prevent abuse

## Production Considerations

1. **CSRF Protection**: Currently disabled for demo. Enable proper CSRF protection in production:
   ```python
   from django.views.decorators.csrf import csrf_protect
   
   @csrf_protect
   @require_http_methods(["POST"])
   def ai_act_chat_api(request):
       ...
   ```

2. **Authentication**: Add authentication middleware to protect the endpoint

3. **Rate Limiting**: Implement rate limiting to prevent abuse

4. **Error Logging**: Add proper error logging and monitoring

5. **Caching**: Consider caching frequent queries

6. **Database Persistence**: Add chat history persistence if needed

## Testing

To test the API endpoint:

```bash
curl -X POST http://localhost:8000/ai-assistant/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are prohibited AI practices?",
    "agent_id": "agent_ai_act",
    "chat_type": "Company"
  }'
```

## Support

For issues or questions, please refer to:
- `AI act/AGENTS.md` - Agent documentation
- `AI act/SETUP_REPORT.md` - Setup troubleshooting
- `ARCHITECTURE.md` - Overall architecture documentation
