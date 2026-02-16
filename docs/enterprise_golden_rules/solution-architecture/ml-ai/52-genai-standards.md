# GenAI Agent Governance Standards

> **Document Owner:** ML Engineering | **Status:** Approved | **Last Updated:** February 2026

## Overview

**Governance and lifecycle standards** for GenAI agents on Databricks. This document covers the WHAT - requirements, thresholds, and compliance checkpoints.

For implementation patterns (code examples), see [51-genai-agent-patterns.md](51-genai-agent-patterns.md).

---

## Golden Rules

| ID | Rule | Severity |
|----|------|----------|
| **ML-08** | Evaluate managed services before custom development | Critical |
| **ML-09** | Create evaluation dataset before development | Critical |
| **ML-10** | Pass LLM judge thresholds before production | Critical |
| **ML-11** | Register all models in Unity Catalog | Critical |
| **ML-12** | Enable production monitoring | Required |
| **ML-13** | Version prompts in Unity Catalog | Required |

---

## Managed Services Decision Framework

**Always evaluate managed services FIRST. Document justification for custom development.**

```
┌─────────────────────────────────────────────────────────────┐
│ Can Knowledge Assistant or Agent Bricks solve the problem? │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
         ┌─────┐                       ┌─────┐
         │ YES │                       │ NO  │
         └──┬──┘                       └──┬──┘
            │                             │
            ▼                             ▼
   Use Managed Service            Build Custom Agent
   (No custom code)               (Full compliance required)
```

### Managed Service Capabilities

| Service | Use Case | Capabilities |
|---------|----------|--------------|
| **Knowledge Assistant** | Document Q&A | Vector search, RAG, UC integration |
| **Multi Agent Supervisor** | Complex workflows | Agent orchestration, handoffs, routing |
| **Genie Spaces** | Data analytics | Natural language to SQL, semantic layer |
| **AI Playground** | Prototyping | Model comparison, prompt testing |

### Custom Development Justification

When choosing custom over managed, document:
1. Which managed services were evaluated
2. Why they don't meet requirements
3. Specific capability gaps
4. Maintenance ownership commitment

---

## Evaluation Dataset Requirements

**Create evaluation dataset BEFORE development begins.**

### Dataset Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `inputs` | dict[Any, Any] | Yes | Agent inputs (query, context) |
| `expectations.expected_response` | str | No | Ground truth answer |
| `expectations.expected_facts` | list[str] | No | Facts that must appear |
| `expectations.guidelines` | str | No | Rules agent must follow |

### Minimum Dataset Size

| Environment | Minimum Records | Coverage |
|-------------|-----------------|----------|
| Development | 50 | Core use cases |
| Staging | 200 | Edge cases included |
| Production | 500+ | Full domain coverage |

### Dataset Creation

```python
import mlflow.genai.datasets as datasets

eval_dataset = datasets.create_dataset(
    name="agent_eval_v1",
    source="catalog.schema.eval_records"
)
```

---

## LLM Judge Thresholds

**All thresholds MUST pass before production deployment.**

| Judge | Threshold | Blocking | Purpose |
|-------|-----------|----------|---------|
| **Safety** | 100% | Yes | No harmful content |
| **Relevance** | ≥ 0.80 | Yes | Query-response alignment |
| **Groundedness** | ≥ 0.70 | Yes | Factual accuracy |
| **Guidelines** | ≥ 0.70 | Yes | Policy compliance |

### Built-in Judges

| Judge | Evaluates |
|-------|-----------|
| `Relevance()` | Is response relevant to the query? |
| `Groundedness()` | Is response factually grounded in context? |
| `Safety()` | Does response contain harmful content? |
| `Guidelines(text)` | Does response follow specified guidelines? |

### Custom Judges

Create domain-specific judges for specialized evaluation:

```python
from mlflow.genai.scorers import scorer

@scorer
def sql_accuracy(outputs, expectations):
    """Verify generated SQL returns correct results."""
    generated = outputs.get("sql_query")
    expected = expectations.get("expected_sql")
    # Custom comparison logic
    return accuracy_score
```

---

## Unity Catalog Model Registration

**All production agents MUST be registered in Unity Catalog.**

### Naming Convention

```
{catalog}.{schema}.{agent_name}

Examples:
- prod_catalog.agents.data_platform_agent
- prod_catalog.agents.cost_analyzer_v2
```

### Required Metadata

| Metadata | Required | Example |
|----------|----------|---------|
| Description | Yes | "Multi-domain data platform agent" |
| Tags | Yes | `domain:platform`, `team:ml-eng` |
| Aliases | Recommended | `Champion`, `Challenger` |

### Registration Benefits

- Centralized access control (GRANT/REVOKE)
- Version management with aliases
- Lineage tracking to training data
- Deployment governance
- Audit trail for compliance

---

## Production Monitoring Requirements

### Online Evaluation

| Metric | Sample Rate | Alert Threshold |
|--------|-------------|-----------------|
| Safety | 100% | Any failure |
| Relevance | 10% | < 0.70 avg |
| Latency | 100% | P95 > 30s |
| Error Rate | 100% | > 5% |

### Scorer Lifecycle

| State | Description |
|-------|-------------|
| Registered | Scorer defined but not running |
| Active | Evaluating traces at sample_rate |
| Stopped | sample_rate = 0, scorer preserved |
| Deleted | Permanently removed |

### Backfill Requirements

When deploying new scorers, backfill historical traces:
- Minimum: 30 days
- Recommended: 90 days

---

## Memory & State Standards

### Memory Architecture

| Layer | Storage | TTL | Purpose |
|-------|---------|-----|---------|
| Short-term | CheckpointSaver | Session | Conversation context |
| Long-term | DatabricksStore | 90 days | User preferences |

### Requirements

- Graceful degradation when memory unavailable
- No PII in long-term storage without encryption
- Session isolation (no cross-user leakage)

---

## Prompt Management Standards

### Storage

All prompts MUST be stored in Unity Catalog tables:

```sql
CREATE TABLE prod_catalog.prompts.agent_prompts (
    prompt_key STRING,
    prompt_text STRING,
    version INT,
    created_at TIMESTAMP,
    created_by STRING
);
```

### Versioning

- Track all prompt changes with version numbers
- Log prompt versions used in each run
- Enable rollback to previous versions

### Review Process

| Change Type | Review Required |
|-------------|-----------------|
| New prompt | Tech lead approval |
| Minor edit | Peer review |
| Major rewrite | Tech lead + evaluation |

---

## Compliance Checkpoints

### Before Development

- [ ] Evaluated Knowledge Assistant for RAG use cases
- [ ] Evaluated Multi Agent Supervisor for workflows
- [ ] Evaluated Genie Spaces for analytics
- [ ] Documented justification for custom development
- [ ] Created evaluation dataset (min 50 records)
- [ ] Defined success criteria and thresholds

### Before Staging

- [ ] Evaluation dataset expanded (min 200 records)
- [ ] All LLM judge thresholds passing
- [ ] MLflow Tracing enabled and verified
- [ ] Model registered in Unity Catalog
- [ ] Prompts stored in UC with versioning
- [ ] Memory fallback tested

### Before Production

- [ ] Evaluation dataset at scale (min 500 records)
- [ ] Safety scoring at 100%
- [ ] Production monitoring configured
- [ ] Historical backfill completed (30+ days)
- [ ] Runbook documented
- [ ] On-call rotation assigned
- [ ] Rollback procedure tested

---

## Exception Process

For threshold exceptions:
1. Document specific use case requiring exception
2. Provide alternative mitigation (e.g., human review)
3. Set review date (max 90 days)
4. Obtain VP-level approval

---

## References

- [Knowledge Assistant](https://docs.databricks.com/generative-ai/knowledge-assistant/)
- [Agent Bricks](https://docs.databricks.com/generative-ai/agent-bricks/)
- [Evaluation Datasets](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/concepts/eval-datasets)
- [Production Quality Monitoring](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/concepts/production-quality-monitoring)
- [MLflow Tracing](https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/tracing/)
