# 01 - Introduction

## Purpose

This document defines the architecture for the **Databricks Health Monitor Agent System** - a production-grade multi-agent system that provides intelligent, conversational access to platform health data. The system showcases Databricks and MLflow best practices while delivering actionable insights across five domains: Cost, Security, Performance, Reliability, and Data Quality.

## Scope

### In Scope

- **Orchestrator Agent**: Supervisor that classifies intent and coordinates worker agents
- **Worker Agents**: 5 domain specialists that query Genie Spaces
- **Genie Integration**: Sole data interface for all structured data queries
- **Utility Tools**: Web search, dashboard linking, alert triggering, runbook retrieval
- **Memory Management**: Short-term conversation context and long-term user preferences
- **MLflow Integration**: Tracing, evaluation, prompt registry, agent logging
- **Deployment**: Model Serving endpoint with Databricks Apps frontend

### Out of Scope

- Direct TVF/Metric View/ML table calls from agents
- Custom embedding models (using Databricks-provided)
- Real-time streaming agent responses (batch mode only)
- Multi-tenant deployment (single workspace focus)

## Prerequisites

### Completed Components (Phases 1-3)

The agent system requires the following components to be deployed:

| Component | Count | Status | Documentation |
|-----------|-------|--------|---------------|
| Gold Layer Tables | 37 | Required | [Gold Layer Design](../../gold_layer_design/) |
| Table-Valued Functions | 60 | Required | [Phase 3.2](../../plans/phase3-addendum-3.2-tvfs.md) |
| Metric Views | 10 | Required | [Phase 3.3](../../plans/phase3-addendum-3.3-metric-views.md) |
| ML Models | 25 | Required | [Phase 3.1](../../plans/phase3-addendum-3.1-ml-models.md) |
| Lakehouse Monitors | 10 | Required | [Phase 3.4](../../plans/phase3-addendum-3.4-lakehouse-monitoring.md) |
| AI/BI Dashboards | 11 | Required | [Phase 3.5](../../plans/phase3-addendum-3.5-ai-bi-dashboards.md) |
| Genie Spaces | 6 | Required | [Phase 3.6](../../plans/phase3-addendum-3.6-genie-spaces.md) |
| SQL Alerts | TBD | Optional | [Phase 3.7](../../plans/phase3-addendum-3.7-alerting-framework.md) |

### Infrastructure Requirements

| Requirement | Specification |
|-------------|---------------|
| Databricks Runtime | 15.4 LTS ML or higher |
| Unity Catalog | Enabled with catalog/schema permissions |
| Model Serving | Serverless endpoints enabled |
| Genie | Enabled for workspace |
| MLflow | Version 3.0+ (mlflow>=3.0.0) |
| Python | 3.10+ |

### Required Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| USE CATALOG | `health_monitor` | Access to Gold layer |
| USE SCHEMA | `health_monitor.gold` | Query tables and functions |
| EXECUTE FUNCTION | All TVFs | Genie uses TVFs internally |
| SELECT | Metric Views | Genie queries metric views |
| SELECT | ML prediction tables | Genie accesses predictions |
| Genie Space Access | All 6 spaces | Agent queries via Genie |
| Model Serving | Create/Manage | Deploy agent endpoint |

## Best Practices Matrix

This implementation showcases **14 of 14** Databricks Agent Best Practices:

| # | Best Practice | Implementation | Document |
|---|---------------|----------------|----------|
| 1 | **Multi-Agent Architecture** | LangGraph supervisor with 5 domain workers | [03-orchestrator](03-orchestrator-agent.md) |
| 2 | **Genie Space Integration** | All data queries via 6 Genie Spaces | [05-genie](05-genie-integration.md) |
| 3 | **MLflow 3.0 Tracing** | Automatic + manual instrumentation | [08-tracing](08-mlflow-tracing.md) |
| 4 | **LLM Judges** | Built-in + 5 custom domain judges | [09-evaluation](09-evaluation-and-judges.md) |
| 5 | **Prompt Registry** | Versioned prompts with aliases | [10-prompt](10-prompt-registry.md) |
| 6 | **Agent Logging** | ChatAgent + Model Registry | [11-logging](11-agent-logging.md) |
| 7 | **Lakebase Memory** | Short-term (24h) + Long-term (1yr) | [07-memory](07-memory-management.md) |
| 8 | **Model Serving** | Serverless endpoint | [13-deployment](13-deployment-and-monitoring.md) |
| 9 | **On-behalf-of-user Auth** | Genie respects user permissions | [05-genie](05-genie-integration.md) |
| 10 | **Production Monitoring** | Traces, metrics, alerts | [13-deployment](13-deployment-and-monitoring.md) |
| 11 | **Evaluation Pipeline** | Synthetic test sets, scorers | [09-evaluation](09-evaluation-and-judges.md) |
| 12 | **Unity Catalog Governance** | Data via Genie only | [05-genie](05-genie-integration.md) |
| 13 | **MCP Integration** | Model Context Protocol ready | [06-utility](06-utility-tools.md) |
| 14 | **Databricks Apps Frontend** | Streamlit chat interface | [13-deployment](13-deployment-and-monitoring.md) |

## Tool Architecture

### Design Principle

> **Agents query data ONLY through Genie Spaces.**
> TVFs, Metric Views, and ML tables are abstracted behind Genie.
> This ensures governance, permission inheritance, and natural language flexibility.

### Tool Inventory (10 Total)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT TOOLS (10 Total)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GENIE SPACE TOOLS (6) - All Data Queries                                  │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                     │
│  │ cost_genie    │ │ security_genie│ │ performance   │                     │
│  │               │ │               │ │ _genie        │                     │
│  │ Abstracts:    │ │ Abstracts:    │ │ Abstracts:    │                     │
│  │ • 15 TVFs     │ │ • 10 TVFs     │ │ • 16 TVFs     │                     │
│  │ • 2 Metrics   │ │ • 2 Metrics   │ │ • 3 Metrics   │                     │
│  │ • 6 ML Models │ │ • 4 ML Models │ │ • 7 ML Models │                     │
│  └───────────────┘ └───────────────┘ └───────────────┘                     │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                     │
│  │ reliability   │ │ quality_genie │ │ unified_genie │                     │
│  │ _genie        │ │               │ │               │                     │
│  │ Abstracts:    │ │ Abstracts:    │ │ Cross-domain  │                     │
│  │ • 12 TVFs     │ │ • 7 TVFs      │ │ queries for   │                     │
│  │ • 1 Metric    │ │ • 2 Metrics   │ │ orchestrator  │                     │
│  │ • 5 ML Models │ │ • 3 ML Models │ │               │                     │
│  └───────────────┘ └───────────────┘ └───────────────┘                     │
│                                                                             │
│  UTILITY TOOLS (4) - Actions and External Data                             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   │
│  │ web_search    │ │ dashboard     │ │ alert_trigger │ │ runbook_rag   │   │
│  │               │ │ _linker       │ │               │ │               │   │
│  │ • Databricks  │ │ • Generate    │ │ • Trigger SQL │ │ • Retrieve    │   │
│  │   status page │ │   dashboard   │ │   alerts      │ │   remediation │   │
│  │ • Docs lookup │ │   deep links  │ │ • Framework   │ │   steps       │   │
│  │ • Real-time   │ │ • 11 AI/BI    │ │   (to build)  │ │ • Vector      │   │
│  │   information │ │   dashboards  │ │               │ │   search      │   │
│  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Genie-Only Data Access?

| Benefit | Description |
|---------|-------------|
| **Permission Inheritance** | Genie respects Unity Catalog permissions via on-behalf-of-user auth |
| **Natural Language Flexibility** | Users can ask questions in any form; Genie interprets |
| **Abstraction** | Agents don't need to know TVF signatures or table schemas |
| **Governance** | All data access is logged, tracked, and auditable |
| **Maintainability** | Add new TVFs/metrics without changing agent code |
| **Consistency** | Same response format regardless of underlying data source |

## Development Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. Environment Setup | 2 days | Dependencies, Genie access, Lakebase tables |
| 2. Orchestrator Agent | 1 week | LangGraph supervisor, intent classification |
| 3. Worker Agents | 1 week | 5 domain specialists + Genie integration |
| 4. Utility Tools | 3 days | Web search, dashboard linker, RAG, alerts |
| 5. Memory Integration | 3 days | Lakebase short/long-term memory |
| 6. MLflow Integration | 1 week | Tracing, logging, prompt registry |
| 7. Evaluation Pipeline | 3 days | LLM judges, evaluation sets |
| 8. Deployment | 2 days | Model Serving, Apps frontend |
| **Total** | **~5 weeks** | Production-ready agent system |

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Data queries via Genie | 100% | 0 direct TVF/table calls |
| MLflow trace coverage | 100% | All operations traced |
| Intent classification accuracy | >90% | Evaluation dataset |
| Response relevance | >85% | LLM judge scores |
| Response latency (P95) | <10s | Production monitoring |
| Evaluation coverage | 5 domains | Custom judges per domain |
| Uptime | 99.5% | Model Serving metrics |

## Document Conventions

### Code Examples

All code examples are:
- **Production-ready**: Can be copied directly into notebooks
- **Fully typed**: Include type hints for clarity
- **Well-commented**: Explain the "why" not just the "what"
- **Tested**: Validated against Databricks Runtime 15.4+

### Diagrams

- Architecture diagrams use Mermaid format
- Data flow diagrams show the complete path from user to data
- Component diagrams show dependencies and interactions

### Configuration

- All configuration uses environment variables or Unity Catalog secrets
- No hardcoded credentials or workspace URLs
- Supports dev/staging/prod environments via parameterization

## Next Steps

1. **Read [02-Architecture Overview](02-architecture-overview.md)** to understand the system design
2. **Review [05-Genie Integration](05-genie-integration.md)** for the core data access pattern
3. **Follow [12-Implementation Guide](12-implementation-guide.md)** for step-by-step setup

