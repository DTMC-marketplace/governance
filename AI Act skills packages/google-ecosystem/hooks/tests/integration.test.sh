#!/usr/bin/env bash
# integration.test.sh - Integration tests for suggest-gemini-docs hook
#
# Tests the UserPromptSubmit hook that detects Gemini CLI topics
# and injects documentation guidance.

set -euo pipefail

# ============================================================================
# Environment Isolation - Clear hook-related env vars for consistent test behavior
# ============================================================================
for var in $(env | grep '^CLAUDE_HOOK_' | cut -d= -f1); do
    unset "$var"
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PLUGIN_ROOT="$(cd "${HOOK_DIR}/.." && pwd)"
HOOK_SCRIPT="${PLUGIN_ROOT}/scripts/hooks/dotnet/suggest-gemini-docs.cs"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
if [[ -t 1 ]]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    GREEN=''
    RED=''
    YELLOW=''
    NC=''
fi

pass_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} PASS: $1"
}

fail_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} FAIL: $1"
    if [[ -n "${2:-}" ]]; then
        echo "  Details: $2"
    fi
}

skip_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${YELLOW}⊙${NC} SKIP: $1"
}

# Find jq - used for JSON validation
find_jq() {
    command -v jq 2>/dev/null || return 1
}

JQ_CMD=$(find_jq || echo "")

# Helper function to run hook with a prompt
run_hook() {
    local prompt="${1:-}"
    local env_enabled="${2:-}"
    local input='{"prompt": "'"$prompt"'"}'

    if [[ -n "$env_enabled" ]]; then
        echo "$input" | CLAUDE_HOOK_SUGGEST_GEMINI_DOCS_ENABLED="$env_enabled" timeout 30 dotnet run "$HOOK_SCRIPT" 2>/dev/null
    else
        echo "$input" | timeout 30 dotnet run "$HOOK_SCRIPT" 2>/dev/null
    fi
}

echo ""
echo "=========================================="
echo "Test Suite: suggest-gemini-docs Integration Tests"
echo "=========================================="
echo ""

# ============================================================================
# SECTION 1: Hook Setup
# ============================================================================
echo "--- Hook Setup ---"

# Test: Hook script exists
if [[ -f "$HOOK_SCRIPT" ]]; then
    pass_test "Hook script exists"
else
    fail_test "Hook script not found at $HOOK_SCRIPT"
fi

# Test: Hook README exists
if [[ -f "${HOOK_DIR}/README.md" ]]; then
    pass_test "Hook README.md exists"
else
    fail_test "Hook README.md not found"
fi

# Test: Hook is a dotnet script
if head -1 "$HOOK_SCRIPT" | grep -q "#!/usr/bin/env dotnet run"; then
    pass_test "Hook has correct dotnet shebang"
else
    fail_test "Hook missing or incorrect shebang"
fi

# ============================================================================
# SECTION 2: Disabled Behavior
# ============================================================================
echo ""
echo "--- Disabled Behavior ---"

# Test: Hook produces no output when explicitly disabled with ENABLED=0
OUTPUT=$(run_hook "Tell me about gemini cli" "0")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && -z "$OUTPUT" ]]; then
    pass_test "Hook produces no output when ENABLED=0"
else
    fail_test "Hook should produce no output when disabled" "output: $OUTPUT"
fi

# Test: Hook disabled with ENABLED=false
OUTPUT=$(run_hook "gemini cli help" "false")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && -z "$OUTPUT" ]]; then
    pass_test "Hook produces no output when ENABLED=false"
else
    fail_test "Hook should produce no output when ENABLED=false" "output: $OUTPUT"
fi

# ============================================================================
# SECTION 3: Enabled Behavior - Tier 1 Keywords (default enabled)
# ============================================================================
echo ""
echo "--- Enabled Behavior - Tier 1 Keywords ---"

# Test: Hook triggers on gemini-cli keyword (default enabled, no env var needed)
OUTPUT=$(run_hook "How do I install gemini-cli?")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && "$OUTPUT" == *"gemini-cli-docs"* ]]; then
    pass_test "Hook triggers on 'gemini-cli' keyword (default enabled)"
else
    fail_test "Hook should trigger on 'gemini-cli'" "output: $OUTPUT"
fi

# Test: Hook triggers on memport keyword
OUTPUT=$(run_hook "How does memport work?")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && "$OUTPUT" == *"gemini-cli-docs"* ]]; then
    pass_test "Hook triggers on 'memport' keyword"
else
    fail_test "Hook should trigger on 'memport'" "output: $OUTPUT"
fi

# Test: Hook triggers on policy-engine keyword
OUTPUT=$(run_hook "What is the policy engine in gemini?")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && "$OUTPUT" == *"gemini-cli-docs"* ]]; then
    pass_test "Hook triggers on 'policy engine' keyword"
else
    fail_test "Hook should trigger on 'policy engine'" "output: $OUTPUT"
fi

# Test: Hook triggers on llms.txt keyword
OUTPUT=$(run_hook "How does gemini use llms.txt?")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && "$OUTPUT" == *"gemini-cli-docs"* ]]; then
    pass_test "Hook triggers on 'llms.txt' keyword"
else
    fail_test "Hook should trigger on 'llms.txt'" "output: $OUTPUT"
fi

# ============================================================================
# SECTION 4: Enabled Behavior - Tier 2 Keywords (require gemini context)
# ============================================================================
echo ""
echo "--- Enabled Behavior - Tier 2 Keywords ---"

# Test: Tier 2 keyword WITH gemini context triggers
OUTPUT=$(run_hook "How does gemini checkpointing work?")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && "$OUTPUT" == *"gemini-cli-docs"* ]]; then
    pass_test "Hook triggers on Tier 2 keyword with gemini context"
else
    fail_test "Hook should trigger on Tier 2 keyword with gemini context" "output: $OUTPUT"
fi

# Test: Tier 2 keyword WITHOUT gemini context does NOT trigger
OUTPUT=$(run_hook "How does checkpointing work in this app?")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && -z "$OUTPUT" ]]; then
    pass_test "Hook does not trigger on Tier 2 keyword without gemini context"
else
    fail_test "Hook should not trigger on Tier 2 keyword without gemini context" "output: $OUTPUT"
fi

# ============================================================================
# SECTION 5: Ecosystem Scoring (Claude vs Gemini)
# ============================================================================
echo ""
echo "--- Ecosystem Scoring ---"

# Test: Claude-dominant prompt should NOT trigger
OUTPUT=$(run_hook "How do I create a Claude Code hook in .claude/hooks?")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && -z "$OUTPUT" ]]; then
    pass_test "Hook does not trigger on Claude-dominant prompts"
else
    fail_test "Hook should not trigger on Claude-dominant prompts" "output: $OUTPUT"
fi

# Test: Prompt with anthropic should NOT trigger
OUTPUT=$(run_hook "How do I use anthropic claude code?")
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && -z "$OUTPUT" ]]; then
    pass_test "Hook does not trigger when 'anthropic' is mentioned"
else
    fail_test "Hook should not trigger when 'anthropic' is mentioned" "output: $OUTPUT"
fi

# ============================================================================
# SECTION 6: JSON Output Validation
# ============================================================================
echo ""
echo "--- JSON Output Validation ---"

OUTPUT=$(run_hook "How do I configure gemini-cli?")

# Test: Output is valid JSON
if [[ -n "$JQ_CMD" ]]; then
    if echo "$OUTPUT" | "$JQ_CMD" empty 2>/dev/null; then
        pass_test "Output is valid JSON"
    else
        fail_test "Output should be valid JSON" "output: $OUTPUT"
    fi

    # Test: Output has hookSpecificOutput
    if echo "$OUTPUT" | "$JQ_CMD" -e '.hookSpecificOutput' >/dev/null 2>&1; then
        pass_test "Output contains hookSpecificOutput"
    else
        fail_test "Output should contain hookSpecificOutput"
    fi

    # Test: hookEventName is UserPromptSubmit
    HOOK_EVENT=$(echo "$OUTPUT" | "$JQ_CMD" -r '.hookSpecificOutput.hookEventName // empty' 2>/dev/null | tr -d '\r')
    if [[ "$HOOK_EVENT" == "UserPromptSubmit" ]]; then
        pass_test "hookEventName is UserPromptSubmit"
    else
        fail_test "hookEventName should be UserPromptSubmit" "got: $HOOK_EVENT"
    fi

    # Test: additionalContext contains system-reminder
    CONTEXT=$(echo "$OUTPUT" | "$JQ_CMD" -r '.hookSpecificOutput.additionalContext // empty' 2>/dev/null)
    if [[ "$CONTEXT" == *"system-reminder"* ]]; then
        pass_test "additionalContext contains system-reminder tags"
    else
        fail_test "additionalContext should contain system-reminder tags"
    fi

    # Test: systemMessage is present
    SYS_MSG=$(echo "$OUTPUT" | "$JQ_CMD" -r '.systemMessage // empty' 2>/dev/null)
    if [[ -n "$SYS_MSG" ]]; then
        pass_test "systemMessage is present"
    else
        fail_test "systemMessage should be present"
    fi
else
    skip_test "jq not found - skipping detailed JSON validation"

    # Basic JSON structure check without jq
    if [[ "$OUTPUT" == *"{"* && "$OUTPUT" == *"}"* && "$OUTPUT" == *"hookSpecificOutput"* ]]; then
        pass_test "Output has JSON structure (basic check)"
    else
        fail_test "Output should have JSON structure"
    fi
fi

# ============================================================================
# SECTION 7: Topic Detection
# ============================================================================
echo ""
echo "--- Topic Detection ---"

# Test: Checkpointing topic detected
OUTPUT=$(run_hook "How do I use gemini checkpointing?")
if [[ "$OUTPUT" == *"checkpointing"* ]]; then
    pass_test "Detects 'checkpointing' topic"
else
    fail_test "Should detect 'checkpointing' topic" "output: $OUTPUT"
fi

# Test: MCP topic detected
OUTPUT=$(run_hook "How do I configure gemini mcp servers?")
if [[ "$OUTPUT" == *"mcp"* || "$OUTPUT" == *"MCP"* ]]; then
    pass_test "Detects 'mcp' topic"
else
    fail_test "Should detect 'mcp' topic" "output: $OUTPUT"
fi

# ============================================================================
# SECTION 8: Exit Code Verification
# ============================================================================
echo ""
echo "--- Exit Code Verification ---"

# Test: Hook always exits 0
echo '{}' | timeout 30 dotnet run "$HOOK_SCRIPT" >/dev/null 2>&1
EXIT_CODE=$?
if [[ $EXIT_CODE -eq 0 ]]; then
    pass_test "Hook exits 0 with empty JSON"
else
    fail_test "Hook should exit 0 with empty JSON" "exit code: $EXIT_CODE"
fi

echo '' | timeout 30 dotnet run "$HOOK_SCRIPT" >/dev/null 2>&1
EXIT_CODE=$?
if [[ $EXIT_CODE -eq 0 ]]; then
    pass_test "Hook exits 0 with empty input"
else
    fail_test "Hook should exit 0 with empty input" "exit code: $EXIT_CODE"
fi

echo '{"prompt": "random unrelated prompt"}' | timeout 30 dotnet run "$HOOK_SCRIPT" >/dev/null 2>&1
EXIT_CODE=$?
if [[ $EXIT_CODE -eq 0 ]]; then
    pass_test "Hook exits 0 with non-matching prompt"
else
    fail_test "Hook should exit 0 with non-matching prompt" "exit code: $EXIT_CODE"
fi

# ============================================================================
# Test Summary
# ============================================================================
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Tests run:    $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"

if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    echo ""
    echo -e "${RED}FAILED${NC} - Some tests did not pass"
    exit 1
else
    echo "Tests failed: 0"
    echo ""
    echo -e "${GREEN}SUCCESS${NC} - All tests passed!"
    exit 0
fi
