---
description: Design an end-to-end ML system from requirements using CRISP-DM methodology and MLOps best practices.
argument-hint: <description>
allowed-tools: Task, Skill
---

# Design ML System

Design a production-ready machine learning system based on the provided requirements.

## Workflow

### Step 1: Load Required Skills

Load these skills for comprehensive design guidance:

- `ml-project-lifecycle` - CRISP-DM methodology
- `model-selection` - Model comparison frameworks
- `token-budgeting` - Cost estimation (if LLM-based)

### Step 2: Spawn ML Architect Agent

Spawn the `ml-architect` agent with the following prompt:

```text
Design an end-to-end ML system for: $ARGUMENTS

Follow CRISP-DM methodology:
1. Business Understanding - Clarify objectives and success criteria
2. Data Understanding - Assess data requirements and availability
3. Data Preparation - Design data pipeline and feature engineering
4. Modeling - Select appropriate algorithms and architecture
5. Evaluation - Define metrics and validation approach
6. Deployment - Design serving infrastructure and MLOps

Provide a complete design document including:
- Architecture diagrams
- Technology recommendations (prefer Azure AI services and .NET)
- Cost estimates
- Implementation roadmap
- Risk assessment
```

### Step 3: Review and Refine

After receiving the design:

1. Verify the design addresses all CRISP-DM phases
2. Check that .NET/Azure technologies are recommended where appropriate
3. Validate cost estimates are realistic
4. Ensure MLOps considerations are included

### Step 4: Document Output

Save the design to an appropriate location if requested:

- `docs/architecture/ml/` for project architecture documentation
- Standalone markdown file for ad-hoc designs

## Example Usage

```bash
# Design a recommendation system
/ai-ml-planning:design-ml "product recommendation system for e-commerce platform with 1M daily users"

# Design a classification system
/ai-ml-planning:design-ml "customer churn prediction model for subscription service"

# Design an NLP system
/ai-ml-planning:design-ml "sentiment analysis pipeline for customer support tickets"
```

## Output Format

The design should include:

1. **Executive Summary** - High-level overview
2. **Business Requirements** - Objectives, metrics, constraints
3. **Data Architecture** - Sources, pipelines, feature stores
4. **Model Architecture** - Algorithms, training, serving
5. **Infrastructure Design** - Compute, storage, networking
6. **MLOps Strategy** - CI/CD, monitoring, retraining
7. **Cost Estimate** - Development and operational costs
8. **Risks and Mitigations** - Known risks and countermeasures
9. **Next Steps** - Prioritized implementation plan
