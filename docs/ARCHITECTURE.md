# Architecture — AI Governance Platform

## System Overview

```
+==================================================================================+
|                          AI GOVERNANCE PLATFORM                                   |
|                     Built on Gemini 3 Pro (1M Token Context)                      |
+==================================================================================+
|                                                                                   |
|  +---------------------------+    +------------------------------------------+   |
|  |     PRESENTATION LAYER    |    |           39 UI PAGES                    |   |
|  |                           |    |  Dashboard | AI Inventory | Compliance   |   |
|  |  Django Views + REST API  |    |  Assessment | Questionnaires | Risk      |   |
|  |  125+ API Endpoints       |    |  Digital Regulations | Agent Creation    |   |
|  +-------------|-------------+    +------------------------------------------+   |
|                |                                                                  |
|  +-------------|----------------------------------------------------------+       |
|  |          APPLICATION LAYER                                             |       |
|  |  Use Cases: GetDashboard | AIActChat | ComplianceScan | Autofill      |       |
|  |  DTOs: DashboardData | ScanResult | ChatResponse | FieldResult        |       |
|  +-------------|----------------------------------------------------------+       |
|                |                                                                  |
|  +-------------|----------------------------------------------------------+       |
|  |            DOMAIN LAYER                                                |       |
|  |  Entities: Agent | UseCase | Model | Dataset | Compliance              |       |
|  |  Services: AIActService | ComplianceService | GovernanceService        |       |
|  |  Repositories: IAgentRepo | IUseCaseRepo | IModelRepo | IDatasetRepo  |       |
|  +-------------|----------------------------------------------------------+       |
|                |                                                                  |
|  +-------------|----------------------------------------------------------+       |
|  |        INFRASTRUCTURE LAYER (Gemini 3 Pro Integration)                 |       |
|  |                                                                        |       |
|  |  +---------------------+  +------------------------+                   |       |
|  |  | AI Act Chat Service |  | Compliance Scanner     |                   |       |
|  |  | 751 lines           |  | Service - 473 lines    |                   |       |
|  |  |                     |  |                         |                   |       |
|  |  | Long Context:       |  | 8-Step Pipeline:       |                   |       |
|  |  | Full EU AI Act      |  | 1. Assess Risk Tier    |                   |       |
|  |  | (591KB) injected    |  | 2. Discover Skills     |                   |       |
|  |  | into system prompt  |  | 3. Load Checklist      |                   |       |
|  |  |                     |  | 4. Build Context       |                   |       |
|  |  | Function Calling:   |  | 5. Gemini 3 Analysis   |                   |       |
|  |  | 3 tools + 5 rounds  |  | 6. Format Report       |                   |       |
|  |  |                     |  | 7. Persist to File     |                   |       |
|  |  | SSE Streaming:      |  | 8. Return JSON         |                   |       |
|  |  | Real-time chunked   |  |                         |                   |       |
|  |  |                     |  | ThinkingLevel.HIGH     |                   |       |
|  |  | ThinkingLevel.HIGH  |  |                         |                   |       |
|  |  +---------------------+  +------------------------+                   |       |
|  |                                                                        |       |
|  |  +---------------------+  +------------------------+                   |       |
|  |  | Governance Agent    |  | Autofill Service       |                   |       |
|  |  | Service - 929 lines |  | 161 lines              |                   |       |
|  |  |                     |  |                         |                   |       |
|  |  | 123 Skills Library  |  | Document Extraction:   |                   |       |
|  |  | Risk Classification |  | PDF, DOCX, TXT, CSV    |                   |       |
|  |  | Article Mapping     |  | JSON, Markdown         |                   |       |
|  |  | Skill Recommendation|  |                         |                   |       |
|  |  | Report Generation   |  | AI Form Completion     |                   |       |
|  |  +---------------------+  +------------------------+                   |       |
|  |                                                                        |       |
|  |  +----------------------------------------------------------+         |       |
|  |  | Mock Repositories (JSON-based, swappable to database)     |         |       |
|  |  | AgentRepo | UseCaseRepo | ModelRepo | DatasetRepo         |         |       |
|  |  +----------------------------------------------------------+         |       |
|  +------------------------------------------------------------------------+       |
|                                                                                   |
+==================================================================================+
                                    |
                                    v
                    +-------------------------------+
                    |     GOOGLE GEMINI 3 PRO       |
                    |   gemini-3-pro-preview         |
                    |   1M Token Context Window      |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    |   REGULATION KNOWLEDGE BASE   |
                    |   267 files | 16 MB           |
                    |   93+ EU AI Act Articles       |
                    |   GDPR Articles               |
                    |   Related EU Directives        |
                    +-------------------------------+
```

---

## Clean Architecture (4 Layers)

### 1. Domain Layer (`governance/domain/`)

Contains core business logic and entities. No dependencies on external frameworks.

```
domain/
├── entities/          # Agent, UseCase, Model, Dataset, Compliance
├── repositories/      # Repository interfaces (contracts)
└── services/         # Domain services (cross-entity business logic)
```

- Pure business logic, no framework dependencies
- Entities are rich domain objects with business rules
- Repository interfaces define contracts (not implementations)

### 2. Application Layer (`governance/application/`)

Orchestrates domain objects to fulfill use cases.

```
application/
├── use_cases/        # GetDashboardDataUseCase, AIActChatUseCase, etc.
├── dtos/            # Data Transfer Objects
└── exceptions/      # Application exceptions
```

- Each use case = single user action
- DTOs transfer data between layers
- No direct database access

### 3. Infrastructure Layer (`governance/infrastructure/`)

Implements technical details — Gemini API services, data access, file I/O.

```
infrastructure/
├── services/        # Gemini AI Act, Scanner, Governance Agent, Autofill
└── repositories/    # Mock repositories (JSON-based, swappable to DB)
```

### 4. Presentation Layer (`governance/presentation/`)

Handles HTTP requests/responses, input validation, dependency injection.

```
presentation/
├── views/           # Django views (controllers)
└── dependency_injection.py
```

### Dependency Flow

```
Presentation --> Application --> Domain
     |                |
Infrastructure <------+
```

Inner layers (Domain) don't know about outer layers. Dependencies point inward.

---

## Design Patterns (7 Patterns)

| Pattern | Implementation |
|---------|---------------|
| Repository | Data access abstraction (swappable mock -> database) |
| Factory | Validated entity creation (AgentFactory) |
| Strategy | Interchangeable compliance frameworks |
| Dependency Injection | Centralized DependencyContainer |
| Use Case | Single-responsibility operations |
| DTO | Cross-layer data transfer |
| Domain Service | Cross-entity business logic |

---

## Multi-Step Agentic Flow

```
User: "Scan my facial recognition system for EU AI Act compliance"
  |
  v
[1] GOVERNANCE AGENT SERVICE (929 lines)
  |-- Classify Risk: "HIGH-RISK" (Biometric identification, Art. 6 Annex III)
  |-- Map Articles: Art. 9 (Risk Management), Art. 10 (Data Governance),
  |                 Art. 13 (Transparency), Art. 14 (Human Oversight)
  |-- Recommend Skills: bias-assessment, fria-assessment, hitl-design,
  |                     ai-transparency-labels, data-classification (12 skills)
  |-- Generate Assessment JSON
  |
  v
[2] COMPLIANCE SCANNER SERVICE (473 lines) -- 8 Steps
  |-- Step 1: Receive governance assessment
  |-- Step 2: Load specific skill content (SKILL.md files)
  |-- Step 3: Load high-risk compliance checklist
  |-- Step 4: Build enriched prompt (assessment + skills + checklist)
  |-- Step 5: Call Gemini 3 Pro API (JSON response mode)
  |-- Step 6: Generate professional markdown report
  |-- Step 7: Save report to /scan-reports/
  |-- Step 8: Return structured scan result
  |
  v
[3] OUTPUT: Comprehensive Compliance Report
  |-- Overall compliance score: 45/100
  |-- 12 specific findings with severity levels
  |-- Article-by-article gap analysis
  |-- Recommended remediation actions
  |-- Professional markdown report file
```

---

## Gemini 3 Features Used

```
+------------------------------------------------------------------+
|                    GEMINI 3 PRO FEATURES                          |
+------------------------------------------------------------------+
|                                                                    |
|  1. LONG CONTEXT (1M Tokens)                                      |
|     Full EU AI Act (591KB) injected into system instruction        |
|     Native reasoning over 181 articles -- no RAG needed            |
|                                                                    |
|  2. THINKING (Deep Reasoning)                                      |
|     ThinkingLevel.HIGH  -> Legal analysis, compliance scan         |
|     ThinkingLevel.MEDIUM -> Document extraction (autofill)         |
|     Chain-of-thought for precise legal interpretation              |
|                                                                    |
|  3. FUNCTION CALLING (Tool Use)                                    |
|     classify_ai_system_risk -> GovernanceAgentService              |
|     get_compliance_skills   -> 123 skills library                  |
|     run_compliance_scan     -> Quick compliance assessment         |
|     Up to 5 rounds of autonomous tool calls per query              |
|                                                                    |
|  4. STREAMING (SSE)                                                |
|     Server-Sent Events for real-time chat responses                |
|     Inline tool-use notifications                                  |
|     Animated cursor during streaming                               |
|                                                                    |
+------------------------------------------------------------------+
```

---

## AI Act Chat Service — Internal Architecture (751 lines)

```
GeminiAIActService
|-- __init__()           -> Client init, function tools, session storage
|-- _load_full_text()    -> Load EU AI Act (591KB) for long context
|
|-- EXTRACTED HELPERS (DRY -- used by both query() and query_stream())
|   |-- _build_system_instruction(full_text) -> System prompt builder
|   |-- _create_chat_session(chat_id)        -> Session bootstrap + config
|   |-- _handle_function_calling_loop()      -> Multi-round tool execution
|   |-- _extract_function_calls(response)    -> Parse tool calls from response
|   |-- _cleanup_session(chat_id)            -> Remove dead sessions
|   +-- _track_message(chat_id, role, text)  -> Conversation history
|
|-- PUBLIC API
|   |-- query(request)        -> Standard JSON response
|   |-- query_stream(request) -> SSE streaming generator
|   +-- _format_response()    -> Build AIActQueryResponse
|
+-- FUNCTION CALLING TOOLS (module-level)
    |-- _build_function_declarations()  -> 3 FunctionDeclaration objects
    |-- _execute_function_call()        -> Dispatcher
    |-- _tool_classify_risk()           -> GovernanceAgentService
    |-- _tool_get_skills()              -> 123 skills library
    +-- _tool_run_scan()                -> Quick compliance scan
```

---

## Why This Is NOT a Prompt Wrapper

| Single Prompt App | Our Platform |
|-------------------|--------------|
| 1 API call | 4+ independent Gemini calls per workflow |
| Static system prompt | Dynamic prompts enriched with governance context |
| No state | Multi-turn chat with conversation history |
| No tools | 3 function calling tools + 123 governance skills |
| No thinking | ThinkingLevel.HIGH for deep legal reasoning |
| No streaming | SSE streaming with tool-use notifications |
| No pipeline | 8-step autonomous scanning pipeline |
| Simple UI | 39 pages, 126+ API endpoints |
| ~50 lines of code | 2,314 lines across 4 Gemini services |
