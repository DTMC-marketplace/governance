#!/usr/bin/env dotnet run
#:property TargetFramework=net10.0
// suggest-gemini-docs.cs - Detect Gemini CLI topics and inject docs reminder
//
// TWO-TIER DETECTION:
// - Tier 1 (high-confidence): Unique Gemini CLI terms - always fire
// - Tier 2 (low-confidence): Generic terms - only fire if "gemini" in prompt
//
// This prevents false positives on generic prompts
//
// Event: UserPromptSubmit
// Purpose: Remind Claude to invoke gemini-cli-docs skill for Gemini CLI topics
//
// Exit Codes:
//   0 - Success (always)
//
// Configuration: Environment variable
// To disable: Set CLAUDE_HOOK_SUGGEST_GEMINI_DOCS_ENABLED=0

using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

// Check if hook is enabled (default: enabled)
var enabled = Environment.GetEnvironmentVariable("CLAUDE_HOOK_SUGGEST_GEMINI_DOCS_ENABLED");
if (enabled == "0" || enabled == "false")
{
    Console.In.ReadToEnd();
    return 0;
}

// Debug mode
var debug = Environment.GetEnvironmentVariable("CLAUDE_HOOK_DEBUG") == "1";

// Read input and extract prompt
var input = Console.In.ReadToEnd();
string? prompt = null;

try
{
    var json = JsonNode.Parse(input);
    prompt = json?["prompt"]?.GetValue<string>();
}
catch
{
    // Failed to parse, exit silently
    return 0;
}

if (string.IsNullOrEmpty(prompt))
{
    return 0;
}

var promptLower = prompt.ToLowerInvariant();

// === ECOSYSTEM SCORING ===
// Prevents cross-ecosystem misfires by detecting which ecosystem the user is asking about
string GetEcosystemContext(string p)
{
    int geminiScore = 0;
    int claudeScore = 0;

    // HIGH-WEIGHT SIGNALS (explicit product mentions) - 10 points each
    if (Regex.IsMatch(p, @"gemini.?cli")) geminiScore += 10;
    if (p.Contains("geminicli")) geminiScore += 10;
    if (Regex.IsMatch(p, @"google.?gemini")) geminiScore += 10;
    if (p.Contains("geminicli.com")) geminiScore += 10;

    if (Regex.IsMatch(p, @"claude\s+code")) claudeScore += 10;
    if (p.Contains("anthropic")) claudeScore += 10;

    // MEDIUM-WEIGHT SIGNALS (config paths, unique terms) - 5 points each
    // Gemini-unique signals
    if (p.Contains(".gemini/")) geminiScore += 5;
    if (p.Contains("~/.gemini")) geminiScore += 5;
    if (p.Contains("gemini.md")) geminiScore += 5;
    if (p.Contains(".geminiignore")) geminiScore += 5;
    if (p.Contains("memport")) geminiScore += 5;
    if (Regex.IsMatch(p, @"trusted.?folder")) geminiScore += 5;
    if (Regex.IsMatch(p, @"policy.?engine")) geminiScore += 5;
    if (p.Contains("llms.txt")) geminiScore += 5;
    if (Regex.IsMatch(p, @"model.?routing")) geminiScore += 5;
    if (Regex.IsMatch(p, @"token.?caching")) geminiScore += 5;
    if (Regex.IsMatch(p, @"prompt.?compression")) geminiScore += 5;
    if (p.Contains("/compress")) geminiScore += 5;
    if (Regex.IsMatch(p, @"/chat\s+(save|resume|delete|share)")) geminiScore += 5;
    if (p.Contains("--yolo")) geminiScore += 5;
    if (Regex.IsMatch(p, @"shadow.?git")) geminiScore += 5;
    if (p.Contains("checkpointing.enabled")) geminiScore += 5;
    if (p.Contains("gemini_api_key")) geminiScore += 5;
    if (Regex.IsMatch(p, @"permissive-open|permissive-closed|restrictive-open")) geminiScore += 5;
    if (Regex.IsMatch(p, @"sandbox-exec|seatbelt")) geminiScore += 5;

    // Claude-unique signals
    if (p.Contains(".claude/")) claudeScore += 5;
    if (p.Contains("claude.md")) claudeScore += 5;
    if (p.Contains(".claude-plugin")) claudeScore += 5;
    if (p.Contains("settings.local.json")) claudeScore += 5;
    if (Regex.IsMatch(p, @"pretooluse|posttooluse|userpromptsubmit")) claudeScore += 5;
    if (Regex.IsMatch(p, @"sessionstart|sessionend|precompact|subagentstop")) claudeScore += 5;
    if (Regex.IsMatch(p, @"allowed-?tools|disallowed-?tools")) claudeScore += 5;
    if (Regex.IsMatch(p, @"permission-?mode|bypasspermissions|acceptedits")) claudeScore += 5;
    if (Regex.IsMatch(p, @"agent-?sdk")) claudeScore += 5;
    if (Regex.IsMatch(p, @"/doctor|/compact|/cost|/statusline|/terminal-setup")) claudeScore += 5;
    if (Regex.IsMatch(p, @"/output-style|/permissions|/memory|/plugin")) claudeScore += 5;
    if (Regex.IsMatch(p, @"managed-settings\.json|managed-mcp\.json")) claudeScore += 5;
    if (Regex.IsMatch(p, @"--dangerously|--permission-prompt-tool")) claudeScore += 5;

    // LOW-WEIGHT SIGNALS (generic but associated terms) - 2 points each
    if (p.Contains("gemini")) geminiScore += 2;
    if (p.Contains("claude")) claudeScore += 2;

    if (debug)
    {
        Console.Error.WriteLine($"ecosystem_score: claude={claudeScore} gemini={geminiScore}");
    }

    // DECISION LOGIC - require significant lead (>5 points) to declare winner
    if (geminiScore > claudeScore + 5) return "gemini";
    if (claudeScore > geminiScore + 5) return "claude";
    return "ambiguous";
}

// Check ecosystem context - exit early if Claude is clearly dominant
var ecosystem = GetEcosystemContext(promptLower);
if (ecosystem == "claude")
{
    if (debug) Console.Error.WriteLine("gemini-hook: exiting, claude dominant");
    return 0;
}

// === TIER 1: HIGH-CONFIDENCE PATTERNS (always match) ===
var tier1Pattern = @"gemini.?cli|geminicli\.com|gemini.?code" +
    @"|memport|policy.?engine|trusted.?folder" +
    @"|model.?routing|flash.?vs.?pro|pro.?vs.?flash" +
    @"|token.?caching|prompt.?compression" +
    @"|gemini.?extension|gemini.?theme" +
    @"|gemini.?mcp|gemini.?server" +
    @"|llms\.txt";

// === TIER 2: LOW-CONFIDENCE PATTERNS (need "gemini" context) ===
var tier2Pattern = @"checkpointing|session|rewind|snapshot" +
    @"|tools?|shell|web.?fetch|web.?search|file.?system" +
    @"|extensions?|plugins?" +
    @"|vscode|vs.?code|jetbrains|intellij|ide.?companion" +
    @"|install|setup|configure|authentication" +
    @"|telemetry|settings|commands?" +
    @"|mcp|model.?context.?protocol" +
    @"|memory.?tool|sandbox|security" +
    @"|quickstart|getting.?started";

// === DETECTION LOGIC ===
bool hasGeminiContext = promptLower.Contains("gemini");
bool matched = false;

// Check Tier 1 first (always match)
if (Regex.IsMatch(promptLower, tier1Pattern))
{
    matched = true;
}

// Check Tier 2 only if gemini context exists
if (hasGeminiContext && Regex.IsMatch(promptLower, tier2Pattern))
{
    matched = true;
}

if (!matched)
{
    return 0;
}

// === TOPIC DETECTION ===
string topic = "gemini-cli";
string keywords = "Gemini CLI documentation";

// Check specific categories (most specific first)
if (Regex.IsMatch(promptLower, @"checkpointing|rewind|snapshot|session"))
{
    topic = "checkpointing"; keywords = "checkpointing, session management, rewind";
}
else if (Regex.IsMatch(promptLower, @"model.?routing|flash|pro"))
{
    topic = "model-routing"; keywords = "model routing, Flash vs Pro";
}
else if (Regex.IsMatch(promptLower, @"token.?caching|prompt.?compression"))
{
    topic = "token-caching"; keywords = "token caching, cost optimization";
}
else if (Regex.IsMatch(promptLower, @"policy.?engine|trusted.?folder"))
{
    topic = "policy-engine"; keywords = "policy engine, trusted folders";
}
else if (promptLower.Contains("memport"))
{
    topic = "memport"; keywords = "memory import/export";
}
else if (Regex.IsMatch(promptLower, @"mcp|model.?context.?protocol"))
{
    topic = "mcp"; keywords = "MCP servers, Model Context Protocol";
}
else if (promptLower.Contains("extension"))
{
    topic = "extensions"; keywords = "extensions, plugins";
}
else if (Regex.IsMatch(promptLower, @"tool|shell|web.?fetch|file.?system"))
{
    topic = "tools"; keywords = "tools API, shell, web fetch";
}
else if (Regex.IsMatch(promptLower, @"vs.?code|vscode|jetbrains|ide"))
{
    topic = "ide-integration"; keywords = "VS Code, JetBrains, IDE companion";
}
else if (Regex.IsMatch(promptLower, @"install|setup|configure|authentication"))
{
    topic = "installation"; keywords = "installation, setup, authentication";
}
else if (Regex.IsMatch(promptLower, @"settings|telemetry|theme"))
{
    topic = "configuration"; keywords = "settings, themes, telemetry";
}
else if (Regex.IsMatch(promptLower, @"commands?"))
{
    topic = "commands"; keywords = "CLI commands";
}
else if (Regex.IsMatch(promptLower, @"quickstart|getting.?started"))
{
    topic = "quickstart"; keywords = "quickstart, getting started";
}

// === OUTPUT ===
var context = $@"<system-reminder>
GEMINI CLI DOCUMENTATION REQUIREMENT DETECTED.

Topic: {topic}
Skill: gemini-cli-docs
Keywords: {keywords}

ACTION: Invoke gemini-cli-docs skill before answering.
</system-reminder>";

var response = new HookResponse
{
    SystemMessage = $"gemini-cli-docs: [{topic}] detected",
    HookSpecificOutput = new UserPromptSubmitOutput
    {
        HookEventName = "UserPromptSubmit",
        AdditionalContext = context
    }
};

Console.WriteLine(JsonSerializer.Serialize(response, HookJsonContext.Default.HookResponse));
return 0;

// Type definitions
record HookResponse
{
    public string? SystemMessage { get; init; }
    public UserPromptSubmitOutput? HookSpecificOutput { get; init; }
}

record UserPromptSubmitOutput
{
    public string? HookEventName { get; init; }
    public string? AdditionalContext { get; init; }
}

// Source-generated JSON serializer context for AOT compatibility
[JsonSourceGenerationOptions(PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase)]
[JsonSerializable(typeof(HookResponse))]
internal partial class HookJsonContext : JsonSerializerContext { }
