---
description: Estimate AI/ML costs including token usage, model pricing, infrastructure, and optimization opportunities.
argument-hint: <description>
allowed-tools: Task, Skill
---

# Estimate AI/ML Costs

Generate a comprehensive cost estimate for an AI/ML system.

## Workflow

### Step 1: Load Required Skills

Load these skills for accurate estimation:

- `token-budgeting` - Token and cost calculations
- `model-selection` - Model pricing comparison
- `rag-architecture` - RAG cost components (if applicable)

### Step 2: Gather Usage Parameters

Collect or estimate:

- **Volume**: Requests per day/month
- **Token Profile**: Average input/output tokens per request
- **Model Requirements**: Quality, latency, features needed
- **Growth**: Expected usage growth rate

### Step 3: Calculate Direct Costs

#### LLM Costs

```text
Monthly LLM Cost = (Input Tokens x Input Price) + (Output Tokens x Output Price)
                 = (Requests x Avg Input) x ($/1M) + (Requests x Avg Output) x ($/1M)
```

#### Embedding Costs (if RAG)

```text
Monthly Embedding Cost = Documents Indexed x Tokens per Doc x Embedding Price
                       + Queries x Query Tokens x Embedding Price
```

#### Vector Storage Costs (if RAG)

```text
Monthly Storage = Documents x Dimensions x 4 bytes x Storage Price
```

### Step 4: Calculate Indirect Costs

- Development and testing usage (~15-25% of production)
- Error handling and retries (~5-10%)
- Monitoring and observability
- Infrastructure (compute, network)

### Step 5: Identify Optimization Opportunities

- Prompt caching potential
- Batch processing savings
- Model cascading strategy
- Smaller model for simple tasks

### Step 6: Generate Cost Report

Create detailed projection with scenarios.

## Example Usage

```bash
# Estimate costs for a chatbot
/ai-ml-planning:estimate-cost "customer support chatbot with 10,000 daily conversations"

# Estimate costs for a RAG system
/ai-ml-planning:estimate-cost "document Q&A system with 50,000 documents and 5,000 daily queries"

# Estimate costs for an agent system
/ai-ml-planning:estimate-cost "autonomous research agent making 100 tool calls per session"
```

## Output Format

```markdown
# AI Cost Estimate: [System Name]

## Executive Summary

| Metric | Value |
|--------|-------|
| Monthly Cost (Expected) | $[X] |
| Annual Cost (Expected) | $[X] |
| Cost per Request | $[X.XXXX] |

---

## Usage Assumptions

### Volume
| Period | Requests | Growth Rate |
|--------|----------|-------------|
| Month 1 | [N] | - |
| Month 6 | [N] | [X%] |
| Year 1 | [N] | [X%] |

### Token Profile
| Component | Tokens | Notes |
|-----------|--------|-------|
| System Prompt | [N] | [Notes] |
| User Input (avg) | [N] | [Notes] |
| Context/RAG | [N] | [Notes] |
| Output (avg) | [N] | [Notes] |
| **Total/Request** | [N] | |

---

## Model Selection

### Primary Model
- **Model**: [Name]
- **Input**: $[X]/1M tokens
- **Output**: $[X]/1M tokens
- **Rationale**: [Why]

### Alternative Considered
| Model | Input | Output | Trade-off |
|-------|-------|--------|-----------|

---

## Cost Breakdown

### LLM Costs
| Component | Monthly Volume | Unit Cost | Monthly Cost |
|-----------|----------------|-----------|--------------|
| Input Tokens | [N]M | $[X]/M | $[X] |
| Output Tokens | [N]M | $[X]/M | $[X] |
| Cached Input | [N]M | $[X]/M | $[X] |
| **Subtotal** | | | **$[X]** |

### Embedding Costs (if applicable)
| Component | Volume | Unit Cost | Monthly Cost |
|-----------|--------|-----------|--------------|
| Document Embedding | [N] docs | $[X] | $[X] |
| Query Embedding | [N] queries | $[X] | $[X] |
| **Subtotal** | | | **$[X]** |

### Infrastructure Costs (if applicable)
| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| Vector Store | [Spec] | $[X] |
| Compute | [Spec] | $[X] |
| Storage | [Spec] | $[X] |
| **Subtotal** | | **$[X]** |

### Overhead
| Category | % of Base | Cost |
|----------|-----------|------|
| Development/Testing | 15% | $[X] |
| Retries/Errors | 5% | $[X] |
| Monitoring | 2% | $[X] |
| **Subtotal** | | **$[X]** |

### Total Monthly Cost: **$[X]**

---

## Scenario Analysis

| Scenario | Volume | Monthly Cost | Annual Cost |
|----------|--------|--------------|-------------|
| Conservative (70%) | [N] | $[X] | $[X] |
| Expected (100%) | [N] | $[X] | $[X] |
| Growth (150%) | [N] | $[X] | $[X] |
| Viral (500%) | [N] | $[X] | $[X] |

---

## Optimization Opportunities

### Prompt Caching
- **Potential Savings**: [X]%
- **Implementation**: [Approach]
- **Estimated Monthly Savings**: $[X]

### Model Cascading
- **Potential Savings**: [X]%
- **Implementation**: Use [smaller model] for [X]% of requests
- **Estimated Monthly Savings**: $[X]

### Batch Processing
- **Potential Savings**: [X]%
- **Implementation**: [Approach]
- **Estimated Monthly Savings**: $[X]

### Total Optimization Potential: **$[X]/month ([Y]%)**

---

## Budget Recommendations

### Thresholds
| Threshold | Daily | Monthly | Action |
|-----------|-------|---------|--------|
| Warning | $[X] | $[X] | Alert team |
| Critical | $[X] | $[X] | Throttle/review |
| Limit | $[X] | $[X] | Block new requests |

### Monitoring
- Dashboard: [Recommendation]
- Alerting: [Configuration]
- Review cadence: [Frequency]

---

## Assumptions and Risks

### Key Assumptions
1. [Assumption 1]
2. [Assumption 2]

### Cost Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk] | [Impact] | [Mitigation] |

---

## Pricing Sources
- [Model pricing as of [Date]]
- [Infrastructure pricing as of [Date]]

*Note: Prices subject to change. Verify current pricing before finalizing budget.*
```
