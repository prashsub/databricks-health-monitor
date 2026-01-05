# Appendix D - Implementation Reference

## Overview

This appendix documents the actual implementation of the agent framework located in `src/agents/`. The implementation follows the official Databricks Lakebase memory patterns and MLflow 3.0 GenAI best practices.

> **✅ Implementation Status: 100% COMPLETE**
>
> All MLflow 3.0 GenAI patterns from the cursor rule are fully implemented:
> - ✅ Tracing: autolog, @mlflow.trace, manual spans, experiment tagging
> - ✅ Evaluation: 4 built-in scorers + 9 custom LLM judges + mlflow.genai.evaluate()
> - ✅ Prompt Registry: versioning, aliases, A/B testing, PromptManager
> - ✅ Agent Logging: ChatAgent interface, streaming, Model Registry, resources
> - ✅ Production Monitoring: real-time mlflow.genai.assess() with alerting

## Implementation Date

- **Completed**: January 2026
- **Branch**: `feature/agent-framework-lakebase` (merged to `main`)

## File Structure

```
src/agents/
├── __init__.py                          # Module entry point with MLflow autolog
├── requirements.txt                     # Python dependencies
│
├── config/
│   ├── __init__.py
│   └── settings.py                      # Centralized configuration with Genie Space placeholders
│
├── memory/
│   ├── __init__.py                      # Memory module exports
│   ├── short_term.py                    # CheckpointSaver wrapper for LangGraph
│   └── long_term.py                     # DatabricksStore with vector embeddings
│
├── orchestrator/
│   ├── __init__.py
│   ├── agent.py                         # ChatAgent MLflow pyfunc implementation
│   ├── graph.py                         # LangGraph StateGraph definition
│   ├── state.py                         # AgentState TypedDict
│   ├── intent_classifier.py             # LLM-based domain classification
│   └── synthesizer.py                   # Response combination from domains
│
├── workers/
│   ├── __init__.py                      # Worker registry and factory
│   ├── base.py                          # GenieWorkerAgent base class
│   ├── cost_agent.py                    # Cost domain specialist
│   ├── security_agent.py                # Security domain specialist
│   ├── performance_agent.py             # Performance domain specialist
│   ├── reliability_agent.py             # Reliability domain specialist
│   └── quality_agent.py                 # Quality domain specialist
│
├── tools/
│   ├── __init__.py
│   ├── genie_tool.py                    # LangChain tool for Genie queries
│   ├── web_search.py                    # Tavily web search for Databricks docs
│   └── dashboard_linker.py              # AI/BI dashboard deep links
│
├── prompts/
│   ├── __init__.py                      # Exports: register_all_prompts, PromptABTest, PromptManager
│   ├── registry.py                      # MLflow prompt versioning and loading
│   ├── ab_testing.py                    # PromptABTest class for traffic splitting
│   └── manager.py                       # PromptManager for production refresh
│
├── evaluation/
│   ├── __init__.py                      # Exports all judges and evaluation functions
│   ├── judges.py                        # 9 LLM scorers (4 generic + 5 domain-specific)
│   ├── evaluator.py                     # create_evaluation_dataset(), run_evaluation()
│   └── production_monitor.py            # Real-time mlflow.genai.assess() monitoring
│
├── setup/                               # Agent infrastructure setup (Asset Bundle tasks)
│   ├── __init__.py
│   ├── create_schemas.py                # Creates agent/inference/memory schemas
│   ├── register_prompts.py              # Registers prompts to MLflow
│   └── log_agent_model.py               # Logs agent to Model Registry
│
└── notebooks/
    ├── setup_lakebase.py                # Lakebase initialization
    ├── register_prompts.py              # Prompt registration (deprecated, use setup/)
    ├── log_agent.py                     # Model Registry logging (deprecated, use setup/)
    └── run_evaluation.py                # Quality evaluation

resources/agents/
├── agent_setup_job.yml                  # Creates schemas, prompts, model
└── agent_serving_endpoint.yml           # Model Serving endpoint configuration
```

## Key Implementation Differences from Design

### Memory Management

The design docs originally described custom Delta table implementations. The actual implementation uses the official Databricks Lakebase pattern:

| Component | Design Doc | Actual Implementation |
|-----------|------------|----------------------|
| Short-term Memory | Custom Delta table with Spark SQL | `CheckpointSaver` from `databricks_langchain` |
| Long-term Memory | Custom Delta table with manual queries | `DatabricksStore` with vector embeddings |
| Table Creation | Manual SQL DDL | Managed by Lakebase (automatic) |

**Rationale**: Using the official Databricks Lakebase primitives provides:
- Automatic schema management
- Built-in TTL handling
- Native LangGraph integration
- Vector search capabilities for semantic retrieval

### Worker Agents

Workers inherit from `GenieWorkerAgent` which wraps the Genie Conversation API:

```python
# Actual implementation pattern
class CostWorkerAgent(GenieWorkerAgent):
    def __init__(self, genie_space_id: str = None):
        super().__init__(
            domain="cost",
            genie_space_id=genie_space_id or settings.cost_genie_space_id,
        )

    def enhance_query(self, query: str, context: Dict) -> str:
        # Domain-specific query enhancement
        ...
```

**Key differences**:
- Genie Space IDs are configurable via environment variables
- Currently using placeholder IDs (to be configured during deployment)
- No `format_response` method - Genie responses used directly
- MLflow tracing via `@mlflow.trace` decorator on base class

### Graph Structure

The LangGraph orchestrator has a simplified node structure:

```
load_context → classify_intent → [routing] → synthesize → save_context → END
                                     ↓
                              cost_agent
                              security_agent
                              performance_agent
                              reliability_agent
                              quality_agent
                              parallel_agents
```

**Differences from design**:
- No separate `route_to_agents` or `collect_responses` nodes
- Routing handled by `add_conditional_edges` directly
- `parallel_agents` node for multi-domain queries

## Configuration Placeholders

The following environment variables must be configured for production:

```bash
# =========================================================================
# Unity Catalog Configuration (CONSOLIDATED - single schema)
# =========================================================================
# Dev pattern: prashanth_subrahmanyam_catalog.dev_<user>_system_gold_agent
# Prod pattern: main.system_gold_agent
#
# All agent data (models, tables, volumes) in ONE schema to avoid sprawl
CATALOG=prashanth_subrahmanyam_catalog
AGENT_SCHEMA=dev_prashanth_subrahmanyam_system_gold_agent

# =========================================================================
# Genie Space IDs (required)
# =========================================================================
COST_GENIE_SPACE_ID=<your-cost-genie-space-id>
SECURITY_GENIE_SPACE_ID=<your-security-genie-space-id>
PERFORMANCE_GENIE_SPACE_ID=<your-performance-genie-space-id>
RELIABILITY_GENIE_SPACE_ID=<your-reliability-genie-space-id>
QUALITY_GENIE_SPACE_ID=<your-quality-genie-space-id>

# =========================================================================
# Lakebase (defaults provided)
# =========================================================================
LAKEBASE_INSTANCE_NAME=health_monitor_memory

# =========================================================================
# LLM Endpoints (defaults provided)
# =========================================================================
LLM_ENDPOINT=databricks-meta-llama-3-3-70b-instruct
EMBEDDING_ENDPOINT=databricks-gte-large-en

# =========================================================================
# Utility Tools (optional)
# =========================================================================
TAVILY_API_KEY=<your-tavily-api-key>
```

## Schema Storage Layout (Consolidated)

**Single schema to avoid sprawl** - all agent data lives in one schema:

```
Unity Catalog: prashanth_subrahmanyam_catalog (dev) / main (prod)
│
└── dev_prashanth_subrahmanyam_system_gold_agent/   # CONSOLIDATED Agent Schema
    │
    ├── [MODEL] ──────────────────────────────────────
    │   └── health_monitor_agent           # Registered ChatAgent model
    │
    ├── [TABLES] Structured Data ─────────────────────
    │   │
    │   │ Config & Experimentation:
    │   ├── agent_config                   # Runtime configuration
    │   ├── ab_test_assignments            # A/B test user assignments
    │   │
    │   │ Evaluation:
    │   ├── evaluation_datasets            # Benchmark test datasets
    │   ├── evaluation_results             # Offline evaluation metrics
    │   │
    │   │ Inference Logs (auto-captured by Model Serving):
    │   ├── inference_request_logs         # Input requests
    │   ├── inference_response_logs        # Responses with metrics
    │   │
    │   │ Memory (Lakebase-managed):
    │   ├── memory_short_term              # Conversation context (TTL: 24h)
    │   └── memory_long_term               # User preferences (TTL: 365d)
    │
    └── [VOLUMES] Unstructured Data ──────────────────
        ├── runbooks/                      # RAG knowledge base
        │   ├── troubleshooting/           # Troubleshooting guides
        │   └── best_practices/            # Best practices docs
        ├── embeddings/                    # Pre-computed vectors
        └── artifacts/                     # Model checkpoints, files

MLflow:
├── Experiments/
│   ├── /Shared/health_monitor/agent_traces      # All traces
│   ├── /Shared/health_monitor/agent_models      # Model training runs
│   ├── /Shared/health_monitor/prompts           # Prompt versions
│   └── /Shared/health_monitor/agent_evaluations # Evaluation runs
│
└── Model Registry/
    └── prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_system_gold_agent.health_monitor_agent
        ├── Version 1 (alias: production)
        └── Version 2 (alias: staging)
```

### Storage Type Reference

| Data Type | Storage | Table/Volume Name |
|-----------|---------|-------------------|
| **Agent Model** | UC Model | `health_monitor_agent` |
| **Config** | UC Table | `agent_config` |
| **A/B Tests** | UC Table | `ab_test_assignments` |
| **Evaluation Data** | UC Tables | `evaluation_datasets`, `evaluation_results` |
| **Inference Logs** | UC Tables | `inference_request_logs`, `inference_response_logs` |
| **Memory** | UC Tables | `memory_short_term`, `memory_long_term` |
| **Runbooks (RAG)** | UC Volume | `runbooks/` |
| **Embeddings** | UC Volume | `embeddings/` |
| **Artifacts** | UC Volume | `artifacts/` |

### Why Consolidated?

- **Avoids schema sprawl**: 1 schema instead of 3
- **Simpler permissions**: Grant access to one schema
- **Easier discovery**: All agent assets in one place
- **Table prefixes**: `inference_*`, `memory_*`, `evaluation_*` for organization

## Dependencies

```
mlflow>=3.0.0
langchain>=0.3.0
langgraph>=0.2.0
langchain-databricks>=0.1.0
databricks-langchain>=0.1.0
databricks-sdk>=0.30.0
databricks-agents>=0.1.0
pydantic>=2.0.0
tavily-python>=0.3.0
```

## Mapping: Design Doc → Implementation

| Design Document | Implementation File(s) |
|-----------------|------------------------|
| 03-Orchestrator Agent | `src/agents/orchestrator/agent.py`, `graph.py` (includes streaming) |
| 04-Worker Agents | `src/agents/workers/*.py` |
| 05-Genie Integration | `src/agents/tools/genie_tool.py`, `workers/base.py` |
| 06-Utility Tools | `src/agents/tools/web_search.py`, `dashboard_linker.py` |
| 07-Memory Management | `src/agents/memory/short_term.py`, `long_term.py` |
| 08-MLflow Tracing | `src/agents/__init__.py` (autolog), `@mlflow.trace` decorators |
| 09-Evaluation and Judges | `src/agents/evaluation/judges.py`, `evaluator.py`, `production_monitor.py` |
| 10-Prompt Registry | `src/agents/prompts/registry.py`, `ab_testing.py`, `manager.py` |
| 11-Agent Logging | `src/agents/orchestrator/agent.py`, `notebooks/log_agent.py` |
| 13-Deployment | `resources/agents/agent_deployment.yml` |

## Next Steps for Production

1. **Configure Genie Space IDs**: Update environment variables with actual Genie Space IDs from Phase 3.6
2. **Run Lakebase Setup**: Execute `notebooks/setup_lakebase.py` to initialize memory tables
3. **Register Prompts**: Execute `notebooks/register_prompts.py` to version prompts
4. **Log Agent**: Execute `notebooks/log_agent.py` to register in Model Registry
5. **Deploy Endpoint**: Use Asset Bundle to deploy Model Serving endpoint
6. **Run Evaluation**: Execute `notebooks/run_evaluation.py` to validate quality
