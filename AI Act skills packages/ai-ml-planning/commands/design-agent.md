---
description: Design an agentic AI workflow including orchestration patterns, tool design, memory management, and error handling.
argument-hint: <description>
allowed-tools: Task, Skill
---

# Design Agentic Workflow

Design an autonomous AI agent system based on the provided requirements.

## Workflow

### Step 1: Load Required Skills

Load these skills for comprehensive design guidance:

- `agentic-workflow-design` - Orchestration patterns
- `prompt-engineering` - Agent prompts
- `ai-safety-planning` - Guardrails
- `token-budgeting` - Cost estimation

### Step 2: Gather Requirements

If not clear from the description, clarify:

- What is the agent's primary objective?
- What level of autonomy is required?
- What actions should the agent be able to take?
- What are the safety/approval requirements?
- What is the expected usage pattern?

### Step 3: Select Architecture Pattern

Based on requirements, recommend:

| Pattern | Use When |
|---------|----------|
| ReAct | Simple, single-turn tasks |
| Plan-Execute | Complex, multi-step tasks |
| Multi-Agent | Parallel, specialized tasks |
| Hierarchical | Complex, interdependent tasks |

### Step 4: Design Components

#### Agent Definition

- Role and responsibilities
- Model selection
- System prompt
- Available tools

#### Tool Design

- Tool inventory
- Input/output schemas
- Error handling
- Rate limits

#### Memory Strategy

- Working memory (context)
- Episodic memory (history)
- Semantic memory (knowledge)

#### Orchestration

- Control flow
- State management
- Handoff protocols

#### Safety

- Guardrails
- Approval gates
- Audit logging

### Step 5: Document Architecture

Create comprehensive design documentation.

## Example Usage

```bash
# Design a research agent
/ai-ml-planning:design-agent "autonomous research agent that finds and summarizes academic papers"

# Design a coding assistant
/ai-ml-planning:design-agent "code review agent that analyzes PRs and suggests improvements"

# Design a data analyst
/ai-ml-planning:design-agent "data analysis agent that queries databases and generates reports"
```

## Output Format

```markdown
# Agentic System Design: [Name]

## Overview
- **Purpose**: [What the agent does]
- **Autonomy Level**: [Full/Supervised/Assisted]
- **Pattern**: [ReAct/Plan-Execute/Multi-Agent/Hierarchical]

## Agent Architecture

### Primary Agent
- **Role**: [Description]
- **Model**: [Selection]
- **System Prompt**: [Summary]

### Worker Agents (if multi-agent)
| Agent | Role | Model | Tools |
|-------|------|-------|-------|

## Tool Inventory

| Tool | Purpose | Input | Output | Safety |
|------|---------|-------|--------|--------|

### Tool Schemas
[JSON schemas for each tool]

## Memory Architecture

### Working Memory
- Context window: [Tokens]
- Summarization: [Strategy]

### Episodic Memory
- Storage: [Approach]
- Retention: [Policy]

### Semantic Memory
- Knowledge base: [Approach]
- RAG integration: [If applicable]

## Orchestration Flow

[Mermaid sequence/flowchart diagram]

### State Transitions
| State | Trigger | Next State |
|-------|---------|------------|

## Safety and Guardrails

### Input Guards
| Guard | Purpose | Implementation |
|-------|---------|----------------|

### Output Filters
| Filter | Purpose | Implementation |
|--------|---------|----------------|

### Approval Gates
| Action | Requires Approval | Approver |
|--------|-------------------|----------|

### Audit Logging
[Logging strategy]

## Error Handling

### Retry Policy
- Max attempts: [N]
- Backoff: [Strategy]

### Fallback Strategy
[Approach for failures]

### Escalation
[When to escalate to human]

## Cost Projection

| Component | Est. Tokens/Request | Monthly Cost |
|-----------|---------------------|--------------|

## Monitoring

### Metrics
| Metric | Target |
|--------|--------|

### Alerting
| Condition | Severity | Action |
|-----------|----------|--------|

## Implementation Plan
1. [Phase 1]
2. [Phase 2]
3. [Phase 3]
```
