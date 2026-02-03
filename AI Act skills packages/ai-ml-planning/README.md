# AI/ML Planning Plugin

AI/ML project planning methodologies for designing AI systems **before development begins**. This plugin provides structured approaches for ML lifecycle planning, prompt engineering, RAG architecture, model selection, AI safety, and agentic workflow design.

## Installation

```bash
/plugin install ai-ml-planning@claude-code-plugins
```

## Skills

| Skill | Description |
|-------|-------------|
| `ml-project-lifecycle` | CRISP-DM, TDSP, MLOps maturity planning |
| `prompt-engineering` | Prompt design, testing, versioning strategies |
| `rag-architecture` | Chunking, embedding, retrieval pipeline design |
| `model-selection` | Capability matching, model comparison frameworks |
| `ai-safety-planning` | Alignment, guardrails, safety evaluation |
| `bias-assessment` | Fairness evaluation, bias detection frameworks |
| `explainability-planning` | XAI requirements, interpretability patterns |
| `hitl-design` | Human-in-the-loop, oversight patterns |
| `token-budgeting` | Cost estimation, token optimization |
| `agentic-workflow-design` | Multi-agent orchestration, tool design |

## Commands

| Command | Description |
|---------|-------------|
| `/ai-ml-planning:design-ml` | Design ML system from requirements |
| `/ai-ml-planning:design-rag` | Design RAG pipeline architecture |
| `/ai-ml-planning:design-agent` | Design agentic workflow |
| `/ai-ml-planning:assess-safety` | Conduct AI safety assessment |
| `/ai-ml-planning:estimate-cost` | Estimate AI/ML costs and tokens |

## Agents

| Agent | Description |
|-------|-------------|
| `ml-architect` | Designs end-to-end ML systems |
| `prompt-engineer` | Optimizes prompts and evaluates quality |
| `ai-safety-reviewer` | Reviews AI systems for safety and alignment |

## Use Cases

### Designing an ML System

```bash
# Plan ML project lifecycle
/ai-ml-planning:design-ml customer churn prediction model

# Design RAG for knowledge base
/ai-ml-planning:design-rag product documentation Q&A system
```

### Designing Agentic Systems

```bash
# Design multi-agent workflow
/ai-ml-planning:design-agent customer service automation

# Estimate costs
/ai-ml-planning:estimate-cost for 1M daily API calls
```

### Safety Assessment

```bash
# Conduct safety review
/ai-ml-planning:assess-safety for medical diagnosis assistant
```

## Methodology Coverage

### ML Project Lifecycle

- CRISP-DM phases (Business Understanding → Deployment)
- Team Data Science Process (TDSP)
- MLOps maturity levels
- Experiment tracking patterns

### Prompt Engineering

- Prompt design patterns (zero-shot, few-shot, CoT)
- Prompt testing frameworks
- Prompt versioning and management
- Evaluation metrics

### RAG Architecture

- Document chunking strategies
- Embedding model selection
- Vector store design
- Retrieval optimization
- Context assembly patterns

### Model Selection

- Task-capability matching
- Model comparison frameworks
- Benchmark interpretation
- Cost-performance tradeoffs

### AI Safety

- EU AI Act risk classification
- NIST AI RMF alignment
- Guardrail implementation
- Red teaming strategies
- Safety evaluation

### Bias Assessment

- Fairness metrics (demographic parity, equalized odds)
- Bias detection techniques
- Mitigation strategies
- Documentation requirements

### Explainability

- XAI requirements by domain
- Local vs global explanations
- SHAP, LIME, attention visualization
- Regulatory requirements

### Human-in-the-Loop

- Review workflow design
- Escalation patterns
- Feedback loops
- Quality assurance

### Token Budgeting

- Cost estimation formulas
- Token optimization techniques
- Context window management
- Batch processing strategies

### Agentic Workflows

- Multi-agent architectures
- Tool design patterns
- Orchestration strategies
- Error handling and recovery

## Integration with Other Plugins

- **systems-design**: Distributed systems patterns for ML
- **compliance-planning**: AI governance alignment
- **data-architecture**: Data pipeline design
- **security**: AI security considerations

## .NET/C# Examples

This plugin provides examples using:

- Semantic Kernel for orchestration
- Azure AI Foundry SDK
- Microsoft.ML for traditional ML
- OpenAI/Azure OpenAI SDKs

## License

MIT - see [LICENSE](../../LICENSE)
