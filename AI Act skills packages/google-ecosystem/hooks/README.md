# google-ecosystem Hooks

Hooks for detecting Gemini CLI topics and suggesting the `gemini-cli-docs` skill.

## Purpose

This hook detects when users are asking about Gemini CLI topics and automatically injects a reminder to invoke the `gemini-cli-docs` skill for accurate documentation.

## Available Hooks

### suggest-gemini-docs

Detects Gemini CLI-related keywords in user prompts and injects documentation guidance.

| Property | Value |
| -------- | ----- |
| **Event** | `UserPromptSubmit` |
| **Matcher** | `*` (all prompts) |
| **Default State** | Enabled |
| **Timeout** | 10 seconds |

#### How It Works

1. **Ecosystem Scoring**: Detects whether the prompt is about Gemini CLI or Claude Code (prevents cross-ecosystem misfires)
2. **Two-Tier Detection**:
   - **Tier 1 (High-confidence)**: Unique Gemini CLI terms (always fire) - e.g., `gemini-cli`, `memport`, `policy-engine`
   - **Tier 2 (Low-confidence)**: Generic terms (only fire if "gemini" in prompt) - e.g., `checkpointing`, `extensions`, `settings`
3. **Topic Detection**: Identifies specific topics (checkpointing, model-routing, MCP, etc.)
4. **Context Injection**: Adds a system reminder with skill name and keywords

#### Configuration

The hook is **enabled by default**. To disable:

```bash
export CLAUDE_HOOK_SUGGEST_GEMINI_DOCS_ENABLED=0
# or
export CLAUDE_HOOK_SUGGEST_GEMINI_DOCS_ENABLED=false
```

To re-enable (if previously disabled):

```bash
unset CLAUDE_HOOK_SUGGEST_GEMINI_DOCS_ENABLED
# or
export CLAUDE_HOOK_SUGGEST_GEMINI_DOCS_ENABLED=1
```

#### Debug Mode

Enable debug output to see ecosystem scoring:

```bash
export CLAUDE_HOOK_DEBUG=1
```

Debug output is written to stderr.

#### Detected Topics

| Topic | Keywords |
| ----- | -------- |
| `gemini-cli` | General Gemini CLI documentation |
| `checkpointing` | Session management, rewind, snapshots |
| `model-routing` | Flash vs Pro, model selection |
| `token-caching` | Cost optimization, prompt compression |
| `policy-engine` | Trusted folders, security policies |
| `memport` | Memory import/export |
| `mcp` | MCP servers, Model Context Protocol |
| `extensions` | Gemini extensions, plugins |
| `tools` | Tools API, shell, web fetch |
| `ide-integration` | VS Code, JetBrains, IDE companion |
| `installation` | Setup, configuration, authentication |
| `configuration` | Settings, themes, telemetry |
| `commands` | CLI commands |
| `quickstart` | Getting started |

## Implementation

- **Script**: `scripts/hooks/dotnet/suggest-gemini-docs.cs`
- **Language**: C# (.NET 10)
- **Exit Code**: Always 0 (never blocks prompts)

## Output Format

When triggered, the hook outputs JSON:

```json
{
  "systemMessage": "gemini-cli-docs: [topic] detected",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "<system-reminder>...skill invocation guidance...</system-reminder>"
  }
}
```

## Related

- See `gemini-cli-docs` skill for Gemini CLI documentation access
- See `claude-ecosystem` plugin for Claude Code documentation hooks
