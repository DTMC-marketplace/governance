# AI Governance Platform — Gemini 3 Hackathon Submission

## Devpost

**Title:** AI Governance Platform — Multi-Agent EU AI Act Compliance Engine

**Short Description:** An autonomous multi-agent system powered by Gemini 3 Pro that helps organizations achieve EU AI Act compliance through intelligent risk classification, multi-step compliance scanning, and legal reasoning over the full regulation text.

**Tags:** ai-governance, eu-ai-act, compliance, gemini-3, multi-agent, clean-architecture, legal-ai, function-calling, thinking, streaming

**Built With:** Python, Django, Google Gemini 3 Pro API, google-genai SDK, Docker, Azure Web Apps

**Links:**
- **Live Demo**: https://governance-fbcsergtb2h9cscy.francecentral-01.azurewebsites.net
- **GitHub**: https://github.com/DTMC-marketplace/governance

---

## Gemini Integration Description (~200 words)

Our platform leverages **Gemini 3 Pro** as the core intelligence across 4 specialized services — this is not a prompt wrapper or baseline RAG.

**Long Context (1M tokens):** The complete EU AI Act (591KB) is injected directly into Gemini 3's system instruction for native reasoning over 181 articles without chunking or retrieval.

**Thinking (Deep Reasoning):** All services use `ThinkingConfig` with `ThinkingLevel.HIGH` for legal analysis and `MEDIUM` for document extraction, enabling chain-of-thought reasoning for precise legal interpretation.

**Function Calling (Tool Use):** The AI Act Chat declares 3 tools — `classify_ai_system_risk`, `get_compliance_skills`, `run_compliance_scan` — that Gemini autonomously invokes during conversation, connecting to the GovernanceAgentService for real governance operations.

**Streaming (SSE):** Real-time Server-Sent Events streaming delivers response chunks as they arrive, with inline tool-use notifications for responsive UX.

**Multi-Service Orchestration:** Four independent Gemini 3 services work together:
1. **Governance Agent** (929 lines) — risk classification, article mapping, 123 skills
2. **Compliance Scanner** (473 lines) — 8-step autonomous pipeline
3. **AI Act Legal Chat** (751 lines) — multi-turn chat with function calling + streaming
4. **Smart Autofill** (161 lines) — document extraction + form completion

---

## Problem Statement

The EU AI Act (Regulation 2024/1689) is the world's first comprehensive AI regulation, affecting every company deploying AI in Europe. Organizations face:

- **181 articles** of complex legal text requiring interpretation
- **4 risk tiers** (Unacceptable, High, Limited, Minimal) with different compliance requirements
- **Cross-regulation overlap** with GDPR, HIPAA, PCI-DSS
- **No standardized tooling** — compliance teams rely on manual legal review

This is not a "single prompt" problem. It requires an orchestrated system that reasons across the entire regulation, classifies AI systems, maps requirements to specific articles, and generates actionable compliance plans.

---

## How We Use Gemini 3

### 1. Long Context Reasoning (1M Token Window)

We inject the **full EU AI Act regulation text (591KB)** directly into Gemini 3 Pro's system instruction. No chunking, no RAG, no retrieval pipeline — the model natively reasons over the entire regulation in a single context. This is only possible with Gemini 3's verified 1M token context window.

### 2. Multi-Service Orchestration (Not a Prompt Wrapper)

The platform orchestrates **4 specialized Gemini 3 services** in a multi-step pipeline:

```
User Input (AI System Description)
    |
    v
[Service 1: Governance Agent] --> Risk Classification + Article Mapping
    |                                (929 lines, 123 skills)
    v
[Service 2: Compliance Scanner] --> 8-Step Compliance Scan Pipeline
    |                                 (473 lines, multi-turn reasoning)
    v
[Service 3: AI Act Chat] -------> Legal Q&A with Full Regulation Context
    |                              (751 lines, function calling + streaming)
    v
[Service 4: Smart Autofill] ----> Document Extraction + Form Completion
                                  (161 lines, multi-format support)
```

Each service makes **independent Gemini 3 API calls** with specialized system instructions, not a single shared prompt.

### 3. Gemini 3 Thinking (Deep Reasoning)

All Gemini services use **ThinkingConfig** with appropriate levels:
- **AI Act Chat**: `ThinkingLevel.HIGH` — deep legal reasoning over 181 articles
- **Compliance Scanner**: `ThinkingLevel.HIGH` — multi-factor risk analysis
- **Smart Autofill**: `ThinkingLevel.MEDIUM` — document extraction accuracy

Thinking enables the model to perform chain-of-thought reasoning before responding, critical for precise legal interpretation.

### 4. Function Calling (Tool Use)

The AI Act Chat service declares **3 function tools** that Gemini can invoke during conversation:
- `classify_ai_system_risk` — Classifies AI systems into EU AI Act risk tiers using GovernanceAgentService
- `get_compliance_skills` — Returns recommended compliance skills for a risk category
- `run_compliance_scan` — Performs quick compliance assessment with action items

This demonstrates true **agentic tool use**: Gemini autonomously decides when to call tools, executes them, and incorporates results into its response — up to 5 rounds of tool calls per query.

### 5. Streaming Response (SSE)

The chat interface uses **Server-Sent Events** for real-time streaming:
- Text chunks stream as they arrive from Gemini 3
- Tool use notifications displayed inline
- Animated cursor during streaming for responsive UX
- Graceful fallback to standard JSON for non-AI-Act agents

### 6. Multi-Step Agentic Pipeline

The Compliance Scanner demonstrates true agentic behavior with 8 autonomous steps:

1. **Assess** — GovernanceAgent classifies the AI system's risk tier
2. **Discover** — Dynamically loads relevant skills from 123 available
3. **Load Checklist** — Retrieves article-specific compliance requirements
4. **Build Context** — Enriches prompt with governance assessment + skill guidelines
5. **Analyze** — Gemini 3 performs deep compliance analysis
6. **Format** — Generates professional markdown compliance report
7. **Persist** — Saves report to file system
8. **Return** — Structured JSON result with scores and recommendations

This is a **Marathon Agent** — a robust system that performs multi-step tool calls with self-correction, not a single prompt-response cycle.

---

## Technical Architecture

### Clean Architecture (4 Layers)

```
Presentation Layer --- Django Views + REST API (125+ endpoints)
         |
Application Layer --- Use Cases + DTOs
         |
  Domain Layer ---- Entities + Services + Repository Interfaces
         |
Infrastructure ---- Gemini API Services + Mock Repositories
```

### Design Patterns (7 Patterns)

| Pattern | Implementation |
|---------|---------------|
| Repository | Data access abstraction (swappable mock -> database) |
| Factory | Validated entity creation (AgentFactory) |
| Strategy | Interchangeable compliance frameworks |
| Dependency Injection | Centralized DependencyContainer |
| Use Case | Single-responsibility operations |
| DTO | Cross-layer data transfer |
| Domain Service | Cross-entity business logic |

### Technology Stack

| Component | Technology |
|-----------|-----------|
| AI Model | **Gemini 3 Pro** (gemini-3-pro-preview) |
| Backend | Python 3.11 + Django 4.2 |
| API | google-genai SDK |
| Deployment | Azure Web Apps + Docker |
| Architecture | Clean Architecture |

---

## Key Features

### AI-Powered Compliance Engine
- **Risk Classification**: Automatic EU AI Act risk tier assignment (Art. 5, 6, 50, 52)
- **Article Mapping**: Maps AI systems to specific regulatory articles and requirements
- **123 Governance Skills**: Dynamic skill library covering safety, ethics, testing, transparency, data governance, and more

### Comprehensive Scanning
- **8-Step Compliance Pipeline**: Automated assessment with professional report generation
- **Multi-Regulation Support**: EU AI Act + GDPR + HIPAA + PCI-DSS
- **NIST AI RMF**: Risk Management Framework profile generation

### Legal AI Assistant
- **Full Regulation Context**: 591KB EU AI Act text loaded via Long Context
- **Multi-Turn Conversations**: Persistent chat sessions with history
- **Citation Accuracy**: Direct article/paragraph references (e.g., "Article 5(1)")
- **Function Calling**: 3 tools (risk classify, skill lookup, compliance scan) invoked autonomously
- **Streaming Response**: Real-time SSE streaming with tool use notifications
- **Deep Thinking**: ThinkingLevel.HIGH for precise legal reasoning

### Smart Document Processing
- **AI Autofill**: Extract data from PDF/DOCX/TXT to auto-fill compliance forms
- **Multi-Format**: PDF, DOCX, TXT, CSV, JSON, Markdown support

### Enterprise UI
- **39 Pages**: Dashboard, AI Inventory, Compliance Hub, Assessment, Questionnaires, Digital Regulations, Risk Registry
- **125+ API Endpoints**: Full REST API for all operations

---

## Project Statistics

| Metric | Value |
|--------|-------|
| Gemini 3 Service Files | 4 |
| Core Service Lines | 2,314 |
| Governance Skills | 123 |
| Regulation Files | 267 (16 MB) |
| EU AI Act Articles | 93+ articles |
| Function Calling Tools | 3 |
| Gemini 3 Features Used | Long Context, Thinking, Function Calling, Streaming |
| UI Pages | 39 |
| API Endpoints | 126+ (including SSE streaming) |
| Domain Entities | 5 |
| Design Patterns | 7 |
| Unit Tests | 57 |
