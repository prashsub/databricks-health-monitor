# Appendix D - Implementation Reference

## Overview

This appendix documents the actual implementation of the agent framework located in `src/agents/`. The implementation follows the official Databricks Lakebase memory patterns and MLflow 3.0 GenAI best practices.

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
│   ├── __init__.py
│   └── registry.py                      # MLflow prompt versioning
│
├── evaluation/
│   ├── __init__.py
│   ├── judges.py                        # Custom LLM scorers
│   └── runner.py                        # Evaluation pipeline
│
└── notebooks/
    ├── setup_lakebase.py                # Lakebase initialization
    ├── register_prompts.py              # Prompt registration
    ├── log_agent.py                     # Model Registry logging
    └── run_evaluation.py                # Quality evaluation

resources/agents/
└── agent_deployment.yml                 # Databricks Asset Bundle configuration
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
# Genie Space IDs (required)
COST_GENIE_SPACE_ID=<your-cost-genie-space-id>
SECURITY_GENIE_SPACE_ID=<your-security-genie-space-id>
PERFORMANCE_GENIE_SPACE_ID=<your-performance-genie-space-id>
RELIABILITY_GENIE_SPACE_ID=<your-reliability-genie-space-id>
QUALITY_GENIE_SPACE_ID=<your-quality-genie-space-id>

# Lakebase (defaults provided)
LAKEBASE_INSTANCE_NAME=health_monitor_memory

# LLM Endpoints (defaults provided)
LLM_ENDPOINT=databricks-meta-llama-3-3-70b-instruct
EMBEDDING_ENDPOINT=databricks-gte-large-en

# Utility Tools (optional)
TAVILY_API_KEY=<your-tavily-api-key>
```

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
| 03-Orchestrator Agent | `src/agents/orchestrator/agent.py`, `graph.py` |
| 04-Worker Agents | `src/agents/workers/*.py` |
| 05-Genie Integration | `src/agents/tools/genie_tool.py`, `workers/base.py` |
| 06-Utility Tools | `src/agents/tools/web_search.py`, `dashboard_linker.py` |
| 07-Memory Management | `src/agents/memory/short_term.py`, `long_term.py` |
| 08-MLflow Tracing | `src/agents/__init__.py` (autolog), `@mlflow.trace` decorators |
| 09-Evaluation and Judges | `src/agents/evaluation/judges.py`, `runner.py` |
| 10-Prompt Registry | `src/agents/prompts/registry.py` |
| 11-Agent Logging | `src/agents/notebooks/log_agent.py` |
| 13-Deployment | `resources/agents/agent_deployment.yml` |

## Next Steps for Production

1. **Configure Genie Space IDs**: Update environment variables with actual Genie Space IDs from Phase 3.6
2. **Run Lakebase Setup**: Execute `notebooks/setup_lakebase.py` to initialize memory tables
3. **Register Prompts**: Execute `notebooks/register_prompts.py` to version prompts
4. **Log Agent**: Execute `notebooks/log_agent.py` to register in Model Registry
5. **Deploy Endpoint**: Use Asset Bundle to deploy Model Serving endpoint
6. **Run Evaluation**: Execute `notebooks/run_evaluation.py` to validate quality
