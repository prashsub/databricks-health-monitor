# Health Monitor Agent - Actual Implementation Guide

## 📚 Training Guide Overview

This folder contains **detailed implementation documentation** for the Databricks Health Monitor Multi-Agent System. Unlike the design documents, this guide shows **exactly how the code works** with code references, file paths, and step-by-step explanations.

**Use this guide to:**
- Understand how each component is implemented
- Find the exact file and line number for any feature
- Learn the patterns and best practices used
- Onboard new team members quickly
- Debug and extend the system

---

## 🗺️ Document Map

| Document | Purpose | Key Topics |
|----------|---------|------------|
| [01-architecture-deep-dive.md](./01-architecture-deep-dive.md) | System architecture with code paths | Module structure, data flow, dependencies |
| [02-core-agent-implementation.md](./02-core-agent-implementation.md) | Main agent class | ChatAgent interface, predict methods, MLflow resources |
| [03-langgraph-orchestration.md](./03-langgraph-orchestration.md) | State machine & graph | Nodes, edges, routing, state management |
| [04-worker-agents-and-genie.md](./04-worker-agents-and-genie.md) | Domain workers | GenieAgent integration, query enhancement |
| [05-memory-system.md](./05-memory-system.md) | Memory management | CheckpointSaver, DatabricksStore, Lakebase |
| [06-tracing-and-observability.md](./06-tracing-and-observability.md) | MLflow tracing | Spans, tags, autolog, trace hierarchy, **prompt-trace linking** |
| [07-configuration-management.md](./07-configuration-management.md) | Settings & config | Genie spaces, environment variables |
| [08-evaluation-and-quality.md](./08-evaluation-and-quality.md) | Quality assurance | Scorers, judges, **synthetic evaluation datasets**, production monitoring |
| [09-deployment-pipeline.md](./09-deployment-pipeline.md) | Deployment workflow | Setup jobs, Model Serving, promotion, **deployment job connection** |
| [10-prompt-management.md](./10-prompt-management.md) | **MLflow Prompt Registry** | `register_prompt()`, aliases, trace linking, versioning |
| [10-experiment-structure.md](./10-experiment-structure.md) | **MLflow Experiment Organization** | Three experiments, run naming, tags, separation of concerns |

---

## 🏗️ Implementation Directory Structure

```
src/agents/
├── __init__.py                    # Module entry, autolog setup
├── requirements.txt               # Python dependencies
│
├── config/                        # ⚙️ Configuration
│   ├── __init__.py
│   ├── settings.py               # Centralized settings (imports from genie_spaces)
│   └── genie_spaces.py           # Single source of truth for Genie IDs + routing
│
├── orchestrator/                  # 🎯 Core Agent (LangGraph)
│   ├── __init__.py
│   ├── agent.py                  # HealthMonitorAgent (ChatAgent interface)
│   ├── graph.py                  # LangGraph StateGraph definition
│   ├── state.py                  # AgentState TypedDict
│   ├── intent_classifier.py      # LLM-based intent classification
│   └── synthesizer.py            # Response synthesis
│
├── workers/                       # 👷 Domain Workers
│   ├── __init__.py
│   ├── base.py                   # BaseWorkerAgent, GenieWorkerAgent
│   ├── cost_agent.py             # Cost domain worker
│   ├── security_agent.py         # Security domain worker
│   ├── performance_agent.py      # Performance domain worker
│   ├── reliability_agent.py      # Reliability domain worker
│   └── quality_agent.py          # Quality domain worker
│
├── tools/                         # 🔧 LangChain Tools
│   ├── __init__.py
│   ├── genie_tool.py             # GenieTool (GenieAgent wrapper)
│   ├── web_search.py             # Tavily web search tool
│   └── runbook_search.py         # Vector search for runbooks
│
├── memory/                        # 🧠 Memory Management
│   ├── __init__.py
│   ├── short_term.py             # CheckpointSaver (conversation state)
│   └── long_term.py              # DatabricksStore (user preferences)
│
├── prompts/                       # 📝 Prompt Templates
│   ├── __init__.py
│   ├── orchestrator.py           # Main orchestrator prompts
│   ├── workers.py                # Domain worker prompts
│   ├── ab_testing.py             # A/B testing for prompts
│   └── manager.py                # PromptManager class
│
├── evaluation/                    # 📊 Evaluation & Monitoring
│   ├── __init__.py
│   ├── evaluator.py              # run_full_evaluation()
│   ├── judges.py                 # Custom LLM judges
│   ├── runner.py                 # Evaluation runner
│   ├── synthesize_dataset.py    # 🆕 Synthetic dataset generation
│   └── production_monitor.py     # Real-time monitoring
│
├── monitoring/                    # 📈 Production Monitoring
│   └── production_monitor.py     # assess() integration
│
├── setup/                         # 🚀 Deployment Scripts
│   ├── create_schemas.py         # UC schema/table creation
│   ├── register_prompts.py       # Prompt registry logging
│   ├── register_scorers.py       # 🆕 Production monitoring scorers
│   ├── create_evaluation_dataset.py # 🆕 Synthetic & manual datasets
│   ├── log_agent_model.py        # Model logging to UC
│   ├── run_evaluation.py         # Evaluation pipeline
│   └── deployment_job.py         # MLflow deployment job + endpoint
│
└── notebooks/                     # 📓 Alternative Notebooks
    ├── log_agent.py
    ├── run_evaluation.py
    └── register_prompts.py
```

---

## 🔑 Key Implementation Patterns

### 1. **Single Source of Truth**

Configuration is centralized to avoid duplication:

```
genie_spaces.py  ← Single source for all Genie Space config
    │
    ├── settings.py (delegates via @property)
    │
    └── All other modules import from settings
```

### 2. **Lazy Initialization**

Heavy resources are initialized on first use:

```python
@property
def graph(self):
    if self._graph is None:
        self._graph = create_orchestrator_graph().compile(...)
    return self._graph
```

### 3. **MLflow Tracing Everywhere**

Every significant operation is traced:

```python
@mlflow.trace(name="classify_intent", span_type="CLASSIFIER")
def classify_intent(state: AgentState) -> Dict:
    ...
```

### 4. **GenieAgent Integration**

All data access flows through GenieAgent:

```python
# Primary import (databricks-agents >= 0.16.0)
try:
    from databricks.agents.genie import GenieAgent
except ImportError:
    from databricks_langchain.genie import GenieAgent

genie = GenieAgent(
    genie_space_id=space_id,
    genie_agent_name=f"{domain}_genie",
)
```

### 5. **Databricks SDK for LLM Calls**

All LLM calls in scorers and utilities use Databricks SDK for reliable authentication:

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

def _call_llm(prompt: str) -> dict:
    w = WorkspaceClient()  # Automatic auth in notebooks
    response = w.serving_endpoints.query(
        name="databricks-claude-3-7-sonnet",
        messages=[ChatMessage(role=ChatMessageRole.USER, content=prompt)],
        temperature=0
    )
    return json.loads(response.choices[0].message.content)
```

**Why Databricks SDK over langchain-databricks?**
- ✅ Automatic authentication in notebooks
- ✅ No package installation issues on serverless compute
- ✅ More reliable in deployment jobs
- ✅ Direct SDK support from Databricks

### 5. **Separated MLflow Experiments**

Runs are organized into three experiments by purpose:

```python
# Three experiments for clean organization
EXPERIMENT_DEVELOPMENT = "/Shared/health_monitor_agent_development"  # Model logging
EXPERIMENT_EVALUATION = "/Shared/health_monitor_agent_evaluation"    # Evaluations
EXPERIMENT_DEPLOYMENT = "/Shared/health_monitor_agent_deployment"    # Pre-deploy validation

# Standard tags for every run
mlflow.set_tags({
    "domain": "all",
    "agent_version": "v4.0",
    "dataset_type": "evaluation",
    "evaluation_type": "comprehensive",
})
```

See [10-experiment-structure.md](./10-experiment-structure.md) for details.

### 6. **MLflow Prompt Registry**

Prompts are registered to MLflow for version control and trace linking:

```python
# Register prompt (in setup job)
mlflow.genai.register_prompt(
    name=f"{catalog}.{schema}.prompt_orchestrator",
    template="You are the orchestrator..."
)

# Load in traced function (creates prompt-trace link)
@mlflow.trace
def predict(query):
    prompt = mlflow.genai.load_prompt(
        "prompts:/catalog.schema.prompt_orchestrator@production"
    )
    # Use prompt...
```

---

## 🎓 Learning Path

### Beginner (New to the codebase)

1. Start with [01-architecture-deep-dive.md](./01-architecture-deep-dive.md)
2. Read [02-core-agent-implementation.md](./02-core-agent-implementation.md)
3. Review [07-configuration-management.md](./07-configuration-management.md)

### Intermediate (Extending the agent)

1. Deep dive into [03-langgraph-orchestration.md](./03-langgraph-orchestration.md)
2. Learn [04-worker-agents-and-genie.md](./04-worker-agents-and-genie.md)
3. Understand [05-memory-system.md](./05-memory-system.md)

### Advanced (Production operations)

1. Master [06-tracing-and-observability.md](./06-tracing-and-observability.md)
2. Study [08-evaluation-and-quality.md](./08-evaluation-and-quality.md)
3. Learn [10-prompt-management.md](./10-prompt-management.md)
4. Follow [09-deployment-pipeline.md](./09-deployment-pipeline.md)

---

## 🔗 Quick Links

### Code Entry Points

| What | File | Line |
|------|------|------|
| Main Agent Class | `src/agents/orchestrator/agent.py` | Line 50 |
| LangGraph Definition | `src/agents/orchestrator/graph.py` | Line 1 |
| Genie Space Config | `src/agents/config/genie_spaces.py` | Line 48 |
| Settings | `src/agents/config/settings.py` | Line 21 |
| Model Logging | `src/agents/setup/log_agent_model.py` | Line 255 |

### Key Classes

| Class | Purpose | File |
|-------|---------|------|
| `HealthMonitorAgent` | Main agent (ChatAgent) | `orchestrator/agent.py` |
| `AgentState` | Graph state TypedDict | `orchestrator/state.py` |
| `IntentClassifier` | Query classification | `orchestrator/intent_classifier.py` |
| `GenieWorkerAgent` | Domain worker base | `workers/base.py` |
| `GenieTool` | LangChain tool wrapper | `tools/genie_tool.py` |
| `ShortTermMemory` | Conversation state | `memory/short_term.py` |
| `LongTermMemory` | User preferences | `memory/long_term.py` |

### Databricks Jobs

| Job | Purpose | YAML |
|-----|---------|------|
| `agent_setup_job` | Full setup pipeline | `resources/agents/agent_setup_job.yml` |
| `agent_deployment_job` | Evaluation & promotion | `resources/agents/agent_deployment_job.yml` |

---

## 📅 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Jan 2026 | System | Initial comprehensive documentation |
| 1.1.0 | Jan 7, 2026 | System | Added 10-prompt-management.md for MLflow Prompt Registry patterns |
| 1.2.0 | Jan 7, 2026 | System | **Major update**: Migrated from `langchain_databricks` to Databricks SDK for LLM calls in scorers. Updated 08-evaluation-and-quality.md with official `@scorer` decorator pattern and `Feedback` return type. Updated 04-worker-agents-and-genie.md with correct `databricks.agents.genie` import priority. Added Databricks SDK pattern documentation to index. |
| 1.3.0 | Jan 7, 2026 | System | **Critical Evaluation Fixes**: (1) Added `_extract_response_text()` helper to handle serialized dict format from `mlflow.genai.evaluate()` - fixes custom scorers returning 0.0. (2) Removed `guidelines/mean` from thresholds - redundant with custom scorers and was blocking deployment. (3) Added `METRIC_ALIASES` documentation for handling different metric naming conventions. (4) Fixed metadata type warning by casting `query_length` to string. See [08-evaluation-and-quality.md](./08-evaluation-and-quality.md) and [09-deployment-pipeline.md](./09-deployment-pipeline.md) for details. |
| 1.4.0 | Jan 8, 2026 | System | **MLflow Experiment Reorganization**: Split single experiment into three purpose-specific experiments (`development`, `evaluation`, `deployment`). Removed run logging from dataset creation and prompt registration. Added standardized run naming (`eval_{domain}_{timestamp}`) and tags (`domain`, `agent_version`, `dataset_type`, `evaluation_type`). See [10-experiment-structure.md](./10-experiment-structure.md). |

---

**Next:** [01-architecture-deep-dive.md](./01-architecture-deep-dive.md)

