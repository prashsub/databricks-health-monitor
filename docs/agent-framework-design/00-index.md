# Agent Framework Design Documentation

## Overview

This documentation suite provides comprehensive architecture and implementation guidance for the **Databricks Health Monitor Multi-Agent System**. The system uses a custom multi-agent supervisor with Genie Spaces as the sole data interface, showcasing 14 Databricks and MLflow best practices.

> **✅ Implementation Status: 100% COMPLETE**
>
> The agent framework has been fully implemented in `src/agents/` with:
> - ✅ MLflow 3.0 Tracing (autolog, @mlflow.trace, manual spans)
> - ✅ MLflow 3.0 Evaluation (4 built-in scorers + 9 custom LLM judges)
> - ✅ MLflow 3.0 Prompt Registry (versioning, aliases, A/B testing, PromptManager)
> - ✅ MLflow 3.0 Agent Logging (ChatAgent interface, streaming, Model Registry)
> - ✅ Production Monitoring (real-time `mlflow.genai.assess()`)
>
> See [Appendix D: Implementation Reference](appendices/D-implementation-reference.md) for the complete file structure.

## Architecture Principle

> **Agents NEVER call TVFs, Metric Views, or ML tables directly.**
> All data queries flow through Genie Spaces, which internally route to the appropriate data assets.

## Document Index

| # | Document | Description |
|---|----------|-------------|
| 01 | [Introduction](01-introduction.md) | Purpose, scope, prerequisites, best practices matrix |
| 02 | [Architecture Overview](02-architecture-overview.md) | System architecture, data flows, technology stack |
| 03 | [Orchestrator Agent](03-orchestrator-agent.md) | Supervisor agent design with LangGraph |
| 04 | [Worker Agents](04-worker-agents.md) | Domain specialist agents (Cost, Security, Performance, Reliability, Quality) |
| 05 | [Genie Integration](05-genie-integration.md) | Genie as sole data interface, Conversation API |
| 06 | [Utility Tools](06-utility-tools.md) | Web search, dashboard linker, alert trigger, runbook RAG |
| 07 | [Memory Management](07-memory-management.md) | Lakebase short-term and long-term memory |
| 08 | [MLflow Tracing](08-mlflow-tracing.md) | MLflow 3.0 tracing instrumentation |
| 09 | [Evaluation and Judges](09-evaluation-and-judges.md) | LLM judges and quality scoring |
| 10 | [Prompt Registry](10-prompt-registry.md) | Prompt version management |
| 11 | [Agent Logging](11-agent-logging.md) | Agent registration and Model Registry |
| 12 | [Implementation Guide](12-implementation-guide.md) | Step-by-step implementation phases |
| 13 | [Deployment and Monitoring](13-deployment-and-monitoring.md) | Production deployment and observability |

## Appendices

| # | Document | Description |
|---|----------|-------------|
| A | [Code Examples](appendices/A-code-examples.md) | Complete working code snippets |
| B | [MLflow Cursor Rule](appendices/B-mlflow-cursor-rule.md) | Cursor rule for MLflow GenAI patterns |
| C | [References](appendices/C-references.md) | Official documentation links |
| D | [Implementation Reference](appendices/D-implementation-reference.md) | Actual implementation file structure |

## Tool Architecture Summary

```
AGENT TOOLS (10 Total)
├── GENIE SPACE TOOLS (6) - All Data Queries
│   ├── cost_genie           # 15 TVFs, 2 Metrics, 6 ML Models
│   ├── security_genie       # 10 TVFs, 2 Metrics, 4 ML Models
│   ├── performance_genie    # 16 TVFs, 3 Metrics, 7 ML Models
│   ├── reliability_genie    # 12 TVFs, 1 Metric, 5 ML Models
│   ├── quality_genie        # 7 TVFs, 2 Metrics, 3 ML Models
│   └── unified_genie        # Cross-domain queries for orchestrator
│
└── UTILITY TOOLS (4) - Actions and External Data
    ├── web_search           # Databricks status, docs, real-time info
    ├── dashboard_linker     # Deep links to 11 AI/BI dashboards
    ├── alert_trigger        # Trigger SQL alerts (framework to build)
    └── runbook_rag          # Vector search over remediation docs
```

## Quick Start

1. **Understand the Architecture**: Start with [02-architecture-overview.md](02-architecture-overview.md)
2. **Set Up Environment**: Follow [12-implementation-guide.md](12-implementation-guide.md) Phase 1
3. **Build Orchestrator**: Follow [03-orchestrator-agent.md](03-orchestrator-agent.md)
4. **Integrate MLflow**: Follow [08-mlflow-tracing.md](08-mlflow-tracing.md)
5. **Deploy**: Follow [13-deployment-and-monitoring.md](13-deployment-and-monitoring.md)

## Best Practices Showcased

| # | Best Practice | Implementation |
|---|---------------|----------------|
| 1 | Multi-Agent Architecture | LangGraph supervisor + domain workers |
| 2 | Genie Space Integration | 6 domain-specific Genie Spaces |
| 3 | MLflow 3.0 Tracing | Automatic + manual instrumentation (✅ 100%) |
| 4 | LLM Judges | Built-in scorers + 9 custom judges (4 generic + 5 domain) |
| 5 | Prompt Registry | Versioned prompts with aliases, A/B testing, PromptManager |
| 6 | Agent Logging | ChatAgent class + Model Registry + streaming (✅ 100%) |
| 7 | Lakebase Memory | Short-term (24h) + Long-term (1yr) |
| 8 | Model Serving | Serverless endpoint deployment |
| 9 | On-behalf-of-user Auth | Genie respects user permissions |
| 10 | Production Monitoring | Real-time quality monitoring with `mlflow.genai.assess()` |
| 11 | Evaluation Pipeline | Built-in scorers + `mlflow.genai.evaluate()` runner |
| 12 | Unity Catalog Governance | Data assets via Genie only |
| 13 | MCP Integration | Model Context Protocol ready |
| 14 | Databricks Apps Frontend | Streamlit chat interface |

## Related Documentation

- [Phase 4: Agent Framework Plan](../../plans/phase4-agent-framework.md)
- [Phase 3.6: Genie Spaces](../../plans/phase3-addendum-3.6-genie-spaces.md)
- [MLflow GenAI Cursor Rule](../../.cursor/rules/ml/28-mlflow-genai-patterns.mdc)

