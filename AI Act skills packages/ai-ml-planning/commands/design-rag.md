---
description: Design a Retrieval-Augmented Generation (RAG) pipeline including chunking, embedding, retrieval, and context assembly strategies.
argument-hint: <description>
allowed-tools: Task, Skill
---

# Design RAG System

Design a production-ready RAG (Retrieval-Augmented Generation) pipeline based on the provided requirements.

## Workflow

### Step 1: Load Required Skills

Load these skills for comprehensive design guidance:

- `rag-architecture` - RAG pipeline patterns
- `model-selection` - Embedding and LLM selection
- `token-budgeting` - Cost estimation

### Step 2: Gather Requirements

If not clear from the description, clarify:

- What documents/content will be indexed?
- What queries will users ask?
- What are the latency requirements?
- What is the expected query volume?
- Are there accuracy/relevance targets?

### Step 3: Design RAG Pipeline

Design each component:

#### Indexing Pipeline

1. **Document Ingestion** - Sources, formats, refresh frequency
2. **Chunking Strategy** - Method, size, overlap
3. **Embedding Model** - Selection, dimensions, cost
4. **Vector Store** - Provider, index configuration

#### Query Pipeline

1. **Query Processing** - Expansion, rewriting
2. **Retrieval Method** - Vector, hybrid, multi-query
3. **Reranking** - Cross-encoder, reciprocal rank fusion
4. **Context Assembly** - Window management, prioritization

#### Generation

1. **LLM Selection** - Model, parameters
2. **Prompt Design** - Template, few-shot examples
3. **Citation** - Source attribution

### Step 4: Document Architecture

Create a design document including:

- Architecture diagram
- Component specifications
- Performance targets
- Cost projections
- Implementation plan

## Example Usage

```bash
# Design a documentation Q&A system
/ai-ml-planning:design-rag "Q&A system for technical documentation with 10,000 pages"

# Design a knowledge base chatbot
/ai-ml-planning:design-rag "customer support chatbot with product manuals and FAQ"

# Design a research assistant
/ai-ml-planning:design-rag "legal research assistant for case law and regulations"
```

## Output Format

```markdown
# RAG Architecture: [Name]

## Overview
[System purpose and scope]

## Document Processing

### Sources
| Source | Format | Size | Refresh |
|--------|--------|------|---------|

### Chunking Strategy
- Method: [Strategy]
- Chunk Size: [N tokens]
- Overlap: [N%]
- Rationale: [Why]

### Embedding
- Model: [Model name]
- Dimensions: [N]
- Cost: $[X] per 1M tokens

## Vector Store

### Provider
- Choice: [Provider]
- Justification: [Why]

### Index Configuration
- Similarity: [Metric]
- Index Type: [HNSW/etc]
- Metadata: [Fields]

## Retrieval Strategy

### Method
- Type: [Vector/Hybrid/Multi-query]
- Top-K: [N]
- Filters: [Metadata filters]

### Reranking
- Method: [Cross-encoder/RRF/None]
- Model: [If applicable]

## Generation

### LLM
- Model: [Selection]
- Temperature: [Value]
- Max Tokens: [Value]

### Prompt Template
[Template structure]

## Performance Targets
| Metric | Target |
|--------|--------|
| Retrieval Latency | < [X]ms |
| E2E Latency | < [X]s |
| Relevance@10 | > [X]% |
| Answer Accuracy | > [X]% |

## Cost Projection
| Component | Monthly Cost |
|-----------|--------------|
| Embeddings | $[X] |
| Vector Store | $[X] |
| LLM | $[X] |
| **Total** | $[X] |

## Architecture Diagram
[Mermaid diagram]

## Implementation Plan
1. [Phase 1]
2. [Phase 2]
3. [Phase 3]
```
